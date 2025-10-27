from flask import Flask, redirect, url_for
import os
from pathlib import Path
from dotenv import load_dotenv
from chat.routes import chat_bp

# Get the path to the flask-chat-app directory (parent of src)
app_root = Path(__file__).parent.parent
# Get the project root (parent of flask-chat-app)
project_root = app_root.parent

# Load environment variables from .env file (check both locations)
env_paths = [
    project_root / ".env",  # Project root
    app_root / ".env"       # flask-chat-app directory
]

env_loaded = False
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Loaded environment variables from {env_path}")
        env_loaded = True
        break

if not env_loaded:
    print(f"⚠️  No .env file found in {[str(p) for p in env_paths]}")
    print("   Create one by copying .env.example to .env")

app = Flask(__name__, 
           template_folder=str(app_root / "templates"),
           static_folder=str(Path(__file__).parent / "static"))
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")

app.register_blueprint(chat_bp)

@app.route("/")
def index():
    return redirect(url_for('chat.chat'))

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "5030"))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
    
    app.run(host=host, port=port, debug=debug)