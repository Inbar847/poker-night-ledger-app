# CLAUDE.md

## Mission

You are building **Poker Night Ledger**, a full-stack mobile app for managing real-world poker nights.

This product is **not** for playing poker online and **not** for gambling automation.  
It is a logistics and accounting app for private in-person games.

The app must support:
- registered users with profiles, history, and personal statistics
- guest participants
- one user acting as the **dealer/host** for a specific game
- real-time updates during a live game
- dealer-controlled buy-ins
- shared side-expenses (pizza, drinks, etc.)
- final chip counts
- deterministic settlement calculations
- a clean list of who pays whom

Read these files before making any major change:
1. `docs/PRODUCT_SPEC.md`
2. `docs/ARCHITECTURE.md`
3. `docs/PLAN.md`

Do **not** skip this reading step.

---

## Core product decisions

These decisions are already approved and must be treated as product truth unless the user explicitly changes them:

1. Support both **registered users** and **guest participants**.
2. Only the **dealer** can update **buy-ins**.
3. The app requires **real-time updates** during a live game.
4. Settlement payment-status tracking is **out of scope for MVP**.
5. Players can join by **invite link** or by being invited as an **existing user**.
6. Statistics are **personal only**; no cross-user leaderboards for MVP.

Additional rule for MVP:
- treat the dealer as the source of truth for the official table ledger
- if there is ambiguity around who may edit a live financial record, default to **dealer-only** for MVP and note the decision in your output

---

## Product model

### Global identity
There is only one global system role: `user`.

### Per-game role
A participant has a role **inside a game**:
- `dealer`
- `player`

The same user may be:
- dealer in one game
- player in another game

Do not model dealer/player as permanent global user roles.

---

## High-level architecture

Use a monorepo with:
- `mobile/` → React Native + Expo + TypeScript
- `backend/` → FastAPI + SQLAlchemy + Alembic + PostgreSQL
- `docs/` → project planning and architecture docs

Recommended supporting libraries:
- mobile routing: Expo Router
- mobile server state: TanStack Query
- mobile local UI state: Zustand
- forms/validation: React Hook Form + Zod
- backend auth: JWT access + refresh tokens
- backend schema validation: Pydantic v2
- testing: pytest on backend, lightweight component/service tests on mobile when useful
- real-time: FastAPI WebSockets for MVP
- image field: `profile_image_url` in MVP data model

Do not introduce a different major stack unless the user explicitly approves it.

---

## Absolute engineering rules

### 1) Work one stage at a time
The source of truth for sequencing is `docs/PLAN.md`.

When asked to build the next stage:
- identify the exact stage
- implement **only that stage**
- stop after the stage is complete
- do not silently continue into the next stage

### 2) Never generate the whole app at once
Prefer small, safe, reviewable changes.

### 3) Separate business logic from UI
Do not bury settlement logic inside screens or route handlers.
Use dedicated service modules.

### 4) Preserve deterministic calculations
All money/chip calculations must be deterministic and testable.
No hidden rounding behavior.
If rounding is needed, do it explicitly and document it.

### 5) Prefer additive changes over rewrites
If files already exist, modify them carefully.
Do not perform broad refactors unless required by the current stage.

### 6) Keep the system type-safe
Use typed request/response schemas and typed frontend models.

### 7) Use migrations
Schema changes must go through Alembic migrations.
Do not rely on ad-hoc table creation once migrations are set up.

### 8) Build for auditability
Every financial outcome should be explainable from stored records:
- buy-ins
- expenses
- final stacks
- settlement result

### 9) Respect permission boundaries
For MVP:
- dealer creates and manages the live game ledger
- participants can view their own data and game data they belong to
- unauthenticated users may only use public auth/join flows as allowed by the current stage

### 10) Do not invent missing product behavior without noting it
If a small decision must be made, choose the safest MVP option and clearly state it in the stage summary.

---

## Backend rules

### Structure
Prefer a clean structure such as:
- `app/main.py`
- `app/core/`
- `app/database/`
- `app/models/`
- `app/schemas/`
- `app/api/routers/`
- `app/services/`
- `app/realtime/`
- `tests/`

### Backend style
- thin routers/controllers
- business logic in services
- SQLAlchemy models in `models`
- Pydantic schemas in `schemas`
- auth dependencies in `core/auth` or similar
- settings in `core/config`
- reusable database session dependency

### Backend quality rules
- always validate ownership/participation before returning game data
- always validate dealer-only mutation endpoints
- write at least basic tests for new core services and critical endpoints
- avoid silently swallowing exceptions
- return consistent error payloads
- prefer explicit transactions for multi-step financial writes

---

## Mobile rules

### Structure
Prefer a clean structure such as:
- `app/` or `src/app/` for routes/screens
- `src/components/`
- `src/features/`
- `src/services/`
- `src/store/`
- `src/types/`
- `src/hooks/`
- `src/lib/`

### Mobile style
- keep screens thin
- move API calls to service/query layers
- keep query keys centralized
- keep pure calculation helpers outside screens
- use form validation
- handle loading/error/empty states
- avoid overengineering UI in early stages

### UX priorities
- fast live table entry
- minimal taps for adding buy-ins
- clear visibility of totals per player
- clear settlement summary
- obvious dealer controls vs read-only player views

---

## Realtime rules

Realtime is required for live games.

For MVP:
- use WebSockets
- clients subscribe to a game room/channel
- server broadcasts structured events when relevant records change

Example event categories:
- participant joined
- buy-in created/updated
- expense created/updated
- final stack updated
- game closed
- settlement recalculated

Do not add Redis or distributed pub/sub unless scaling requirements explicitly appear.
A single-instance WebSocket manager is enough for MVP.

---

## Data and calculation rules

The financial engine must support:
- multiple buy-ins per participant
- registered users and guests
- shared expenses split across selected participants
- final chip counts
- chip-to-cash conversion
- optimized transfer generation

Keep these concepts separate:
1. poker ledger
2. side-expense ledger
3. final combined balance
4. optimized transfer plan

Important:
- a dealer may also be a player financially
- guests can participate in a game even without a registered account
- stats are personal and computed only for registered users

---

## What to output after each stage

After finishing a stage, always provide:

1. **What was implemented**
2. **Files added/changed**
3. **Commands to run**
4. **Manual test steps**
5. **Automated tests added/run**
6. **Any assumptions or small product decisions made**
7. **What is intentionally left for the next stage**

Keep that summary concise and practical.

---

## When blocked

If blocked by ambiguity:
- do not redesign the product
- inspect the docs
- choose the safest MVP interpretation
- state the assumption clearly

If blocked by missing environment setup:
- create the minimal setup needed for the current stage
- do not jump ahead into future stages

---

## Never do these without explicit approval

- replacing FastAPI with another backend framework
- replacing Expo/React Native with Flutter or native apps
- removing guest support
- removing realtime requirements
- changing dealer-only buy-in control
- adding payments/escrow/wallet functionality
- adding social feed, chat, leaderboard, or advanced analytics
- adding broad refactors outside the current stage

---

## Definition of done

A stage is done only if:
- code for that stage exists
- basic tests exist where appropriate
- the app/backend can run for that stage
- no unrelated architecture drift was introduced
- the summary clearly explains what changed

---

## Post-MVP (Phase 2)

The MVP is complete through Stage 9.

Phase 2 adds social features, UX polish, and in-app notifications.  
Before working on any Phase 2 stage, read these docs in addition to the standard three:

4. `docs/PHASE2_PRODUCT_SPEC.md` — Phase 2 product goals and feature rules
5. `docs/PHASE2_ARCHITECTURE.md` — new models, endpoints, services, and mobile modules
6. `docs/PHASE2_PLAN.md` — stage-by-stage implementation plan (Stages 10–17)
7. `docs/KNOWN_ISSUES.md` — documented bugs targeted for Phase 2

Phase 2 stages are numbered 10–17.  
All MVP behavior (guest support, realtime, dealer-only buy-in control, settlement engine) is preserved unless `PHASE2_PRODUCT_SPEC.md` explicitly overrides it.

The same "one stage at a time" rule applies. Do not silently continue into the next stage.

---

## Post-Phase-2 (Phase 3)

Phase 2 is complete through Stage 17.

Phase 3 adds game lifecycle improvements, invitation rework, early cash-out, and behavior fixes.  
Before working on any Phase 3 stage, read these docs in addition to the standard three:

8. `docs/PHASE3_PRODUCT_SPEC.md` — Phase 3 product goals, behavior fixes, and feature rules
9. `docs/PHASE3_ARCHITECTURE.md` — new models, endpoints, services, and mobile changes
10. `docs/PHASE3_PLAN.md` — stage-by-stage implementation plan (Stages 18–23)

Phase 3 stages are numbered 18–23.  
All MVP and Phase 2 behavior is preserved unless `PHASE3_PRODUCT_SPEC.md` explicitly overrides it.

The same "one stage at a time" rule applies. Do not silently continue into the next stage.

---

## Post-Phase-3 (Phase 4)

Phase 3 is complete through Stage 23.

Phase 4 adds live invitation popups, retroactive game editing, player-added expenses, and UX polish.  
Before working on any Phase 4 stage, read these docs in addition to the standard three:

11. `docs/PHASE4_PRODUCT_SPEC.md` — Phase 4 product goals, permission changes, and feature rules
12. `docs/PHASE4_ARCHITECTURE.md` — new models, endpoints, services, and mobile changes
13. `docs/PHASE4_PLAN.md` — stage-by-stage implementation plan (Stages 24–29)

Phase 4 stages are numbered 24–29.  
All MVP, Phase 2, and Phase 3 behavior is preserved unless `PHASE4_PRODUCT_SPEC.md` explicitly overrides it.

The same "one stage at a time" rule applies. Do not silently continue into the next stage.

---

## Post-Phase-4 (Phase 5)

Phase 4 is complete through Stage 29.

Phase 5 is a **frontend redesign and design-system phase only**. It rebuilds every mobile screen using a shared component library and design token system. **No backend code, API contracts, or data models are changed.**

Before working on any Phase 5 stage, read these docs in addition to the standard three:

14. `docs/PHASE5_PRODUCT_SPEC.md` — Phase 5 design philosophy, principles, and product rules
15. `docs/PHASE5_ARCHITECTURE.md` — component architecture, token system, and mobile structure changes
16. `docs/PHASE5_PLAN.md` — stage-by-stage implementation plan (Stages 30–41)
17. `docs/frontend/DESIGN_LANGUAGE.md` — detailed design language specification
18. `docs/frontend/COMPONENT_RULES.md` — rules for building and using shared components
19. `docs/frontend/SCREEN_SPECS.md` — per-screen visual and interaction specifications

Phase 5 stages are numbered 30–41.  
All MVP, Phase 2, Phase 3, and Phase 4 behavior is preserved. Phase 5 changes **only** the visual presentation layer.

For Phase 5 stages, use the `frontend-phase5-stage` skill instead of the generic `execute-stage` skill. The `frontend-ui-qa` skill is available for verifying design system compliance after screen rebuilds.

The same "one stage at a time" rule applies. Do not silently continue into the next stage.
