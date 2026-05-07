# ARCHITECTURE.md

# Architecture overview

Poker Night Ledger is a mobile-first full-stack application with a dedicated backend and database.

Recommended stack:
- **Mobile:** React Native + Expo + TypeScript
- **Backend:** FastAPI + SQLAlchemy + Pydantic + Alembic
- **Database:** PostgreSQL
- **Realtime:** WebSockets
- **Auth:** JWT access + refresh
- **Client data fetching:** TanStack Query
- **Client local UI state:** Zustand

---

# Monorepo structure

Recommended repository layout:

```text
poker-night-ledger/
├─ mobile/
├─ backend/
├─ docs/
├─ CLAUDE.md
└─ .claude/
   └─ settings.json
```

Suggested deeper structure:

```text
backend/
├─ app/
│  ├─ api/
│  │  └─ routers/
│  ├─ core/
│  ├─ database/
│  ├─ models/
│  ├─ realtime/
│  ├─ schemas/
│  ├─ services/
│  └─ main.py
├─ alembic/
├─ tests/
├─ pyproject.toml
└─ .env.example

mobile/
├─ app/
├─ src/
│  ├─ components/
│  ├─ features/
│  ├─ hooks/
│  ├─ lib/
│  ├─ services/
│  ├─ store/
│  └─ types/
├─ package.json
└─ .env.example
```

---

# System components

## Mobile app
Responsibilities:
- authentication UX
- profile screens
- game creation/join flows
- live game views
- settlement screen
- history/stats screens
- WebSocket client integration
- local presentation state

## Backend API
Responsibilities:
- authentication
- authorization
- persistence
- invitation handling
- game lifecycle
- live ledger mutations
- settlement calculation
- historical aggregation
- WebSocket event broadcast

## PostgreSQL
Responsibilities:
- durable storage for users, games, participants, ledger records, and history

---

# Domain model

## 1) users
Represents a permanent registered identity.

Suggested fields:
- `id`
- `email` (unique)
- `password_hash`
- `full_name`
- `phone`
- `profile_image_url`
- `created_at`
- `updated_at`

## 2) games
Represents a single poker night/session.

Suggested fields:
- `id`
- `title`
- `created_by_user_id`
- `dealer_user_id`
- `scheduled_at` or `started_at`
- `chip_cash_rate`
- `currency`
- `status` (`lobby`, `active`, `closed`)
- `invite_token` (nullable / rotatable)
- `created_at`
- `updated_at`
- `closed_at` (nullable)

Note:
`created_by_user_id` and `dealer_user_id` may be the same in MVP.

## 3) participants
Represents a game-scoped participant.

Suggested fields:
- `id`
- `game_id`
- `user_id` (nullable for guests)
- `guest_name` (nullable for registered users)
- `participant_type` (`registered`, `guest`)
- `role_in_game` (`dealer`, `player`)
- `joined_at`

Important:
A guest is represented here, not in `users`.

## 4) buy_ins
Represents each cash entry for chips.

Suggested fields:
- `id`
- `game_id`
- `participant_id`
- `cash_amount`
- `chips_amount`
- `buy_in_type` (`initial`, `rebuy`, `addon`)
- `created_by_user_id`
- `created_at`
- `updated_at`

Rules:
- dealer-only mutation in MVP
- multiple buy-ins allowed per participant

## 5) expenses
Represents side expenses such as pizza.

Suggested fields:
- `id`
- `game_id`
- `title`
- `total_amount`
- `paid_by_participant_id`
- `created_by_user_id`
- `created_at`
- `updated_at`

## 6) expense_splits
Represents how a single expense is distributed.

Suggested fields:
- `id`
- `expense_id`
- `participant_id`
- `share_amount`

Rule:
- sum of `share_amount` rows must equal `expenses.total_amount`

## 7) final_stacks
Represents the final chip count per participant for a game.

Suggested fields:
- `id`
- `game_id`
- `participant_id`
- `chips_amount`
- `created_at`
- `updated_at`

Rule:
- at most one final stack row per participant per game

## 8) refresh_tokens (optional but recommended)
If refresh tokens are stored server-side.

Suggested fields:
- `id`
- `user_id`
- `token_hash`
- `expires_at`
- `revoked_at`
- `created_at`

---

# Core backend modules

## auth service
Responsibilities:
- register
- login
- issue access token
- issue refresh token
- get current user

## user service
Responsibilities:
- fetch/update profile
- basic user lookup for invitations

## game service
Responsibilities:
- create game
- list games
- fetch game details
- transition state: lobby → active → closed

## participant service
Responsibilities:
- invite registered user
- add guest
- join by token
- enforce per-game roles

## buy-in service
Responsibilities:
- create/list/update/delete buy-ins
- validate dealer permissions
- validate participant belongs to game

## expense service
Responsibilities:
- create/list/update/delete expenses
- validate split totals
- validate participants belong to game

## final stack service
Responsibilities:
- set/update final stacks
- validate one row per participant per game

## settlement service
Responsibilities:
- aggregate all ledger data
- compute balances
- compute optimized transfer list
- produce audit view

## realtime service
Responsibilities:
- manage active WebSocket connections
- subscribe by game
- broadcast structured events

## stats service
Responsibilities:
- compute personal stats for registered users
- return history summaries and aggregates

---

# API design outline

Recommended REST-style outline:

## Auth
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`

## Users
- `GET /users/me`
- `PATCH /users/me`

## Games
- `POST /games`
- `GET /games`
- `GET /games/{game_id}`
- `POST /games/{game_id}/start`
- `POST /games/{game_id}/close`

## Invitations / participants
- `POST /games/{game_id}/invite-link`
- `POST /games/join-by-token`
- `POST /games/{game_id}/invite-user`
- `POST /games/{game_id}/guests`
- `GET /games/{game_id}/participants`

## Buy-ins
- `POST /games/{game_id}/buy-ins`
- `GET /games/{game_id}/buy-ins`
- `PATCH /games/{game_id}/buy-ins/{buy_in_id}`
- `DELETE /games/{game_id}/buy-ins/{buy_in_id}`

## Expenses
- `POST /games/{game_id}/expenses`
- `GET /games/{game_id}/expenses`
- `PATCH /games/{game_id}/expenses/{expense_id}`
- `DELETE /games/{game_id}/expenses/{expense_id}`

## Final stacks
- `PUT /games/{game_id}/final-stacks/{participant_id}`
- `GET /games/{game_id}/final-stacks`

## Settlement
- `GET /games/{game_id}/settlement`
- `GET /games/{game_id}/settlement/audit`

## History / stats
- `GET /history/games`
- `GET /history/games/{game_id}`
- `GET /stats/me`

---

# Auth and permissions

## Authentication
Use JWT:
- short-lived access token
- longer-lived refresh token

## Authorization
Rules:
- only authenticated users access protected endpoints
- only participants of a game can read game data
- only dealer can mutate official ledger records in MVP
- guests have no standalone authenticated account in MVP

Authorization checks should live in reusable dependencies/services, not duplicated ad-hoc in each route.

---

# Realtime design

Use WebSockets for MVP.

## Suggested connection pattern
- client authenticates first over normal auth flow
- client opens WebSocket
- client subscribes to a specific `game_id`
- server verifies access
- server adds socket to that game room
- server broadcasts events to all sockets in that room

## Suggested event envelope

```json
{
  "type": "buyin.created",
  "game_id": "uuid-or-int",
  "timestamp": "iso8601",
  "payload": {}
}
```

Keep event names stable and payloads explicit.

## Minimum event types
- `game.participant_joined`
- `game.started`
- `buyin.created`
- `buyin.updated`
- `buyin.deleted`
- `expense.created`
- `expense.updated`
- `expense.deleted`
- `final_stack.updated`
- `game.closed`
- `settlement.updated`

---

# Settlement calculation design

## Inputs
- game chip cash rate
- all buy-ins
- all expenses and splits
- all final stacks

## Participant totals
For each participant:

### A. Buy-in total
`total_buy_ins = sum(all buy_in.cash_amount)`

### B. Final poker value
`final_chip_cash_value = final_stack.chips_amount * game.chip_cash_rate`

### C. Poker result
`poker_balance = final_chip_cash_value - total_buy_ins`

### D. Expense result
`expense_balance = amount_paid_for_group - owed_expense_share`

### E. Final result
`net_balance = poker_balance + expense_balance`

## Transfer optimization
Create two lists:
- creditors: participants with positive balance
- debtors: participants with negative balance

Then greedily match debtors to creditors in a deterministic order until all balances are settled.

Requirements:
- transfer list should be zero-sum
- output should be deterministic
- rounding strategy must be explicit and tested

---

# Personal statistics design

Stats are for registered users only.

Suggested aggregates:
- total games played
- total games hosted
- cumulative net result
- average net result per game
- number of profitable games
- win rate (`profitable_games / games_played`)
- recent games summary

Guest-only identities should not get their own profile stats.

---

# Mobile architecture guidance

## State split
Use:
- TanStack Query for server data
- Zustand for local UI state
- screen-local state for transient input only

## Example feature grouping
- `features/auth`
- `features/profile`
- `features/games`
- `features/buyins`
- `features/expenses`
- `features/settlement`
- `features/history`

## Screen priorities
Build the simplest usable flow first:
1. auth
2. create/join game
3. lobby
4. live ledger
5. settlement
6. history/stats

---

# Validation rules

Recommended MVP validation:
- buy-in cash amount > 0
- buy-in chips amount >= 0
- expense total > 0
- expense splits must sum to expense total
- final stack chips >= 0
- participant must belong to game
- game must not accept live ledger changes after close
- only dealer can mutate protected game ledger endpoints
- only participants can view game internals

---

# Testing priorities

Highest priority backend tests:
1. auth flow
2. create game / join game
3. dealer-only buy-in permissions
4. expense split validation
5. settlement deterministic scenarios
6. access control for game reads

Highest priority mobile tests/manual QA:
1. login/register
2. create game
3. join game
4. add buy-in as dealer
5. observe realtime update as participant
6. close game and view settlement
