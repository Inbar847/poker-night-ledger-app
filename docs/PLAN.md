# PLAN.md

This file is the execution roadmap for **Poker Night Ledger**.  
Claude must implement **one stage at a time** and stop after the requested stage.

---

# Stage 0 — Monorepo bootstrap and local development foundation

## Goal
Create the initial monorepo and a clean local development baseline for mobile + backend.

## Deliverables
- root repo structure:
  - `mobile/`
  - `backend/`
  - `docs/`
  - `CLAUDE.md`
  - `.claude/settings.json`
- backend FastAPI app boots successfully
- backend has a `/health` endpoint
- backend Docker setup for PostgreSQL
- backend environment example file
- Alembic initialized but first migration may wait until Stage 1 if cleaner
- mobile Expo app boots successfully
- mobile has minimal navigation/screen shell
- root README with setup commands

## Suggested tasks
1. Create repo structure
2. Initialize backend project
3. Add config management and DB connection scaffolding
4. Add Docker Compose for PostgreSQL
5. Initialize mobile Expo TypeScript app
6. Add baseline route/screen structure
7. Add shared docs/README

## Acceptance criteria
- `docker compose up -d postgres` works
- backend starts and `/health` returns success
- mobile app runs in Expo
- no business logic yet
- no auth yet
- no game models yet

## Stop boundary
Stop after foundation is running.  
Do not implement auth or product entities yet.

---

# Stage 1 — Backend auth, users, profiles, and migrations

## Goal
Build the backend identity foundation.

## Deliverables
- user model
- Alembic migration(s)
- register endpoint
- login endpoint
- refresh token flow
- current user endpoint
- update profile endpoint
- profile fields:
  - full_name
  - phone
  - email
  - password_hash
  - profile_image_url
- password hashing
- JWT auth
- backend tests for core auth flows

## Suggested endpoints
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `GET /users/me`
- `PATCH /users/me`

## Acceptance criteria
- a user can register and login
- protected endpoints require auth
- profile can be fetched and updated
- migrations are working
- auth tests pass

## Stop boundary
Do not build mobile auth screens yet beyond placeholders if needed for wiring.  
Do not build games yet.

---

# Stage 2 — Game creation, participants, guests, and invitation flows

## Goal
Model games and participants, including registered users and guests.

## Deliverables
- game model
- participant model
- guest participant support
- create game flow
- dealer assignment on game creation
- invite existing registered user
- join via invite link/token
- lobby state for a game before play starts
- permissions for dealer vs participant
- backend tests for game creation and joining

## Product rules
- game creator becomes `dealer`
- dealer can also be a financial participant
- participant may be:
  - registered user
  - guest
- guest must belong to a specific game only, not become a global user automatically

## Suggested endpoints
- `POST /games`
- `GET /games/:game_id`
- `GET /games`
- `POST /games/:game_id/invite-link`
- `POST /games/join-by-token`
- `POST /games/:game_id/invite-user`
- `POST /games/:game_id/guests`
- `GET /games/:game_id/participants`

## Acceptance criteria
- dealer can create a game
- a registered user can join via invite link
- dealer can add a guest participant
- permissions are enforced
- tests cover join flows and access control

## Stop boundary
Do not implement buy-ins, expenses, or settlements yet.

---

# Stage 3 — Core live game ledger: buy-ins, expenses, final stacks, closing a game

## Goal
Build the core financial record system for a live game.

## Deliverables
- buy-in model + CRUD as needed
- expense model + split model
- final stack model
- game status transitions:
  - lobby
  - active
  - closed
- close-game flow
- validation rules for ledger integrity
- backend tests for core ledger flows

## Product rules
- only dealer can create/update/delete buy-ins
- for MVP, treat dealer as the owner of official financial edits
- participants can view game ledger but not mutate it unless explicitly opened by current scope
- expenses can be split across selected participants
- final stack exists once per participant per game

## Suggested endpoints
- `POST /games/:game_id/start`
- `POST /games/:game_id/buy-ins`
- `GET /games/:game_id/buy-ins`
- `POST /games/:game_id/expenses`
- `GET /games/:game_id/expenses`
- `PUT /games/:game_id/final-stacks/:participant_id`
- `GET /games/:game_id/final-stacks`
- `POST /games/:game_id/close`

## Acceptance criteria
- dealer can record multiple buy-ins for any participant
- expenses can be split among selected participants
- final stacks can be entered for all participants
- a game can move to closed state
- integrity checks prevent invalid operations

## Stop boundary
Do not implement optimized settlement algorithm yet.

---

# Stage 4 — Settlement engine and audit breakdown

## Goal
Build deterministic financial calculations and optimized transfer suggestions.

## Deliverables
- calculation service(s) for:
  - total buy-ins
  - poker outcome from final stacks
  - expense netting
  - combined final balances
  - optimized transfer generation
- settlement response models
- audit/breakdown endpoint
- backend tests for edge cases and deterministic outcomes

## Required formulas
For each participant:
1. `total_buy_ins = sum(cash_amount of buy-ins)`
2. `final_chip_cash_value = final_chips * chip_cash_rate`
3. `poker_balance = final_chip_cash_value - total_buy_ins`
4. `expense_balance = amount_paid_for_group - owed_expense_share`
5. `net_balance = poker_balance + expense_balance`

Then:
- participants with positive net balance should receive money
- participants with negative net balance should pay money
- generate a minimized, deterministic transfer list

## Edge cases to test
- multiple buy-ins
- guests mixed with users
- dealer is also a player
- expenses shared across subset only
- zero-sum validation
- rounding behavior

## Suggested endpoints
- `GET /games/:game_id/settlement`
- `GET /games/:game_id/settlement/audit`

## Acceptance criteria
- settlement output is deterministic
- transfer list sums correctly
- audit output explains how each value was derived
- tests cover realistic scenarios

## Stop boundary
Do not implement realtime transport yet.

---

# Stage 5 — Realtime transport for live game updates

## Goal
Make active games update live across connected clients.

## Deliverables
- WebSocket connection flow
- authenticated subscription to a game room
- structured event payloads
- broadcast on:
  - participant join
  - game start
  - buy-in changes
  - expense changes
  - final stack changes
  - game close
  - settlement update trigger
- reconnect-safe client contract documentation
- backend tests where practical

## Suggested event types
- `game.participant_joined`
- `game.started`
- `buyin.created`
- `buyin.updated`
- `expense.created`
- `expense.updated`
- `final_stack.updated`
- `game.closed`
- `settlement.updated`

## Acceptance criteria
- two clients connected to the same game receive live updates
- unauthorized client cannot subscribe
- payload shape is documented and stable

## Stop boundary
Do not build full mobile screens yet.

---

# Stage 6 — Mobile auth and profile flows

## Goal
Build the user-facing mobile authentication and profile foundation.

## Deliverables
- login screen
- register screen
- authenticated app shell
- token storage
- auth guard
- profile screen
- profile edit flow
- profile image URL field handling
- server-state integration for auth/profile

## Acceptance criteria
- register/login/logout work on device
- auth persists correctly
- profile fetch/update works
- loading and error states exist

## Stop boundary
Do not build full game management flow yet.

---

# Stage 7 — Mobile game flows and realtime integration

## Goal
Build the live game experience in the mobile app.

## Deliverables
- home/dashboard
- create game flow
- join by invite link/token flow
- game lobby
- participant list
- dealer live ledger screen
- buy-in entry flow
- expense entry flow
- final stack entry flow
- settlement screen
- realtime updates wired into the UI

## UX priorities
- dealer actions should be fast
- clear visual separation between dealer controls and participant view-only state
- totals should always be visible
- important live mutations should confirm success/failure clearly

## Acceptance criteria
- a dealer can run a whole game from the app
- a participant can join and watch updates live
- settlement is visible at game end
- the core MVP flow is usable end-to-end

## Stop boundary
Do not implement history/stats yet.

---

# Stage 8 — History, game details, and personal statistics

## Goal
Build historical visibility and personal stats.

## Deliverables
- my games list
- game details screen
- personal stats endpoint(s)
- profile statistics UI
- basic aggregates such as:
  - total games played
  - total games hosted
  - cumulative profit/loss
  - average result per game
  - win rate by positive/negative net result
  - recent games summary

## Important rule
Statistics are personal only for MVP.  
No public leaderboard or social comparison layer.

## Acceptance criteria
- user can browse previous games
- user can inspect a historical game
- profile shows personal summary stats
- stats exclude guest-only identities from personal profiles

## Stop boundary
Do not add extra analytics beyond approved scope.

---

# Stage 9 — Hardening, QA, dev UX, and release readiness

## Goal
Stabilize the MVP.

## Deliverables
- improved validation and error messages
- seed/demo data flow
- test coverage improvements
- linting/formatting cleanup
- env examples
- production-readiness notes
- backup/recovery notes for DB
- release checklist

## Acceptance criteria
- key flows are testable locally end-to-end
- setup instructions are clean
- obvious bugs found during manual QA are fixed
- docs match implementation

## Stop boundary
Stop after MVP hardening.  
Do not expand scope into payments, chat, or social features.

---

# Stage execution rules

For every stage Claude must:

1. Restate the stage goal in 3-6 bullets.
2. List the files likely to be created/changed.
3. Implement only that stage.
4. Run or describe the exact commands needed.
5. Add/update tests where relevant.
6. End with:
   - summary
   - changed files
   - commands
   - manual test steps
   - assumptions
   - next recommended stage

If implementation reveals a structural issue:
- fix only what is necessary for the current stage
- do not silently refactor unrelated areas
