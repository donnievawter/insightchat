# 🐳 Docker Deployment Guide

This guide covers deploying InsightChat using Docker Compose with uv for dependency management.

## 📋 Prerequisites

- Docker & Docker Compose installed
- (Optional) Make for convenient commands

## 🚀 Quick Start

### 1. **Set up environment**
```bash
# Copy environment template
cp .env.docker.example .env.docker

# Edit with your configuration
nano .env.docker
```

### 2. **Start services**
```bash
# Using make (recommended)
make up

# Or directly with docker-compose
docker-compose up -d
```

### 3. **Pull Ollama models**
```bash
# Pull recommended models
make pull-models

# Or pull specific model
docker-compose exec ollama ollama pull llama3.2:latest
```

### 4. **Access the application**
- **InsightChat**: http://localhost:5030
- **Ollama API**: http://localhost:11434

## 🛠️ Available Commands

```bash
make help           # Show all available commands
make build          # Build Docker images
make up             # Start in background
make dev            # Start in foreground with logs
make down           # Stop services
make logs           # View InsightChat logs
make shell          # Access container shell
make test-rag       # Test RAG functionality
make clean          # Clean up containers and volumes
```

## 🏗️ Architecture

The Docker setup includes:

- **InsightChat**: Main Flask application with uv
- **Ollama**: Local AI model server (optional)
- **Volumes**: Persistent storage for Ollama models
- **Networks**: Internal communication between services

## ⚙️ Configuration

### Environment Variables

Set these in `.env.docker`:

```bash
# Flask Configuration
FLASK_SECRET_KEY=your-secure-secret-key
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=5030

# Ollama Configuration
OLLAMA_URL=http://ollama:11434/api/chat

# RAG Configuration
RAG_API_URL=https://your-rag-service.com
```

### External Ollama

To use external Ollama instead of containerized:

```yaml
# In docker-compose.override.yml
services:
  insightchat:
    environment:
      - OLLAMA_URL=http://your-ollama-host:11434/api/chat
  
  ollama:
    profiles:
      - disabled
```

## 🌍 Production Deployment

### Using production compose file:
```bash
# Start production deployment
make prod

# Or manually
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Production features:
- Debug mode disabled
- Proper logging configuration  
- Health checks enabled
- Auto-restart policies

## 🔧 Customization

### Custom Dockerfile

The Dockerfile uses:
- **Multi-stage build** for optimization
- **uv** for fast dependency management
- **Non-root user** for security
- **Health checks** for monitoring

### Volume Mounts

```yaml
services:
  insightchat:
    volumes:
      # Custom configuration
      - ./custom-config:/app/config:ro
      # Logs directory
      - ./logs:/app/logs
```

## 🐛 Troubleshooting

### View logs
```bash
# InsightChat logs
make logs

# All service logs  
make logs-all

# Specific service
docker-compose logs ollama
```

### Test RAG connection
```bash
# Test RAG functionality
make test-rag

# Access container for debugging
make shell
```

### Common issues

1. **Port conflicts**: Change ports in docker-compose.yml
2. **Model not found**: Pull models with `make pull-models`
3. **RAG connection**: Verify RAG_API_URL in .env.docker
4. **Permissions**: Ensure proper file permissions for volumes

## 🚀 Advanced Usage

### GPU Support (NVIDIA)

Uncomment GPU section in docker-compose.yml:

```yaml
ollama:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

### Custom Networks

```yaml
networks:
  insightchat-network:
    external: true
    name: your-existing-network
```

### Scaling

```bash
# Scale InsightChat instances
docker-compose up -d --scale insightchat=3
```

## 📊 Monitoring

### Health Checks

Services include health checks accessible via:
```bash
docker-compose ps
```

### Logs

```bash
# Follow logs in real-time
docker-compose logs -f

# Export logs
docker-compose logs > deployment.log
```

## 🔄 Updates

```bash
# Update and rebuild
git pull
make build
make down
make up
```

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [uv Documentation](https://github.com/astral-sh/uv)
- [Ollama Docker Guide](https://ollama.ai/blog/ollama-docker)