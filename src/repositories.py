"""Repository initialization and access.

This module imports and initializes repositories from the MCP project.
Both API and MCP use the same Firestore client and repository implementations.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud.firestore import Client

# Load .env file if it exists (for local development)
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Import Firestore client from MCP project
# Note: In production, these could be shared via a common package
# For now, we'll import directly (requires MCP to be in Python path or installed)
try:
    # Try importing from installed package
    from vibe_trade_mcp.db.firestore_client import FirestoreClient
    from vibe_trade_mcp.db.card_repository import CardRepository
    from vibe_trade_mcp.db.strategy_repository import StrategyRepository
except ImportError:
    # Fallback: import from relative path (for development)
    import sys
    from pathlib import Path

    mcp_path = Path(__file__).parent.parent.parent / "vibe-trade-mcp" / "src"
    if mcp_path.exists():
        sys.path.insert(0, str(mcp_path.parent))
        from db.firestore_client import FirestoreClient
        from db.card_repository import CardRepository
        from db.strategy_repository import StrategyRepository
    else:
        raise ImportError(
            "Could not import MCP repositories. "
            "Ensure vibe-trade-mcp is installed or in the Python path."
        )

# Initialize Firestore client
project = os.getenv("GOOGLE_CLOUD_PROJECT")
if not project:
    raise ValueError("GOOGLE_CLOUD_PROJECT environment variable must be set")

database = os.getenv("FIRESTORE_DATABASE")
if not database:
    raise ValueError(
        "FIRESTORE_DATABASE environment variable must be set. "
        "For emulator: FIRESTORE_DATABASE=(default) "
        "For production: FIRESTORE_DATABASE=strategy"
    )
# Use None for "(default)" database (emulator limitation)
database = None if database == "(default)" else database

firestore_client: Client = FirestoreClient.get_client(project=project, database=database)

# Initialize repositories
card_repository = CardRepository(client=firestore_client)
strategy_repository = StrategyRepository(client=firestore_client)

