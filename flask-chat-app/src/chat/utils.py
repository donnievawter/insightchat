import requests
import os
import html
from textwrap import shorten
from .config import DEFAULT_SYSTEM_PROMPT, DEFAULT_TEMPERATURE

def clean_markdown(text):
    """Clean up markdown formatting"""
    text = text.replace("<p>```", "```").replace("```</p>", "```")
    return text

def build_chat_payload(model, prompt, prior_messages=None, system_prompt=None, temperature=None):
    messages = prior_messages[:] if prior_messages else []

    # Only add system prompt if one doesn't exist AND system_prompt is provided
    if system_prompt is not None and not any(m["role"] == "system" for m in messages):
        messages.insert(0, {"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "temperature": temperature
    }

    return payload, messages

def fetch_repo_chunks(prompt, k=None, rag_api_url=None, return_chunks=False):
    """Fetch relevant document chunks from RAG API for context
    
    Args:
        prompt: The query prompt
        k: Number of chunks to retrieve (default 5)
        rag_api_url: RAG API endpoint URL
        return_chunks: If True, return both context and chunk data; if False, return only context
    
    Returns:
        If return_chunks is True: (context_string, chunks_list)
        If return_chunks is False: context_string (legacy behavior)
    """
    k = k or 5  # Default value
    if not rag_api_url:
        print("DEBUG: No RAG API URL provided")
        return (None, []) if return_chunks else None

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
            return (None, []) if return_chunks else None
            
        # Process chunks for context and UI display
        context_parts = []
        chunk_data = []
        
        for i, r in enumerate(results):
            content = r.get("content", "")
            if content:
                # For context (escape HTML and truncate)
                context_content = html.escape(content)
                context_content = shorten(context_content, width=800, placeholder=" …")
                src = r.get("metadata", {}).get("source", "unknown")
                context_parts.append(f"---\nSource: {src}\n{context_content}\n")
                
                # For UI display (preserve original content and metadata)
                chunk_info = {
                    "content": content,  # Full original content
                    "metadata": r.get("metadata", {}),
                    "start_index": r.get("start_index", 0),  # Character index in source document
                    "score": r.get("score", 0)  # Relevance score if available
                }
                chunk_data.append(chunk_info)
                
                print(f"DEBUG: Processed RAG result {i+1}: {len(content)} chars from {src}")
        
        if not context_parts:
            print("DEBUG: No valid content in RAG results")
            return (None, []) if return_chunks else None
            
        # Build context string
        joined = "Use the following retrieved document excerpts to answer the user query (do not cite unless asked):\n\n" + "\n".join(context_parts)
        final_context = shorten(joined, width=4000, placeholder="\n[truncated]")
        print(f"DEBUG: Final context length: {len(final_context)} chars")
        
        if return_chunks:
            return final_context, chunk_data
        else:
            return final_context
        
    except requests.exceptions.ConnectionError as e:
        print(f"DEBUG: RAG connection error: {e}")
        return (None, []) if return_chunks else None
    except requests.exceptions.Timeout as e:
        print(f"DEBUG: RAG timeout error: {e}")
        return (None, []) if return_chunks else None
    except requests.exceptions.HTTPError as e:
        print(f"DEBUG: RAG HTTP error: {e}")
        return (None, []) if return_chunks else None
    except Exception as e:
        print(f"DEBUG: RAG unexpected error: {e}")
        return (None, []) if return_chunks else None

def fetch_document_content(source, rag_api_url=None):
    """Fetch full document content from RAG API or file system
    
    Args:
        source: Document source/path identifier
        rag_api_url: RAG API endpoint URL
    
    Returns:
        Document content as string, or None if not found
    """
    if not rag_api_url:
        print(f"DEBUG: No RAG API URL provided for document {source}")
        return None
    
    try:
        # Try to fetch document from RAG API document endpoint
        url = f"{rag_api_url.rstrip('/')}/document"
        payload = {"file_path": source}
        print(f"DEBUG: Making document request to {url}")
        print(f"DEBUG: Payload: {payload}")
        print(f"DEBUG: Full URL: {url}")
        
        resp = requests.post(url, json=payload, timeout=10)
        print(f"DEBUG: Document response status: {resp.status_code}")
        print(f"DEBUG: Document response headers: {dict(resp.headers)}")
        
        # Log the raw response content for debugging
        try:
            response_text = resp.text
            print(f"DEBUG: Raw response content (first 500 chars): {response_text[:500]}")
        except Exception as e:
            print(f"DEBUG: Could not read response text: {e}")
        
        if resp.status_code == 404:
            print(f"DEBUG: Document not found (404): {source}")
            return None
        
        if resp.status_code != 200:
            print(f"DEBUG: HTTP error {resp.status_code}: {resp.reason}")
            return None
            
        resp.raise_for_status()
        
        # Try to parse JSON response
        try:
            data = resp.json()
            print(f"DEBUG: Successfully parsed JSON response")
            print(f"DEBUG: JSON response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            print(f"DEBUG: Response data type: {type(data)}")
        except Exception as json_error:
            print(f"DEBUG: Failed to parse JSON response: {json_error}")
            print(f"DEBUG: Response content type: {resp.headers.get('content-type', 'unknown')}")
            return None
        
        content = data.get("content", "")
        content_type = data.get("content_type", "")
        print(f"DEBUG: Extracted content field, type: {type(content)}, length: {len(content) if content else 0}")
        print(f"DEBUG: Content type from API: {content_type}")
        
        if content:
            print(f"DEBUG: Retrieved document content: {len(content)} characters")
            
            # Check if this looks like base64 encoded content
            is_base64_image = False
            
            # Check if this looks like base64 encoded binary content (images, PDFs, etc.)
            binary_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.pdf']
            binary_prefixes = ['iVBORw0KGgo', '/9j/', 'R0lGODlh', 'UklGR', 'JVBERi0']  # PNG, JPG, GIF, RIFF, PDF
            
            if (content_type and ('image' in content_type or 'octet-stream' in content_type or 'pdf' in content_type)) or \
               (source and any(source.lower().endswith(ext) for ext in binary_extensions)) or \
               (content.startswith(tuple(binary_prefixes))):
                print("DEBUG: Detected potential base64 binary content (image/PDF)")
                try:
                    import base64
                    # Try to decode as base64
                    decoded_content = base64.b64decode(content)
                    print(f"DEBUG: Successfully decoded base64 content: {len(decoded_content)} bytes")
                    return decoded_content
                except Exception as decode_error:
                    print(f"DEBUG: Base64 decode failed: {decode_error}, treating as text")
            
            print(f"DEBUG: Treating as text content, preview (first 100 chars): {content[:100]}")
            return content
        else:
            print("DEBUG: Empty document content returned")
            print(f"DEBUG: Available data keys: {list(data.keys()) if isinstance(data, dict) else 'None'}")
            print(f"DEBUG: Data values preview: {str(data)[:200] if data else 'None'}")
            return None
            
    except requests.exceptions.ConnectionError as e:
        print(f"DEBUG: Document connection error: {e}")
        return None
    except requests.exceptions.Timeout as e:
        print(f"DEBUG: Document timeout error: {e}")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"DEBUG: Document HTTP error: {e}")
        return None
    except Exception as e:
        print(f"DEBUG: Document unexpected error: {e}")
        return None

def get_available_models(ollama_base_url=None):
    """Fetch available models from Ollama API"""
    if not ollama_base_url:
        ollama_base_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        # Remove /api/chat if it's there, we need just the base URL
        ollama_base_url = ollama_base_url.replace("/api/chat", "")
        print(f"DEBUG: Using Ollama base URL: {ollama_base_url}")       
    try:
        tags_url = f"{ollama_base_url.rstrip('/')}/api/tags"
        # print(f"DEBUG: Fetching models from {tags_url}")  # Commented out to reduce log noise
        
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
        
        # print(f"DEBUG: Found {len(models)} available models")  # Commented out to reduce log noise
        return models
        
    except Exception as e:
        print(f"ERROR: Failed to fetch models from Ollama API: {e}")
        # Return empty list if API fails - don't pretend models are available
        return []

def prompt_model(model, prompt, history=None, system_prompt=None):
    """Send a prompt to Ollama and get the response"""
    # If system_prompt is None, use default. If empty string, skip (already in history)
    if system_prompt is None:
        system_prompt = DEFAULT_SYSTEM_PROMPT
    elif system_prompt == "":
        system_prompt = None  # Signal to build_chat_payload to skip adding system message
    
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
    
    payload, updated_history = build_chat_payload(
        model, prompt,
        prior_messages=history,
        system_prompt=system_prompt,
        temperature=DEFAULT_TEMPERATURE
    )
    # Minimal debug logging
    print("DEBUG: ===== OLLAMA REQUEST =====")
    print("DEBUG: Model:", payload.get('model'))
    print("DEBUG: Number of messages:", len(payload.get('messages', [])))
    total_content_size = sum(len(msg.get('content', '')) for msg in payload.get('messages', []))
    print(f"DEBUG: Total content size: {total_content_size:,} characters")
    print("DEBUG: ===== SENDING REQUEST =====")
    # Removed excessive content dumping to focus on the real issue
    try:
        # Configurable timeout - default 600 seconds (10 minutes) for large context processing
        timeout = int(os.getenv("OLLAMA_TIMEOUT", 600))
        print(f"DEBUG: Using Ollama timeout: {timeout} seconds")
        
        # Check if this is a very large context that might cause issues
        total_chars = sum(len(msg.get('content', '')) for msg in payload.get('messages', []))
        if total_chars > 100000:
            print(f"DEBUG: WARNING - Very large context ({total_chars:,} chars) - processing may take several minutes with {payload.get('model')}")
            print(f"DEBUG: Consider using models with larger context windows like qwen2.5vl:latest or qwen3-coder:30b for better performance")
            # Don't reduce timeout - large contexts need time!
        
        print(f"DEBUG: Sending POST request to {ollama_url}")
        
        response = requests.post(ollama_url, json=payload, timeout=timeout)
        print(f"DEBUG: Received response from Ollama, status: {response.status_code}")
        
        response.raise_for_status()
        response_data = response.json()
        print(f"DEBUG: Response JSON keys: {list(response_data.keys())}")
        
        content = response_data.get("message", {}).get("content", "").strip()
        print(f"DEBUG: Extracted content length: {len(content):,} chars")
    except requests.exceptions.Timeout as e:
        timeout_min = timeout // 60
        content = f"⏰ Request timed out after {timeout} seconds ({timeout_min} minutes). The model may be processing a very large context. Try:\n\n1. Using a model with larger context window (e.g., qwen3-coder:30b)\n2. Reducing document size\n3. Breaking complex queries into smaller parts\n\nError details: {str(e)}"
    except Exception as e:
        content = f"Error communicating with Ollama: {str(e)}"

    # Return just the response content and updated history
    return content, updated_history