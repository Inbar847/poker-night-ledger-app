---
name: execute-stage
description: Execute exactly one approved stage from docs/PLAN.md for Poker Night Ledger. Read CLAUDE.md and all project docs first, stay within the requested stage boundary, and stop when the stage is complete.
---

# execute-stage

Use this skill when the user asks to implement a specific stage from the project plans.

## Phase routing

- **Stages 0–9:** Read `docs/PLAN.md`, `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`
- **Stages 10–17:** Also read `docs/PHASE2_PRODUCT_SPEC.md`, `docs/PHASE2_ARCHITECTURE.md`, `docs/PHASE2_PLAN.md`
- **Stages 18–23:** Also read `docs/PHASE3_PRODUCT_SPEC.md`, `docs/PHASE3_ARCHITECTURE.md`, `docs/PHASE3_PLAN.md`
- **Stages 24–29:** Also read `docs/PHASE4_PRODUCT_SPEC.md`, `docs/PHASE4_ARCHITECTURE.md`, `docs/PHASE4_PLAN.md`
- **Stages 30–41:** Use the `frontend-phase5-stage` skill instead — it has Phase 5-specific rules for the frontend redesign. If invoked here, redirect to that skill.

## Required behavior

1. Read `CLAUDE.md` and the docs listed for the stage's phase (see phase routing above).

2. Identify the exact stage requested by the user.

3. Before coding, provide:
   - a concise restatement of the stage goal
   - likely files to be created/changed
   - any small assumptions

4. Implement **only** the requested stage.
   - Do not continue into future stages.
   - Do not perform broad refactors unless strictly necessary.
   - Keep business logic out of UI.
   - Preserve approved product rules.

5. Add or update tests where relevant.

6. At the end, provide:
   - what was implemented
   - changed files
   - commands to run
   - manual test steps
   - tests run
   - assumptions/deferred items

7. Stop and wait for the next instruction.

## Product-specific constraints

- Support registered users and guests.
- Only the dealer can update buy-ins.
- Realtime is required.
- Settlement payment-status tracking is out of scope for MVP.
- Invite flow must support links/tokens and inviting existing users.
- Statistics are personal only.
- Dealer is the MVP source of truth for official ledger edits.
