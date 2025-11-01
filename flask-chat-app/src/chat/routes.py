from flask import Blueprint, render_template, request, session, redirect
import os
import io
import zipfile
import xml.etree.ElementTree as ET
from .utils import prompt_model, fetch_repo_chunks, get_available_models, fetch_document_content

def extract_docx_text(docx_content):
    """Extract text content from a DOCX file (which is a ZIP archive)"""
    try:
        # DOCX files are ZIP archives containing XML files
        if isinstance(docx_content, str):
            # If content is a string, it might be base64 encoded
            import base64
            try:
                docx_content = base64.b64decode(docx_content)
            except:
                # If it's not base64, assume it's already bytes
                docx_content = docx_content.encode('utf-8')
        
        # Open the DOCX as a ZIP file
        with zipfile.ZipFile(io.BytesIO(docx_content), 'r') as docx_zip:
            # The main document content is in word/document.xml
            if 'word/document.xml' in docx_zip.namelist():
                document_xml = docx_zip.read('word/document.xml')
                
                # Parse the XML
                root = ET.fromstring(document_xml)
                
                # Extract text from all text nodes
                # The namespace for Word documents
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                
                # Find all text elements
                text_elements = root.findall('.//w:t', ns)
                extracted_text = []
                
                for text_elem in text_elements:
                    if text_elem.text:
                        extracted_text.append(text_elem.text)
                
                # Join all text with spaces and clean up
                full_text = ' '.join(extracted_text)
                
                # Clean up extra whitespace and normalize line breaks
                import re
                full_text = re.sub(r'\s+', ' ', full_text).strip()
                
                return full_text
            else:
                print("DEBUG: word/document.xml not found in DOCX archive")
                return None
                
    except zipfile.BadZipFile:
        print("DEBUG: File is not a valid ZIP/DOCX archive")
        return None
    except ET.ParseError as e:
        print(f"DEBUG: XML parsing error: {e}")
        return None
    except Exception as e:
        print(f"DEBUG: Unexpected error extracting DOCX text: {e}")
        return None

chat_bp = Blueprint('chat', __name__)

@chat_bp.route("/chat", methods=["GET", "POST"])
def chat():
    if request.method == "GET":
        # Initialize session if needed
        if "message_history" not in session:
            session["message_history"] = []
        system_prompt = request.args.get("context", "You are a helpful assistant.")
        session["system_prompt"] = system_prompt
        
        # Get available models from Ollama
        available_models = get_available_models()
        
        # Determine default model from environment or fallback
        default_model = os.getenv("DEFAULT_MODEL", "llama3.2:latest")
        
        # If the default model from env is not available, use first available or fallback
        if available_models:
            available_model_names = [model["name"] for model in available_models]
            if default_model not in available_model_names:
                print(f"DEBUG: DEFAULT_MODEL '{default_model}' not found in available models, using first available")
                default_model = available_models[0]["name"]
        
        current_model = session.get("model", default_model)
        current_use_repo_docs = session.get("use_repo_docs", False)
        
        return render_template("chat.html", 
                             message_history=session["message_history"],
                             available_models=available_models,
                             model=current_model,
                             use_repo_docs=current_use_repo_docs)

    if request.method == "POST":
        # Get form data
        model = request.form.get("model", "llama3.2:latest")
        prompt = request.form.get("prompt", "").strip()
        use_repo_docs = bool(request.form.get("use_repo_docs"))
        
        if not prompt:
            return render_template("chat.html", 
                                 message_history=session.get("message_history", []),
                                 error="Please enter a message")

        # Initialize message history if not exists
        if "message_history" not in session:
            session["message_history"] = []

        # Store model and RAG preference in session
        session["model"] = model
        session["use_repo_docs"] = use_repo_docs

        # Add user message to history
        session["message_history"].append({"role": "user", "content": prompt})

        # Check if we can reuse context from recent conversation
        recent_full_context = None
        recent_analyzed_docs = []
        
        # Look for recent messages with full document analysis
        for msg in reversed(session["message_history"][-3:]):  # Check last 3 messages
            if msg.get("hybrid_analysis") and msg.get("analyzed_documents"):
                recent_analyzed_docs = msg["analyzed_documents"]
                print(f"DEBUG: Found recent full document analysis: {recent_analyzed_docs}")
                # Check if current query might be about the same documents
                query_lower = prompt.lower()
                doc_keywords = ["document", "portfolio", "csv", "file", "data", "rows", "columns"]
                if any(keyword in query_lower for keyword in doc_keywords):
                    print(f"DEBUG: Follow-up query detected, will reuse recent context")
                    # We'll fetch the same documents again but skip RAG search
                    break
        
        # Fetch context from RAG if requested
        context_text = None
        rag_chunks = []
        
        if use_repo_docs:
            k = 5  # Default number of chunks
            rag_api_url = os.getenv("RAG_API_URL")
            print(f"DEBUG: RAG enabled, API URL: {rag_api_url}")  # Debug log
            
            if not rag_api_url:
                print("DEBUG: RAG_API_URL not set in environment variables")
                session["message_history"].append({
                    "role": "assistant", 
                    "content": "⚠️ RAG is enabled but RAG_API_URL environment variable is not set. Please configure it in your .env file."
                })
                session.modified = True
                return render_template("chat.html", 
                                     message_history=session["message_history"],
                                     available_models=get_available_models(),
                                     model=model,
                                     use_repo_docs=use_repo_docs)
            
            # Decide whether to do new RAG search or reuse recent context
            if recent_analyzed_docs:
                print(f"DEBUG: Reusing recent document context instead of new RAG search")
                # Skip RAG search, we'll fetch the same documents directly
                analyze_documents = recent_analyzed_docs
                rag_chunks = []  # No new chunks needed
                context_text = None  # No new RAG context needed
            else:
                # Get both context and chunk data via normal RAG search
                context_text, rag_chunks = fetch_repo_chunks(prompt, k=k, rag_api_url=rag_api_url, return_chunks=True)
                print(f"DEBUG: RAG context retrieved: {bool(context_text)}")  # Debug log
                print(f"DEBUG: RAG chunks retrieved: {len(rag_chunks)}")  # Debug log
            
            # Hybrid approach: Check if any found documents need full-document analysis
            full_document_context = None
            
            # If reusing recent context, analyze_documents is already set
            if not recent_analyzed_docs and rag_chunks:
                analyze_documents = []
                for chunk in rag_chunks:
                    source = chunk.get('metadata', {}).get('source', '')
                    if source.startswith('analyze/'):
                        analyze_documents.append(source)
                        print(f"DEBUG: Found analyze/ document: {source}")
            
            # Fetch full content for analyze/ documents (either new or reused)
            if 'analyze_documents' in locals() and analyze_documents:
                    full_docs = []
                    for doc_source in set(analyze_documents):  # Remove duplicates
                        try:
                            print(f"DEBUG: Fetching full document: {doc_source}")
                            full_content = fetch_document_content(doc_source, rag_api_url)
                            if full_content:
                                # Only use actual complete documents (typically CSVs, text files)
                                # Skip binary content and very large files
                                if isinstance(full_content, bytes):
                                    print(f"DEBUG: Skipping binary document {doc_source} for full context")
                                    continue
                                elif len(full_content) > 300000:  # More realistic limit
                                    # Document too large for context - offer chunked processing
                                    print(f"DEBUG: Document {doc_source} too large ({len(full_content)} chars) - offering chunked processing")
                                    
                                    # Import chunked processing capability
                                    from .document_processor import summarize_large_document, get_processing_recommendation
                                    
                                    # Check if user wants chunked processing (keywords that suggest they want analysis)
                                    analysis_keywords = ['analyze', 'summary', 'summarize', 'overview', 'what', 'how', 'why', 'findings', 'conclusion']
                                    wants_analysis = any(keyword in prompt.lower() for keyword in analysis_keywords)
                                    
                                    if wants_analysis:
                                        print(f"DEBUG: User query suggests document analysis - processing {doc_source} in chunks")
                                        # Process the large document using chunked approach
                                        chunked_result = summarize_large_document(doc_source, full_content, prompt, model)
                                        
                                        if chunked_result["success"]:
                                            # Replace the normal response with the chunked analysis
                                            large_doc_response = f"""📄 **Analyzed Large Document: {doc_source}** ({chunked_result['document_size']:,} characters)

{chunked_result['response']}

---
📊 **Processing Details:**
- Document processed in {chunked_result['total_chunks']} chunks
- Analyzed {chunked_result['chunks_analyzed']} most relevant sections
- {len(chunked_result['relevant_chunks'])} sections found highly relevant

💡 **For deeper analysis**, ask follow-up questions about specific sections or topics."""
                                            
                                            # Store this as a special response that bypasses normal LLM processing
                                            if 'large_doc_responses' not in locals():
                                                large_doc_responses = []
                                            large_doc_responses.append(large_doc_response)
                                        else:
                                            # Fallback to suggestion message
                                            recommendation = get_processing_recommendation(len(full_content), prompt)
                                            large_doc_message = f"""📄 **{doc_source}** - {recommendation}"""
                                            if 'large_docs_info' not in locals():
                                                large_docs_info = []
                                            large_docs_info.append(large_doc_message)
                                    else:
                                        # User didn't ask for analysis - just provide guidance
                                        recommendation = get_processing_recommendation(len(full_content), prompt)
                                        large_doc_message = f"""📄 **{doc_source}** - {recommendation}"""
                                        if 'large_docs_info' not in locals():
                                            large_docs_info = []
                                        large_docs_info.append(large_doc_message)
                                    
                                    continue
                                elif full_content[:100].startswith(('JVBERi', '%PDF', '\x00', 'PK\x03\x04')):
                                    print(f"DEBUG: Skipping binary-encoded document {doc_source}")
                                    continue
                                else:
                                    full_docs.append(f"---\nFull Document: {doc_source}\n{full_content}\n")
                                    print(f"DEBUG: Retrieved full document {doc_source}: {len(full_content)} chars")
                        except Exception as e:
                            print(f"DEBUG: Error fetching full document {doc_source}: {e}")
                    
                    if full_docs:
                        full_document_context = """PRIORITY: Complete documents for comprehensive analysis (use these for accurate counts and detailed analysis):

IMPORTANT INSTRUCTIONS FOR CSV/STRUCTURED DATA ANALYSIS:
- When counting rows, count each line that contains data (including header)
- When counting properties/records, count data rows only (exclude header)  
- When analyzing CSV data, examine the complete structure systematically
- For row counts: Count every line break to get total rows
- For data counts: Count entries excluding the header row

""" + "\n".join(full_docs)
                        print(f"DEBUG: Full document context length: {len(full_document_context)} chars")
            
            # Build final context - prioritize full documents first
            final_context_parts = []
            if full_document_context:
                final_context_parts.append(full_document_context)
            if context_text:
                final_context_parts.append("\n---\nAdditional context from document chunks:\n" + context_text)
            
            # Enhanced system prompt for better structured data analysis
            base_system_prompt = session.get("system_prompt", "You are a helpful assistant.")
            
            # Add CSV analysis instructions if we have full document context
            if 'full_document_context' in locals() and full_document_context:
                enhanced_system_prompt = base_system_prompt + """

ADDITIONAL INSTRUCTIONS FOR DOCUMENT ANALYSIS:
- When analyzing CSV/tabular data, be systematic and precise
- For row counting: Count each line including header (total rows in file)
- For data record counting: Count data rows only, excluding header
- When given complete documents, use them as the authoritative source
- Double-check your counting by examining the structure carefully
"""
            else:
                enhanced_system_prompt = base_system_prompt

            if final_context_parts:
                combined_context = "\n\n".join(final_context_parts)
                print(f"DEBUG: Combined context length: {len(combined_context)} chars")
                
                # Check if context is too large for the model (qwen2.5vl has 128K token limit)
                MAX_CONTEXT_CHARS = 300000  # ~75K tokens, leaving room for other content
                
                if len(combined_context) > MAX_CONTEXT_CHARS:
                    print(f"DEBUG: Context too large ({len(combined_context)} chars), chunking intelligently")
                    
                    # If we have full documents, try to find the most relevant section
                    if full_document_context:
                        # Split the full document context and find relevant section
                        full_doc_lines = full_document_context.split('\n')
                        
                        # Look for query-relevant content
                        if prompt:
                            query_words = prompt.lower().split()
                            scored_sections = []
                            
                            # Score sections by query relevance
                            current_section = []
                            current_score = 0
                            lines_per_section = 1000  # ~50KB per section
                            
                            for i, line in enumerate(full_doc_lines):
                                current_section.append(line)
                                line_lower = line.lower()
                                current_score += sum(1 for word in query_words if word in line_lower)
                                
                                if len(current_section) >= lines_per_section or i == len(full_doc_lines) - 1:
                                    section_text = '\n'.join(current_section)
                                    scored_sections.append((current_score, section_text))
                                    current_section = []
                                    current_score = 0
                            
                            # Use the highest-scoring section
                            if scored_sections:
                                best_section = max(scored_sections, key=lambda x: x[0])[1]
                                combined_context = best_section[:MAX_CONTEXT_CHARS]
                                print(f"DEBUG: Using most relevant section ({len(combined_context)} chars)")
                            else:
                                combined_context = combined_context[:MAX_CONTEXT_CHARS]
                                print(f"DEBUG: Using truncated context ({len(combined_context)} chars)")
                        else:
                            # No query, just use the beginning
                            combined_context = combined_context[:MAX_CONTEXT_CHARS]
                            print(f"DEBUG: Using truncated context ({len(combined_context)} chars)")
                    else:
                        # Just truncate
                        combined_context = combined_context[:MAX_CONTEXT_CHARS]
                        print(f"DEBUG: Truncated context to {len(combined_context)} chars")
                
                # Combine the enhanced system prompt with the (potentially truncated) context
                full_system_message = enhanced_system_prompt + "\n\n" + combined_context
                print(f"DEBUG: Full system message length: {len(full_system_message)} chars")
                
                # Insert combined system message temporarily for this query
                temp_history = [{"role": "system", "content": full_system_message}] + session["message_history"]
            else:
                print("DEBUG: No context retrieved from RAG")
                temp_history = session["message_history"]
        else:
            print("DEBUG: RAG not enabled for this query")
            temp_history = session["message_history"]
            enhanced_system_prompt = session.get("system_prompt", "You are a helpful assistant.")

        # Check if we have a complete chunked response that bypasses normal LLM processing
        if 'large_doc_responses' in locals() and large_doc_responses:
            # We have a complete response from chunked processing - use it directly
            final_response = "\n\n".join(large_doc_responses)
            print(f"DEBUG: Using chunked document response ({len(final_response)} chars)")
        else:
            # Normal LLM processing
            
            # Get response from Ollama
            try:
                # Check if we have large document messages to prepend
                response_prefix = ""
                if 'large_docs_info' in locals() and large_docs_info:
                    response_prefix = "\n\n".join(large_docs_info) + "\n\n---\n\n"
            # If we have context, the system message is already in temp_history, so don't pass separate system_prompt
            if final_context_parts:
                print("DEBUG: Using context-enhanced system message from history")
                print("DEBUG: temp_history length:", len(temp_history))
                print("DEBUG: First message in temp_history:", temp_history[0] if temp_history else "None")
                print("DEBUG: System message preview (first 500 chars):", temp_history[0].get('content', '')[:500] if temp_history and temp_history[0].get('role') == 'system' else "No system message found")
                
                response_text, _ = prompt_model(
                    model=model, 
                    prompt=prompt, 
                    history=temp_history[:-1]  # Exclude the current user message since it's added in prompt_model
                    # No system_prompt parameter - it's already in the history
                )
            else:
                print("DEBUG: Using standalone system prompt (no context)")
                response_text, _ = prompt_model(
                    model=model, 
                    prompt=prompt, 
                    history=temp_history[:-1] if temp_history else session["message_history"][:-1],
                    system_prompt=enhanced_system_prompt
                )
            
                # Add assistant response to permanent history with RAG chunks if available
                # Prepend large document info if any
                final_response = response_prefix + response_text if response_prefix else response_text
                
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                final_response = error_msg
                
        # Create assistant message for both chunked and normal responses        
        assistant_message = {
            "role": "assistant", 
            "content": final_response
        }
        
        # Include RAG chunks if they were used (only for normal processing)
        if 'rag_chunks' in locals() and rag_chunks:
            assistant_message["rag_chunks"] = rag_chunks
        
        # Include hybrid analysis information
        if 'full_document_context' in locals() and full_document_context:
            assistant_message["hybrid_analysis"] = True
            assistant_message["analyzed_documents"] = list(set(analyze_documents)) if 'analyze_documents' in locals() else []
            # Store the primary analyzed documents in session for context continuity
            session["last_analyzed_documents"] = list(set(analyze_documents)) if 'analyze_documents' in locals() else []
        
        # Mark if this was a chunked processing response
        if 'large_doc_responses' in locals() and large_doc_responses:
            assistant_message["chunked_processing"] = True
            
        session["message_history"].append(assistant_message)
        session.modified = True  # Mark session as modified
            session.modified = True

        # Get available models for the template
        available_models = get_available_models()
        
        return render_template("chat.html", 
                             message_history=session["message_history"],
                             available_models=available_models,
                             model=model,
                             use_repo_docs=use_repo_docs)

@chat_bp.route("/reset", methods=["POST"])
def reset():
    session.clear()
    return redirect("/chat")

@chat_bp.route("/test", methods=["GET"])
def test_route():
    """Test route to verify blueprint registration"""
    print("TEST ROUTE HIT!")
    return "Test route working", 200

@chat_bp.route("/document", methods=["GET"])
def get_document():
    """Serve document content for the document viewer"""
    print("="*50)
    print("DOCUMENT ROUTE HIT!")
    print("="*50)
    
    from flask import jsonify
    from .utils import fetch_document_content
    
    source = request.args.get("source")
    format_param = request.args.get("format")  # Check for format=text parameter
    print(f"DEBUG: Document route called with source: '{source}', format: '{format_param}'")
    print(f"DEBUG: All request args: {dict(request.args)}")
    
    if not source:
        print("DEBUG: No source parameter provided")
        return jsonify({"error": "No source specified"}), 400
    
    # URL decode the source to handle any double encoding
    import urllib.parse
    decoded_source = urllib.parse.unquote(source)
    print(f"DEBUG: Decoded source: '{decoded_source}'")
    
    rag_api_url = os.getenv("RAG_API_URL")
    print(f"DEBUG: RAG_API_URL: {rag_api_url}")
    
    if not rag_api_url:
        print("DEBUG: RAG_API_URL not configured")
        return jsonify({"error": "RAG API not configured"}), 503
    
    try:
        print(f"DEBUG: Attempting to fetch document content for: {decoded_source}")
        content = fetch_document_content(decoded_source, rag_api_url)
        print(f"DEBUG: fetch_document_content returned: {type(content)} with length {len(content) if content else 0}")
        
        if content is None:
            print(f"DEBUG: Content is None, returning 404 for {decoded_source}")
            return jsonify({"error": "Document not found or not accessible"}), 404
        
        # Check if this is a DOCX file and text extraction is requested
        file_extension = decoded_source.split('.')[-1].lower() if '.' in decoded_source else ''
        
        if file_extension in ['docx', 'doc'] and format_param == 'text':
            print(f"DEBUG: DOCX text extraction requested for {decoded_source}")
            try:
                # Extract text from DOCX content
                extracted_text = extract_docx_text(content)
                if extracted_text:
                    print(f"DEBUG: Extracted {len(extracted_text)} characters from DOCX")
                    return extracted_text, 200, {'Content-Type': 'text/plain; charset=utf-8'}
                else:
                    print(f"DEBUG: No text extracted from DOCX")
                    return "No readable text found in document", 200, {'Content-Type': 'text/plain; charset=utf-8'}
            except Exception as docx_error:
                print(f"DEBUG: DOCX text extraction failed: {docx_error}")
                return f"Error extracting text from DOCX: {str(docx_error)}", 500, {'Content-Type': 'text/plain; charset=utf-8'}
        
        # Determine content type based on file extension
        content_type_map = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'svg': 'image/svg+xml',
            'bmp': 'image/bmp',
            'pdf': 'application/pdf',
            'json': 'application/json',
            'xml': 'application/xml',
            'html': 'text/html',
            'css': 'text/css',
            'js': 'application/javascript',
        }
        
        content_type = content_type_map.get(file_extension, 'text/plain; charset=utf-8')
        print(f"DEBUG: Using content type: {content_type} for extension: {file_extension}")
        
        # Handle binary vs text content
        if isinstance(content, bytes):
            print(f"DEBUG: Returning binary content ({len(content)} bytes) for {decoded_source}")
            from flask import Response
            return Response(content, 200, {'Content-Type': content_type})
        else:
            print(f"DEBUG: Returning text content ({len(content)} chars) for {decoded_source}")
            return content, 200, {'Content-Type': content_type}
        
    except Exception as e:
        print(f"DEBUG: Exception in document route for {decoded_source}: {type(e).__name__}: {e}")
        import traceback
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500