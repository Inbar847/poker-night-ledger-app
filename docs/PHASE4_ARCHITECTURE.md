# PHASE4_ARCHITECTURE.md

# Phase 4 Architecture

This document extends `ARCHITECTURE.md`, `PHASE2_ARCHITECTURE.md`, and `PHASE3_ARCHITECTURE.md` for post-Phase-3 development.  
**Do not modify earlier architecture documents.** All prior architecture is preserved unless this document explicitly overrides it.

---

## Stack additions

No new framework dependencies are required for Phase 4.  
All additions fit within the existing FastAPI + SQLAlchemy + React Native + Expo stack.

---

## Database model changes

All schema changes must go through Alembic migrations.

---

### 12) game_edits (new table)

Represents an audit trail entry for a retroactive edit to a closed game.

Suggested fields:
- `id` (UUID, PK)
- `game_id` (FK -> games.id)
- `edited_by_user_id` (FK -> users.id) -- the dealer who made the edit
- `edit_type` -- enum: `buyin_created`, `buyin_updated`, `buyin_deleted`, `final_stack_updated`
- `entity_id` (UUID) -- the ID of the buy-in or final-stack row that was changed
- `before_data` (JSONB, nullable) -- snapshot of the record before the change (null for creates)
- `after_data` (JSONB, nullable) -- snapshot of the record after the change (null for deletes)
- `created_at`

Rules:
- Append-only: audit records cannot be updated or deleted
- One row per individual edit operation
- `before_data` and `after_data` capture the relevant fields (cash_amount, chips_amount, participant_id, etc.)

Indexes:
- `(game_id, created_at)` -- for listing audit trail per game

---

### Notification model changes (existing table: notifications)

Add to `NotificationType` enum:
- `game_resettled`

Migration: add enum value (check whether the enum is stored as varchar or native PG enum and handle accordingly).

---

### Expense model changes (existing table: expenses)

No schema changes required. The existing `created_by_user_id` field is used for permission checks (creator can edit/delete their own expense). The existing dealer check is relaxed to also allow the creator.

---

## Changes to existing backend services

### expense service (permission model change)

**Current behavior:** All expense mutations (create, update, delete) require the caller to be the dealer.

**Phase 4 behavior:**
- **Create:** any active participant can create an expense (not just the dealer)
- **Update:** the creator of the expense OR the dealer can update it
- **Delete:** the creator of the expense OR the dealer can delete it
- **Validation:** participants with `left_early` status cannot create new expenses
- **Guest expenses:** guests cannot create expenses directly (no auth session). The dealer creates on their behalf, as before.

Implementation:
- In the expense creation endpoint, replace the dealer-only check with a participant-existence check + status check (`active` only)
- **Payer constraint for non-dealers:** when a non-dealer creates an expense, validate that `paid_by_participant_id` matches the creator's own participant record. The dealer is exempt and can set any participant as payer.
- In expense update/delete endpoints, check `expense.created_by_user_id == current_user.id OR participant.role_in_game == dealer`

### game_invitation_service (no backend changes)

The service already allows invitations when `game.status != closed`. No code changes needed. The Phase 4 change is mobile-only (exposing the invite button on the active game screen).

### notification_service (extended)

New function:
- `delete_all_for_user(db, user_id)` -- permanently deletes all notification records for the user from the database (not mark-as-read; actual row deletion)

### notification_service (extended for re-settlement cleanup)

New function:
- `delete_settlement_owed_for_game(db, game_id)` -- deletes all `settlement_owed` notifications for a specific game
  - Called before re-settlement to clear stale debtor notifications
  - Matches notifications by `data->>'game_id'` filter

### settlement_service (extended for re-settlement)

New function:
- `resettle_game(db, game)` -- recompute settlement for a closed game using the current buy-in and final-stack data
  - Uses the stored `shortage_strategy` from the original close (if any)
  - Re-evaluates shortage amount (may increase, decrease, or disappear after the edit)
  - If shortage is eliminated, clears `shortage_amount` and `shortage_strategy` on the game
  - Returns the new settlement result
  - Called after any retroactive edit to a closed game

---

## New backend services

### game_edit_service

Responsibilities:
- `record_edit(db, game_id, edited_by_user_id, edit_type, entity_id, before_data, after_data)` -- create an audit trail entry
- `list_edits_for_game(db, game_id)` -- return all edits for a game, ordered by created_at ascending
- `edit_closed_game_buyin(db, game, buyin_id, update_data, editor_user_id)` -- edit a buy-in on a closed game
  - Validate: editor is the dealer
  - Validate: game is closed
  - Record the before/after in audit trail
  - Apply the change
  - Trigger re-settlement (full downstream effects -- see below)
- `create_closed_game_buyin(db, game, buyin_data, editor_user_id)` -- add a new buy-in to a closed game
  - Same validations and side effects as above
- `delete_closed_game_buyin(db, game, buyin_id, editor_user_id)` -- remove a buy-in from a closed game
  - Same validations and side effects
- `edit_closed_game_final_stack(db, game, participant_id, chips_amount, editor_user_id)` -- edit a final stack on a closed game
  - Same validations and side effects

**Re-settlement downstream effects (triggered by every edit operation above):**
1. Call `notification_service.delete_settlement_owed_for_game(db, game.id)` to clear stale debtor notifications
2. Call `settlement_service.resettle_game(db, game)` to recompute balances and transfers
3. Shortage logic is re-evaluated using the stored `shortage_strategy`; if the shortage is eliminated, clear the shortage fields on the game
4. Create new `settlement_owed` notifications for the updated debtor list (registered users only)
5. Create a `game_resettled` notification for all registered participants

### personal_ws_service

Responsibilities:
- Manage personal WebSocket connections per user (separate from per-game connections)
- `connect(user_id, websocket)` -- register a connection
- `disconnect(user_id, websocket)` -- remove a connection
- `send_to_user(user_id, event)` -- send an event to all active connections for a user

Implementation:
- In-memory dict: `user_id -> set[WebSocket]` (same pattern as the game room manager)
- A user may have multiple connections (multiple devices/tabs)
- No Redis or external pub/sub required for MVP

---

## New API endpoints

### Notifications

```
DELETE  /notifications                   -- delete all notifications for current user
```

### Game editing (retroactive)

```
GET    /games/{game_id}/edits            -- list audit trail for a game
POST   /games/{game_id}/edits/buy-ins              -- add a buy-in to a closed game
PATCH  /games/{game_id}/edits/buy-ins/{buyin_id}   -- edit a buy-in on a closed game
DELETE /games/{game_id}/edits/buy-ins/{buyin_id}   -- delete a buy-in from a closed game
PATCH  /games/{game_id}/edits/final-stacks/{participant_id}  -- edit a final stack on a closed game
```

### Personal WebSocket

```
WS     /ws/user                          -- personal WebSocket channel (authenticated)
```

---

## Changes to existing endpoints

### `POST /games/{game_id}/expenses` (permission relaxed)

- Remove dealer-only requirement
- Allow any active participant to create an expense
- Validate: participant status is `active` (not `left_early` or `removed_before_start`)
- Validate: game is active
- **Payer constraint:** if the caller is not the dealer, validate that `paid_by_participant_id` matches the caller's own participant record. The dealer can set any participant as payer.
- No other changes to request/response shape

### `PATCH /games/{game_id}/expenses/{expense_id}` (permission relaxed)

- Allow update if caller is the dealer OR the creator of the expense (`expense.created_by_user_id == current_user.id`)
- No other changes

### `DELETE /games/{game_id}/expenses/{expense_id}` (permission relaxed)

- Allow delete if caller is the dealer OR the creator of the expense
- No other changes

### `POST /games/{game_id}/invitations` (no backend change)

Already allows invitations for active games. No code changes.

---

## New Pydantic schemas

### GameEditResponse
```python
id: UUID
game_id: UUID
edited_by_user_id: UUID
edited_by_display_name: str
edit_type: str  # buyin_created, buyin_updated, buyin_deleted, final_stack_updated
entity_id: UUID
before_data: dict | None
after_data: dict | None
created_at: datetime
```

### GameEditType (enum)
```python
buyin_created = "buyin_created"
buyin_updated = "buyin_updated"
buyin_deleted = "buyin_deleted"
final_stack_updated = "final_stack_updated"
```

### ClosedGameBuyInCreate
```python
participant_id: UUID
cash_amount: Decimal
chips_amount: Decimal
buy_in_type: str  # initial, rebuy, addon
```

### ClosedGameBuyInUpdate
```python
cash_amount: Decimal | None = None
chips_amount: Decimal | None = None
```

### ClosedGameFinalStackUpdate
```python
chips_amount: Decimal
```

---

## New mobile modules

### `src/hooks/usePersonalSocket.ts`
- Establishes a personal WebSocket connection to `/ws/user`
- Authenticated with JWT (same pattern as useGameSocket)
- Listens for `user.game_invitation` events
- On receiving an invitation event, triggers the popup via a Zustand store or context
- Reconnection strategy: same exponential backoff as useGameSocket

### `src/features/invitations/InvitationPopup.tsx`
- Full-screen overlay component rendered at the app shell level (in `app/(app)/_layout.tsx`)
- Shows game title, inviter name, Accept/Decline buttons, and a dismiss option
- Accept calls the existing `POST /games/{game_id}/invitations/{id}/accept` endpoint
- Decline calls `POST /games/{game_id}/invitations/{id}/decline`
- Dismiss closes the popup without acting on the invitation
- Uses a Zustand store (`invitationPopupStore`) to manage pending popup state

### `src/store/invitationPopupStore.ts`
- Zustand store for managing the invitation popup queue
- State: `pendingInvitation: {gameId, invitationId, gameTitle, inviterName} | null`
- Actions: `showPopup(data)`, `clearPopup()`
- The personal WebSocket hook writes to this store; the popup component reads from it

### `src/features/game-edits/`
- `gameEditService.ts` -- API calls for retroactive editing and audit trail
- `useGameEdits.ts` -- TanStack Query hooks for audit trail and mutations
- `EditHistoryScreen.tsx` -- screen showing the audit trail for a closed game
- Integration into the existing settlement/game-detail screen for dealers to trigger edits

---

## Changes to existing mobile modules

### Active game screen (`app/(app)/games/[id]/index.tsx`)
- Add "Invite Friend" button for dealers (reuses `InviteFriendModal`)
- Button is visible during active game status (currently only in lobby)

### InviteFriendModal (`src/features/invitations/InviteFriendModal.tsx`)
- Increase modal height to 60%+ of screen
- Add a text input for filtering the friends list by name (client-side filter)
- Move the friends list higher in the modal layout

### NotificationsScreen (`src/features/notifications/NotificationsScreen.tsx`)
- Add "Delete All" button in the header or as a list header action
- Call `DELETE /notifications` and clear the local query cache on success

### Expense creation in active game
- Remove dealer-only gating on the "Add Expense" button
- Any active participant sees the "Add Expense" button
- Expense edit/delete buttons: show for the creator of the expense and for the dealer

### Closed game detail / settlement screen
- Dealer sees "Edit Buy-Ins" and "Edit Final Stacks" actions (only on closed games)
- "View Edit History" link to the audit trail screen
- After an edit, settlement data refreshes automatically

### App shell (`app/(app)/_layout.tsx`)
- Render `InvitationPopup` component at the shell level
- Initialize `usePersonalSocket` hook for the authenticated user

---

## New query keys

Add to `queryKeys.ts`:
```ts
gameEdits: 'gameEdits',
```

---

## Realtime additions

### New WebSocket channel

- `WS /ws/user` -- personal user channel
- Authenticated with JWT token (query parameter or first message)
- Server manages connections per user_id
- Used for delivering events that are not tied to a specific game room

### New WebSocket event types

- `user.game_invitation` -- sent to the invited user's personal channel when a game invitation is created
  - Payload: `{ invitation_id, game_id, game_title, inviter_name }`

### Existing events (no changes)
All existing per-game event types continue to function as before.

---

## Testing additions

New backend test coverage required:
- Expense creation by non-dealer active participant (allowed, self as payer)
- Expense creation by non-dealer with different payer (blocked -- payer must be self)
- Expense creation by dealer with any payer (allowed)
- Expense creation by left_early participant (blocked)
- Expense edit/delete by creator (allowed) and by non-creator non-dealer (blocked)
- Retroactive buy-in edit on closed game: audit trail created, settlement recomputed
- Retroactive buy-in create/delete on closed game: same validations
- Retroactive final stack edit on closed game: same validations
- Retroactive edit on active/lobby game (blocked -- use normal flow)
- Retroactive edit by non-dealer (blocked)
- Audit trail listing returns all edits in chronological order with correct before/after data
- Re-settlement after edit: shortage re-evaluated, stale `settlement_owed` notifications deleted, new ones created
- Re-settlement after edit that eliminates shortage: shortage fields cleared on game
- `game_resettled` notification created for all registered participants after re-settlement
- Delete all notifications permanently removes all records for the user (not just mark-as-read)
- Personal WebSocket connection and event delivery (integration test if feasible)

New mobile QA flows:
- Dealer invites friend from active game screen (not just lobby)
- Invite modal shows friends list higher on screen with filter input
- User receives live popup when invited while app is open
- Popup Accept/Decline work correctly; dismiss leaves invitation pending
- User deletes all notifications; badge resets to 0
- Any participant adds a side expense during active game
- Creator edits/deletes their own expense; non-creator non-dealer cannot
- Dealer edits buy-in on closed game; settlement updates; audit trail shows the change
- All participants see the audit trail for a closed game
- Participants receive `game_resettled` notification after retroactive edit
