#!/usr/bin/env python3
"""
Test script for RAG functionality

This script helps you test if your RAG API is working correctly
"""

import os
import sys
from pathlib import Path

# Add the src directory to Python path
src_dir = Path(__file__).parent / "flask-chat-app" / "src"
sys.path.insert(0, str(src_dir))

def test_rag():
    from chat.utils import fetch_repo_chunks
    
    # Test configuration
    test_prompt = "What is machine learning?"
    rag_api_url = os.getenv("RAG_API_URL")
    
    print("=== RAG Test ===")
    print(f"RAG_API_URL from environment: {rag_api_url}")
    
    if not rag_api_url:
        print("❌ RAG_API_URL not set!")
        print("Please set RAG_API_URL in your .env file or environment")
        print("Example: RAG_API_URL=http://localhost:8000")
        return
    
    print(f"Testing RAG with prompt: '{test_prompt}'")
    print(f"API URL: {rag_api_url}")
    print("-" * 50)
    
    # Test the RAG function
    result = fetch_repo_chunks(test_prompt, k=3, rag_api_url=rag_api_url)
    
    if result:
        print("✅ RAG test successful!")
        print(f"Context length: {len(result)} characters")
        print("\nFirst 500 characters of retrieved context:")
        print("-" * 50)
        print(result[:500] + "..." if len(result) > 500 else result)
    else:
        print("❌ RAG test failed - no context retrieved")
        print("\nPossible issues:")
        print("1. RAG service is not running")
        print("2. RAG_API_URL is incorrect")
        print("3. RAG service returned no results")
        print("4. Network connectivity issues")

def test_environment():
    print("=== Environment Test ===")
    print(f"OLLAMA_URL: {os.getenv('OLLAMA_URL', 'Not set')}")
    print(f"RAG_API_URL: {os.getenv('RAG_API_URL', 'Not set')}")
    print(f"FLASK_SECRET_KEY: {'Set' if os.getenv('FLASK_SECRET_KEY') else 'Not set'}")
    print("")

if __name__ == "__main__":
    # Load environment variables
    try:
        from dotenv import load_dotenv
        
        # Check multiple possible locations for .env file
        env_paths = [
            Path(__file__).parent / ".env",                    # Project root
            Path(__file__).parent / "flask-chat-app" / ".env"  # flask-chat-app directory
        ]
        
        env_loaded = False
        for env_file in env_paths:
            if env_file.exists():
                load_dotenv(env_file)
                print(f"✅ Loaded .env from {env_file}")
                env_loaded = True
                break
        
        if not env_loaded:
            print(f"⚠️  No .env file found in {[str(p) for p in env_paths]}")
        print()
    except ImportError:
        print("⚠️  python-dotenv not available, using system environment only")
        print()
    
    test_environment()
    test_rag()