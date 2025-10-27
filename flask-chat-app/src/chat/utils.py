def clean_markdown(text):
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
    k = 5  # Default value
    if not rag_api_url:
        return None

    try:
        resp = requests.post(
            f"{rag_api_url.rstrip('/')}/query",
            json={"prompt": prompt, "k": k},
            timeout=6
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        parts = []
        for r in results:
            content = r.get("content", "")
            content = html.escape(content)
            content = shorten(content, width=800, placeholder=" …")
            src = r.get("metadata", {}).get("source", "unknown")
            parts.append(f"---\nSource: {src}\n{content}\n")
        if not parts:
            return None
        joined = "Use the following retrieved document excerpts to answer the user query (do not cite unless asked):\n\n" + "\n".join(parts)
        return shorten(joined, width=4000, placeholder="\n[truncated]")
    except Exception as e:
        print(f"fetch_repo_chunks error: {e}")
        return None

def prompt_model(model, prompt, history=None, ollama_url=None, system_prompt="Respond to queries in English"):
    payload, updated_history = build_chat_payload(
        model, prompt,
        prior_messages=history,
        system_prompt=system_prompt,
        temperature=0.7
    )

    try:
        timeout = 120
        response = requests.post(f"{ollama_url}", json=payload, timeout=timeout)
        response.raise_for_status()
        content = response.json().get("message", {}).get("content", "").strip()
    except Exception as e:
        content = f"Error: {str(e)}"

    non_system_history = [m for m in updated_history if m.get("role") != "system"]

    return {
        "model": model,
        "timestamp": datetime.datetime.now().strftime("%Y:%m:%d %H:%M:%S"),
        "prompt": prompt,
        "history": non_system_history,
        "response": content
    }, updated_history