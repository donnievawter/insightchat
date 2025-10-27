#!/usr/bin/env python3
"""
InsightChat - AI-powered chat application with RAG support

This is a simple launcher for the Flask chat application.
For development, you can also run the app directly:
    cd flask-chat-app/src && python app.py
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Launch the InsightChat Flask application"""
    
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    app_dir = script_dir / "flask-chat-app" / "src"
    
    # Load environment variables from .env file if it exists
    try:
        from dotenv import load_dotenv
        env_path = script_dir / "flask-chat-app" / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✓ Loaded environment from {env_path}")
        else:
            print(f"⚠️  No .env file found at {env_path}")
    except ImportError:
        print("⚠️  python-dotenv not available, using system environment only")
    app_file = app_dir / "app.py"
    
    if not app_file.exists():
        print("Error: Flask app not found at", app_file)
        print("Make sure you're in the insightchat project directory.")
        sys.exit(1)
    
    # Change to the app directory
    os.chdir(app_dir)
    
    # Launch the Flask app
    print("Starting InsightChat...")
    print("Visit http://localhost:5050 in your browser")
    print("Press Ctrl+C to stop")
    
    try:
        subprocess.run([sys.executable, "app.py"], check=True)
    except KeyboardInterrupt:
        print("\nInsightChat stopped.")
    except subprocess.CalledProcessError as e:
        print(f"Error running app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
