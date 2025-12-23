"""Authentication utilities for extracting user ID from Firebase or NextAuth tokens."""

import os
from typing import Annotated, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Try to import Firebase Admin SDK
try:
    import firebase_admin
    from firebase_admin import auth, credentials

    # Initialize Firebase Admin SDK (uses Application Default Credentials on GCP)
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    auth = None

# NextAuth JWT secret (for backward compatibility, optional now)
NEXTAUTH_SECRET = os.getenv("NEXTAUTH_SECRET")

# Create security scheme that doesn't require auth (auto_error=False)
security = HTTPBearer(auto_error=False)


def get_user_id_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> Optional[str]:
    """Extract and validate user_id from Firebase or NextAuth JWT token (optional).

    Tries Firebase first, then falls back to NextAuth for backward compatibility.
    Returns None if no token provided (allows unauthenticated access).

    Args:
        credentials: HTTP Bearer token from Authorization header (optional)

    Returns:
        user_id: User identifier (Firebase UID or NextAuth user ID), or None if no token provided

    Raises:
        HTTPException: If token is invalid or expired (only if token is provided)
    """
    if not credentials:
        return None

    token = credentials.credentials

    # Try Firebase first
    if FIREBASE_AVAILABLE and auth:
        try:
            decoded_token = auth.verify_id_token(token)
            user_id = decoded_token.get("uid")
            if user_id:
                return str(user_id)
        except Exception:
            # Not a Firebase token, try NextAuth below
            pass

    # Fall back to NextAuth (for backward compatibility)
    if NEXTAUTH_SECRET:
        try:
            payload = jwt.decode(
                token,
                NEXTAUTH_SECRET,
                algorithms=["HS256"],
                options={"verify_signature": True, "verify_exp": True},
            )
            user_id = payload.get("sub") or payload.get("user", {}).get("id")
            if user_id:
                return str(user_id)
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
            )

    # If we get here, token was provided but couldn't be validated
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or unsupported token",
    )


def get_user_id_required(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    """Extract and validate user_id from token (REQUIRED).

    Raises 401 if no token or invalid token.
    Use this for endpoints that require authentication (like list endpoints).

    Args:
        credentials: HTTP Bearer token from Authorization header

    Returns:
        user_id: User identifier (Firebase UID or NextAuth user ID)

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

