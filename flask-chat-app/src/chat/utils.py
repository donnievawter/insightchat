import requests
import os
import html
from textwrap import shorten

def clean_markdown(text):
    """Clean up markdown formatting"""
    text = text.replace("<p>```", "```").replace("```</p>", "```")
    return text

def build_chat_payload(model, prompt, prior_messages=None, system_prompt="Respond to queries in English", temperature=0.7):
    messages = prior_messages[:] if prior_messages else []

    if not any(m["role"] == "system" for m in messages):
        messages.insert(0, {"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "temperature": temperature
    }

    return payload, messages

def fetch_repo_chunks(prompt, k=None, rag_api_url=None):
    """Fetch relevant document chunks from RAG API for context"""
    k = k or 5  # Default value
    if not rag_api_url:
        print("DEBUG: No RAG API URL provided")
        return None

    try:
        url = f"{rag_api_url.rstrip('/')}/query"
        payload = {"prompt": prompt, "k": k}
        print(f"DEBUG: Making RAG request to {url} with payload: {payload}")
        
        resp = requests.post(url, json=payload, timeout=6)
        print(f"DEBUG: RAG response status: {resp.status_code}")
        
        resp.raise_for_status()
        data = resp.json()
        print(f"DEBUG: RAG response data keys: {list(data.keys()) if data else 'None'}")
        
        results = data.get("results", [])
        print(f"DEBUG: Number of RAG results: {len(results)}")
        
        if not results:
            print("DEBUG: No results returned from RAG API")
            return None
            
        parts = []
        for i, r in enumerate(results):
            content = r.get("content", "")
            if content:
                content = html.escape(content)
                content = shorten(content, width=800, placeholder=" …")
                src = r.get("metadata", {}).get("source", "unknown")
                parts.append(f"---\nSource: {src}\n{content}\n")
                print(f"DEBUG: Processed RAG result {i+1}: {len(content)} chars from {src}")
        
        if not parts:
            print("DEBUG: No valid content in RAG results")
            return None
            
        joined = "Use the following retrieved document excerpts to answer the user query (do not cite unless asked):\n\n" + "\n".join(parts)
        final_context = shorten(joined, width=4000, placeholder="\n[truncated]")
        print(f"DEBUG: Final context length: {len(final_context)} chars")
        return final_context
        
    except requests.exceptions.ConnectionError as e:
        print(f"DEBUG: RAG connection error: {e}")
        return None
    except requests.exceptions.Timeout as e:
        print(f"DEBUG: RAG timeout error: {e}")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"DEBUG: RAG HTTP error: {e}")
        return None
    except Exception as e:
        print(f"DEBUG: RAG unexpected error: {e}")
        return None

def get_available_models(ollama_base_url=None):
    """Fetch available models from Ollama API"""
    if not ollama_base_url:
        ollama_base_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        # Remove /api/chat if it's there, we need just the base URL
        ollama_base_url = ollama_base_url.replace("/api/chat", "")
    
    try:
        tags_url = f"{ollama_base_url.rstrip('/')}/api/tags"
        print(f"DEBUG: Fetching models from {tags_url}")
        
        response = requests.get(tags_url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        models = []
        
        if "models" in data:
            for model_info in data["models"]:
                model_name = model_info.get("name", "")
                # Skip embedding models
                if "embed" not in model_name.lower():
                    models.append({
                        "name": model_name,
                        "size": model_info.get("size", 0),
                        "family": model_info.get("details", {}).get("family", ""),
                        "parameter_size": model_info.get("details", {}).get("parameter_size", "")
                    })
        
        print(f"DEBUG: Found {len(models)} available models")
        return models
        
    except Exception as e:
        print(f"DEBUG: Error fetching models: {e}")
        # Return fallback models if API fails
        return [
            {"name": "llama3.2:latest", "family": "llama", "parameter_size": "3B"},
            {"name": "llama2:latest", "family": "llama", "parameter_size": "7B"}
        ]

def prompt_model(model, prompt, history=None, system_prompt="You are a helpful assistant."):
    """Send a prompt to Ollama and get the response"""
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
    
    payload, updated_history = build_chat_payload(
        model, prompt,
        prior_messages=history,
        system_prompt=system_prompt,
        temperature=0.7
    )

    try:
        timeout = 120
        response = requests.post(ollama_url, json=payload, timeout=timeout)
        response.raise_for_status()
        content = response.json().get("message", {}).get("content", "").strip()
    except Exception as e:
        content = f"Error communicating with Ollama: {str(e)}"

    # Return just the response content and updated history
    return content, updated_history