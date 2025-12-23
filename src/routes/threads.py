"""Thread endpoints with user scoping."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.auth import get_user_id, get_user_id_required
from src.repositories import strategy_repository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/threads", tags=["threads"])


class ThreadResponse(BaseModel):
    """Response model for a thread."""

    thread_id: str
    strategy_id: str | None
    strategy_name: str | None
    strategy_status: str | None
    created_at: str | None
    updated_at: str | None


@router.get("", response_model=list[ThreadResponse])
async def get_threads(
    user_id: Annotated[str, Depends(get_user_id_required)],  # REQUIRED auth for listing
) -> list[ThreadResponse]:
    """Get all threads for the authenticated user.

    **Requires authentication** - prevents unauthenticated users from seeing all threads.

    Returns threads by querying strategies owned by the user.

    Args:
        user_id: User ID from Firebase token (required)

    Returns:
        List of threads with associated strategy information

    Raises:
        HTTPException: If user is not authenticated
    """
    try:
        # Get all strategies for this user
        strategies = strategy_repository.get_by_owner_id(user_id)

        # Build a map of thread_id -> strategy info
        thread_map: dict[str, dict] = {}

        for strategy in strategies:
            if not strategy.thread_id:
                continue

            thread_id = strategy.thread_id

            # If thread already exists, keep the one with the latest updated_at
            if thread_id in thread_map:
                existing_updated = thread_map[thread_id].get("updated_at", "")
                if strategy.updated_at > existing_updated:
                    thread_map[thread_id] = {
                        "thread_id": thread_id,
                        "strategy_id": strategy.id,
                        "strategy_name": strategy.name,
                        "strategy_status": strategy.status,
                        "created_at": strategy.created_at,
                        "updated_at": strategy.updated_at,
                    }
            else:
                thread_map[thread_id] = {
                    "thread_id": thread_id,
                    "strategy_id": strategy.id,
                    "strategy_name": strategy.name,
                    "strategy_status": strategy.status,
                    "created_at": strategy.created_at,
                    "updated_at": strategy.updated_at,
                }

        # Convert to list and sort by updated_at (most recent first)
        threads = list(thread_map.values())
        threads.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

        logger.info(f"Found {len(threads)} threads for user {user_id}")

        return [ThreadResponse(**thread) for thread in threads]

    except Exception as e:
        logger.error(f"Error querying threads for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.get("/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: str,
    user_id: Annotated[str | None, Depends(get_user_id)] = None,  # Optional auth
) -> ThreadResponse:
    """Get a specific thread by ID.

    **Authentication is optional:**
    - If thread's strategy has no owner_id: anyone can access (unauthenticated OK)
    - If thread's strategy has owner_id: only the owner can access (must be authenticated and match)

    Args:
        thread_id: Thread identifier
        user_id: User ID from token (optional)

    Returns:
        Thread information with associated strategy

    Raises:
        HTTPException: If thread not found or access denied
    """
    try:
        # Get strategy by thread_id
        strategy = strategy_repository.get_by_thread_id(thread_id)

        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Thread not found: {thread_id}",
            )

        # Access control:
        # - If strategy has no owner_id: anyone can access (unauthenticated OK)
        # - If strategy has owner_id: only the owner can access
        if strategy.owner_id:
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required: this thread belongs to a user",
                )
            if user_id != strategy.owner_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: thread belongs to another user",
                )

        # Strategy has no owner_id OR user is the owner - allow access
        return ThreadResponse(
            thread_id=thread_id,
            strategy_id=strategy.id,
            strategy_name=strategy.name,
            strategy_status=strategy.status,
            created_at=strategy.created_at,
            updated_at=strategy.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying thread {thread_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )

