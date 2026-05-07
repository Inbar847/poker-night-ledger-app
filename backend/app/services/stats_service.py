"""
Stats service — Stage 8.

Computes personal game history and statistics for a registered user.
Guest-only identities cannot authenticate and will never reach these endpoints.

All stats are restricted to closed games where the calling user was a
registered participant (Participant.user_id == user.id).
"""

import uuid
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session

from app.models.game import Game, GameStatus
from app.models.ledger import BuyIn, Expense, ExpenseSplit, FinalStack
from app.models.participant import Participant
from app.schemas.settlement import SettlementResponse
from app.schemas.stats import (
    GameHistoryItem,
    LeaderboardEntry,
    LeaderboardResponse,
    RecentGameSummary,
    UserStats,
    UserStatsView,
)
from app.services.settlement_service import get_settlement

_TWO = Decimal("0.01")
_RECENT_LIMIT = 5


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _participant_net_balance(
    db: Session,
    participant: Participant,
    game: Game,
) -> Decimal | None:
    """
    Compute the net_balance for a single participant in a game.
    Returns None if the participant has no final stack recorded.

    Formula mirrors settlement_service:
        total_buy_ins         = sum(buy_in.cash_amount)
        final_chip_cash_value = quantize(chips * chip_cash_rate, 2dp, ROUND_HALF_UP)
        poker_balance         = final_chip_cash_value - total_buy_ins
        amount_paid           = sum(expense.total_amount where paid_by == participant)
        owed_share            = sum(split.share_amount where split.participant == participant)
        expense_balance       = amount_paid - owed_share
        net_balance           = poker_balance + expense_balance
    """
    final_stack = (
        db.query(FinalStack)
        .filter(
            FinalStack.game_id == game.id,
            FinalStack.participant_id == participant.id,
        )
        .first()
    )
    if final_stack is None:
        return None

    buy_ins = (
        db.query(BuyIn)
        .filter(BuyIn.game_id == game.id, BuyIn.participant_id == participant.id)
        .all()
    )
    total_buy_ins = sum((b.cash_amount for b in buy_ins), Decimal("0"))

    final_chip_cash_value = (
        final_stack.chips_amount * game.chip_cash_rate
    ).quantize(_TWO, rounding=ROUND_HALF_UP)
    poker_balance = final_chip_cash_value - total_buy_ins

    # Expenses paid by this participant for the whole group
    expenses_paid = (
        db.query(Expense)
        .filter(
            Expense.game_id == game.id,
            Expense.paid_by_participant_id == participant.id,
        )
        .all()
    )
    amount_paid = sum((e.total_amount for e in expenses_paid), Decimal("0"))

    # This participant's share of all expenses in the game
    expense_ids = [
        e.id
        for e in db.query(Expense.id).filter(Expense.game_id == game.id)
    ]
    owed_share = Decimal("0")
    if expense_ids:
        splits = (
            db.query(ExpenseSplit)
            .filter(
                ExpenseSplit.participant_id == participant.id,
                ExpenseSplit.expense_id.in_(expense_ids),
            )
            .all()
        )
        owed_share = sum((s.share_amount for s in splits), Decimal("0"))

    expense_balance = amount_paid - owed_share
    return poker_balance + expense_balance


def _total_buy_ins_for_participant(
    db: Session, participant: Participant, game: Game
) -> Decimal:
    buy_ins = (
        db.query(BuyIn)
        .filter(BuyIn.game_id == game.id, BuyIn.participant_id == participant.id)
        .all()
    )
    return sum((b.cash_amount for b in buy_ins), Decimal("0"))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_history(db: Session, user_id: uuid.UUID) -> list[GameHistoryItem]:
    """
    Return all closed, non-hidden games where the user was a registered
    participant, ordered by closed_at descending (most recent first).
    """
    participants = (
        db.query(Participant)
        .filter(Participant.user_id == user_id, Participant.hidden_at.is_(None))
        .all()
    )
    if not participants:
        return []

    game_ids = [p.game_id for p in participants]
    games = (
        db.query(Game)
        .filter(Game.id.in_(game_ids), Game.status == GameStatus.closed)
        .order_by(Game.closed_at.desc())
        .all()
    )

    participant_by_game: dict[uuid.UUID, Participant] = {
        p.game_id: p for p in participants
    }

    result: list[GameHistoryItem] = []
    for game in games:
        p = participant_by_game[game.id]
        net = _participant_net_balance(db, p, game)
        total_buy_ins = _total_buy_ins_for_participant(db, p, game)
        result.append(
            GameHistoryItem(
                game_id=game.id,
                title=game.title,
                currency=game.currency,
                chip_cash_rate=game.chip_cash_rate,
                closed_at=game.closed_at,  # type: ignore[arg-type]
                role_in_game=p.role_in_game.value,
                net_balance=net,
                total_buy_ins=total_buy_ins,
            )
        )
    return result


def get_history_game(
    db: Session, game_id: uuid.UUID, user_id: uuid.UUID
) -> SettlementResponse | None:
    """
    Return the full settlement view for a single closed game.
    Returns None if the game does not exist, is not closed, or the user
    was not a registered participant.
    """
    game = (
        db.query(Game)
        .filter(Game.id == game_id, Game.status == GameStatus.closed)
        .first()
    )
    if game is None:
        return None

    participant = (
        db.query(Participant)
        .filter(
            Participant.game_id == game_id,
            Participant.user_id == user_id,
        )
        .first()
    )
    if participant is None:
        return None

    return get_settlement(db, game)


def get_stats(db: Session, user_id: uuid.UUID) -> UserStats:
    """
    Compute personal stats for a registered user across all closed games
    where they were a registered participant.
    """
    participants = (
        db.query(Participant).filter(Participant.user_id == user_id).all()
    )
    if not participants:
        return UserStats(
            total_games_played=0,
            total_games_hosted=0,
            games_with_result=0,
            cumulative_net=Decimal("0"),
            average_net=None,
            profitable_games=0,
            win_rate=None,
            recent_games=[],
        )

    game_ids = [p.game_id for p in participants]
    games = (
        db.query(Game)
        .filter(Game.id.in_(game_ids), Game.status == GameStatus.closed)
        .order_by(Game.closed_at.desc())
        .all()
    )

    participant_by_game: dict[uuid.UUID, Participant] = {
        p.game_id: p for p in participants
    }

    total_games_played = len(games)
    total_games_hosted = sum(
        1 for g in games if g.dealer_user_id == user_id
    )

    # Compute net balance once per game, reuse for both stats and recent_games
    net_by_game: dict[uuid.UUID, Decimal | None] = {}
    for game in games:
        p = participant_by_game[game.id]
        net_by_game[game.id] = _participant_net_balance(db, p, game)

    net_balances = [n for n in net_by_game.values() if n is not None]
    games_with_result = len(net_balances)
    profitable_games = sum(1 for n in net_balances if n > Decimal("0"))

    cumulative_net = sum(net_balances, Decimal("0")).quantize(
        _TWO, rounding=ROUND_HALF_UP
    )
    average_net = (
        (cumulative_net / games_with_result).quantize(_TWO, rounding=ROUND_HALF_UP)
        if games_with_result > 0
        else None
    )
    win_rate = (
        round(profitable_games / games_with_result, 4)
        if games_with_result > 0
        else None
    )

    recent_games = [
        RecentGameSummary(
            game_id=game.id,
            title=game.title,
            closed_at=game.closed_at,  # type: ignore[arg-type]
            net_balance=net_by_game[game.id],
            currency=game.currency,
        )
        for game in games[:_RECENT_LIMIT]
    ]

    return UserStats(
        total_games_played=total_games_played,
        total_games_hosted=total_games_hosted,
        games_with_result=games_with_result,
        cumulative_net=cumulative_net,
        average_net=average_net,
        profitable_games=profitable_games,
        win_rate=win_rate,
        recent_games=recent_games,
    )


def get_leaderboard(db: Session, current_user_id: uuid.UUID) -> LeaderboardResponse:
    """
    Return the friend leaderboard for the current user.

    Includes:
    - The current user themselves
    - All accepted friends (both directions)

    Sorted by:
    1. cumulative_net descending (primary)
    2. win_rate descending (secondary; None treated as -inf)
    3. total_games_played descending (tertiary)
    4. user_id ascending (stable tie-break)

    Privacy: no gating applied here — every entry is either self or an accepted
    friend, so full stats are appropriate for all entries.
    """
    # Local import to avoid circular dependency at module load time.
    from app.services.friendship_service import list_friends  # noqa: PLC0415
    from app.models.user import User  # noqa: PLC0415

    # Collect user IDs: self + all accepted friends
    friend_entries = list_friends(db, current_user_id)
    friend_ids = [fe.friend.id for fe in friend_entries]
    all_user_ids = [current_user_id] + friend_ids

    # Batch-compute stats for all users
    raw_entries: list[tuple[uuid.UUID, UserStats]] = []
    for uid in all_user_ids:
        stats = get_stats(db, uid)
        raw_entries.append((uid, stats))

    # Fetch user records for name/image in one query
    users = db.query(User).filter(User.id.in_(all_user_ids)).all()
    user_map: dict[uuid.UUID, User] = {u.id: u for u in users}

    # Sort: cumulative_net desc, win_rate desc (None → -1), games_played desc, user_id asc
    def _sort_key(item: tuple[uuid.UUID, UserStats]):
        uid, s = item
        return (
            -s.cumulative_net,
            -(s.win_rate if s.win_rate is not None else -1.0),
            -s.total_games_played,
            str(uid),
        )

    raw_entries.sort(key=_sort_key)

    entries: list[LeaderboardEntry] = []
    for rank, (uid, stats) in enumerate(raw_entries, start=1):
        user = user_map.get(uid)
        entries.append(
            LeaderboardEntry(
                rank=rank,
                user_id=uid,
                full_name=user.full_name if user else None,
                profile_image_url=user.profile_image_url if user else None,
                total_games_played=stats.total_games_played,
                games_with_result=stats.games_with_result,
                cumulative_net=stats.cumulative_net,
                win_rate=stats.win_rate,
                is_self=(uid == current_user_id),
            )
        )

    return LeaderboardResponse(entries=entries)


def get_user_stats_view(
    db: Session, target_user_id: uuid.UUID, viewer_user_id: uuid.UUID
) -> UserStatsView:
    """
    Return stats for `target_user_id` as seen by `viewer_user_id`.

    Privacy rule (enforced here, not in the router):
    - If viewer == target: full stats.
    - If viewer is an accepted friend of target: full stats.
    - Otherwise: only total_games_played, with is_friend_access=False.

    This function is the single authoritative privacy gate for user stats.
    """
    # Local import to avoid circular dependency at module load time.
    from app.services.friendship_service import are_friends  # noqa: PLC0415

    is_self = viewer_user_id == target_user_id
    has_full_access = is_self or are_friends(db, viewer_user_id, target_user_id)

    full = get_stats(db, target_user_id)

    if not has_full_access:
        return UserStatsView(
            is_friend_access=False,
            total_games_played=full.total_games_played,
        )

    return UserStatsView(
        is_friend_access=True,
        total_games_played=full.total_games_played,
        total_games_hosted=full.total_games_hosted,
        games_with_result=full.games_with_result,
        cumulative_net=full.cumulative_net,
        average_net=full.average_net,
        profitable_games=full.profitable_games,
        win_rate=full.win_rate,
        recent_games=full.recent_games,
    )
