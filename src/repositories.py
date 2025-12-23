"""Repository initialization and access.

This module imports and initializes repositories from the MCP project.
Both API and MCP use the same Firestore client and repository implementations.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud.firestore import Client

logger = logging.getLogger(__name__)

# Load .env file if it exists (for local development)
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Import Firestore client from MCP package
# vibe-trade-mcp is installed as a Python package dependency
from vibe_trade_mcp.db.firestore_client import FirestoreClient
from vibe_trade_mcp.db.card_repository import CardRepository
from vibe_trade_mcp.db.strategy_repository import StrategyRepository

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

logger.info(f"Initializing Firestore client: project={project}, database={database}")

try:
    firestore_client: Client = FirestoreClient.get_client(project=project, database=database)
    logger.info(f"✅ Firestore client initialized successfully")
    logger.info(f"   Client project: {firestore_client.project}")
    logger.info(f"   Client database: {getattr(firestore_client, '_database', 'default')}")
except Exception as e:
    logger.error(f"❌ Failed to initialize Firestore client: {e}", exc_info=True)
    raise

# Initialize repositories
try:
    card_repository = CardRepository(client=firestore_client)
    strategy_repository = StrategyRepository(client=firestore_client)
    logger.info("✅ Repositories initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize repositories: {e}", exc_info=True)
    raise

