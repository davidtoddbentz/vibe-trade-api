"""Strategy endpoints with user scoping."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from src.auth import get_user_id, get_user_id_required
from src.repositories import card_repository, strategy_repository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/strategies", tags=["strategies"])


class StrategyWithCardsResponse(BaseModel):
    """Response model for strategy with attached cards."""

    strategy: dict
    cards: list[dict]
    card_count: int


def _build_strategy_dict(strategy) -> dict:
    """Build strategy dictionary from Strategy model."""
    return {
        "id": strategy.id,
        "owner_id": strategy.owner_id,
        "thread_id": strategy.thread_id,
        "name": strategy.name,
        "status": strategy.status,
        "universe": strategy.universe,
        "attachments": [att.model_dump() for att in strategy.attachments],
        "version": strategy.version,
        "created_at": strategy.created_at,
        "updated_at": strategy.updated_at,
    }


def _get_strategy_cards(strategy) -> list[dict]:
    """Get all cards attached to a strategy with attachment metadata."""
    cards = []
    for attachment in strategy.attachments:
        card = card_repository.get_by_id(attachment.card_id)
        if card:
            card_dict = card.model_dump()
            card_dict["role"] = attachment.role
            card_dict["enabled"] = attachment.enabled
            card_dict["overrides"] = attachment.overrides
            cards.append(card_dict)
    return cards


@router.get("", response_model=list[dict])
async def get_strategies(
    user_id: Annotated[str, Depends(get_user_id_required)],  # REQUIRED auth for listing
) -> list[dict]:
    """Get all strategies for the authenticated user.

    **Requires authentication** - prevents unauthenticated users from seeing all strategies.

    Args:
        user_id: User ID from Firebase token (required)

    Returns:
        List of user's strategies

    Raises:
        HTTPException: If user is not authenticated
    """
    try:
        user_strategies = strategy_repository.get_by_owner_id(user_id)
        return [_build_strategy_dict(s) for s in user_strategies]
    except Exception as e:
        logger.error(f"Error querying strategies for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.get("/threads/{thread_id}/strategy", response_model=StrategyWithCardsResponse)
async def get_strategy_by_thread_id(
    thread_id: str,
    user_id: Annotated[str | None, Depends(get_user_id)] = None,  # Optional auth
) -> StrategyWithCardsResponse:
    """Get a strategy by thread_id with all its attached cards.

    **Authentication is optional:**
    - If strategy has no owner_id: anyone can access (unauthenticated OK)
    - If strategy has owner_id: only the owner can access (must be authenticated and match)

    Args:
        thread_id: Thread identifier
        user_id: User ID from token (optional)

    Returns:
        Strategy data with attached cards

    Raises:
        HTTPException: If strategy not found or access denied
    """
    try:
        strategy = strategy_repository.get_by_thread_id(thread_id)

        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No strategy found for thread_id: {thread_id}",
            )

        # Access control:
        # - If strategy has no owner_id: anyone can access (unauthenticated OK)
        # - If strategy has owner_id: only the owner can access
        if strategy.owner_id:
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required: this strategy belongs to a user",
                )
            if user_id != strategy.owner_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: strategy belongs to another user",
                )

        # Strategy has no owner_id OR user is the owner - allow access
        cards = _get_strategy_cards(strategy)

        return StrategyWithCardsResponse(
            strategy=_build_strategy_dict(strategy),
            cards=cards,
            card_count=len(cards),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying strategy by thread_id {thread_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.get("/{strategy_id}", response_model=StrategyWithCardsResponse)
async def get_strategy_by_id(
    strategy_id: str,
    user_id: Annotated[str | None, Depends(get_user_id)] = None,  # Optional auth
) -> StrategyWithCardsResponse:
    """Get a strategy by ID with all its attached cards.

    **Authentication is optional:**
    - If strategy has no owner_id: anyone can access (unauthenticated OK)
    - If strategy has owner_id: only the owner can access (must be authenticated and match)

    Args:
        strategy_id: Strategy identifier
        user_id: User ID from token (optional)

    Returns:
        Strategy data with attached cards

    Raises:
        HTTPException: If strategy not found or access denied
    """
    strategy = strategy_repository.get_by_id(strategy_id)
    if strategy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy not found: {strategy_id}",
        )

    # Access control:
    # - If strategy has no owner_id: anyone can access (unauthenticated OK)
    # - If strategy has owner_id: only the owner can access
    if strategy.owner_id:
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required: this strategy belongs to a user",
            )
        if user_id != strategy.owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: strategy belongs to another user",
            )

    # Strategy has no owner_id OR user is the owner - allow access
    cards = _get_strategy_cards(strategy)

    return StrategyWithCardsResponse(
        strategy=_build_strategy_dict(strategy),
        cards=cards,
        card_count=len(cards),
    )
