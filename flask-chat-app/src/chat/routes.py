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
        current_model = session.get("model", available_models[0]["name"] if available_models else "llama2:latest")
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
            
            # Get both context and chunk data
            context_text, rag_chunks = fetch_repo_chunks(prompt, k=k, rag_api_url=rag_api_url, return_chunks=True)
            print(f"DEBUG: RAG context retrieved: {bool(context_text)}")  # Debug log
            print(f"DEBUG: RAG chunks retrieved: {len(rag_chunks)}")  # Debug log
            
            if context_text:
                print(f"DEBUG: Context length: {len(context_text)} chars")  # Debug log
                # Insert context as system message temporarily for this query
                temp_history = [{"role": "system", "content": context_text}] + session["message_history"]
            else:
                print("DEBUG: No context retrieved from RAG")
                temp_history = session["message_history"]
        else:
            print("DEBUG: RAG not enabled for this query")
            temp_history = session["message_history"]

        # Get response from Ollama
        try:
            system_prompt = session.get("system_prompt", "You are a helpful assistant.")
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
    
    rag_api_url = os.getenv("RAG_API_URL")
    print(f"DEBUG: RAG_API_URL: {rag_api_url}")
    
    if not rag_api_url:
        print("DEBUG: RAG_API_URL not configured")
        return jsonify({"error": "RAG API not configured"}), 503
    
    try:
        print(f"DEBUG: Attempting to fetch document content for: {source}")
        content = fetch_document_content(source, rag_api_url)
        print(f"DEBUG: fetch_document_content returned: {type(content)} with length {len(content) if content else 0}")
        
        if content is None:
            print(f"DEBUG: Content is None, returning 404 for {source}")
            return jsonify({"error": "Document not found or not accessible"}), 404
        
        # Determine content type based on file extension
        file_extension = source.split('.')[-1].lower() if '.' in source else ''
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
            print(f"DEBUG: Returning binary content ({len(content)} bytes) for {source}")
            from flask import Response
            return Response(content, 200, {'Content-Type': content_type})
        else:
            print(f"DEBUG: Returning text content ({len(content)} chars) for {source}")
            return content, 200, {'Content-Type': content_type}
        
    except Exception as e:
        print(f"DEBUG: Exception in document route for {source}: {type(e).__name__}: {e}")
        import traceback
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500