"""
Schemas for Stage 8: history and personal statistics.
Stage 17 additions: LeaderboardEntry and LeaderboardResponse for friend leaderboard.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class GameHistoryItem(BaseModel):
    """Summary of one closed game for the history list."""

    game_id: uuid.UUID
    title: str
    currency: str
    chip_cash_rate: Decimal
    closed_at: datetime
    role_in_game: str  # "dealer" | "player"
    # None if the user has no final stack (incomplete settlement)
    net_balance: Decimal | None
    total_buy_ins: Decimal


class RecentGameSummary(BaseModel):
    """Compact game summary used inside UserStats.recent_games."""

    game_id: uuid.UUID
    title: str
    closed_at: datetime
    net_balance: Decimal | None
    currency: str


class UserStats(BaseModel):
    """Personal statistics for a registered user."""

    total_games_played: int
    total_games_hosted: int
    # games_with_result: closed games where the user has a final stack
    games_with_result: int
    cumulative_net: Decimal
    # None when games_with_result == 0
    average_net: Decimal | None
    profitable_games: int
    # None when games_with_result == 0
    win_rate: float | None
    recent_games: list[RecentGameSummary]


class UserStatsView(BaseModel):
    """
    Stats response for GET /users/{user_id}/stats.

    `total_games_played` is always present.
    All other fields are None when `is_friend_access` is False (viewer is not a friend
    and not the user themselves). The mobile client uses `is_friend_access` to decide
    whether to render the full stats block or a locked/placeholder block.
    """

    is_friend_access: bool
    total_games_played: int

    # Present only when is_friend_access is True
    total_games_hosted: int | None = None
    games_with_result: int | None = None
    cumulative_net: Decimal | None = None
    average_net: Decimal | None = None
    profitable_games: int | None = None
    win_rate: float | None = None
    recent_games: list[RecentGameSummary] | None = None


# ---------------------------------------------------------------------------
# Stage 17 — Friend leaderboard
# ---------------------------------------------------------------------------


class LeaderboardEntry(BaseModel):
    """
    One row in the friend leaderboard.

    Always includes the user's own entry plus all accepted friends.
    All stat fields are always present (no privacy gate needed: every user
    in the leaderboard is either self or an accepted friend).
    """

    rank: int
    user_id: uuid.UUID
    full_name: str | None
    profile_image_url: str | None
    total_games_played: int
    games_with_result: int
    cumulative_net: Decimal
    win_rate: float | None
    is_self: bool


class LeaderboardResponse(BaseModel):
    """Response shape for GET /social/leaderboard."""

    entries: list[LeaderboardEntry]
