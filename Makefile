.PHONY: help install dev test lint format clean run build push

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	uv sync

dev: ## Run development server with hot reload
	uv run uvicorn src.main:app --reload --port 8080

test: ## Run tests
	uv run pytest

lint: ## Run linter
	uv run ruff check src/

format: ## Format code
	uv run ruff format src/

clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .ruff_cache/ htmlcov/

run: ## Run production server
	uv run uvicorn src.main:app --host 0.0.0.0 --port 8080

build: ## Build Docker image
	docker build -t vibe-trade-api:latest .

push: ## Push Docker image to Artifact Registry (requires GCP auth)
	@if [ -z "$(REGION)" ] || [ -z "$(PROJECT_ID)" ]; then \
		echo "Error: REGION and PROJECT_ID must be set"; \
		echo "Usage: make push REGION=us-central1 PROJECT_ID=your-project-id"; \
		exit 1; \
	fi
	docker tag vibe-trade-api:latest $(REGION)-docker.pkg.dev/$(PROJECT_ID)/vibe-trade-api/vibe-trade-api:latest
	docker push $(REGION)-docker.pkg.dev/$(PROJECT_ID)/vibe-trade-api/vibe-trade-api:latest

