.PHONY: help build up-api up-cli down logs clean

help:
	@echo "Personal Care Chatbot - Docker Commands"
	@echo "========================================"
	@echo "make build      - Build Docker images"
	@echo "make up-api     - Start FastAPI application"
	@echo "make up-cli     - Start CLI application"
	@echo "make down       - Stop all services"
	@echo "make logs       - View logs"
	@echo "make clean      - Remove all containers and volumes"
	@echo ""

build:
	@echo "Building Docker images..."
	docker-compose build

up-api:
	@echo "Starting FastAPI application..."
	docker-compose up -d postgres redis api
	@echo ""
	@echo "✅ FastAPI is running at http://localhost:8000"
	@echo "📊 View logs: make logs"
	@echo "🛑 Stop: make down"

up-cli:
	@echo "Starting CLI application..."
	docker-compose up -d postgres redis
	@echo "Waiting for services to be ready..."
	@sleep 5
	docker-compose --profile cli run --rm cli
	@echo ""

down:
	@echo "Stopping all services..."
	docker-compose --profile cli down

logs:
	docker-compose logs -f

clean:
	@echo "Removing all containers, volumes, and images..."
	docker-compose --profile cli down -v
	docker system prune -af
