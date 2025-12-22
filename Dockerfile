FROM python:3.11-slim

WORKDIR /app

# Install uv for linux/amd64
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN chmod +x /usr/local/bin/uv

# Copy dependency files and source code
COPY pyproject.toml ./
COPY uv.lock ./
COPY src/ ./src/

# Install dependencies
RUN uv sync --no-dev --frozen

# Expose port (Cloud Run uses PORT env var, default to 8080)
ENV PORT=8080
EXPOSE 8080

# Run the FastAPI server
CMD ["sh", "-c", "uv run uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}"]

