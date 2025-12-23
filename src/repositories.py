"""Repository initialization and access.

This module imports and initializes repositories from the MCP project.
Both API and MCP use the same Firestore client and repository implementations.
"""

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv
from google.cloud.firestore import Client

if TYPE_CHECKING:
    from vibe_trade_mcp.db.card_repository import CardRepository
    from vibe_trade_mcp.db.strategy_repository import StrategyRepository

logger = logging.getLogger(__name__)

# Load .env file if it exists (for local development)
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Lazy imports - only import when needed
# This allows the module to be imported even if vibe-trade-mcp isn't installed
_FirestoreClient = None
_CardRepository = None
_StrategyRepository = None

# Initialize Firestore client and repositories lazily
# These will be initialized when first accessed
_firestore_client: Client | None = None
_card_repository = None
_strategy_repository = None


def _import_mcp_modules():
    """Lazy import of MCP modules."""
    global _FirestoreClient, _CardRepository, _StrategyRepository
    
    if _FirestoreClient is not None:
        return  # Already imported
    
    try:
        from vibe_trade_mcp.db.firestore_client import FirestoreClient
        from vibe_trade_mcp.db.card_repository import CardRepository
        from vibe_trade_mcp.db.strategy_repository import StrategyRepository
        
        _FirestoreClient = FirestoreClient
        _CardRepository = CardRepository
        _StrategyRepository = StrategyRepository
    except ImportError as e:
        logger.error(f"❌ Failed to import vibe-trade-mcp: {e}", exc_info=True)
        raise ImportError(
            "vibe-trade-mcp package is not installed. "
            "Install it with: uv pip install --index-url <artifact-registry-url> vibe-trade-mcp"
        ) from e


def _initialize_repositories() -> None:
    """Initialize Firestore client and repositories."""
    global _firestore_client, _card_repository, _strategy_repository
    
    if _firestore_client is not None:
        return  # Already initialized
    
    # Import MCP modules first (lazy)
    _import_mcp_modules()
    
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
        _firestore_client = _FirestoreClient.get_client(project=project, database=database)
        logger.info(f"✅ Firestore client initialized successfully")
        logger.info(f"   Client project: {_firestore_client.project}")
        logger.info(f"   Client database: {getattr(_firestore_client, '_database', 'default')}")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Firestore client: {e}", exc_info=True)
        raise

    # Initialize repositories
    try:
        _card_repository = _CardRepository(client=_firestore_client)
        _strategy_repository = _StrategyRepository(client=_firestore_client)
        logger.info("✅ Repositories initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize repositories: {e}", exc_info=True)
        raise


# Lazy initialization - initialize on first access
def get_firestore_client() -> Client:
    """Get Firestore client (lazy initialization)."""
    _initialize_repositories()
    return _firestore_client


def get_card_repository():
    """Get card repository (lazy initialization)."""
    _initialize_repositories()
    return _card_repository


def get_strategy_repository():
    """Get strategy repository (lazy initialization)."""
    _initialize_repositories()
    return _strategy_repository


# For backward compatibility, provide module-level access (lazy)
class _LazyRepositories:
    """Lazy accessor for repositories."""
    
    @property
    def firestore_client(self) -> Client:
        """Get Firestore client."""
        return get_firestore_client()
    
    @property
    def card_repository(self):  # type: ignore
        """Get card repository."""
        return get_card_repository()
    
    @property
    def strategy_repository(self):  # type: ignore
        """Get strategy repository."""
        return get_strategy_repository()


# Create singleton instance for backward compatibility
_repos = _LazyRepositories()

# Module-level accessors (backward compatible)
def __getattr__(name: str):
    """Lazy module-level attribute access."""
    if name == "firestore_client":
        return get_firestore_client()
    elif name == "card_repository":
        return get_card_repository()
    elif name == "strategy_repository":
        return get_strategy_repository()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
