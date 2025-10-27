# 🚀 Quick Docker Setup for External Ollama

This setup is optimized for running InsightChat in a lightweight container while using an external Ollama instance on a high-memory Mac.

## 📋 Setup Steps

### 1. **Configure Environment**
```bash
# Create environment file
make setup

# Edit .env.docker with your Mac's IP address
nano .env.docker
```

Update the Ollama URL to point to your Mac:
```bash
# Replace with your Mac's IP address or use host.docker.internal for same machine
OLLAMA_URL=http://192.168.1.100:11434/api/chat
RAG_API_URL=https://rag.hlab.cam
FLASK_SECRET_KEY=your-secret-key
```

### 2. **Ensure Ollama is accessible**

On your Mac running Ollama, make sure it's accessible from Docker:
```bash
# Start Ollama with host binding (if not already)
OLLAMA_HOST=0.0.0.0 ollama serve

# Test from your Docker host
curl http://your-mac-ip:11434/api/tags
```

### 3. **Start InsightChat**
```bash
# Build and start
make build
make up

# Or in one command
make dev
```

### 4. **Test the setup**
```bash
# Test RAG functionality
make test-rag

# View logs
make logs

# Access container for debugging
make shell
```

## 🌐 Access Points

- **InsightChat**: http://localhost:5030
- **External Ollama**: http://your-mac-ip:11434

## 🔧 Configuration Notes

### Network Connectivity
- Container uses `host.docker.internal` to access host services
- For production, use actual IP addresses
- Ensure firewall allows connections on port 11434

### Lightweight Container
- Only runs Flask app with uv
- No GPU requirements
- Minimal memory footprint
- Fast startup time

### External Dependencies
- **Ollama**: Runs on Mac with 128GB RAM
- **RAG Service**: External service at rag.hlab.cam
- **Models**: Managed on the external Mac

## 🚨 Troubleshooting

### Connection Issues
```bash
# Test Ollama connectivity from container
make shell
curl $OLLAMA_URL/api/tags

# Check if Mac Ollama is accessible
curl http://your-mac-ip:11434/api/tags
```

### Common Solutions
1. **Mac Firewall**: Allow connections on port 11434
2. **Ollama Host**: Ensure OLLAMA_HOST=0.0.0.0 when starting Ollama
3. **Network**: Use IP address instead of hostname if DNS issues
4. **Docker Network**: Container is on bridge network with external access

## 📝 Quick Commands

```bash
make help       # Show all commands
make setup      # Create .env.docker template  
make build      # Build container
make up         # Start in background
make dev        # Start with logs
make logs       # View logs
make shell      # Access container
make test-rag   # Test RAG functionality
make clean      # Clean up
```

This setup gives you the best of both worlds: lightweight containers for the web app and your powerful Mac handling the heavy AI model inference! 🎯