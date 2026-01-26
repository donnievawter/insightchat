# InsightChat

A clean, modern AI-powered chat application with optional RAG (Retrieval-Augmented Generation) support using Ollama.

## Features

- 🤖 **Multiple AI Models**: Support for various Ollama models (Llama 3.2, Llama 3.1, Mistral, CodeLlama, etc.)
- 🎙️ **Voice Input**: Record audio and automatically transcribe to text using Whisper
- 🔍 **RAG Integration**: Optional context enhancement using external document retrieval
- 🔧 **External Tools Integration**: Connect to specialized APIs (weather, quotes, calendar, etc.) for real-time data
- 📄 **Document Viewer**: View and interact with various document types (PDF, CSV, DOCX, images, audio files, Jupyter notebooks, and more)
- 📓 **Jupyter Notebook Support**: View, download, and load .ipynb files with syntax-highlighted code cells, formatted markdown, and rendered outputs
- 🎵 **Audio File Support**: Play audio files (.wav, .mp3, .m4a, .flac, .ogg) directly in the document viewer
- 🗣️ **Voice Assistant API**: Full voice-to-voice assistant with audio transcription and TTS broadcast
- 📅 **Calendar Integration**: Query your calendar with natural language
- 💬 **Clean Chat Interface**: Modern, responsive web interface with mobile support
- ⚡ **Fast & Local**: Runs entirely on your local machine with Ollama
- 🛠 **Simple Setup**: Easy configuration and deployment

## Quick Start

### Prerequisites

- Python 3.9+
- [Ollama](https://ollama.ai) installed and running
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/donnievawter/insightchat.git
   cd insightchat
   ```

2. **Install dependencies**

   ```bash
   uv sync
   ```

3. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env file with your settings
   ```

4. **Start Ollama (if not already running)**

   ```bash
   ollama serve
   ```

5. **Pull an AI model**

   ```bash
   ollama pull llama3.2:latest
   ```

6. **Run the application**

   ```bash
   # Method 1: Using the launcher (recommended)
   uv run main.py
   
   # Method 2: Direct Flask run
   cd flask-chat-app/src
   uv run app.py
   ```

7. **Open your browser**
   Visit `http://localhost:5050`

## Configuration

### Environment Variables

- `FLASK_SECRET_KEY`: Secret key for Flask sessions
- `OLLAMA_URL`: Ollama API endpoint (default: `http://localhost:11434/api/chat`)
- `RAG_API_URL`: Optional RAG service endpoint
- `WHISPER_URL`: Whisper transcription service endpoint (default: `https://whisper.hlab.cam`)
- `TTS_BROADCAST_URL`: TTS broadcast endpoint (default: `https://tts.hlab.cam/speak`)
- `TTS_TIMEOUT`: TTS request timeout in seconds (default: `60`)
- `SERVICE_TIMEOUT`: Timeout for external services in seconds (default: `60`)
- `LOCAL_TIMEZONE`: Your local timezone (default: `America/Denver`)
- `FLASK_DEBUG`: Debug mode (default: `True`)
- `TOOL_WEATHER_ENABLED`: Enable weather tool (default: `false`)
- `TOOL_CALENDAR_ENABLED`: Enable calendar tool (default: `false`)

### Available Models

The application supports any model available through Ollama:

- `llama3.2:latest` - Latest Llama 3.2 (default)
- `llama3.1:latest` - Llama 3.1
- `mistral:latest` - Mistral
- `codellama:latest` - Code Llama
- And many more...

## Voice Input

InsightChat supports voice input for hands-free interaction:

1. Click the microphone (🎤) button next to the text input
2. Speak your question
3. Click the stop (⏹️) button when finished
4. The transcribed text will automatically appear in the input field
5. Click "Send" to submit to the AI

**Requirements**: A Whisper transcription service must be configured via `WHISPER_URL` in your `.env` file.

## Voice Assistant API

InsightChat includes a dedicated `/api/voice-query` endpoint for full voice-to-voice assistant integration with TTS broadcast:

### Features

- 🎤 Audio file transcription (via Whisper)
- 🤖 Tool-aware AI responses (weather, calendar, RAG)
- 📢 TTS broadcast to Google speakers
- 🗣️ Configurable voice models and speakers

### Quick Example

```bash
# Send audio file with TTS broadcast
python test_voice_api.py \
  --audio my_question.wav \
  --speaker "media_player.bedroom" \
  --tts-model "random"

# Or send text query
python test_voice_api.py \
  --text "What's the weather today?" \
  --broadcast
```

See **[VOICE_API.md](VOICE_API.md)** for complete API documentation and integration examples.

## RAG Integration

To enable RAG (Retrieval-Augmented Generation):

1. Set up a RAG service endpoint
2. Configure `RAG_API_URL` in your `.env` file
3. Toggle "Use RAG Context" in the chat interface

### Document Browser

When RAG is enabled, InsightChat includes a **Document Browser** feature that lets you manually select and load documents from your RAG system:

**Features:**
- 📚 **Browse All Documents** - View all documents indexed in your RAG system
- 🔍 **Live Search** - Filter documents by filename or folder path (e.g., type "topology" to see all documents in the topology directory)
- 📥 **Manual Load** - Load all chunks from any document, even if it wasn't returned in automatic search results
- 👁️ **Quick Preview** - View documents directly from the browser

**How to Use:**
1. Click the "📚 Browse Documents" button in the chat interface
2. Search for documents by typing in the search box (searches both filenames and paths)
3. Click "📥 Load" on any document to include all its chunks in your next question
4. Click "👁️ View" to preview the document content

This is especially useful when you know a specific document is relevant but the automatic RAG search didn't include it in the results.

### File Upload

Upload new documents directly to your RAG system from the chat interface:

**Features:**
- 📤 **Direct Upload** - Upload files directly from the chat interface to your RAG system
- 🔄 **Automatic Ingestion** - Files are automatically processed and indexed by the RAG system
- 📁 **Multiple Formats** - Supports PDF, TXT, MD, CSV, DOCX, DOC, JSON, XML, HTML, and more

**How to Use:**
1. Click the "📤 Upload File" button in the chat interface
2. Select the file you want to upload
3. Wait for the success notification
4. The file will appear in the Document Browser shortly after ingestion completes

**Note:** Upload uses a proxy endpoint to avoid CORS issues, so files are securely uploaded through the Flask backend to the RAG API.

### Response Management

**Download Markdown:**
- Every assistant response includes a "💾 MD" button
- Click to download the raw markdown content of that response
- Perfect for saving documentation, analysis results, or generated content
- Downloads as a `.md` file with timestamp

This feature is especially useful when the AI generates valuable documentation (like network topology descriptions) that you want to save and reuse.

## External Tools Integration

InsightChat can integrate with external APIs to provide specialized real-time data (weather, quotes, calendar, etc.). See **[TOOLS.md](TOOLS.md)** for detailed documentation.

### Quick Setup - Weather & Calendar Integration

1. **Enable tools in `.env`:**
   ```bash
   TOOL_WEATHER_ENABLED=true
   TOOL_WEATHER_API_URL=http://localhost:8000
   
   TOOL_CALENDAR_ENABLED=true
   TOOL_CALENDAR_API_URL=https://ics.hlab.cam
   ```

2. **Start your services** (if needed)

3. **Ask questions naturally:**
   - "What's the current temperature?"
   - "Do I have any meetings today?"
   - "What's on my calendar tomorrow?"
   - "Is it windy outside?"

The tool system automatically detects intent and calls appropriate APIs. No special syntax needed!

### Features

- ✅ **Intent-Based Routing** - Automatically detects which tools to use based on query context
- ✅ **Configuration-Driven** - Enable/disable tools via environment variables
- ✅ **Extensible** - Easy to add new tools
- ✅ **Works with RAG** - Combines tool data with document retrieval
- ✅ **Graceful Degradation** - Works without tools if unavailable
- ✅ **Smart Context Matching** - Distinguishes between similar queries (e.g., calendar events vs. document searches)

For complete documentation on adding new tools, see **[TOOLS.md](TOOLS.md)**.

## Document Viewing

InsightChat includes a built-in document viewer that supports multiple file types:

### Supported Formats

- **Audio Files**: WAV, MP3, M4A, FLAC, OGG - Play audio directly with HTML5 audio controls
- **Images**: PNG, JPG, JPEG, GIF, WEBP, SVG, BMP
- **Documents**: PDF (inline viewer), DOCX (text extraction)
- **Data**: CSV/TSV (interactive table view)
- **Email**: EML, EMLX (formatted email viewer)
- **Text**: MD, TXT, JSON, XML, YAML, and more

### Using the Document Viewer

1. When RAG is enabled, source documents appear with each AI response
2. Click "View Document" on any source to open it in the viewer
3. For audio files, use the built-in player controls to play, pause, seek, and adjust volume
4. Download any document using the download button in the viewer header

## Development

### Project Structure

```
insightchat/
├── flask-chat-app/
│   ├── src/
│   │   ├── app.py              # Main Flask application
│   │   ├── chat/
│   │   │   ├── routes.py       # Chat routes and API endpoints
│   │   │   ├── utils.py        # Utility functions
│   │   │   ├── tool_router.py  # External tools orchestration
│   │   │   ├── tools/          # External API integrations
│   │   │   │   ├── base_tool.py
│   │   │   │   ├── weather_tool.py
│   │   │   │   ├── calendar_tool.py
│   │   │   │   └── quotes_tool.py
│   │   │   └── whisper_client.py # Whisper API client
│   │   └── static/
│   │       └── css/
│   │           └── style.css   # Styles
│   └── templates/
│       └── chat.html          # Main chat template
├── test_voice_api.py          # Voice API test CLI tool
├── .env                       # Your configuration (gitignored)
├── .env.example               # Environment variables template
├── pyproject.toml             # Project dependencies
├── TOOLS.md                   # External tools documentation
├── VOICE_API.md               # Voice assistant API documentation
└── README.md                  # This file
```

### Adding New Models

To add support for new Ollama models, update the model dropdown in `templates/chat.html`:

```html
<option value="your-model:latest">Your Model</option>
```

## License

This project is open source and available under the [MIT License](LICENSE).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
