# PHASE4_PLAN.md

This file is the execution roadmap for **Phase 4** of Poker Night Ledger.  
Claude must implement **one stage at a time** and stop after the requested stage.

Read `PHASE4_PRODUCT_SPEC.md` and `PHASE4_ARCHITECTURE.md` before implementing any stage.  
The MVP stages (0-9), Phase 2 stages (10-17), and Phase 3 stages (18-23) are complete and must not be regressed.

---

# Stage 24 — Invite friends during active games + notification delete-all

## Goal
Extend the invitation flow so dealers can invite friends from the active game screen (not just lobby) and add a delete-all action to the notifications screen.

## Scope
- Mobile: add invite button to active game screen, notifications delete-all
- Backend: add `DELETE /notifications` endpoint

## Backend verification
The backend `game_invitation_service.create_invitation` only blocks invitations when `game.status == closed` (line 36). Invitations during `lobby` and `active` games are already accepted server-side. No backend changes are needed for the invite-during-active feature.

## Deliverables

### Backend
- Add `DELETE /notifications` endpoint in the notifications router
  - Permanently deletes all notification records for the authenticated user from the database (not mark-as-read -- actual row deletion)
  - Returns 204 No Content
- Add `delete_all_for_user(db, user_id)` to `notification_service`
- Backend test: delete-all removes all notifications and returns empty list on subsequent GET

### Mobile
- Active game screen (`app/(app)/games/[id]/index.tsx`): add "Invite Friend" button visible to dealers when game is active
  - Currently the invite button is gated by `game.status === "lobby"` (line 645). Remove this status gate so it shows for both `lobby` and `active`.
  - Reuse the existing `InviteFriendModal` component
  - Same flow as lobby: select friend -> create pending invitation
- Notifications screen: add "Delete All" button
  - Calls `DELETE /notifications`
  - On success: invalidate notifications and unread-count queries
  - Hides when notification list is empty
- Add `deleteAllNotifications` to notifications service and hook

## Files likely to change/add

**Backend:**
- `app/api/routers/notifications.py` (add delete-all endpoint)
- `app/services/notification_service.py` (add delete function)
- `tests/test_notifications.py` (add delete-all test)

**Mobile:**
- `mobile/app/(app)/games/[id]/index.tsx` (add invite button for active games)
- `mobile/src/features/notifications/NotificationsScreen.tsx` (add delete-all button)
- `mobile/src/services/notificationsService.ts` (add delete API call)
- `mobile/src/hooks/useNotifications.ts` (add delete mutation hook)

## Acceptance criteria
- Dealer sees "Invite Friend" on the active game screen (not only lobby)
- Invite flow works identically to lobby (select friend, pending invitation created)
- Non-dealer participants do not see the invite button
- "Delete All" permanently removes all notifications from the database; badge resets to 0
- Deleting when no notifications exist is a no-op (204)

## Stop boundary
Do not change the invite modal layout yet. Do not add personal WebSocket or live popup.

---

# Stage 25 — Invite friend modal layout improvement

## Goal
Improve the InviteFriendModal so the friends list appears higher on screen and is easier to browse, with a client-side search filter.

## Scope
- Mobile only -- no backend changes

## Deliverables
- Increase modal height to occupy at least 60% of screen height
- Add a TextInput at the top of the modal for filtering friends by display name (client-side)
- Friends list renders immediately below the search input
- Filter is case-insensitive partial match on display name
- Empty filter shows all friends
- Empty state ("No friends found") when filter matches nothing
- Preserve all existing mutation flow and success/error handling

## Files likely to change

**Mobile:**
- `mobile/src/features/invitations/InviteFriendModal.tsx`

## Acceptance criteria
- Modal is tall enough that friends list is comfortably visible
- Search input filters the friends list in real time
- Selecting a friend still sends the invitation correctly
- Long friends lists are scrollable within the modal

## Stop boundary
Do not add personal WebSocket or live popup. Do not change backend.

---

# Stage 26 — Live invitation popup (personal WebSocket)

## Goal
When a user is invited to a game while the app is in the foreground, show an immediate popup with Accept/Decline. Introduce a personal WebSocket channel for user-level events.

## Scope
- Backend: personal WebSocket endpoint + event delivery
- Mobile: personal WebSocket hook, popup store, popup component

## Deliverables

### Backend
- Personal WebSocket endpoint: `WS /ws/user`
  - Authenticate via JWT (token as query parameter)
  - Register connection in a per-user in-memory manager (`personal_ws_manager`)
  - On disconnect, remove from manager
- `personal_ws_manager` (new module in `app/realtime/`):
  - `connect(user_id, ws)`, `disconnect(user_id, ws)`, `send_to_user(user_id, event)`
  - In-memory dict: `user_id -> set[WebSocket]`
- When a game invitation is created (`game_invitation_service.create_invitation`):
  - After creating the notification, also send a `user.game_invitation` event to the invited user's personal channel
  - Payload: `{ invitation_id, game_id, game_title, inviter_name }`
- Backend test: personal WS connection lifecycle (if feasible with test client)

### Mobile
- `usePersonalSocket` hook:
  - Connects to `WS /ws/user` with JWT auth
  - Listens for `user.game_invitation` events
  - On event: writes to `invitationPopupStore`
  - Same reconnection strategy as `useGameSocket` (exponential backoff)
  - Initialized in the authenticated app shell
- `invitationPopupStore` (Zustand):
  - State: `pendingInvitation: { invitationId, gameId, gameTitle, inviterName } | null`
  - Actions: `showPopup(data)`, `clearPopup()`
- `InvitationPopup` component:
  - Rendered in `app/(app)/_layout.tsx` (above all screens)
  - Shows modal overlay with game title, inviter name
  - Accept button: calls accept endpoint, clears popup, navigates to game (optional)
  - Decline button: calls decline endpoint, clears popup
  - Dismiss (backdrop tap): clears popup without acting (invitation stays pending)
  - Loading states for accept/decline mutations
- Cleanup: disconnect personal WebSocket on logout

## Files likely to change/add

**Backend:**
- `app/realtime/personal_manager.py` (new)
- `app/api/routers/ws.py` or `app/main.py` (add personal WS route)
- `app/services/game_invitation_service.py` (send personal WS event)
- `app/realtime/events.py` (add user.game_invitation event builder)

**Mobile:**
- `mobile/src/hooks/usePersonalSocket.ts` (new)
- `mobile/src/store/invitationPopupStore.ts` (new)
- `mobile/src/features/invitations/InvitationPopup.tsx` (new)
- `mobile/app/(app)/_layout.tsx` (render popup + init personal socket)
- `mobile/src/store/authStore.ts` (cleanup on logout)

## Acceptance criteria
- Personal WebSocket connects on app launch (authenticated)
- User receives popup immediately when invited to a game
- Accept from popup adds user as participant; popup closes
- Decline from popup marks invitation as declined; popup closes
- Dismiss closes popup; invitation remains pending in notifications
- Popup does not reappear for the same invitation after dismiss
- If WebSocket is disconnected, user still sees the notification (no popup)
- Personal WebSocket reconnects on disconnect (same backoff strategy)

## Stop boundary
Do not add player-added expenses or retroactive game editing. Do not change the per-game WebSocket.

---

# Stage 27 — Player-added side expenses

## Goal
Allow any active participant (not just the dealer) to create side expenses during an active game. The dealer retains full edit/delete authority over all expenses. Buy-ins remain dealer-only.

## Scope
- Backend: relax permission checks on expense endpoints
- Mobile: show expense creation UI to all active participants

## Deliverables

### Backend
- `POST /games/{game_id}/expenses`: remove dealer-only check, allow any active participant
  - Validate: participant status is `active` (block `left_early` and `removed_before_start`)
  - **Payer constraint:** if the caller is not the dealer, validate that `paid_by_participant_id` matches the caller's own participant record. A non-dealer cannot create an expense claiming someone else paid. The dealer is exempt and can set any payer.
  - Keep all other validations (splits sum to total, amounts > 0, game is active)
- `PATCH /games/{game_id}/expenses/{expense_id}`: allow if caller is the dealer OR `expense.created_by_user_id == current_user.id`
- `DELETE /games/{game_id}/expenses/{expense_id}`: same permission rule as PATCH
- Backend tests:
  - Non-dealer active participant creates expense with self as payer (allowed)
  - Non-dealer active participant creates expense with different payer (blocked)
  - Dealer creates expense with any payer (allowed)
  - Left_early participant creates an expense (blocked)
  - Creator edits own expense (allowed)
  - Creator deletes own expense (allowed)
  - Non-creator non-dealer edits expense (blocked)
  - Non-creator non-dealer deletes expense (blocked)
  - Dealer edits any expense (allowed)
  - Dealer deletes any expense (allowed)

### Mobile
- Active game screen: show "Add Expense" button to all participants (not just dealer)
- Expense creation form: for non-dealers, auto-set payer to self (do not show payer selector or lock it to self)
- Expense list: show edit/delete actions for entries the current user created
- Expense list: show edit/delete actions for all entries if current user is dealer
- Hide edit/delete for entries created by others (unless dealer)

## Files likely to change/add

**Backend:**
- `app/api/routers/ledger.py` (relax permission checks)
- `tests/test_ledger.py` (add permission tests)

**Mobile:**
- `mobile/app/(app)/games/[id]/index.tsx` (show expense button to all participants)
- `mobile/app/(app)/games/[id]/expense.tsx` (adjust payer logic for non-dealers)
- Expense list/card component (conditional edit/delete visibility)

## Acceptance criteria
- Any active participant can add an expense where they are the payer
- Non-dealer cannot create an expense claiming a different payer
- Dealer can create expenses with any payer (unchanged behavior)
- The creator can edit or delete their own expense
- The dealer can edit or delete any expense
- Other participants cannot edit or delete expenses they did not create
- Buy-in creation remains dealer-only (no changes)
- All expense validation rules still apply
- WebSocket broadcast works as before

## Stop boundary
Do not change buy-in permissions. Do not add retroactive editing.

---

# Stage 28 — Retroactive game editing: backend

## Goal
Allow the dealer to edit buy-ins and final stacks on closed games, with automatic re-settlement and a full audit trail. Backend only.

## Scope
- Backend: new model, service, endpoints, re-settlement logic
- No mobile changes in this stage

## Deliverables

### Database
- `game_edits` table + Alembic migration (see architecture doc for schema)
- `GameEditType` enum: `buyin_created`, `buyin_updated`, `buyin_deleted`, `final_stack_updated`
- Add `game_resettled` to `NotificationType` enum (migration)

### Service: `game_edit_service`
- `edit_closed_game_buyin(db, game, buyin_id, update_data, editor_user_id)`
  - Validate: game is closed, editor is dealer
  - Capture before-snapshot of the buy-in
  - Apply changes
  - Record audit entry (with before/after data)
  - Trigger re-settlement (see downstream effects below)
  - Commit
- `create_closed_game_buyin(db, game, buyin_data, editor_user_id)` -- same pattern
- `delete_closed_game_buyin(db, game, buyin_id, editor_user_id)` -- same pattern
- `edit_closed_game_final_stack(db, game, participant_id, chips_amount, editor_user_id)` -- same pattern
- `list_edits_for_game(db, game_id)` -- returns audit trail in chronological order

### Re-settlement downstream effects (triggered by every edit)
1. Delete all existing `settlement_owed` notifications for the game (`notification_service.delete_settlement_owed_for_game`)
2. Recompute settlement from current ledger data (`settlement_service.resettle_game`)
3. Re-evaluate shortage: the shortage amount may change; reuse the stored `shortage_strategy`. If shortage is eliminated, clear `shortage_amount` and `shortage_strategy` on the game.
4. Create new `settlement_owed` notifications for the updated debtor list (registered users only)
5. Create a `game_resettled` notification for all registered participants

### Service: `settlement_service` (extended)
- `resettle_game(db, game)` -- recompute settlement using current ledger data
  - Uses stored `shortage_strategy` from the game record (if any)
  - Re-evaluates shortage amount; clears shortage fields if eliminated
  - Returns new settlement data

### Service: `notification_service` (extended)
- `delete_settlement_owed_for_game(db, game_id)` -- deletes all `settlement_owed` notifications for a specific game (matches by `data->>'game_id'`)

### Router: game edits
- `GET /games/{game_id}/edits` -- list audit trail (any participant)
- `POST /games/{game_id}/edits/buy-ins` -- add buy-in to closed game (dealer only)
- `PATCH /games/{game_id}/edits/buy-ins/{buyin_id}` -- edit buy-in (dealer only)
- `DELETE /games/{game_id}/edits/buy-ins/{buyin_id}` -- delete buy-in (dealer only)
- `PATCH /games/{game_id}/edits/final-stacks/{participant_id}` -- edit final stack (dealer only)

### Tests
- Edit buy-in on closed game: audit trail created with correct before/after data, settlement recomputed
- Add buy-in to closed game: audit trail, re-settlement
- Delete buy-in from closed game: audit trail, re-settlement
- Edit final stack on closed game: audit trail, re-settlement
- Edit on active game: blocked (400)
- Edit by non-dealer: blocked (403)
- Audit trail lists all edits chronologically with correct before/after snapshots
- Re-settlement produces correct transfers after edit
- Re-settlement with shortage: shortage re-evaluated, stale `settlement_owed` deleted, new ones created
- Re-settlement that eliminates shortage: shortage fields cleared on game
- `game_resettled` notification created for all registered participants
- Multiple sequential edits produce multiple audit trail entries

## Files likely to change/add

**Backend:**
- `app/models/game_edit.py` (new)
- `app/models/__init__.py` (register new model)
- `app/schemas/game_edit.py` (new)
- `app/services/game_edit_service.py` (new)
- `app/services/settlement_service.py` (add resettle_game)
- `app/services/notification_service.py` (add delete_settlement_owed_for_game)
- `app/api/routers/game_edits.py` (new)
- `app/main.py` (register new router)
- `app/models/notification.py` (add enum value)
- Alembic migration(s)
- `tests/test_game_edits.py` (new)

## Acceptance criteria
- Dealer can edit/add/delete buy-ins and edit final stacks on closed games
- Each edit creates an audit trail entry with before/after data
- Settlement is recomputed after every edit
- Shortage logic is re-evaluated; stale settlement notifications are replaced
- Non-dealer edits are blocked
- Edits on non-closed games are blocked
- All registered participants receive a `game_resettled` notification
- Existing close-game and settlement flows are unaffected

## Stop boundary
Do not build the mobile UI for editing. Do not change the mobile settlement screen. Backend only.

---

# Stage 29 — Retroactive game editing: mobile

## Goal
Add the mobile UI for dealers to edit buy-ins and final stacks on closed games, and display the audit trail.

## Scope
- Mobile only -- no backend changes

## Deliverables

### Edit UI
- Closed game detail screen: dealer sees "Edit Game" or "Edit Buy-Ins" / "Edit Final Stacks" actions
- Edit buy-in flow: list existing buy-ins with edit/delete options; "Add Buy-In" button
  - Edit opens a pre-filled form (cash amount, chips amount)
  - Delete shows confirmation dialog
  - Add opens the standard buy-in form
- Edit final stack flow: list final stacks with edit option
  - Edit opens a pre-filled form (chips amount)
- After each edit: settlement refreshes automatically (invalidate settlement query)

### Audit trail
- "Edit History" link on the closed game detail or settlement screen
- `EditHistoryScreen`: lists all edits chronologically
  - Each entry shows: who edited, what changed (entity type + field), when, before/after values
  - Read-only for all participants
  - Clearly answers: "what changed, who changed it, and when"

### Notifications
- Handle `game_resettled` notification type in `NotificationItem`
  - Display: "Settlement updated for [game_title]"
  - Tap navigates to the game settlement screen

## Files likely to change/add

**Mobile:**
- `mobile/src/features/game-edits/gameEditService.ts` (new)
- `mobile/src/features/game-edits/useGameEdits.ts` (new)
- `mobile/src/features/game-edits/EditHistoryScreen.tsx` (new)
- `mobile/app/(app)/games/[id]/index.tsx` or settlement screen (add edit actions for dealer)
- `mobile/src/features/notifications/NotificationItem.tsx` (handle game_resettled)
- `mobile/src/types/notification.ts` (add game_resettled type)
- `mobile/src/types/game.ts` (add game edit types)
- `mobile/src/lib/queryKeys.ts` (add gameEdits key)
- Expo Router: add route for edit history screen

## Acceptance criteria
- Dealer can edit buy-ins and final stacks on closed games from the mobile app
- Settlement screen updates after each edit
- Audit trail screen shows all edits with clear before/after values
- Non-dealer participants can view the audit trail but not edit
- `game_resettled` notification renders correctly and navigates to settlement
- Active/lobby games do not show retroactive edit actions (they use the normal flow)

## Stop boundary
This is the final Phase 4 stage. Do not begin Phase 5 work.

---

# Phase 4 stage execution rules

For every Phase 4 stage Claude must:

1. Read `PHASE4_PRODUCT_SPEC.md` and `PHASE4_ARCHITECTURE.md` before starting.
2. Restate the stage goal in 3-6 bullets.
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
Do not regress any MVP behavior (Stages 0-9), Phase 2 behavior (Stages 10-17), or Phase 3 behavior (Stages 18-23).
