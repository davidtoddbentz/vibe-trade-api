"""Strategy management endpoints (user-scoped)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.auth import get_user_id
from src.repositories import card_repository, firestore_client, strategy_repository

router = APIRouter(prefix="/api/strategies", tags=["strategies"])


class StrategyWithCardsResponse(BaseModel):
    """Response model for strategy with attached cards."""

    strategy: dict
    cards: list[dict]
    card_count: int


@router.get("")
async def list_strategies(
    user_id: Annotated[str, Depends(get_user_id)],
) -> list[dict]:
    """List all strategies for the authenticated user.

    Args:
        user_id: User ID from JWT (verified, not from user input)

    Returns:
        List of user's strategies
    """
    # Get all strategies and filter by owner_id
    # TODO: Add get_by_owner_id method to StrategyRepository for efficiency
    all_strategies = strategy_repository.get_all()
    user_strategies = [s for s in all_strategies if s.owner_id == user_id]

    return [
        {
            "id": s.id,
            "owner_id": s.owner_id,
            "name": s.name,
            "status": s.status,
            "universe": s.universe,
            "attachments": [att.model_dump() for att in s.attachments],
            "version": s.version,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
        }
        for s in user_strategies
    ]


@router.get("/{strategy_id}", response_model=StrategyWithCardsResponse)
async def get_strategy_with_cards(
    strategy_id: str,
    user_id: Annotated[str, Depends(get_user_id)],
) -> StrategyWithCardsResponse:
    """Get a strategy with all its attached cards (ensures user owns it).

    Args:
        strategy_id: Strategy identifier
        user_id: User ID from JWT (verified, not from user input)

    Returns:
        Strategy data with attached cards

    Raises:
        HTTPException: If strategy not found or user doesn't own it
    """
    # Get strategy
    strategy = strategy_repository.get_by_id(strategy_id)
    if strategy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy not found: {strategy_id}",
        )

    # Verify user owns this strategy
    if strategy.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: strategy belongs to another user",
        )

    # Get all cards attached to this strategy
    cards = []
    for attachment in strategy.attachments:
        card = card_repository.get_by_id(attachment.card_id)
        if card:
            # Include card data with attachment metadata
            card_dict = card.model_dump()
            card_dict["role"] = attachment.role
            card_dict["enabled"] = attachment.enabled
            card_dict["overrides"] = attachment.overrides
            cards.append(card_dict)

    return StrategyWithCardsResponse(
        strategy={
            "id": strategy.id,
            "owner_id": strategy.owner_id,
            "name": strategy.name,
            "status": strategy.status,
            "universe": strategy.universe,
            "attachments": [att.model_dump() for att in strategy.attachments],
            "version": strategy.version,
            "created_at": strategy.created_at,
            "updated_at": strategy.updated_at,
        },
        cards=cards,
        card_count=len(cards),
    )


@router.get("/threads/{thread_id}/strategy", response_model=StrategyWithCardsResponse)
async def get_strategy_by_thread(
    thread_id: str,
    user_id: Annotated[str, Depends(get_user_id)],
) -> StrategyWithCardsResponse:
    """Get strategy linked to a thread (ensures user owns the thread).

    Args:
        thread_id: Thread identifier
        user_id: User ID from JWT (verified, not from user input)

    Returns:
        Strategy data with attached cards

    Raises:
        HTTPException: If thread not found, user doesn't own thread, or no strategy linked
    """
    # Get thread and verify ownership
    from src.models.thread import Thread

    thread_doc = firestore_client.collection("threads").document(thread_id).get()
    if not thread_doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread not found: {thread_id}",
        )

    thread_data = thread_doc.to_dict()
    if not thread_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread not found: {thread_id}",
        )

    thread = Thread.from_dict(thread_data, thread_id=thread_id)

    # Verify user owns this thread
    if thread.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: thread belongs to another user",
        )

    # Check if thread has linked strategy
    if not thread.strategy_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread {thread_id} has no linked strategy",
        )

    # Get strategy (already verified user owns thread, so strategy ownership is implied)
    return await get_strategy_with_cards(thread.strategy_id, user_id)

