"""Authentication utilities for extracting user ID from Firebase tokens."""

import logging
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

# Try to import and initialize Firebase Admin SDK
FIREBASE_AVAILABLE = False
auth = None
firebase_admin = None

try:
    import firebase_admin
    from firebase_admin import auth, credentials

    # Initialize Firebase Admin SDK (uses Application Default Credentials on GCP)
    if not firebase_admin._apps:
        try:
            firebase_admin.initialize_app()
            logger.info("✅ Firebase Admin SDK initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Firebase Admin SDK: {e}", exc_info=True)
            raise
    FIREBASE_AVAILABLE = True
    logger.info("✅ Firebase authentication available")
except ImportError as e:
    logger.error(f"❌ Firebase Admin SDK not installed: {e}")
    FIREBASE_AVAILABLE = False
    auth = None
except Exception as e:
    logger.error(f"❌ Firebase Admin SDK initialization failed: {e}", exc_info=True)
    FIREBASE_AVAILABLE = False
    auth = None

# Create security scheme that doesn't require auth (auto_error=False)
security = HTTPBearer(auto_error=False)


def get_user_id_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> Optional[str]:
    """Extract and validate user_id from Firebase ID token (optional).

    Returns None if no token provided (allows unauthenticated access).

    Args:
        credentials: HTTP Bearer token from Authorization header (optional)

    Returns:
        user_id: User identifier (Firebase UID), or None if no token provided

    Raises:
        HTTPException: If token is invalid or expired (only if token is provided)
    """
    if not credentials:
        return None

    token = credentials.credentials

    # Clean and validate token format
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )

    # Remove any whitespace
    token = token.strip()

    # Basic validation: Firebase tokens are JWTs with 3 parts separated by dots
    parts = token.split('.')
    if len(parts) != 3:
        logger.warning(f"Invalid token format: expected 3 parts, got {len(parts)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format: token must be a valid JWT",
        )

    # Verify Firebase token
    if not FIREBASE_AVAILABLE or not auth:
        logger.error("Firebase authentication not available - check server logs for initialization errors")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Firebase authentication not available on server. Check server logs for details.",
        )

    try:
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token.get("uid")
        if user_id:
            return str(user_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Firebase token missing user ID",
            )
    except ValueError as e:
        # ValueError often indicates token format issues (like padding)
        error_msg = str(e)
        if "padding" in error_msg.lower():
            logger.warning(f"Token padding error - token may be truncated or malformed: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format: token appears to be truncated or malformed. Please ensure you're using a complete Firebase ID token.",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {error_msg}",
        )
    except Exception as e:
        # Check if it's a Firebase-specific exception
        if firebase_admin and hasattr(firebase_admin.exceptions, 'InvalidArgumentError'):
            if isinstance(e, firebase_admin.exceptions.InvalidArgumentError):
                error_msg = str(e)
                if "padding" in error_msg.lower():
                    logger.warning(f"Token padding error: {error_msg}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid token format: token appears to be truncated or malformed. Please ensure you're using a complete Firebase ID token.",
                    )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid Firebase token: {error_msg}",
                )
        
        # Log and re-raise as generic error
        logger.error(f"Firebase verification error: {e}", exc_info=True)
        error_msg = str(e)
        if "padding" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format: token appears to be truncated or malformed. Please ensure you're using a complete Firebase ID token.",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Firebase token verification failed: {error_msg}",
        )


def get_user_id_required(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    """Extract and validate user_id from Firebase token (REQUIRED).

    Raises 401 if no token or invalid token.
    Use this for endpoints that require authentication (like list endpoints).

    Args:
        credentials: HTTP Bearer token from Authorization header

    Returns:
        user_id: User identifier (Firebase UID)

    Raises:
        HTTPException: If no token provided or token is invalid
    """
    user_id = get_user_id_optional(credentials)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user_id


# Alias for backward compatibility and easier use
get_user_id = get_user_id_optional

