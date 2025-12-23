"""Strategy endpoints with user scoping."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from src.auth import get_user_id
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


@router.get("", response_model=list[dict] | StrategyWithCardsResponse)
async def get_strategies(
    user_id: Annotated[str | None, Depends(get_user_id)],
    thread_id: str | None = Query(None, description="Optional thread_id to filter by"),
) -> list[dict] | StrategyWithCardsResponse:
    """Get strategies for the authenticated user.
    
    If thread_id is provided, returns a single strategy with cards.
    Otherwise, returns a list of all user's strategies.

    Args:
        user_id: User ID from JWT (optional, auth disabled for now)
        thread_id: Optional thread_id to get strategy by thread

    Returns:
        If thread_id provided: StrategyWithCardsResponse with strategy and cards
        Otherwise: List of user's strategies
    """
    # If thread_id is provided, return single strategy with cards
    if thread_id:
        logger.info(f"Querying strategy by thread_id: {thread_id}")
        
        try:
            strategy = strategy_repository.get_by_thread_id(thread_id)
            logger.info(f"Strategy found: {strategy.id if strategy else None}")
        except Exception as e:
            logger.error(f"Error querying strategies by thread_id: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )
        
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No strategy found for thread_id: {thread_id}",
            )
        
        # Verify user owns this strategy (only if authenticated and strategy has owner_id)
        # Skip check if user_id is None (auth disabled)
        if user_id and user_id != "anonymous_user" and strategy.owner_id and strategy.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: strategy belongs to another user",
            )
        
        # Get all cards attached to this strategy
        cards = _get_strategy_cards(strategy)
        
        return StrategyWithCardsResponse(
            strategy=_build_strategy_dict(strategy),
            cards=cards,
            card_count=len(cards),
        )
    
    # Otherwise, return list of all strategies for user
    # If authenticated (user_id is not None and not "anonymous_user"), filter by user_id
    # Otherwise return all strategies (auth disabled)
    if user_id and user_id != "anonymous_user":
        user_strategies = strategy_repository.get_by_owner_id(user_id)
    else:
        # Auth disabled: return all strategies
        user_strategies = strategy_repository.get_all()

    return [_build_strategy_dict(s) for s in user_strategies]


@router.get("/{strategy_id}", response_model=StrategyWithCardsResponse)
async def get_strategy_by_id(
    strategy_id: str,
    user_id: Annotated[str | None, Depends(get_user_id)] = None,
) -> StrategyWithCardsResponse:
    """Get a strategy by ID with all its attached cards.

    Args:
        strategy_id: Strategy identifier
        user_id: User ID from JWT (optional, auth disabled for now)

    Returns:
        Strategy data with attached cards

    Raises:
        HTTPException: If strategy not found or user doesn't own it (if authenticated)
    """
    # Get strategy
    strategy = strategy_repository.get_by_id(strategy_id)
    if strategy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy not found: {strategy_id}",
        )

    # Verify user owns this strategy (only if authenticated and strategy has owner_id)
    if user_id and strategy.owner_id and strategy.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: strategy belongs to another user",
        )

    # Get all cards attached to this strategy
    cards = _get_strategy_cards(strategy)

    return StrategyWithCardsResponse(
        strategy=_build_strategy_dict(strategy),
        cards=cards,
        card_count=len(cards),
    )
