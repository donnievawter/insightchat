from flask import Blueprint, render_template, request, session, redirect
import uuid
import os
import hashlib
from .utils import fetch_repo_chunks, prompt_model, clean_markdown, keyword_file, describe_file

chat_bp = Blueprint('chat', __name__)

@chat_bp.route("/chat", methods=["GET", "POST"])
def chat():
    if request.method == "GET":
        session.clear()
        session["system_prompt"] = request.args.get("context", "Respond to queries in English")
        return render_template("chat.html")

    if request.method == "POST":
        model = request.form.get("model")
        prompt = request.form.get("prompt", "").strip()
        use_repo_docs = bool(request.form.get("use_repo_docs"))
        session["use_repo_docs"] = use_repo_docs

        job_id = str(uuid.uuid4())
        session["job_id"] = job_id

        if use_repo_docs:
            k = 5  # Default value for k
            rag_api_url = os.getenv("RAG_API_URL")
            context_text = fetch_repo_chunks(prompt, k=k, rag_api_url=rag_api_url)
            if context_text:
                session["message_history"].insert(0, {"role": "system", "content": context_text})

        active_model = session.get("model", model)
        session["model"] = active_model

        image = request.files.get("file")
        if image:
            filename_hash = hashlib.md5(image.read()).hexdigest() + "_" + image.filename
            static_dir = os.path.join(os.path.dirname(__file__), "static", "uploads")
            os.makedirs(static_dir, exist_ok=True)
            image_path = os.path.join(static_dir, filename_hash)
            image.seek(0)
            image.save(image_path)
            session["image_path"] = filename_hash

            result = describe_file(image_path, prompt=prompt or "Describe the image in detail", model=active_model, job_id=job_id)
            response_text = clean_markdown(result["description"])
            session["message_history"].append({"role": "assistant", "content": response_text})

        else:
            response_data = prompt_model(model=active_model, prompt=prompt, history=session.get("message_history", []))
            response_text = clean_markdown(response_data["response"])
            session["message_history"].append({"role": "assistant", "content": response_text})

        return render_template("chat.html", result=response_text, image_path=session.get("image_path"))

@chat_bp.route("/reset", methods=["POST"])
def reset():
    session.clear()
    return redirect("/chat")