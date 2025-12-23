"""JWT authentication and user extraction from NextAuth tokens."""

import os
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# NextAuth JWT secret (must match UI's NEXTAUTH_SECRET)
NEXTAUTH_SECRET = os.getenv("NEXTAUTH_SECRET")
if not NEXTAUTH_SECRET:
    raise ValueError("NEXTAUTH_SECRET environment variable is required")

# Create security scheme that doesn't require auth (auto_error=False)
security = HTTPBearer(auto_error=False)


def get_user_id_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str | None:
    """Extract and validate user_id from NextAuth JWT token (optional).

    Validates the JWT token from the Authorization header and extracts the user_id.
    The user_id comes from verified headers (not user input), preventing injection attacks.
    
    If no token is provided, returns None (auth is disabled for now).

    Args:
        credentials: HTTP Bearer token from Authorization header (optional)

    Returns:
        user_id: User identifier extracted from JWT payload, or None if no token provided

    Raises:
        HTTPException: If token is invalid or expired (only if token is provided)
    """
    # If no credentials provided, return None (auth disabled for now)
    if not credentials:
        return None
    
    token = credentials.credentials

    try:
        # Decode and verify JWT using NextAuth secret
        # NextAuth uses HS256 algorithm by default
        payload = jwt.decode(
            token,
            NEXTAUTH_SECRET,
            algorithms=["HS256"],
            options={"verify_signature": True, "verify_exp": True},
        )

        # Extract user_id from payload
        # NextAuth typically stores user ID in 'sub' field or 'user.id'
        user_id = payload.get("sub") or payload.get("user", {}).get("id")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing user identifier",
            )

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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}",
        )


# Alias for backward compatibility and easier use
get_user_id = get_user_id_optional

