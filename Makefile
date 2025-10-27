.PHONY: build up down logs shell test clean prod

# Development commands
build:
	docker compose build

up:
	docker compose up -d

dev:
	docker compose up

down:
	docker compose down

logs:
	docker compose logs -f insightchat

logs-all:
	docker compose logs -f

# Production commands
prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-build:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml build

prod-down:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# Utility commands
shell:
	docker compose exec insightchat /bin/bash

test-rag:
	docker compose exec insightchat uv run test_rag.py

restart:
	docker compose restart insightchat

clean:
	docker compose down -v
	docker system prune -f

# Setup commands
setup:
	cp .env.docker.example .env.docker
	@echo "Please edit .env.docker with your Ollama Mac IP address and other configuration"

# Note: Ollama runs externally - use these commands on your Mac
# ollama pull llama3.2:latest
# ollama pull mistral:latest

help:
	@echo "Available commands:"
	@echo "  build     - Build Docker images"
	@echo "  up        - Start services in background"
	@echo "  dev       - Start services in foreground"
	@echo "  down      - Stop services"
	@echo "  logs      - View InsightChat logs"
	@echo "  logs-all  - View all service logs"
	@echo "  prod      - Start production deployment"
	@echo "  shell     - Access InsightChat container shell"
	@echo "  test-rag  - Test RAG functionality"
	@echo "  clean     - Remove containers and cleanup"
	@echo "  setup     - Create .env.docker from template"
	@echo ""
	@echo "Note: Ollama runs externally on Mac with 128GB RAM"
	@echo "Configure OLLAMA_URL in .env.docker to point to your Mac"
