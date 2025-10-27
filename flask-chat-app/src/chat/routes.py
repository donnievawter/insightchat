from flask import Blueprint, render_template, request, session, redirect
import os
from .utils import prompt_model, fetch_repo_chunks

chat_bp = Blueprint('chat', __name__)

@chat_bp.route("/chat", methods=["GET", "POST"])
def chat():
    if request.method == "GET":
        # Initialize session if needed
        if "message_history" not in session:
            session["message_history"] = []
        system_prompt = request.args.get("context", "You are a helpful assistant.")
        session["system_prompt"] = system_prompt
        return render_template("chat.html", message_history=session["message_history"])

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
                                     model=model,
                                     use_repo_docs=use_repo_docs)
            
            context_text = fetch_repo_chunks(prompt, k=k, rag_api_url=rag_api_url)
            print(f"DEBUG: RAG context retrieved: {bool(context_text)}")  # Debug log
            
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
            
            # Add assistant response to permanent history
            session["message_history"].append({"role": "assistant", "content": response_text})
            session.modified = True  # Mark session as modified
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            session["message_history"].append({"role": "assistant", "content": error_msg})
            session.modified = True

        return render_template("chat.html", 
                             message_history=session["message_history"],
                             model=model,
                             use_repo_docs=use_repo_docs)

@chat_bp.route("/reset", methods=["POST"])
def reset():
    session.clear()
    return redirect("/chat")