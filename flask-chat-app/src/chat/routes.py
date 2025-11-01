from flask import Blueprint, render_template, request, session, redirect
import os
from .utils import prompt_model, fetch_repo_chunks, get_available_models, fetch_document_content

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
                                # Skip binary content (PDFs, images) - only use text-based documents for full context
                                if isinstance(full_content, bytes):
                                    print(f"DEBUG: Skipping binary document {doc_source} for full context (binary content not suitable for LLM)")
                                    continue
                                elif len(full_content) > 500000:  # Skip very large documents that might be binary-as-text
                                    print(f"DEBUG: Skipping very large document {doc_source} ({len(full_content)} chars) - likely binary")
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
            
            if final_context_parts:
                combined_context = "\n\n".join(final_context_parts)
                print(f"DEBUG: Combined context length: {len(combined_context)} chars")
                # Insert context as system message temporarily for this query
                temp_history = [{"role": "system", "content": combined_context}] + session["message_history"]
            else:
                print("DEBUG: No context retrieved from RAG")
                temp_history = session["message_history"]
        else:
            print("DEBUG: RAG not enabled for this query")
            temp_history = session["message_history"]

        # Get response from Ollama
        try:
            # Enhanced system prompt for better structured data analysis
            base_system_prompt = session.get("system_prompt", "You are a helpful assistant.")
            
            # Add CSV analysis instructions if we have full document context
            if 'full_document_context' in locals() and full_document_context:
                system_prompt = base_system_prompt + """

ADDITIONAL INSTRUCTIONS FOR DOCUMENT ANALYSIS:
- When analyzing CSV/tabular data, be systematic and precise
- For row counting: Count each line including header (total rows in file)
- For data record counting: Count data rows only, excluding header
- When given complete documents, use them as the authoritative source
- Double-check your counting by examining the structure carefully
"""
            else:
                system_prompt = base_system_prompt
            

            
            response_text, _ = prompt_model(
                model=model, 
                prompt=prompt, 
                history=temp_history[:-1],  # Exclude the current user message since it's added in prompt_model
                system_prompt=system_prompt
            )
            
            # Add assistant response to permanent history with RAG chunks if available
            assistant_message = {
                "role": "assistant", 
                "content": response_text
            }
            
            # Include RAG chunks if they were used
            if rag_chunks:
                assistant_message["rag_chunks"] = rag_chunks
            
            # Include hybrid analysis information
            if 'full_document_context' in locals() and full_document_context:
                assistant_message["hybrid_analysis"] = True
                assistant_message["analyzed_documents"] = list(set(analyze_documents)) if 'analyze_documents' in locals() else []
                # Store the primary analyzed documents in session for context continuity
                session["last_analyzed_documents"] = list(set(analyze_documents)) if 'analyze_documents' in locals() else []
                
            session["message_history"].append(assistant_message)
            session.modified = True  # Mark session as modified
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            session["message_history"].append({"role": "assistant", "content": error_msg})
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

@chat_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for monitoring services"""
    return {"status": "healthy", "service": "insightchat"}, 200

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
    print(f"DEBUG: Document route called with source: '{source}'")
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
        
        # Determine content type based on file extension
        file_extension = decoded_source.split('.')[-1].lower() if '.' in decoded_source else ''
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