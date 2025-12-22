FROM python:3.11-slim

WORKDIR /app

# Install uv for linux/amd64
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN chmod +x /usr/local/bin/uv

# Install keyring for GCP Artifact Registry authentication
RUN pip install --no-cache-dir keyring keyrings.google-artifactregistry-auth

# Copy API project
COPY pyproject.toml ./
COPY uv.lock ./
COPY src/ ./src/

# Install dependencies first (creates the uv-managed venv)
RUN uv sync --no-dev --frozen

# Install vibe-trade-mcp from GCP Artifact Registry
# For Cloud Build: Authentication is automatic via service account credentials
# For local Docker builds: Use Docker BuildKit secrets to pass access token
# For local dev (make install): Uses gcloud auth print-access-token directly
RUN --mount=type=secret,id=gcp_token \
    if [ -f /run/secrets/gcp_token ]; then \
        uv pip install \
            --index-url "https://oauth2accesstoken:$(cat /run/secrets/gcp_token)@us-central1-python.pkg.dev/vibe-trade-475704/vibe-trade-python/simple/" \
            --extra-index-url https://pypi.org/simple/ \
            vibe-trade-mcp; \
    else \
        echo "Installing vibe-trade-mcp (assuming Cloud Build with automatic auth via keyring)..."; \
        uv pip install \
            --index-url https://us-central1-python.pkg.dev/vibe-trade-475704/vibe-trade-python/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            vibe-trade-mcp; \
    fi

# Expose port (Cloud Run uses PORT env var, default to 8080)
ENV PORT=8080
EXPOSE 8080

# Run the FastAPI server
CMD ["sh", "-c", "uv run uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}"]

