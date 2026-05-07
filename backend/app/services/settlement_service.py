"""
Settlement service — Stage 4.

Calculation chain per participant:
  total_buy_ins         = sum(buy_in.cash_amount)
  final_chip_cash_value = quantize(final_chips * chip_cash_rate, "0.01", ROUND_HALF_UP)
  poker_balance         = final_chip_cash_value - total_buy_ins
  amount_paid           = sum(expense.total_amount where paid_by == participant)
  owed_share            = sum(split.share_amount where split.participant == participant)
  expense_balance       = amount_paid - owed_share
  net_balance           = poker_balance + expense_balance

Transfer reduction (greedy, deterministic):
  - Debtors  sorted by (net_balance ASC,  participant_id ASC)  → most negative first
  - Creditors sorted by (net_balance DESC, participant_id ASC) → most positive first
  - Each debtor is matched to creditors one at a time until the debtor's obligation
    is cleared, producing a compact, deterministic transfer list.
  - This is a greedy heuristic, not a globally optimal algorithm; finding the true
    minimum transfer count is NP-hard in general.  For typical poker games (≤10
    players) the greedy output is practically indistinguishable from optimal.

Rounding:
  chip_cash_rate is Numeric(12,4). Multiplying chips × rate may produce up to 6
  decimal places.  We quantize to 2dp (ROUND_HALF_UP) before further arithmetic.
  All other stored amounts are Numeric(12,2) — exact 2-decimal Decimals.
  After rounding, the sum of net balances may deviate from 0 by ≤ a few cents;
  this residual is surfaced in the audit response and does not affect transfers.
"""

import uuid
from dataclasses import dataclass, field
from decimal import ROUND_FLOOR, ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session

from app.models.game import Game
from app.models.ledger import BuyIn, Expense, ExpenseSplit, FinalStack
from app.models.participant import Participant, ParticipantStatus
from app.models.user import User

# Only active and left_early participants are included in settlement.
_SETTLEMENT_ELIGIBLE_STATUSES = (ParticipantStatus.active, ParticipantStatus.left_early)
from app.schemas.settlement import (
    BuyInLineItem,
    ExpensePaidLineItem,
    ExpenseSplitLineItem,
    ParticipantAudit,
    ParticipantBalance,
    SettlementAuditResponse,
    SettlementResponse,
    Transfer,
)

_TWO_PLACES = Decimal("0.01")


# ---------------------------------------------------------------------------
# Internal computation dataclass
# ---------------------------------------------------------------------------


@dataclass
class _ParticipantCalc:
    participant: Participant
    display_name: str

    # Raw inputs
    buy_ins: list[BuyIn] = field(default_factory=list)
    final_stack: FinalStack | None = None
    expenses_paid: list[Expense] = field(default_factory=list)
    expense_splits: list[tuple[ExpenseSplit, Expense]] = field(default_factory=list)

    # Computed
    total_buy_ins: Decimal = Decimal("0")
    final_chips: Decimal | None = None
    final_chip_cash_value: Decimal | None = None
    poker_balance: Decimal | None = None
    amount_paid_for_group: Decimal = Decimal("0")
    owed_expense_share: Decimal = Decimal("0")
    expense_balance: Decimal = Decimal("0")
    net_balance: Decimal | None = None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _display_name(participant: Participant, user: User | None) -> str:
    if participant.guest_name:
        return participant.guest_name
    if user and user.full_name:
        return user.full_name
    if user:
        return user.email
    return f"Unknown ({participant.id})"


def _compute_calc(
    calc: _ParticipantCalc,
    chip_cash_rate: Decimal,
) -> None:
    """Fill computed fields on a _ParticipantCalc in-place."""
    calc.total_buy_ins = sum(
        (b.cash_amount for b in calc.buy_ins), Decimal("0")
    )

    if calc.final_stack is not None:
        calc.final_chips = calc.final_stack.chips_amount
        calc.final_chip_cash_value = (calc.final_chips * chip_cash_rate).quantize(
            _TWO_PLACES, rounding=ROUND_HALF_UP
        )
        calc.poker_balance = calc.final_chip_cash_value - calc.total_buy_ins
    else:
        calc.final_chips = None
        calc.final_chip_cash_value = None
        calc.poker_balance = None

    calc.amount_paid_for_group = sum(
        (e.total_amount for e in calc.expenses_paid), Decimal("0")
    )
    calc.owed_expense_share = sum(
        (split.share_amount for split, _ in calc.expense_splits), Decimal("0")
    )
    calc.expense_balance = calc.amount_paid_for_group - calc.owed_expense_share

    if calc.poker_balance is not None:
        calc.net_balance = calc.poker_balance + calc.expense_balance
    else:
        calc.net_balance = None


def _build_calcs(db: Session, game: Game) -> list[_ParticipantCalc]:
    """Load all game data and build per-participant calculation objects.

    Only settlement-eligible participants (active, left_early) are included.
    Participants with removed_before_start are excluded entirely.
    """
    participants: list[Participant] = (
        db.query(Participant)
        .filter(
            Participant.game_id == game.id,
            Participant.status.in_(_SETTLEMENT_ELIGIBLE_STATUSES),
        )
        .order_by(Participant.joined_at)
        .all()
    )

    # Load user rows for registered participants
    user_ids = [p.user_id for p in participants if p.user_id is not None]
    users_by_id: dict[uuid.UUID, User] = {}
    if user_ids:
        for user in db.query(User).filter(User.id.in_(user_ids)).all():
            users_by_id[user.id] = user

    # Load ledger data
    buy_ins: list[BuyIn] = (
        db.query(BuyIn)
        .filter(BuyIn.game_id == game.id)
        .order_by(BuyIn.created_at)
        .all()
    )
    expenses: list[Expense] = (
        db.query(Expense)
        .filter(Expense.game_id == game.id)
        .order_by(Expense.created_at)
        .all()
    )
    expense_ids = [e.id for e in expenses]
    splits: list[ExpenseSplit] = []
    if expense_ids:
        splits = (
            db.query(ExpenseSplit)
            .filter(ExpenseSplit.expense_id.in_(expense_ids))
            .all()
        )
    expense_by_id: dict[uuid.UUID, Expense] = {e.id: e for e in expenses}

    final_stacks: list[FinalStack] = (
        db.query(FinalStack)
        .filter(FinalStack.game_id == game.id)
        .all()
    )
    stack_by_participant: dict[uuid.UUID, FinalStack] = {
        fs.participant_id: fs for fs in final_stacks
    }

    # Build a calc object per participant
    participant_by_id: dict[uuid.UUID, _ParticipantCalc] = {}
    for p in participants:
        user = users_by_id.get(p.user_id) if p.user_id else None
        calc = _ParticipantCalc(
            participant=p,
            display_name=_display_name(p, user),
            final_stack=stack_by_participant.get(p.id),
        )
        participant_by_id[p.id] = calc

    for b in buy_ins:
        if b.participant_id in participant_by_id:
            participant_by_id[b.participant_id].buy_ins.append(b)

    for e in expenses:
        if e.paid_by_participant_id in participant_by_id:
            participant_by_id[e.paid_by_participant_id].expenses_paid.append(e)

    for s in splits:
        if s.participant_id in participant_by_id:
            expense = expense_by_id.get(s.expense_id)
            if expense:
                participant_by_id[s.participant_id].expense_splits.append((s, expense))

    calcs = list(participant_by_id.values())
    for calc in calcs:
        _compute_calc(calc, game.chip_cash_rate)

    return calcs


# ---------------------------------------------------------------------------
# Transfer generation
# ---------------------------------------------------------------------------


def _generate_transfers(
    calcs: list[_ParticipantCalc],
    shortage_shares: dict[uuid.UUID, Decimal] | None = None,
) -> list[Transfer]:
    """
    Generate a compact, deterministic transfer list from computed balances.

    When shortage_shares is provided, uses adjusted_net_balance
    (net_balance - shortage_share) instead of raw net_balance for transfers.

    Only called when all participants have a net_balance (is_complete == True).

    Sort order for determinism:
    - Debtors:   (balance ASC,  str(participant_id) ASC)  → most negative first
    - Creditors: (balance DESC, str(participant_id) ASC)  → most positive first

    Participants with balance == 0 are excluded from both lists and produce
    no transfer rows.
    """
    shares = shortage_shares or {}

    def _effective_balance(c: _ParticipantCalc) -> Decimal:
        if c.net_balance is None:
            return Decimal("0")
        share = shares.get(c.participant.id, Decimal("0"))
        return (c.net_balance - share).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)

    debtors = sorted(
        [c for c in calcs if c.net_balance is not None and _effective_balance(c) < Decimal("0")],
        key=lambda c: (_effective_balance(c), str(c.participant.id)),
    )
    creditors = sorted(
        [c for c in calcs if c.net_balance is not None and _effective_balance(c) > Decimal("0")],
        key=lambda c: (-_effective_balance(c), str(c.participant.id)),
    )

    # Work on mutable copies of remaining amounts (using adjusted balances)
    debtor_remaining = [abs(_effective_balance(c)) for c in debtors]
    creditor_remaining = [_effective_balance(c) for c in creditors]

    transfers: list[Transfer] = []
    i = 0
    j = 0

    while i < len(debtors) and j < len(creditors):
        # Skip exhausted slots (can arise from rounding residuals)
        if debtor_remaining[i] <= Decimal("0"):
            i += 1
            continue
        if creditor_remaining[j] <= Decimal("0"):
            j += 1
            continue

        amount = min(debtor_remaining[i], creditor_remaining[j])
        # Quantize to 2dp — amounts should already be 2dp, but guard against
        # any accumulated floating-point drift during greedy iteration.
        amount = amount.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)

        if amount > Decimal("0"):
            transfers.append(
                Transfer(
                    from_participant_id=debtors[i].participant.id,
                    from_display_name=debtors[i].display_name,
                    to_participant_id=creditors[j].participant.id,
                    to_display_name=creditors[j].display_name,
                    amount=amount,
                )
            )

        debtor_remaining[i] -= amount
        creditor_remaining[j] -= amount

        if debtor_remaining[i] <= Decimal("0"):
            i += 1
        if creditor_remaining[j] <= Decimal("0"):
            j += 1

    return transfers


# ---------------------------------------------------------------------------
# Shortage calculation
# ---------------------------------------------------------------------------


def compute_shortage_amount(calcs: list[_ParticipantCalc]) -> Decimal:
    """
    Return the shortage amount (≥ 0) from raw net balances.

    Shortage is defined as: sum(net_balance for all complete participants) > 0.
    A positive sum means participants collectively claim more cash value than
    they put in (due to chip-rate rounding), so winners must absorb the gap.

    Returns 0.00 when settlement is incomplete or no shortage exists.
    """
    if not all(c.net_balance is not None for c in calcs):
        return Decimal("0")
    total = sum(
        (c.net_balance for c in calcs if c.net_balance is not None),
        Decimal("0"),
    ).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
    return max(total, Decimal("0"))


def distribute_shortage(
    calcs: list[_ParticipantCalc],
    shortage_amount: Decimal,
    strategy: str,
) -> dict[uuid.UUID, Decimal]:
    """
    Return a mapping of participant_id → shortage_share (all ≥ 0).

    Algorithms:
    - proportional_winners: only participants with raw_net > 0 absorb.
      Each winner's share is proportional to their raw winning amount,
      floored to 2dp. The 1¢ remainder is distributed to the largest
      winner(s) first (stable tie-break: participant_id ASC).
      If no winners exist, falls back to equal_all.

    - equal_all: all participants with a final stack absorb equally.
      Base share floored to 2dp. Remainder distributed 1¢ at a time
      in participant_id ASC order.

    Rounding guarantee: sum(shares.values()) == shortage_amount exactly.
    """
    if shortage_amount <= Decimal("0"):
        return {}

    complete_calcs = [c for c in calcs if c.net_balance is not None]
    if not complete_calcs:
        return {}

    effective_strategy = strategy
    winners = [c for c in complete_calcs if c.net_balance > Decimal("0")]  # type: ignore[operator]
    if effective_strategy == "proportional_winners" and not winners:
        effective_strategy = "equal_all"

    if effective_strategy == "proportional_winners":
        total_winner_net = sum(c.net_balance for c in winners)  # type: ignore[misc]
        # Floor each share to avoid over-allocation
        sorted_winners = sorted(
            winners,
            key=lambda c: (-c.net_balance, str(c.participant.id)),  # type: ignore[operator]
        )
        shares: dict[uuid.UUID, Decimal] = {}
        allocated = Decimal("0")
        for w in sorted_winners:
            raw_share = (
                w.net_balance / total_winner_net * shortage_amount  # type: ignore[operator]
            ).quantize(_TWO_PLACES, rounding=ROUND_FLOOR)
            shares[w.participant.id] = raw_share
            allocated += raw_share

        # Distribute remainder 1¢ at a time, largest winner first
        remainder_cents = int((shortage_amount - allocated) / Decimal("0.01"))
        for w in sorted_winners[:remainder_cents]:
            shares[w.participant.id] += Decimal("0.01")

        return shares

    # equal_all
    n = len(complete_calcs)
    base = (shortage_amount / n).quantize(_TWO_PLACES, rounding=ROUND_FLOOR)
    sorted_pids = sorted(
        [c.participant.id for c in complete_calcs], key=str
    )
    shares_eq: dict[uuid.UUID, Decimal] = {pid: base for pid in sorted_pids}
    allocated_eq = base * n
    remainder_cents_eq = int((shortage_amount - allocated_eq) / Decimal("0.01"))
    for pid in sorted_pids[:remainder_cents_eq]:
        shares_eq[pid] += Decimal("0.01")

    return shares_eq


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _is_complete(calcs: list[_ParticipantCalc]) -> bool:
    return all(c.net_balance is not None for c in calcs)


def _to_participant_balance(
    calc: _ParticipantCalc,
    shortage_shares: dict[uuid.UUID, Decimal] | None = None,
) -> ParticipantBalance:
    share = (shortage_shares or {}).get(calc.participant.id, Decimal("0"))
    adjusted = (
        (calc.net_balance - share).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
        if calc.net_balance is not None
        else None
    )
    return ParticipantBalance(
        participant_id=calc.participant.id,
        display_name=calc.display_name,
        participant_type=calc.participant.participant_type.value,
        total_buy_ins=calc.total_buy_ins,
        final_chips=calc.final_chips,
        final_chip_cash_value=calc.final_chip_cash_value,
        poker_balance=calc.poker_balance,
        amount_paid_for_group=calc.amount_paid_for_group,
        owed_expense_share=calc.owed_expense_share,
        expense_balance=calc.expense_balance,
        net_balance=calc.net_balance,
        shortage_share=share,
        adjusted_net_balance=adjusted,
    )


def _to_participant_audit(
    calc: _ParticipantCalc,
    shortage_shares: dict[uuid.UUID, Decimal] | None = None,
) -> ParticipantAudit:
    share = (shortage_shares or {}).get(calc.participant.id, Decimal("0"))
    adjusted = (
        (calc.net_balance - share).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
        if calc.net_balance is not None
        else None
    )
    buy_in_items = [
        BuyInLineItem(
            buy_in_id=b.id,
            cash_amount=b.cash_amount,
            chips_amount=b.chips_amount,
            buy_in_type=b.buy_in_type,
            created_at=b.created_at,
        )
        for b in calc.buy_ins
    ]
    expenses_paid_items = [
        ExpensePaidLineItem(
            expense_id=e.id,
            expense_title=e.title,
            total_amount=e.total_amount,
        )
        for e in calc.expenses_paid
    ]
    expense_split_items = [
        ExpenseSplitLineItem(
            expense_id=split.expense_id,
            expense_title=expense.title,
            share_amount=split.share_amount,
        )
        for split, expense in calc.expense_splits
    ]
    return ParticipantAudit(
        participant_id=calc.participant.id,
        display_name=calc.display_name,
        participant_type=calc.participant.participant_type.value,
        total_buy_ins=calc.total_buy_ins,
        final_chips=calc.final_chips,
        final_chip_cash_value=calc.final_chip_cash_value,
        poker_balance=calc.poker_balance,
        amount_paid_for_group=calc.amount_paid_for_group,
        owed_expense_share=calc.owed_expense_share,
        expense_balance=calc.expense_balance,
        net_balance=calc.net_balance,
        shortage_share=share,
        adjusted_net_balance=adjusted,
        buy_in_items=buy_in_items,
        expenses_paid_items=expenses_paid_items,
        expense_split_items=expense_split_items,
    )


def get_settlement(db: Session, game: Game) -> SettlementResponse:
    """Compute and return the settlement summary for a game.

    If the game was closed with a shortage strategy, shortage_shares are
    applied to adjusted_net_balance and transfers.
    """
    calcs = _build_calcs(db, game)
    complete = _is_complete(calcs)

    shortage_amount = game.shortage_amount or Decimal("0")
    shortage_strategy = game.shortage_strategy

    shortage_shares: dict[uuid.UUID, Decimal] = {}
    if complete and shortage_amount > Decimal("0") and shortage_strategy:
        shortage_shares = distribute_shortage(calcs, shortage_amount, shortage_strategy)

    transfers = _generate_transfers(calcs, shortage_shares) if complete else []

    return SettlementResponse(
        game_id=game.id,
        game_status=game.status.value,
        chip_cash_rate=game.chip_cash_rate,
        currency=game.currency,
        is_complete=complete,
        balances=[_to_participant_balance(c, shortage_shares) for c in calcs],
        transfers=transfers,
        shortage_amount=shortage_amount,
        shortage_strategy=shortage_strategy,
    )


def resettle_game(db: Session, game: Game) -> SettlementResponse:
    """Recompute settlement for a closed game after a retroactive edit.

    - Uses stored shortage_strategy from the game record (if any)
    - Re-evaluates shortage amount from current ledger data
    - If shortage is eliminated, clears shortage fields on the game
    - If shortage persists/changes, updates shortage_amount on the game
    - Returns the new SettlementResponse (used by caller for notifications)

    Uses flush() so the caller controls the transaction boundary.
    """
    calcs = _build_calcs(db, game)
    new_shortage = compute_shortage_amount(calcs)

    strategy = game.shortage_strategy

    if new_shortage > Decimal("0") and strategy:
        game.shortage_amount = new_shortage
    elif new_shortage <= Decimal("0"):
        # Shortage eliminated — clear fields
        game.shortage_amount = None
        game.shortage_strategy = None
        strategy = None

    db.flush()

    # Now compute the final settlement with updated shortage fields
    shortage_amount = game.shortage_amount or Decimal("0")
    shortage_shares: dict[uuid.UUID, Decimal] = {}
    if _is_complete(calcs) and shortage_amount > Decimal("0") and strategy:
        shortage_shares = distribute_shortage(calcs, shortage_amount, strategy)

    transfers = _generate_transfers(calcs, shortage_shares) if _is_complete(calcs) else []

    return SettlementResponse(
        game_id=game.id,
        game_status=game.status.value,
        chip_cash_rate=game.chip_cash_rate,
        currency=game.currency,
        is_complete=_is_complete(calcs),
        balances=[_to_participant_balance(c, shortage_shares) for c in calcs],
        transfers=transfers,
        shortage_amount=shortage_amount,
        shortage_strategy=game.shortage_strategy,
    )


def get_settlement_audit(db: Session, game: Game) -> SettlementAuditResponse:
    """Compute and return the full audit breakdown for a game."""
    calcs = _build_calcs(db, game)
    complete = _is_complete(calcs)

    shortage_amount = game.shortage_amount or Decimal("0")
    shortage_strategy = game.shortage_strategy

    shortage_shares: dict[uuid.UUID, Decimal] = {}
    if complete and shortage_amount > Decimal("0") and shortage_strategy:
        shortage_shares = distribute_shortage(calcs, shortage_amount, shortage_strategy)

    transfers = _generate_transfers(calcs, shortage_shares) if complete else []

    completed_net_balances = [c.net_balance for c in calcs if c.net_balance is not None]
    net_balance_sum: Decimal | None = None
    if completed_net_balances:
        net_balance_sum = sum(completed_net_balances, Decimal("0")).quantize(
            _TWO_PLACES, rounding=ROUND_HALF_UP
        )

    return SettlementAuditResponse(
        game_id=game.id,
        game_status=game.status.value,
        chip_cash_rate=game.chip_cash_rate,
        currency=game.currency,
        is_complete=complete,
        net_balance_sum=net_balance_sum,
        participants=[_to_participant_audit(c, shortage_shares) for c in calcs],
        transfers=transfers,
        shortage_amount=shortage_amount,
        shortage_strategy=shortage_strategy,
    )
