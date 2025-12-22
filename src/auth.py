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

security = HTTPBearer()


def get_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> str:
    """Extract and validate user_id from NextAuth JWT token.

    Validates the JWT token from the Authorization header and extracts the user_id.
    The user_id comes from verified headers (not user input), preventing injection attacks.

    Args:
        credentials: HTTP Bearer token from Authorization header

    Returns:
        user_id: User identifier extracted from JWT payload

    Raises:
        HTTPException: If token is invalid, expired, or missing user_id
    """
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

