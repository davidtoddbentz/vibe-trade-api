# Quick Start: Using vibe-trade-mcp from Artifact Registry

## For Local Development

### Option 1: Use Artifact Registry (Test Production Setup)

```bash
# 1. Authenticate with GCP
gcloud auth application-default login

# 2. Install dependencies
cd vibe-trade-api
uv sync

# 3. Verify import works
uv run python -c "from vibe_trade_mcp.db.firestore_client import FirestoreClient; print('✅ OK')"
```

### Option 2: Use Local Path (Faster Development)

1. Uncomment in `pyproject.toml`:
   ```toml
   [tool.uv.sources]
   vibe-trade-mcp = { path = "../vibe-trade-mcp", editable = true }
   ```

2. Install:
   ```bash
   uv sync
   ```

## For Production (Cloud Run)

The Dockerfile automatically uses Artifact Registry. No changes needed!

**Before deploying**, ensure `vibe-trade-mcp` is published:

```bash
cd vibe-trade-mcp
make publish
```

## Publishing vibe-trade-mcp

When you update `vibe-trade-mcp`, publish it:

```bash
cd vibe-trade-mcp
make publish
```

The package will be available at:
```
https://us-central1-python.pkg.dev/vibe-trade-475704/vibe-trade-python/simple/
```

## Troubleshooting

See `ARTIFACT_REGISTRY.md` for detailed troubleshooting.

**Quick checks:**
- ✅ Authenticated? `gcloud auth list`
- ✅ Package published? `cd vibe-trade-mcp && make publish`
- ✅ Service account has permissions? (Check Terraform)

