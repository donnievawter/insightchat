from flask import Flask, render_template, request, session
import os
import uuid
import hashlib
from chat.routes import chat_bp

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your_secret_key")

app.register_blueprint(chat_bp)

@app.route("/")
def index():
    return render_template("chat.html")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5050, debug=True)