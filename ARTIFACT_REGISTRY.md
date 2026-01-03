# Artifact Registry Setup Guide

This guide explains how to use `vibe-trade-mcp` from GCP Artifact Registry in `vibe-trade-api`.

## Overview

`vibe-trade-api` depends on `vibe-trade-mcp` which is published to GCP Artifact Registry. The package is configured in `pyproject.toml` to use the Artifact Registry index.

## Configuration

### Production (Cloud Run)

The Artifact Registry index is configured in `pyproject.toml`:

```toml
[[tool.uv.index]]
name = "gcp-artifact-registry"
url = "https://us-central1-python.pkg.dev/vibe-trade-475704/vibe-trade-python/simple/"
explicit = false
```

**Authentication**: Cloud Run automatically authenticates using the service account credentials. The service account (`vibe-trade-api-runner`) has `roles/artifactregistry.reader` permission granted via Terraform.

### Local Development

For local development, you have two options:

#### Option 1: Use Artifact Registry (Recommended for testing production setup)

1. **Authenticate with GCP**:
   ```bash
   gcloud auth application-default login
   ```

2. **Install dependencies**:
   ```bash
   cd vibe-trade-api
   uv sync
   ```

#### Option 2: Use Local Path Dependency (Faster iteration)

1. **Uncomment the local path dependency** in `pyproject.toml`:
   ```toml
   [tool.uv.sources]
   vibe-trade-mcp = { path = "../vibe-trade-mcp", editable = true }
   ```

2. **Comment out the Artifact Registry index** (or leave it - uv will prefer the path source):
   ```toml
   # [[tool.uv.index]]
   # name = "gcp-artifact-registry"
   # url = "https://us-central1-python.pkg.dev/vibe-trade-475704/vibe-trade-python/simple/"
   # explicit = false
   ```

3. **Install dependencies**:
   ```bash
   cd vibe-trade-api
   uv sync
   ```

## Publishing vibe-trade-mcp

When `vibe-trade-mcp` is updated, publish it to Artifact Registry:

```bash
cd vibe-trade-mcp
make publish
```

This will:
1. Build the package
2. Authenticate with GCP
3. Upload to Artifact Registry

## Troubleshooting

### Issue: "Could not find a version that satisfies the requirement vibe-trade-mcp"

**Symptoms**: Installation fails with version not found error.

**Causes & Solutions**:

1. **Package not published yet**:
   ```bash
   cd vibe-trade-mcp
   make publish
   ```

2. **Wrong repository URL**:
   - Check `pyproject.toml` has the correct URL
   - Get the correct URL from Terraform:
     ```bash
     cd vibe-trade-terraform
     terraform output python_package_repo_url
     ```

3. **Authentication issues (local dev)**:
   ```bash
   gcloud auth application-default login
   gcloud auth print-access-token  # Verify you can get a token
   ```

4. **Service account permissions (Cloud Run)**:
   - Verify Terraform has granted permissions:
     ```bash
     cd vibe-trade-terraform
     terraform show | grep artifactregistry.reader
     ```
   - The service account should have `roles/artifactregistry.reader` on the Python repository

### Issue: "401 Unauthorized" or "403 Forbidden"

**Symptoms**: Authentication/authorization errors when installing.

**Solutions**:

1. **For local development**:
   ```bash
   gcloud auth application-default login
   ```

2. **For Cloud Run**:
   - Check service account has correct permissions in Terraform
   - Verify the service account is assigned to the Cloud Run service:
     ```bash
     gcloud run services describe vibe-trade-api --region=us-central1 --format="value(spec.template.spec.serviceAccountName)"
     ```

### Issue: "Package version already exists"

**Symptoms**: Publishing fails with "already exists" error.

**Solution**: This is normal if you're republishing the same version. Either:
- Increment the version in `vibe-trade-mcp/pyproject.toml`
- Or ignore the error (the package is already available)

### Issue: Docker build fails in CI/CD

**Symptoms**: Docker build fails when trying to install `vibe-trade-mcp`.

**Solutions**:

1. **For Cloud Build**:
   - Ensure the Cloud Build service account has `roles/artifactregistry.reader`
   - Or use a service account with appropriate permissions

2. **For local Docker builds**:
   ```bash
   # Authenticate Docker with Artifact Registry
   gcloud auth configure-docker us-central1-python.pkg.dev
   
   # Or use application-default credentials
   gcloud auth application-default login
   ```

### Issue: Import works locally but fails in Cloud Run

**Symptoms**: Code works locally but fails in production.

**Solutions**:

1. **Check service account permissions**:
   ```bash
   gcloud projects get-iam-policy vibe-trade-475704 \
     --flatten="bindings[].members" \
     --filter="bindings.members:serviceAccount:vibe-trade-api-runner@vibe-trade-475704.iam.gserviceaccount.com" \
     --format="table(bindings.role)"
   ```

2. **Verify the package is published**:
   ```bash
   # List packages in the repository
   gcloud artifacts packages list \
     --repository=vibe-trade-python \
     --location=us-central1 \
     --format="table(name,createTime)"
   ```

3. **Check Cloud Run logs**:
   ```bash
   gcloud run services logs read vibe-trade-api --region=us-central1 --limit=50
   ```

## Verifying Setup

### Test local installation:
```bash
cd vibe-trade-api
uv sync
uv run python -c "from vibe_trade_mcp.db.firestore_client import FirestoreClient; print('✅ Import successful')"
```

### Test Artifact Registry access:
```bash
# Get repository URL
cd vibe-trade-terraform
REPO_URL=$(terraform output -raw python_package_repo_url)

# Test install
pip install --index-url $REPO_URL vibe-trade-mcp
```

### Verify service account permissions:
```bash
gcloud artifacts repositories get-iam-policy vibe-trade-python \
  --location=us-central1 \
  --format="table(bindings.role,bindings.members)"
```

## Getting Help

If you encounter issues:

1. Check Cloud Run logs for detailed error messages
2. Verify authentication: `gcloud auth list`
3. Verify service account permissions in Terraform
4. Check Artifact Registry repository exists and has packages
5. Review `vibe-trade-mcp/PUBLISHING.md` for publishing details

