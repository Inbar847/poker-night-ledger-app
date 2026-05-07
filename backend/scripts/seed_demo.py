#!/usr/bin/env python
"""
Seed script -- creates a complete demo game in the database.

Usage (from the backend/ directory with venv active):
    python scripts/seed_demo.py

What it creates:
  - 3 registered users: alice (dealer), bob (player), carol (player)
  - 1 guest participant: Dave Guest
  - 1 game in closed state with buy-ins, expense, final stacks

Idempotency:
  Users are reused if they already exist.
  Each run creates one new demo game.

Requirements:
  DATABASE_URL must be reachable (run "docker compose up -d postgres" first).
  Run "alembic upgrade head" before running this script.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import secrets
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.models.game import Game, GameStatus
from app.models.ledger import BuyIn, BuyInType, Expense, ExpenseSplit, FinalStack
from app.models.participant import Participant, ParticipantType, RoleInGame
from app.models.user import User

DEMO_USERS = [
    {"email": "alice@demo.com", "full_name": "Alice Demo", "password": "demo1234"},
    {"email": "bob@demo.com",   "full_name": "Bob Demo",   "password": "demo1234"},
    {"email": "carol@demo.com", "full_name": "Carol Demo", "password": "demo1234"},
]

CHIP_CASH_RATE = Decimal("0.01")
CURRENCY = "USD"


def _get_or_create_user(db, email, full_name, password):
    user = db.query(User).filter(User.email == email).first()
    if user:
        print(f"  Existing user: {email}")
        return user
    user = User(
        email=email,
        full_name=full_name,
        password_hash=hash_password(password),
    )
    db.add(user)
    db.flush()
    print(f"  Created user:  {email}")
    return user


def seed(db):
    print("\n=== Poker Night Ledger -- Demo Seed ===\n")

    print("-- Users --")
    alice = _get_or_create_user(db, **DEMO_USERS[0])
    bob   = _get_or_create_user(db, **DEMO_USERS[1])
    carol = _get_or_create_user(db, **DEMO_USERS[2])

    print("\n-- Game --")
    game = Game(
        title="Demo Poker Night",
        created_by_user_id=alice.id,
        dealer_user_id=alice.id,
        chip_cash_rate=CHIP_CASH_RATE,
        currency=CURRENCY,
        status=GameStatus.active,
        invite_token=secrets.token_urlsafe(32),
    )
    db.add(game)
    db.flush()
    print(f'  Created game: {game.id} -- "{game.title}"')

    print("\n-- Participants --")
    p_alice = Participant(
        game_id=game.id, user_id=alice.id,
        participant_type=ParticipantType.registered, role_in_game=RoleInGame.dealer,
    )
    p_bob = Participant(
        game_id=game.id, user_id=bob.id,
        participant_type=ParticipantType.registered, role_in_game=RoleInGame.player,
    )
    p_carol = Participant(
        game_id=game.id, user_id=carol.id,
        participant_type=ParticipantType.registered, role_in_game=RoleInGame.player,
    )
    p_dave = Participant(
        game_id=game.id, guest_name="Dave Guest",
        participant_type=ParticipantType.guest, role_in_game=RoleInGame.player,
    )
    db.add_all([p_alice, p_bob, p_carol, p_dave])
    db.flush()
    print("  alice (dealer), bob (player), carol (player), Dave Guest (guest)")

    print("\n-- Buy-ins --")
    # Total chips in: 10000+5000+5000+5000+5000 = 30000
    # Total cash in:  100+50+50+50+50 = 300
    buy_ins = [
        BuyIn(game_id=game.id, participant_id=p_alice.id,
              cash_amount=Decimal("100"), chips_amount=Decimal("10000"),
              buy_in_type=BuyInType.initial, created_by_user_id=alice.id),
        BuyIn(game_id=game.id, participant_id=p_bob.id,
              cash_amount=Decimal("50"), chips_amount=Decimal("5000"),
              buy_in_type=BuyInType.initial, created_by_user_id=alice.id),
        BuyIn(game_id=game.id, participant_id=p_bob.id,
              cash_amount=Decimal("50"), chips_amount=Decimal("5000"),
              buy_in_type=BuyInType.rebuy, created_by_user_id=alice.id),
        BuyIn(game_id=game.id, participant_id=p_carol.id,
              cash_amount=Decimal("50"), chips_amount=Decimal("5000"),
              buy_in_type=BuyInType.initial, created_by_user_id=alice.id),
        BuyIn(game_id=game.id, participant_id=p_dave.id,
              cash_amount=Decimal("50"), chips_amount=Decimal("5000"),
              buy_in_type=BuyInType.initial, created_by_user_id=alice.id),
    ]
    db.add_all(buy_ins)
    db.flush()
    print(f"  {len(buy_ins)} buy-in records (alice=100, bob=100, carol=50, dave=50)")

    print("\n-- Expenses --")
    pizza = Expense(
        game_id=game.id, title="Pizza",
        total_amount=Decimal("40"),
        paid_by_participant_id=p_alice.id,
        created_by_user_id=alice.id,
    )
    db.add(pizza)
    db.flush()
    db.add_all([
        ExpenseSplit(expense_id=pizza.id, participant_id=p_alice.id, share_amount=Decimal("10")),
        ExpenseSplit(expense_id=pizza.id, participant_id=p_bob.id,   share_amount=Decimal("10")),
        ExpenseSplit(expense_id=pizza.id, participant_id=p_carol.id, share_amount=Decimal("10")),
        ExpenseSplit(expense_id=pizza.id, participant_id=p_dave.id,  share_amount=Decimal("10")),
    ])
    print("  Pizza $40.00, split evenly among all 4 participants")

    print("\n-- Final stacks --")
    # Chips redistribute: alice wins most; total stays 30000
    # alice: 14000, bob: 8000, carol: 4000, dave: 4000
    db.add_all([
        FinalStack(game_id=game.id, participant_id=p_alice.id, chips_amount=Decimal("14000")),
        FinalStack(game_id=game.id, participant_id=p_bob.id,   chips_amount=Decimal("8000")),
        FinalStack(game_id=game.id, participant_id=p_carol.id, chips_amount=Decimal("4000")),
        FinalStack(game_id=game.id, participant_id=p_dave.id,  chips_amount=Decimal("4000")),
    ])
    print("  alice=14000  bob=8000  carol=4000  dave=4000 (sum=30000 chips)")

    game.status = GameStatus.closed
    game.closed_at = datetime.now(timezone.utc)

    db.commit()

    print("\n=== Done! ===")
    print(f"  Game ID  : {game.id}")
    print(f"  Status   : {game.status.value}")
    print("\nDemo login credentials  (password: demo1234):")
    print("  alice@demo.com  (dealer)")
    print("  bob@demo.com    (player)")
    print("  carol@demo.com  (player)")
    print("\nUseful API calls (authenticate as alice first):")
    print(f"  GET  /games/{game.id}/settlement")
    print(f"  GET  /games/{game.id}/settlement/audit")
    print("  GET  /history/games")
    print("  GET  /stats/me")
    print()


if __name__ == "__main__":
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        seed(db)
