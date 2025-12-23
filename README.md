# Vibe Trade API

FastAPI server for vibe-trade with Firebase authentication and user-scoped data access.

## Overview

This API provides user-facing endpoints for:
- Thread management (persistent agent conversations)
- Strategy access (user-scoped)
- Firebase authentication via ID tokens

## Architecture

- **Authentication**: Firebase ID tokens (validated via Firebase Admin SDK)
- **Data Access**: Direct Firestore access (shared repositories with MCP)
- **User Scoping**: All data operations are scoped to `user_id` extracted from verified Firebase tokens

## Setup

### Prerequisites

- Python 3.10+
- Google Cloud Project with Firestore
- Firebase project (for authentication)

### Installation

```bash
# Install dependencies
uv sync

# Or with pip
pip install -e .
```

### Environment Variables

Create a `.env` file:

```bash
# Google Cloud
GOOGLE_CLOUD_PROJECT=your-project-id
FIRESTORE_DATABASE=strategy  # or "(default)" for emulator

# Server
PORT=8080

# CORS (comma-separated origins, or "*" for all)
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

**Note**: Firebase Admin SDK uses Application Default Credentials on GCP Cloud Run. For local development, you may need to set up service account credentials.

### Running Locally

```bash
# Development server
uvicorn src.main:app --reload --port 8080

# Or with uv
uv run uvicorn src.main:app --reload --port 8080
```

### Running with Firestore Emulator

```bash
# Set emulator host
export FIRESTORE_EMULATOR_HOST=localhost:8080
export FIRESTORE_DATABASE="(default)"

# Run server
uvicorn src.main:app --reload
```

## API Endpoints

### Authentication

All endpoints require Firebase authentication via `Authorization: Bearer <token>` header.

The token must be a valid Firebase ID token obtained from the client-side Firebase SDK.

### Threads

- `POST /api/threads` - Create a new thread
- `GET /api/threads` - List user's threads
- `GET /api/threads/{thread_id}` - Get thread (verifies ownership)

### Strategies

- `GET /api/strategies` - List user's strategies
- `GET /api/strategies/{strategy_id}` - Get strategy with cards (verifies ownership)
- `GET /api/strategies/threads/{thread_id}/strategy` - Get strategy linked to thread

## Development

### Project Structure

```
src/
  ├── main.py           # FastAPI app
  ├── auth.py           # JWT validation
  ├── repositories.py    # Firestore repositories (imported from MCP)
  ├── models/
  │   └── thread.py     # Thread domain model
  └── routes/
      ├── threads.py    # Thread endpoints
      └── strategies.py # Strategy endpoints
```

### Dependencies

- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `firebase-admin` - Firebase Admin SDK for token verification
- `google-cloud-firestore` - Firestore client
- `pydantic` - Data validation

## Security

- **Token Validation**: All Firebase ID tokens are validated using Firebase Admin SDK
- **User Scoping**: `user_id` is extracted from verified Firebase tokens (not user input)
- **Ownership Verification**: All data access verifies user ownership
- **No Injection**: Owner ID comes from verified headers, preventing injection attacks

## Notes

- This API shares repositories with the MCP project
- MCP remains internal-only (no direct user access)
- Agent calls MCP tools directly, API accesses Firestore directly

