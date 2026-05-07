# PHASE3_PLAN.md

This file is the execution roadmap for **Phase 3** of Poker Night Ledger.  
Claude must implement **one stage at a time** and stop after the requested stage.

Read `PHASE3_PRODUCT_SPEC.md` and `PHASE3_ARCHITECTURE.md` before implementing any stage.  
The MVP stages (0–9) and Phase 2 stages (10–17) are complete and must not be regressed.

---

# Stage 18 — Notification badge and mark-all-read fixes (P0)

## Goal
Fix the notification badge to reflect only unread notifications and auto-clear when the user enters the notifications screen.

## Scope
- Primarily mobile — no backend changes required (endpoints already exist)

## Deliverables
- Notification badge component reads from `GET /notifications/unread-count` and hides when count is 0
- `NotificationsScreen` calls `POST /notifications/read-all` on screen focus (via `useFocusEffect` or equivalent)
- After mark-all-read succeeds, invalidate the `notificationsUnread` query so the badge updates immediately
- Verify that marking a single notification as read also decrements the badge count

## Files likely to change
- `mobile/src/features/notifications/NotificationsScreen.tsx`
- `mobile/src/hooks/useNotifications.ts`
- Notification badge component (in app shell / tab bar)
- `mobile/src/lib/queryKeys.ts` (if unread count key needs adjustment)

## Acceptance criteria
- Badge shows exact unread count; 0 hides the badge
- Entering notifications screen marks all as read and badge drops to 0
- New notifications arriving after screen mount are not auto-read
- Marking a single notification read decrements badge by 1

## Stop boundary
Fix only the badge and auto-read behavior. Do not change notification creation logic or add new types.

---

# Stage 19 — Close game validation: require final stacks (P0)

## Goal
Block the dealer from closing a game when any settlement-eligible participant is missing a final chip count. Return a clear error listing who is missing.

## Scope
- Backend: add validation to close-game flow
- Mobile: handle new error response and display missing participants

## Deliverables

### Backend
- In the `POST /games/{game_id}/close` endpoint, before proceeding with close:
  1. Query all participants for the game
  2. Filter to those requiring a final stack (all participants for now; once participant statuses exist, filter to `active` and `left_early`)
  3. Check that each has a `final_stacks` row
  4. If any are missing, return HTTP 400 with `detail` and `missing_final_stacks` array
- New response schema: `CloseGameValidationError` with `missing_final_stacks: list[MissingFinalStack]`
- Backend tests: close blocked when stacks missing, allowed when all present

### Mobile
- Close-game error handler parses the `missing_final_stacks` response
- Renders a clear list: "Cannot close game. Missing final chip counts for: Alice, Bob, Guest 1"
- Dealer can dismiss the error and navigate to enter the missing values

## Files likely to change/add

**Backend:**
- `app/api/routers/games.py` (extend close_game endpoint)
- `app/schemas/game.py` (add MissingFinalStack, CloseGameValidationError schemas)
- `tests/test_close_validation.py`

**Mobile:**
- `mobile/app/(app)/games/[id]/index.tsx` or relevant active game screen
- Close-game UI component

## Acceptance criteria
- Closing a game with all final stacks present succeeds as before
- Closing a game with any missing final stacks returns 400 with the list of who is missing
- Mobile displays the error clearly with participant names
- Shortage flow still works correctly when stacks are complete

## Stop boundary
Do not add participant lifecycle statuses yet. All participants are treated as requiring final stacks.

---

# Stage 20 — Participant lifecycle statuses

## Goal
Add a `status` field to the participant model to support `active`, `left_early`, and `removed_before_start` lifecycle states.

## Scope
- Backend: model change, migration, service updates
- No mobile UI changes yet (UI comes in later stages)

## Deliverables
- Add `ParticipantStatus` enum: `active`, `left_early`, `removed_before_start`
- Add `status` column to `participants` table (default: `active`)
- Alembic migration: add column with default value, backfill existing rows to `active`
- Update `ParticipantResponse` schema to include `status`
- Update `participant_service`:
  - `set_participant_status(db, participant_id, status)`
  - `get_settlement_eligible_participants(db, game_id)` — returns `active` + `left_early`
- Update close-game validation (Stage 19) to exclude `removed_before_start` from final-stack requirement
- Update `settlement_service._build_calcs` to filter to settlement-eligible participants only
- Backend tests for status transitions and settlement eligibility filtering

## Files likely to change/add

**Backend:**
- `app/models/participant.py` (add enum + field)
- `app/schemas/participant.py` (add status to response)
- `app/services/participant_service.py` (new functions)
- `app/services/settlement_service.py` (filter by status)
- `app/api/routers/games.py` (update close validation to use status)
- Alembic migration
- `tests/test_participant_status.py`

**Mobile:**
- `mobile/src/types/game.ts` (add status to participant type)

## Acceptance criteria
- All existing participants have `active` status after migration
- New participants default to `active`
- Settlement calculations exclude `removed_before_start` participants
- Close-game validation only requires final stacks for `active` and `left_early` participants
- Existing tests continue to pass (all participants are `active` by default)

## Stop boundary
Do not implement the early cash-out flow or remove-from-lobby UI. Only add the model and service-level support.

---

# Stage 21 — Early cash-out flow

## Goal
Allow a player to leave an active game early by entering their own final chip count. The dealer retains the ability to review and edit the cash-out value.

## Scope
- Backend: new endpoint and service
- Mobile: cash-out UI for players, status display

## Deliverables

### Backend
- `early_cashout_service.py`:
  - `cashout(db, game_id, participant_id, chips_amount, caller_user_id)`:
    - Validate game is active
    - Validate caller is the participant (user_id matches)
    - Validate participant status is `active`
    - Create or update `final_stacks` record
    - Set participant status to `left_early`
- New endpoint: `POST /games/{game_id}/cashout`
  - Request body: `{ chips_amount: Decimal }`
  - Only the player themselves can call this for their own participant record
- Existing `PUT /games/{game_id}/final-stacks/{participant_id}` remains dealer-only — dealer can edit the early cash-out value
- A `left_early` participant cannot add more buy-ins (enforce in buy-in creation)
- Backend tests for early cash-out lifecycle

### Mobile
- "Cash Out" button visible to non-dealer players during active game (only for their own row)
- `CashoutModal`: player enters their final chip count, confirms
- After cash-out: player's row shows "Left Early" badge, game becomes read-only for them
- Dealer sees the player's early cash-out value in the final stacks list and can edit it
- WebSocket event broadcast on cash-out (reuse `final_stack.updated` + `game.participant_status_changed`)

## Files likely to change/add

**Backend:**
- `app/services/early_cashout_service.py`
- `app/api/routers/games.py` (add cashout endpoint)
- `app/schemas/game.py` or `app/schemas/cashout.py` (request/response schemas)
- `app/api/routers/ledger.py` (enforce no buy-in for left_early — if buy-in creation is here)
- `tests/test_early_cashout.py`

**Mobile:**
- `mobile/src/features/cashout/CashoutModal.tsx`
- `mobile/src/services/gameService.ts` (add cashout API call)
- Active game screen (add cash-out button, left_early badge)

## Acceptance criteria
- A player can enter their own final chip count and leave early
- The player's status changes to `left_early`
- The dealer can edit the early cash-out value
- A `left_early` player cannot add more buy-ins
- Settlement includes the `left_early` player's result correctly
- Close-game validation passes for `left_early` participants (they already have a final stack)

## Stop boundary
Do not implement the invitation rework. Do not add `removed_before_start` UI.

---

# Stage 22 — Game invitation rework (friend-only pending invitations)

## Goal
Replace the immediate-add invite flow with a pending invitation model. Dealers invite only accepted friends; invited users accept or decline.

## Scope
- Backend: new model, service, endpoints
- Mobile: new invitation UI, lobby changes, notification handling

## Deliverables

### Backend
- `game_invitations` table + Alembic migration
- `GameInvitationStatus` enum: `pending`, `accepted`, `declined`
- `GameInvitation` SQLAlchemy model
- `game_invitation_service.py`:
  - `create_invitation` — validate friend relationship, no duplicate, create notification
  - `accept_invitation` — validate caller, create participant, update status
  - `decline_invitation` — validate caller, update status
  - `list_pending_for_game` — dealer's lobby view
  - `list_pending_for_user` — invited user's view
- Router: `app/api/routers/game_invitations.py`
- Deprecate or redirect `POST /games/{game_id}/invite-user` to the new flow
- WebSocket broadcast `game.invitation_accepted` when a user accepts
- Backend tests for full invitation lifecycle

### Mobile
- Replace `InvitePlayerModal` (user search) with `InviteFriendModal` (friends list only)
- Game lobby: add "Pending Invitations" section (dealer view)
- Notifications: handle game invitation with Accept/Decline buttons
- `gameInvitationService.ts` — API calls
- `useGameInvitations.ts` — hooks

## Files likely to change/add

**Backend:**
- `app/models/game_invitation.py`
- `app/schemas/game_invitation.py`
- `app/services/game_invitation_service.py`
- `app/api/routers/game_invitations.py`
- `app/api/routers/games.py` (deprecate invite-user)
- `app/realtime/events.py` (add invitation_accepted event)
- Alembic migration
- `tests/test_game_invitations.py`

**Mobile:**
- `mobile/src/features/invitations/InviteFriendModal.tsx`
- `mobile/src/features/invitations/PendingInvitationCard.tsx`
- `mobile/src/services/gameInvitationService.ts`
- `mobile/src/hooks/useGameInvitations.ts`
- `mobile/app/(app)/games/[id]/lobby.tsx` (pending invitations section)
- `mobile/src/features/notifications/NotificationItem.tsx` (handle game_invitation with actions)

## Acceptance criteria
- Dealer sees only accepted friends in the invite flow
- Inviting a friend creates a pending invitation (not a participant)
- Invited user receives a notification with accept/decline
- Accepting adds the user as a participant; lobby updates in real time
- Declining removes the invitation silently
- Duplicate invitation guard enforced
- Old `invite-user` endpoint is deprecated or redirected

## Stop boundary
Do not change the invite-link/token flow. Do not add remove-from-lobby functionality.

---

# Stage 23 — Settlement transfer notifications

## Goal
After a game is closed, notify registered users who owe money (debtors) about their settlement obligations.

## Scope
- Backend: notification creation after settlement
- Mobile: render new notification type

## Deliverables

### Backend
- Add `settlement_owed` to `NotificationType` enum (migration if needed for stored enum values)
- In the close-game flow, after settlement is computed:
  - Iterate the transfer list
  - For each transfer where `from_participant` has a `user_id`:
    - Create a `settlement_owed` notification with data: `{ game_id, game_title, to_display_name, amount, currency }`
- Backend tests: verify notifications are created for debtors only, not creditors, not guests

### Mobile
- `NotificationItem`: render `settlement_owed` type
  - Display: "You owe [to_display_name] [amount] [currency] from [game_title]"
  - Tap navigates to the game's settlement screen

## Files likely to change/add

**Backend:**
- `app/models/notification.py` (add enum value)
- `app/api/routers/games.py` (add notification creation in close_game)
- Alembic migration (if the enum is stored natively — check current implementation)
- `tests/test_settlement_notifications.py`

**Mobile:**
- `mobile/src/features/notifications/NotificationItem.tsx` (render new type)
- `mobile/src/types/notification.ts` (add type)

## Acceptance criteria
- After game close, each registered debtor receives one notification per transfer they owe
- Notification message includes recipient name, amount, and currency
- Creditors and guests do not receive settlement notifications
- Tapping the notification navigates to the game settlement screen
- Existing notification types are unaffected

## Stop boundary
Do not add payment tracking or confirmation flows. Notification is informational only.

---

# Phase 3 stage execution rules

For every Phase 3 stage Claude must:

1. Read `PHASE3_PRODUCT_SPEC.md` and `PHASE3_ARCHITECTURE.md` before starting.
2. Restate the stage goal in 3–6 bullets.
3. List files to be created/changed.
4. Implement only that stage.
5. Run or describe the exact commands needed.
6. Add/update tests where relevant.
7. End with:
   - summary
   - changed files
   - commands
   - manual test steps
   - assumptions
   - next recommended stage

Do not silently continue into the next stage.  
Do not regress any MVP behavior (Stages 0–9) or Phase 2 behavior (Stages 10–17).
