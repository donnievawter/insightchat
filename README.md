# InsightChat

A clean, modern AI-powered chat application with optional RAG (Retrieval-Augmented Generation) support using Ollama.

## Features

- 🤖 **Multiple AI Models**: Support for various Ollama models (Llama 3.2, Llama 3.1, Mistral, CodeLlama, etc.)
- 🔍 **RAG Integration**: Optional context enhancement using external document retrieval
- 💬 **Clean Chat Interface**: Modern, responsive web interface
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
   cp flask-chat-app/.env.example flask-chat-app/.env
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
- `FLASK_DEBUG`: Debug mode (default: `True`)

### Available Models

The application supports any model available through Ollama:

- `llama3.2:latest` - Latest Llama 3.2 (default)
- `llama3.1:latest` - Llama 3.1
- `mistral:latest` - Mistral
- `codellama:latest` - Code Llama
- And many more...

## RAG Integration

To enable RAG (Retrieval-Augmented Generation):

1. Set up a RAG service endpoint
2. Configure `RAG_API_URL` in your `.env` file
3. Toggle "Use RAG Context" in the chat interface

## Development

### Project Structure

```
insightchat/
├── flask-chat-app/
│   ├── src/
│   │   ├── app.py              # Main Flask application
│   │   ├── chat/
│   │   │   ├── routes.py       # Chat routes and logic
│   │   │   └── utils.py        # Utility functions
│   │   └── static/
│   │       └── css/
│   │           └── style.css   # Styles
│   ├── templates/
│   │   └── chat.html          # Main chat template
│   └── .env.example           # Environment variables template
├── pyproject.toml             # Project dependencies
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
