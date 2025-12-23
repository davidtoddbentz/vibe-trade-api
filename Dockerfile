FROM python:3.11-slim

WORKDIR /workspace

# Install uv for linux/amd64
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN chmod +x /usr/local/bin/uv

# Copy both projects to match the expected directory structure
# pyproject.toml references ../vibe-trade-mcp, so we need:
# /workspace/vibe-trade-api/ (where we'll work)
# /workspace/vibe-trade-mcp/ (the dependency)
COPY vibe-trade-mcp/ ./vibe-trade-mcp/
COPY vibe-trade-api/ ./vibe-trade-api/

# Install dependencies from the API directory
# uv sync will resolve the ../vibe-trade-mcp path dependency
WORKDIR /workspace/vibe-trade-api
RUN uv sync --no-dev --frozen

# Sanity-check import at build time
RUN .venv/bin/python -c "import vibe_trade_mcp; print('vibe_trade_mcp import ok')"

# Expose port (Cloud Run uses PORT env var, default to 8080)
ENV PORT=8080
EXPOSE 8080

# Run the FastAPI server (do NOT use `uv run` at runtime)
WORKDIR /workspace/vibe-trade-api
CMD ["sh", "-c", ".venv/bin/python -m uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
