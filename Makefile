.PHONY: install locally run test lint lint-fix format format-check check ci clean \
	docker-build docker-push docker-build-push deploy deploy-image force-revision

install:
	@echo "📦 Installing dependencies..."
	@echo "   Using local path dependency for vibe-trade-mcp (../vibe-trade-mcp)"
	uv sync --all-groups

# Setup for local development: install deps, fix linting, and format code
locally: install lint-fix format
	@echo "✅ Local setup complete!"

# Run the server locally
# Uses emulator if FIRESTORE_EMULATOR_HOST is set in .env, otherwise production
run:
	@bash -c '\
	if [ -f .env ]; then \
		export $$(grep -v "^#" .env | xargs); \
	fi; \
	if [ -z "$$FIRESTORE_EMULATOR_HOST" ] && [ -z "$$GOOGLE_CLOUD_PROJECT" ]; then \
		echo "⚠️  Warning: Neither FIRESTORE_EMULATOR_HOST nor GOOGLE_CLOUD_PROJECT set"; \
		echo "   For local dev: export FIRESTORE_EMULATOR_HOST=localhost:8081"; \
		echo "   For production: export GOOGLE_CLOUD_PROJECT=vibe-trade-475704"; \
	fi; \
	if [ -n "$$FIRESTORE_EMULATOR_HOST" ]; then \
		nc -z localhost 8081 2>/dev/null || (echo "❌ Firestore emulator is not running on localhost:8081"; echo "   Start it with: make emulator (in vibe-trade-mcp)"; exit 1); \
		echo "✅ Firestore emulator is running"; \
	fi; \
	echo "🚀 Starting API server..."; \
	if [ -n "$$FIRESTORE_EMULATOR_HOST" ]; then \
		echo "   Using Firestore Emulator: $$FIRESTORE_EMULATOR_HOST"; \
	else \
		echo "   Using Production Firestore: $$GOOGLE_CLOUD_PROJECT"; \
	fi; \
	echo "   Endpoint: http://localhost:8080"; \
	uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8080'

# Development server with hot reload
dev: run

test:
	uv run python -m pytest tests/ -v

test-cov:
	uv run python -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=html --cov-fail-under=60

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check . --fix

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

check: lint format-check test-cov
	@echo "✅ All checks passed!"

ci: lint-fix format-check test-cov
	@echo "✅ CI checks passed!"

clean:
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov/ coverage.xml
	rm -rf *.egg-info build/ dist/

# Docker commands - use environment variable or default
# Set ARTIFACT_REGISTRY_URL env var or it will use the default
ARTIFACT_REGISTRY_URL ?= us-central1-docker.pkg.dev/vibe-trade-475704/vibe-trade-api
IMAGE_TAG := $(ARTIFACT_REGISTRY_URL)/vibe-trade-api:latest

# Note: vibe-trade-mcp is now a local path dependency (no version pinning needed)

docker-build:
	@echo "🏗️  Building Docker image..."
	@echo "   Image: $(IMAGE_TAG)"
	@echo "   Using local path dependency for vibe-trade-mcp"
	@echo "   Building from parent directory to include both projects"
	@cd .. && DOCKER_BUILDKIT=1 docker build --platform linux/amd64 \
		-f vibe-trade-api/Dockerfile \
		-t $(IMAGE_TAG) \
		.
	@echo "✅ Build complete"

docker-push:
	@echo "📤 Pushing Docker image..."
	@echo "   Image: $(IMAGE_TAG)"
	docker push $(IMAGE_TAG)
	@echo "✅ Push complete"

docker-build-push: docker-build docker-push

# Deployment workflow
# Step 1: Build and push Docker image
# Step 2: Force Cloud Run to use the new image
# For infrastructure changes, run 'terraform apply' in vibe-trade-terraform separately
deploy: docker-build-push force-revision
	@echo ""
	@echo "✅ Code deployment complete!"

# Force Cloud Run to create a new revision with the latest image
# Uses environment variables or defaults
force-revision:
	@echo "🔄 Forcing Cloud Run to use latest image..."
	@SERVICE_NAME=$${SERVICE_NAME:-vibe-trade-api} && \
		REGION=$${REGION:-us-central1} && \
		PROJECT_ID=$${PROJECT_ID:-vibe-trade-475704} && \
		IMAGE_REPO=$${ARTIFACT_REGISTRY_URL:-us-central1-docker.pkg.dev/vibe-trade-475704/vibe-trade-api} && \
		echo "   Service: $$SERVICE_NAME" && \
		echo "   Region: $$REGION" && \
		echo "   Image: $$IMAGE_REPO/vibe-trade-api:latest" && \
		gcloud run services update $$SERVICE_NAME \
			--region=$$REGION \
			--project=$$PROJECT_ID \
			--image=$$IMAGE_REPO/vibe-trade-api:latest \
			2>&1 | grep -E "(Deploying|revision|Service URL|Done)" || (echo "⚠️  Update may have failed or no changes needed" && exit 1)

deploy-image: docker-build-push
	@echo ""
	@echo "✅ Image deployed!"
	@echo "📋 Run 'make force-revision' to update Cloud Run, or 'terraform apply' in vibe-trade-terraform for infrastructure changes"
