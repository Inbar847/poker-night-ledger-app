# PHASE3_ARCHITECTURE.md

# Phase 3 Architecture

This document extends `ARCHITECTURE.md` and `PHASE2_ARCHITECTURE.md` for post-Phase-2 development.  
**Do not modify ARCHITECTURE.md or PHASE2_ARCHITECTURE.md.** All prior architecture is preserved unless this document explicitly overrides it.

---

## Stack additions

No new framework dependencies are required for Phase 3.  
All additions fit within the existing FastAPI + SQLAlchemy + React Native + Expo stack.

---

## Database model changes

All schema changes must go through Alembic migrations.

---

### 11) game_invitations (new table)

Represents a pending game invitation from a dealer to a friend.

Suggested fields:
- `id` (UUID, PK)
- `game_id` (FK → games.id)
- `invited_user_id` (FK → users.id)
- `invited_by_user_id` (FK → users.id) — the dealer who sent the invitation
- `status` — enum: `pending`, `accepted`, `declined`
- `created_at`
- `updated_at`

Rules:
- unique constraint on `(game_id, invited_user_id)` — one invitation per user per game
- only the invited user can accept or decline
- accepting creates a participant record and updates the invitation status atomically

Indexes:
- `(invited_user_id, status)` — for listing pending invitations
- `(game_id, status)` — for dealer's view of pending invitations in lobby

---

### Participant model changes (existing table: participants)

Add field:
- `status` — enum: `active`, `left_early`, `removed_before_start` — default `active`

Migration:
- Add `status` column with default `active` to existing rows
- All existing participants get `active` status

---

### Notification model changes (existing table: notifications)

Add to `NotificationType` enum:
- `settlement_owed`

No structural changes to the notifications table.

---

## Changes to existing backend services

### game_service (extended)

#### Close-game validation
Before transitioning `active → closed`, validate:
1. Query all participants for the game
2. Filter to those requiring a final stack: `status IN ('active', 'left_early')`
3. For each, check that a `final_stacks` row exists
4. If any are missing, raise a structured error containing the list of `{participant_id, display_name}` for participants without final stacks

The router converts this error into an HTTP 400 with the missing participants list.

### participant_service (extended)

New functions:
- `set_participant_status(db, participant_id, status)` — update the status field
- `get_settlement_eligible_participants(db, game_id)` — returns participants with status `active` or `left_early`

### settlement_service (extended)

- `_build_calcs` must filter to settlement-eligible participants only (status `active` or `left_early`)
- Participants with `removed_before_start` are excluded from all settlement calculations

### notification_service (extended)

No API changes. New call sites:
- After game close + settlement computation: create `settlement_owed` notifications for registered debtors

---

## New backend services

### game_invitation_service

Responsibilities:
- `create_invitation(db, game_id, invited_user_id, invited_by_user_id)` — create pending invitation
  - Validate: invited user is an accepted friend of the dealer
  - Validate: no existing pending or accepted invitation for this user+game
  - Create `game_invitation` notification for the invited user
- `accept_invitation(db, invitation_id, user_id)` — accept and create participant
  - Validate: caller is the invited user
  - Validate: invitation is pending
  - Create participant record (registered, player role, active status)
  - Update invitation status to `accepted`
- `decline_invitation(db, invitation_id, user_id)` — decline
  - Validate: caller is the invited user
  - Update invitation status to `declined`
- `list_pending_for_game(db, game_id)` — pending invitations for dealer's lobby view
- `list_pending_for_user(db, user_id)` — pending invitations for the invited user

### early_cashout_service

Responsibilities:
- `cashout(db, game_id, participant_id, chips_amount, caller_user_id)` — process early cash-out
  - Validate: game is active
  - Validate: caller is the participant themselves (user_id matches)
  - Validate: participant status is `active`
  - Create or update final_stack record for the participant
  - Set participant status to `left_early`
- Dealer override: the existing `PUT /games/{game_id}/final-stacks/{participant_id}` endpoint (dealer-only) continues to work for editing any participant's final stack, including those who left early

---

## New API endpoints

### Game invitations

```
POST   /games/{game_id}/invitations           — dealer invites a friend
GET    /games/{game_id}/invitations            — list invitations for a game (dealer view)
POST   /games/{game_id}/invitations/{id}/accept  — invited user accepts
POST   /games/{game_id}/invitations/{id}/decline — invited user declines
GET    /invitations/pending                    — list pending invitations for current user
```

### Early cash-out

```
POST   /games/{game_id}/cashout                — player cashes out early (enters own final stack)
```

---

## Changes to existing endpoints

### `POST /games/{game_id}/close`

Add pre-close validation:
- Query settlement-eligible participants (status `active` or `left_early`)
- Check each has a final_stack row
- If any are missing, return HTTP 400 with:
```json
{
  "detail": "Cannot close game: missing final chip counts",
  "missing_final_stacks": [
    {"participant_id": "uuid", "display_name": "Alice"},
    {"participant_id": "uuid", "display_name": "Guest 1"}
  ]
}
```

Add post-close settlement notifications:
- After settlement is computed, iterate transfers
- For each transfer where `from_participant` has a `user_id`, create a `settlement_owed` notification

### `POST /games/{game_id}/invite-user` (Phase 2 behavior overridden)

This endpoint is replaced by the new `POST /games/{game_id}/invitations` endpoint.  
The old endpoint should either redirect to the new one or be deprecated.  
The key behavioral change: inviting no longer immediately adds a participant.

### `PUT /games/{game_id}/final-stacks/{participant_id}` (extended)

No permission change — dealer-only.  
Dealer can now also edit final stacks for `left_early` participants (the early cash-out value).

---

## New mobile modules

### `src/features/invitations/`
- `gameInvitationService.ts` — API calls for creating, accepting, declining invitations
- `useGameInvitations.ts` — TanStack Query hooks
- `PendingInvitationCard.tsx` — component for accept/decline in notifications or dedicated screen
- `InviteFriendModal.tsx` — modal for dealer to select a friend to invite (replaces the generic user search)

### `src/features/cashout/`
- `cashoutService.ts` — API call for early cash-out
- `useCashout.ts` — TanStack Query mutation hook
- `CashoutModal.tsx` — modal for a player to enter their final chip count and confirm leaving early

---

## Changes to existing mobile modules

### Notifications
- `NotificationsScreen.tsx`: call `POST /notifications/read-all` on screen mount (useEffect or useFocusEffect)
- `useNotifications.ts`: ensure unread count query uses the correct endpoint and invalidates properly after mark-all-read
- Badge component: ensure it renders from the `unread-count` query, hides when 0

### Game lobby
- Show pending invitations section (dealer view)
- Replace user-search invite with friend-list invite
- Show participant status badges (active, left_early)

### Active game screen
- Add "Cash Out" button for non-dealer players (only visible to the player themselves)
- Show `left_early` status next to participants who have cashed out

### Close game flow
- Handle new 400 error with `missing_final_stacks` array
- Render the list of missing participants clearly before allowing retry

### Settlement screen
- Handle `settlement_owed` notification type in `NotificationItem` — navigate to settlement view

---

## New query keys

Add to `queryKeys.ts`:
```ts
gameInvitations: 'gameInvitations',
pendingInvitations: 'pendingInvitations',
```

---

## Realtime additions

### New WebSocket event types

- `game.invitation_accepted` — broadcast to game room when a user accepts an invitation and joins as participant
  - Payload: `{ participant_id, user_id, display_name }`

### Existing events (no changes)
All existing event types continue to function as before.

---

## New Pydantic schemas

### GameInvitationCreate
```python
game_id: UUID       # path parameter
invited_user_id: UUID
```

### GameInvitationResponse
```python
id: UUID
game_id: UUID
invited_user_id: UUID
invited_user_display_name: str
invited_by_user_id: UUID
status: str  # pending, accepted, declined
created_at: datetime
```

### CashoutRequest
```python
chips_amount: Decimal  # the player's final chip count
```

### CloseGameError (new error response)
```python
detail: str
missing_final_stacks: list[MissingFinalStack]
```

### MissingFinalStack
```python
participant_id: UUID
display_name: str
```

---

## Testing additions

New backend test coverage required:
- Close-game validation: blocked when final stacks missing, allowed when all present
- Close-game validation with mixed statuses (active, left_early, removed_before_start)
- Game invitation lifecycle: create → accept, create → decline, duplicate guard, non-friend guard
- Early cash-out: player enters own final stack, status changes to left_early, dealer can edit
- Settlement notifications: debtors receive `settlement_owed`, creditors and guests do not
- Settlement excludes `removed_before_start` participants

New mobile QA flows:
- Notification badge shows correct unread count; clears on entering notifications screen
- Dealer cannot close game with missing final stacks; sees list of who is missing
- Dealer invites a friend; friend sees pending notification; accepts → appears in game
- Player cashes out early; their result is included in final settlement
- After game close, debtor receives settlement notification
