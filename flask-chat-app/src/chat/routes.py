from flask import Blueprint, render_template, request, session, redirect
import os
import requests
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
                             use_repo_docs=current_use_repo_docs,
                             RAG_API_URL=os.getenv("RAG_API_URL", ""))

    if request.method == "POST":
        # Get form data
        model = request.form.get("model", "llama3.2:latest")
        prompt = request.form.get("prompt", "").strip()
        use_repo_docs = bool(request.form.get("use_repo_docs"))
        
        # Check if there's pre-loaded context from Load Source button
        loaded_context = request.form.get("loaded_context")
        loaded_source_meta = request.form.get("loaded_source_meta")
        
        if not prompt:
            return render_template("chat.html", 
                                 message_history=session.get("message_history", []),
                                 error="Please enter a message",
                                 available_models=get_available_models(),
                                 model=model,
                                 use_repo_docs=use_repo_docs,
                                 RAG_API_URL=os.getenv("RAG_API_URL", ""))

        # Initialize message history if not exists
        if "message_history" not in session:
            session["message_history"] = []

        # Store model and RAG preference in session
        session["model"] = model
        session["use_repo_docs"] = use_repo_docs

        # Add user message to history
        session["message_history"].append({"role": "user", "content": prompt})

        # Clean up session to prevent cookie size issues - be more aggressive
        def cleanup_message_history():
            """Keep only the last 6 messages and aggressively remove metadata to stay under 4KB cookie limit"""
            print(f"DEBUG: Session cleanup - current history length: {len(session['message_history'])}")
            
            # More aggressive message limit
            if len(session["message_history"]) > 6:
                session["message_history"] = session["message_history"][-6:]
                print(f"DEBUG: Trimmed message history to last 6 messages")
            
            # Remove ALL large metadata from ALL messages except the very last one
            for i, msg in enumerate(session["message_history"]):
                if i < len(session["message_history"]) - 1:  # Keep metadata only for the last message
                    if "rag_chunks" in msg:
                        del msg["rag_chunks"]
                        print(f"DEBUG: Removed rag_chunks from message {i}")
                    if "sources" in msg:
                        del msg["sources"] 
                        print(f"DEBUG: Removed sources from message {i}")
                        
            # Calculate approximate session size
            import json
            import sys
            session_str = json.dumps(dict(session), default=str)
            session_size = sys.getsizeof(session_str.encode('utf-8'))
            print(f"DEBUG: Estimated session size after cleanup: {session_size} bytes")
        
        cleanup_message_history()

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
        sources_found = []  # Initialize sources list
        
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
                                     use_repo_docs=use_repo_docs,
                                     RAG_API_URL=os.getenv("RAG_API_URL", ""))
            
            # Check if user has pre-loaded context from Load Source button
            if loaded_context:
                print(f"DEBUG: Using pre-loaded context from Load Source button")
                context_text = loaded_context
                rag_chunks = []  # No need for regular RAG chunks
                
                # Parse source metadata if available
                if loaded_source_meta:
                    import json
                    try:
                        meta = json.loads(loaded_source_meta)
                        source_path = meta.get('source_path', '')
                        context_type = meta.get('context_type', 'unknown')
                        print(f"DEBUG: Loaded context from {source_path} ({context_type})")
                        
                        # Add source info for display
                        if source_path:
                            file_ext = source_path.split('.')[-1].lower() if '.' in source_path else ''
                            is_csv = file_ext == 'csv' or context_type == 'csv_full'
                            sources_found.append({
                                'path': source_path,
                                'filename': source_path.split('/')[-1],
                                'is_csv': is_csv,
                                'file_type': file_ext
                            })
                    except json.JSONDecodeError:
                        print("DEBUG: Could not parse loaded source metadata")
            # Decide whether to do new RAG search or reuse recent context
            elif recent_analyzed_docs:
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
            
            # Collect source information for later loading if user requests it
            if rag_chunks:
                unique_sources = set()
                for chunk in rag_chunks:
                    source = chunk.get('metadata', {}).get('source', '')
                    if source and source not in unique_sources:
                        unique_sources.add(source)
                        # Determine file type for special handling hints
                        file_ext = source.split('.')[-1].lower() if '.' in source else ''
                        is_csv = file_ext == 'csv'
                        sources_found.append({
                            'path': source,
                            'filename': source.split('/')[-1],
                            'is_csv': is_csv,
                            'file_type': file_ext
                        })
                print(f"DEBUG: Found {len(sources_found)} unique sources in chunks")
            
            # Use the RAG context if we have it
            if context_text:
                combined_context = context_text
                print(f"DEBUG: Using RAG chunks context length: {len(combined_context)} chars")
                # Insert context as system message temporarily for this query
                temp_history = [{"role": "system", "content": combined_context}] + session["message_history"]
            else:
                print("DEBUG: No context retrieved from RAG")
                temp_history = session["message_history"]
        else:
            # RAG not enabled - just get available documents for Load button functionality
            rag_api_url = os.getenv("RAG_API_URL")
            if rag_api_url:
                try:
                    # Get available documents list
                    response = requests.get(f"{rag_api_url}/documents")
                    if response.status_code == 200:
                        available_docs = response.json().get('documents', [])
                        for doc in available_docs:
                            # Determine file type for special handling hints
                            file_ext = doc.split('.')[-1].lower() if '.' in doc else ''
                            is_csv = file_ext == 'csv'
                            sources_found.append({
                                'path': doc,
                                'filename': doc.split('/')[-1],
                                'is_csv': is_csv,
                                'file_type': file_ext
                            })
                        print(f"DEBUG: Found {len(sources_found)} available documents for loading")
                except requests.RequestException as e:
                    print(f"DEBUG: Could not fetch available documents: {e}")
            
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
            
            # Add assistant response to permanent history with sources for potential loading
            assistant_message = {
                "role": "assistant", 
                "content": response_text
            }
            
            # Include RAG chunks if they were used (for backwards compatibility)
            if rag_chunks:
                assistant_message["rag_chunks"] = rag_chunks
            
            # Include sources information for Load button functionality
            if sources_found:
                assistant_message["sources"] = sources_found
                print(f"DEBUG: Stored {len(sources_found)} sources in assistant message")
                
            session["message_history"].append(assistant_message)
            
            # Inline session cleanup to prevent cookie overflow
            print(f"DEBUG: Post-response cleanup - history length: {len(session['message_history'])}")
            if len(session["message_history"]) > 6:
                session["message_history"] = session["message_history"][-6:]
                print(f"DEBUG: Trimmed message history to last 6 messages")
            
            # Remove metadata from older messages
            for i, msg in enumerate(session["message_history"]):
                if i < len(session["message_history"]) - 1:
                    if "rag_chunks" in msg:
                        del msg["rag_chunks"]
                    if "sources" in msg:
                        del msg["sources"]
            
            session.modified = True  # Mark session as modified
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            session["message_history"].append({"role": "assistant", "content": error_msg})
            
            # Inline session cleanup for error case
            if len(session["message_history"]) > 6:
                session["message_history"] = session["message_history"][-6:]
            
            session.modified = True

        # Get available models for the template
        available_models = get_available_models()
        
        return render_template("chat.html", 
                             message_history=session["message_history"],
                             available_models=available_models,
                             model=model,
                             use_repo_docs=use_repo_docs,
                             RAG_API_URL=os.getenv("RAG_API_URL", ""))

@chat_bp.route("/reset", methods=["POST"])
def reset():
    session.clear()
    return redirect("/chat")

@chat_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for monitoring services"""
    return {"status": "healthy", "service": "insightchat"}, 200

@chat_bp.route("/load_source", methods=["POST"])
def load_source():
    """Load expanded context for a specific source and re-run the last query"""
    from flask import jsonify
    from .utils import fetch_repo_chunks, fetch_document_content
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
    
    source_path = data.get("source_path")
    
    if not source_path:
        return jsonify({"error": "Missing source_path"}), 400
    
    # Get RAG API URL
    rag_api_url = os.getenv("RAG_API_URL")
    if not rag_api_url:
        return jsonify({"error": "RAG API not configured"}), 503
    
    try:
        # Check if this is a CSV file - if so, load full document
        is_csv = source_path.endswith('.csv')
        
        if is_csv:
            print(f"DEBUG: Loading full CSV document for: {source_path}")
            # For CSV files, load the complete document
            full_content = fetch_document_content(source_path, rag_api_url)
            if full_content and not isinstance(full_content, bytes):
                enhanced_context = f"""PRIORITY: Complete CSV document for comprehensive analysis:

IMPORTANT INSTRUCTIONS FOR CSV ANALYSIS:
- When counting rows, count each line including header (total rows in file)
- When counting properties/records, count data rows only (exclude header)  
- Examine the complete structure systematically
- For row counts: Count every line break to get total rows
- For data counts: Count entries excluding the header row

---
Full Document: {source_path}
{full_content}
---"""
            else:
                return jsonify({"error": "Could not load CSV content"}), 500
        else:
            print(f"DEBUG: Loading expanded chunks for source: {source_path}")
            # Use the new RAG API endpoint to get all chunks for this document
            import requests
            
            try:
                response = requests.post(
                    f"{rag_api_url}/get_chunks_for_document",
                    json={
                        "source": source_path,
                        "limit": 0  # 0 means get all chunks
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    chunks_data = response.json()
                    chunks = chunks_data.get('chunks', [])
                    
                    if chunks:
                        # Combine all chunks for this source
                        chunk_contents = [chunk.get('content', '') for chunk in chunks]
                        enhanced_context = f"""Expanded context from all chunks in {source_path}:

{chr(10).join(chunk_contents)}"""
                    else:
                        return jsonify({"error": f"No chunks found for source: {source_path}"}), 404
                else:
                    print(f"DEBUG: RAG API returned status {response.status_code}: {response.text}")
                    return jsonify({"error": f"RAG API error: {response.status_code}"}), 500
                    
            except requests.RequestException as e:
                print(f"DEBUG: Error calling RAG API: {e}")
                return jsonify({"error": f"Failed to fetch chunks: {str(e)}"}), 500
        
        return jsonify({
            "success": True,
            "enhanced_context": enhanced_context,
            "source_path": source_path,
            "context_type": "csv_full" if is_csv else "expanded_chunks"
        })
        
    except Exception as e:
        print(f"DEBUG: Error in load_source: {e}")
        return jsonify({"error": str(e)}), 500

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
            'eml': 'message/rfc822',
            'emlx': 'message/rfc822',
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

@chat_bp.route("/render_email", methods=["GET"])
def render_email():
    """Render an email file as formatted HTML for viewing in browser"""
    from flask import jsonify
    import requests
    from email import policy
    from email.parser import BytesParser
    import html
    
    source = request.args.get("source")
    print(f"DEBUG: Email render route called with source: '{source}'")
    
    if not source:
        print("DEBUG: No source parameter provided")
        return jsonify({"error": "No source specified"}), 400
    
    # URL decode the source
    import urllib.parse
    decoded_source = urllib.parse.unquote(source)
    print(f"DEBUG: Decoded source: '{decoded_source}'")
    
    rag_api_url = os.getenv("RAG_API_URL")
    print(f"DEBUG: RAG_API_URL: {rag_api_url}")
    
    if not rag_api_url:
        print("DEBUG: RAG_API_URL not configured")
        return jsonify({"error": "RAG API not configured"}), 503
    
    try:
        # Get the raw email file from RAG API's /document endpoint
        from .utils import fetch_document_content
        email_content = fetch_document_content(decoded_source, rag_api_url)
        print(f"DEBUG: Retrieved email file, size: {len(email_content) if email_content else 0} bytes")
        
        if not email_content:
            print("DEBUG: No email content retrieved")
            return jsonify({"error": "Email file not found"}), 404
        
        # Ensure we have bytes for the email parser
        if isinstance(email_content, str):
            email_content = email_content.encode('utf-8')
        
        # Parse the email
        from io import BytesIO
        email_buffer = BytesIO(email_content)
        
        # Mac .emlx files have a header line with message length, skip it
        first_line = email_buffer.readline()
        # If it looks like a length header (just digits), it's .emlx format
        if first_line.strip().isdigit():
            # Continue reading from current position (after the length line)
            msg = BytesParser(policy=policy.default).parse(email_buffer)
        else:
            # Regular .eml file, rewind and parse from beginning
            email_buffer.seek(0)
            msg = BytesParser(policy=policy.default).parse(email_buffer)
        
        print(f"DEBUG: Email parsed successfully")
        
        # Extract metadata
        subject = html.escape(msg.get('subject', '(No Subject)'))
        from_addr = html.escape(msg.get('from', '(Unknown Sender)'))
        to_addr = html.escape(msg.get('to', '(Unknown Recipient)'))
        date = html.escape(msg.get('date', '(No Date)'))
        
        # Extract body content
        body_text = ""
        body_html = None
        
        if msg.is_multipart():
            # Handle multipart messages
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))
                
                # Skip attachments
                if 'attachment' in content_disposition:
                    continue
                    
                # Get plain text parts
                if content_type == 'text/plain':
                    try:
                        text = part.get_content()
                        if text:
                            body_text += text + "\n"
                    except Exception as e:
                        print(f"DEBUG: Error getting plain text part: {e}")
                        pass
                        
                # Get HTML parts
                elif content_type == 'text/html':
                    try:
                        html_content = part.get_content()
                        body_html = html_content
                    except Exception as e:
                        print(f"DEBUG: Error getting HTML part: {e}")
                        pass
        else:
            # Simple non-multipart message
            content_type = msg.get_content_type()
            if content_type == 'text/plain':
                try:
                    body_text = msg.get_content()
                except Exception as e:
                    print(f"DEBUG: Error getting plain text content: {e}")
                    pass
            elif content_type == 'text/html':
                try:
                    body_html = msg.get_content()
                except Exception as e:
                    print(f"DEBUG: Error getting HTML content: {e}")
                    pass
        
        # Render HTML response
        if body_html:
            # Use the HTML version if available
            email_body = f"""
                <div style="border: 1px solid #ddd; padding: 15px; margin-top: 15px; background: white;">
                    {body_html}
                </div>
            """
        else:
            # Use plain text, convert to HTML with line breaks
            escaped_text = html.escape(body_text.strip())
            formatted_text = escaped_text.replace('\n', '<br>\n')
            email_body = f"""
                <div style="border: 1px solid #ddd; padding: 15px; margin-top: 15px; background: white; white-space: pre-wrap; font-family: monospace;">
                    {formatted_text}
                </div>
            """
        
        # Build email content for embedding in modal (not a full HTML page)
        html_content = f"""
<style>
    .email-container {{
        background: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    .email-header {{
        background: #f8f9fa;
        padding: 20px;
        border-bottom: 2px solid #e9ecef;
    }}
    .email-subject {{
        font-size: 24px;
        font-weight: 600;
        margin: 0 0 15px 0;
        color: #212529;
    }}
    .email-meta {{
        display: grid;
        gap: 8px;
        font-size: 14px;
        color: #495057;
    }}
    .email-meta-row {{
        display: flex;
    }}
    .email-meta-label {{
        font-weight: 600;
        min-width: 80px;
        color: #6c757d;
    }}
    .email-meta-value {{
        flex: 1;
    }}
    .email-body {{
        padding: 20px;
    }}
    .file-info {{
        background: #e9ecef;
        padding: 10px 20px;
        border-top: 1px solid #ddd;
        font-size: 12px;
        color: #6c757d;
    }}
</style>
<div class="email-container">
    <div class="email-header">
        <h1 class="email-subject">{subject}</h1>
        <div class="email-meta">
            <div class="email-meta-row">
                <span class="email-meta-label">From:</span>
                <span class="email-meta-value">{from_addr}</span>
            </div>
            <div class="email-meta-row">
                <span class="email-meta-label">To:</span>
                <span class="email-meta-value">{to_addr}</span>
            </div>
            <div class="email-meta-row">
                <span class="email-meta-label">Date:</span>
                <span class="email-meta-value">{date}</span>
            </div>
        </div>
    </div>
    <div class="email-body">
        {email_body}
    </div>
    <div class="file-info">
        File: {html.escape(decoded_source)}
    </div>
</div>
        """
        
        print(f"DEBUG: Rendered email content, length: {len(html_content)} chars")
        return html_content, 200, {'Content-Type': 'text/html; charset=utf-8'}
            
    except requests.RequestException as e:
        print(f"DEBUG: Request exception getting email file: {e}")
        return jsonify({"error": f"Failed to retrieve email file: {str(e)}"}), 503
    except Exception as e:
        print(f"DEBUG: Exception in render_email: {type(e).__name__}: {e}")
        import traceback
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500