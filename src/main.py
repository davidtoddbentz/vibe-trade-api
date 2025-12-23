"""FastAPI application with JWT authentication."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routes import strategies, threads

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables

env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    logger.info("🚀 Starting Vibe Trade API Server...")
    logger.info(f"📡 Server running on port {os.getenv('PORT', '8080')}")
    logger.info(f"🔧 GOOGLE_CLOUD_PROJECT: {os.getenv('GOOGLE_CLOUD_PROJECT')}")
    logger.info(f"🔧 FIRESTORE_DATABASE: {os.getenv('FIRESTORE_DATABASE')}")
    logger.info(f"🔧 FIRESTORE_EMULATOR_HOST: {os.getenv('FIRESTORE_EMULATOR_HOST', 'Not set (using production)')}")
    
    # Log Firestore connection info (lazy - only when accessed)
    # Don't access repositories here to avoid triggering import during startup
    # They will be initialized when first used by endpoints
    
    logger.info("✅ Ready for requests")
    yield
    # Shutdown
    logger.info("👋 Shutting down Vibe Trade API Server...")


# Create FastAPI app
app = FastAPI(
    title="Vibe Trade API",
    description="API server for vibe-trade with JWT authentication",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
# In production, restrict origins to your UI domain
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(strategies.router)
app.include_router(threads.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}





