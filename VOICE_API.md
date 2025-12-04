# Voice Query API

The `/api/voice-query` endpoint provides a stateless API for voice assistant integration, processing queries through the full InsightChat pipeline (tools + RAG + LLM).

## Endpoint

```
POST /api/voice-query
```

## Features

- **Audio transcription** via Whisper API
- **Tool integration** (calendar, weather, etc.)
- **RAG context** from document repository
- **LLM processing** with configurable models
- **Optional TTS broadcast** to Google speakers
- **Stateless** - no session management required

## Request Formats

### Option 1: Audio File Upload

```bash
curl -X POST http://localhost:5030/api/voice-query \
  -F "file=@recording.wav" \
  -F "use_rag=true" \
  -F "broadcast=true" \
  -F "model=qwen2.5vl:latest"
```

### Option 2: Pre-transcribed Text

```bash
curl -X POST http://localhost:5030/api/voice-query \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What is on my calendar today?",
    "use_rag": true,
    "broadcast": true,
    "model": "qwen2.5vl:latest"
  }'
```

## Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file` | file | - | Audio file (multipart upload) |
| `text` | string | - | Pre-transcribed text (JSON) |
| `model` | string | `DEFAULT_MODEL` | Ollama model to use |
| `use_rag` | boolean | `true` | Enable RAG context retrieval |
| `broadcast` | boolean | `false` | Broadcast response to TTS |
| `language` | string | - | Language code for transcription |

**Note:** Either `file` or `text` must be provided (not both).

## Response Format

```json
{
  "success": true,
  "query": "What's on my calendar today?",
  "response": "You have one event scheduled for today: **Adndy Thomas Zoom** at 9:00 PM - 10:00 PM MST",
  "tools_used": ["calendar"],
  "broadcast_sent": true
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether the request succeeded |
| `query` | string | The transcribed or provided query text |
| `response` | string | The LLM's response text |
| `tools_used` | array | List of tools that handled the query |
| `broadcast_sent` | boolean | Whether TTS broadcast succeeded |
| `error` | string | Error message (only if `success: false`) |

## Error Responses

```json
{
  "success": false,
  "error": "No audio file or text provided"
}
```

HTTP status codes:
- `200` - Success
- `400` - Bad request (missing parameters)
- `500` - Server error

## Configuration

Add to your `.env` file:

```bash
# TTS Broadcast Service (optional)
TTS_BROADCAST_URL=https://tts.hlab.cam/broadcast
TTS_TIMEOUT=10
```

## Python Example

Using the provided test script:

```python
from test_voice_api import test_voice_query

# Text query
result = test_voice_query(
    text="What's the weather like?",
    use_rag=True,
    broadcast=True
)

# Audio query
result = test_voice_query(
    audio_file="recording.wav",
    broadcast=True
)
```

## Integration with Wake Word Listener

Your wake word listener can make simple HTTP calls:

```python
import requests

def handle_voice_command(audio_file_path):
    """Process wake word triggered audio"""
    
    with open(audio_file_path, 'rb') as f:
        response = requests.post(
            'http://insightchat-server:5030/api/voice-query',
            files={'file': (audio_file_path, f, 'audio/wav')},
            data={'broadcast': 'true'}
        )
    
    result = response.json()
    
    if result['success']:
        print(f"Query: {result['query']}")
        print(f"Response: {result['response']}")
        if result['broadcast_sent']:
            print("Response played on speakers")
    else:
        print(f"Error: {result['error']}")
```

## Tool Integration

The voice query endpoint automatically uses all configured tools:

- **Calendar** - "What's on my calendar today?"
- **Weather** - "What's the weather like?"
- Additional tools can be added via the tool router

## RAG Integration

When `use_rag: true`, the endpoint:
1. Checks if tools can handle the query
2. If not, fetches relevant context from your RAG API
3. Includes context in the LLM prompt

## System Prompt

Voice queries use a specialized system prompt optimized for speech:

> "You are a helpful voice assistant. Provide clear, concise responses suitable for speech. Keep answers brief unless detail is specifically requested."

This ensures responses are appropriate for TTS broadcast.

## Testing

```bash
# Simple text query
./test_voice_api.py --text "What time is it?"

# Calendar query with broadcast
./test_voice_api.py --text "What's on my calendar?" --broadcast

# Audio file
./test_voice_api.py --audio recording.wav --broadcast

# Custom model
./test_voice_api.py --text "Tell me a joke" --model llama3.2:latest
```

## Architecture

```
Wake Word Listener (on LAN device)
    ↓
    └─→ POST /api/voice-query (audio file)
            ↓
            ├─→ Whisper API (transcription)
            ├─→ Tool Router (calendar, weather, etc.)
            ├─→ RAG API (document context)
            └─→ Ollama LLM (response generation)
                    ↓
                    └─→ TTS API (optional broadcast)
                            ↓
                            └─→ Google Speakers
```

## Advantages Over Separate App

✓ **Reuses existing code**: Tools, RAG, LLM integration  
✓ **Single deployment**: One Docker container  
✓ **Shared configuration**: Same models, APIs, settings  
✓ **Consistent behavior**: Web and voice use same logic  
✓ **Easy maintenance**: Update once, benefits both interfaces  

## Future Enhancements

- [ ] Conversation history for follow-up questions
- [ ] Voice-specific tool responses (shorter format)
- [ ] Multiple TTS voice options
- [ ] Streaming responses
- [ ] Wake word detection in this app
