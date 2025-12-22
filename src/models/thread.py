"""Thread domain model for agent conversations."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class Thread(BaseModel):
    """Thread domain model for persistent agent conversations.

    A thread represents a conversation session with the agent.
    Threads are scoped to users and can be linked to strategies.
    """

    id: str = Field(..., description="Thread identifier (Firestore document ID)")
    user_id: str = Field(..., description="User identifier (from JWT)")
    strategy_id: str | None = Field(
        None, description="Linked strategy identifier (optional)"
    )
    created_at: str = Field(..., description="ISO8601 timestamp of creation")
    updated_at: str = Field(..., description="ISO8601 timestamp of last update")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional thread metadata"
    )

    @classmethod
    def from_dict(cls, data: dict[str, Any], thread_id: str | None = None) -> "Thread":
        """Create Thread from dictionary (e.g., from Firestore).

        Args:
            data: Dictionary containing thread data
            thread_id: Optional thread ID (if not in data dict, e.g., from Firestore document ID)
        """
        data_copy = data.copy()
        # If thread_id is provided separately (from Firestore doc ID), use it
        if thread_id is not None:
            data_copy["id"] = thread_id
        return cls(**data_copy)

    def to_dict(self) -> dict[str, Any]:
        """Convert Thread to dictionary for Firestore storage."""
        return {
            "user_id": self.user_id,
            "strategy_id": self.strategy_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }

    @staticmethod
    def now_iso() -> str:
        """Get current timestamp in ISO8601 format."""
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

