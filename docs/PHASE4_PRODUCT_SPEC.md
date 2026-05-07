# PHASE4_PRODUCT_SPEC.md

# Phase 4 — Live invitations, retroactive editing, player expenses, and UX polish

This document extends `PRODUCT_SPEC.md`, `PHASE2_PRODUCT_SPEC.md`, and `PHASE3_PRODUCT_SPEC.md` for post-Phase-3 development.  
**Do not modify earlier product spec documents.** All MVP, Phase 2, and Phase 3 behavior is preserved unless this document explicitly overrides it.

---

## Phase 4 goal

Improve the real-time social experience, give dealers editing power over past games, let any participant log side expenses, and polish the notifications and invitation UX.

---

## What is preserved from MVP, Phase 2, and Phase 3

- Guest participant support (no changes)
- Dealer-only buy-in control (no changes)
- WebSocket realtime for live games (extended with personal user channel)
- Personal statistics for registered users (no changes)
- Settlement engine and audit trail (extended with re-settlement on edits)
- Game states: lobby -> active -> closed (no changes)
- Invite link / token join flow (no changes)
- Friends system, user search, public profiles (no changes)
- Friend leaderboard (no changes)
- Buy-in smart autofill (no changes)
- Pending game invitation model (extended to active games)
- Early cash-out and participant lifecycle statuses (no changes)
- Settlement transfer notifications (no changes)
- Close-game validation requiring final stacks (no changes)

---

## Feature 1 — Invite friends during active games

**Phase 3 behavior (extended):** The dealer can invite accepted friends from the game lobby. The invitation system already permits invitations while a game is active (backend does not restrict by status except `closed`), but the mobile UI only surfaces the invite button in the lobby view.

**Phase 4 behavior:**
- The dealer can invite accepted friends at any point before the game is closed: lobby or active
- The active game screen shows an "Invite Friend" button (dealer only)
- The same pending invitation flow applies: friend receives notification, accepts/declines
- Accepted friends join as participants with `active` status even mid-game
- New participants who join mid-game start with zero buy-ins (dealer adds buy-ins as usual)

**Backend verification (confirmed):**
- The backend `game_invitation_service.create_invitation` only blocks invitations when `game.status == closed` (line 36 of `game_invitation_service.py`)
- Invitations during `lobby` and `active` games are already accepted server-side
- No backend changes are required for this feature

**Rules:**
- This is a mobile-only UI change: expose the existing invite button on the active game screen for dealers
- All existing backend guards apply (friends-only, no duplicate invitations, game not closed)

---

## Feature 2 — Notifications UX polish

### 2a — Delete all notifications

**Current behavior:** Users can mark notifications as read (individually or all-at-once) but cannot delete them. Old notifications accumulate indefinitely.

**Phase 4 behavior:**
- Add a "Delete All" action to the notifications screen
- Deleting removes all notifications for the current user from the database
- The UI clears immediately after deletion
- The unread badge resets to 0

**Rules:**
- "Delete All" permanently removes notification records from the database -- this is true deletion, not marking as read
- Delete is destructive and permanent -- no undo
- Only the notification owner can delete their own notifications
- The action deletes all notifications (read and unread), not just read ones
- Individual notification deletion is out of scope for Phase 4

### 2b — Invite friend modal layout improvement

**Current behavior:** The `InviteFriendModal` renders a FlatList of friends in a bottom slide-up modal. When the list is long, selection and results appear low on screen, making it awkward to use.

**Phase 4 behavior:**
- Adjust the modal layout so the friends list appears higher on screen
- The search/filter input (if added) appears at the top of the modal
- Results begin immediately below the search input, not at the bottom of the screen
- The modal occupies at least 60% of screen height so content is comfortably visible
- Add a search/filter input to filter the friends list by name (client-side filtering of already-fetched friends)

**Rules:**
- No backend changes required
- Keep the same mutation flow and success/error handling

---

## Feature 3 — Live invitation popup

**Current behavior:** When a user is invited to a game, they receive an in-app notification. They must navigate to the notifications screen to see and act on it.

**Phase 4 behavior:**
- When a user is invited to a game while the app is in the foreground, an immediate popup/modal appears over the current screen
- The popup shows: game title, inviter's name, and Accept/Decline buttons
- Accepting from the popup adds the user as a participant (same as accepting from notifications)
- Declining from the popup marks the invitation as declined (same as declining from notifications)
- Dismissing the popup (swipe away or backdrop tap) does not accept or decline -- the invitation remains pending in notifications
- Notifications remain the persistent fallback: if the user misses the popup (app backgrounded, popup dismissed), the notification is still in their notifications list

**Technical approach:**
- Introduce a personal WebSocket channel per authenticated user (`user.{user_id}`)
- The backend sends a `user.game_invitation` event to the invited user's personal channel when a game invitation is created
- The mobile app maintains this personal WebSocket connection alongside the per-game connection
- The popup component lives at the app shell level (above all screens) so it can appear regardless of current navigation state

**Rules:**
- The popup appears only once per invitation -- if dismissed, it does not reappear
- If the user is already on the notifications screen when invited, the popup still appears (the notification also appears in the list below)
- The personal WebSocket channel is authenticated with the same JWT used for API calls
- The personal channel does not replace the per-game WebSocket -- both coexist
- If the WebSocket is disconnected when the invitation is created, the user sees only the notification (no popup)

---

## Feature 4 — Retroactive game editing

**Current behavior:** Once a game is closed, its buy-ins and final stacks are immutable. The dealer cannot correct mistakes discovered after the game ends.

**Phase 4 behavior:**
- The dealer can edit buy-ins and final chip counts on closed games
- Edits trigger automatic re-settlement: the settlement transfers are recomputed from the updated ledger data
- All edits are tracked in an audit trail so changes are transparent and explainable
- Participants receive a notification when a closed game they participated in is re-settled

**Scope of editable fields (closed games only):**
- Buy-in cash amount and chips amount (edit existing, add new, delete existing)
- Final stack chips amount (edit existing)
- Expenses, participant list, and game metadata are NOT editable retroactively

**Audit trail:**
- Every edit to a closed game creates a `game_edit` audit record
- Each record captures: who made the edit, what was changed (before/after values), and when
- The audit trail is viewable by any participant of the game
- The audit trail is append-only -- audit records cannot be edited or deleted

**Re-settlement (downstream effects):**
- After any edit to a closed game's buy-ins or final stacks, the full settlement is automatically recomputed from scratch
- The new settlement replaces the previous one entirely (new balances, new transfer list)
- Shortage logic is re-evaluated: the shortage amount may change after the edit, and the stored `shortage_strategy` from the original close is reused to distribute the updated shortage
- If the edit eliminates the shortage entirely, the shortage fields are cleared
- Previous `settlement_owed` notifications from the original close become stale. On re-settlement:
  - All existing `settlement_owed` notifications for the game are deleted
  - New `settlement_owed` notifications are created for the updated debtor list
  - A `game_resettled` notification is sent to all registered participants informing them the settlement has changed
- The `game_resettled` notification includes the game title so recipients know which game was affected

**Audit trail requirements:**
- Every edit creates exactly one `game_edit` record capturing: who edited, what entity was changed, the full before-state and after-state, and a timestamp
- The audit trail is append-only -- records cannot be edited or deleted
- The audit trail is viewable by any participant of the game (read-only)
- Multiple edits to the same field create multiple audit records (not overwritten)
- The audit trail clearly answers: "what changed, who changed it, and when"

**Rules:**
- Only the dealer can edit a closed game
- The game must be in `closed` status to be edited retroactively (lobby and active games use the normal live editing flow)
- Shortage strategy (if applicable) is preserved from the original close -- re-settlement uses the same strategy
- The audit trail is per-game, not per-field
- History and personal statistics are updated to reflect the corrected values (they are always computed from current data, so no explicit invalidation is needed)

---

## Feature 5 — Player-added side expenses

**Phase 3 behavior (overridden for expenses only):** Only the dealer can create, edit, and delete expenses.

**Phase 4 behavior:**
- Any active participant can add a side expense during an active game, provided they are the payer for that expense
- This is a **direct-add** model, not proposal/approval -- the expense is recorded immediately
- The dealer retains full authority: the dealer can create expenses for any payer, and can edit or delete any expense regardless of who created it
- The expense creator can edit or delete their own expense
- Other participants (non-dealer, non-creator) cannot edit or delete expenses they did not create

**Permission model for expenses:**

| Action | Who can do it |
|---|---|
| Create expense (self as payer) | Any active participant |
| Create expense (any payer) | Dealer only |
| Edit own expense | The participant who created it |
| Edit any expense | Dealer only |
| Delete own expense | The participant who created it |
| Delete any expense | Dealer only |
| View expenses | Any participant in the game |

**Payer constraint for non-dealer expense creation:**
- When a non-dealer participant creates an expense, the `paid_by_participant_id` must be their own participant ID
- A non-dealer cannot create an expense and claim someone else paid for it
- The dealer is exempt from this constraint and can set any participant as the payer (preserving existing behavior)
- This ensures non-dealer participants can only log expenses they personally paid for

**Rules:**
- Buy-ins remain **dealer-only** -- this change applies only to side expenses
- Guests cannot create expenses directly (they have no authenticated session). The dealer creates expenses on behalf of guests, as before
- The `created_by_user_id` field on expenses identifies who created the record and is used for edit/delete permission checks
- The `paid_by_participant_id` field identifies who paid for the expense -- for non-dealers, this must match the creator's participant record
- Expense creation is only allowed during active games (same as current behavior)
- Participants with `left_early` status cannot create new expenses
- All existing expense validation rules apply (splits must sum to total, amounts > 0, participants must belong to game)
- WebSocket broadcast on expense create/edit/delete works as before -- all connected clients see the update

---

## New notification types

| Type | Trigger | Recipient |
|---|---|---|
| `game_resettled` | Closed game re-settled after retroactive edit | All registered participants |

All existing notification types from Phase 2 and Phase 3 are preserved unchanged.

---

## Permissions model additions

| Action | Who can do it |
|---|---|
| Invite friend during active game | Dealer only (friends-only) |
| Delete all notifications | Notification owner only |
| Edit closed game buy-ins | Dealer only |
| Edit closed game final stacks | Dealer only |
| View game edit audit trail | Any participant of the game |
| Create side expense (active game) | Any active participant |
| Edit own expense | Creator of the expense |
| Edit any expense | Dealer only |
| Delete own expense | Creator of the expense |
| Delete any expense | Dealer only |

---

## Out of scope for Phase 4

- Push notifications (APNs / FCM)
- Individual notification deletion (only delete-all for now)
- Retroactive editing of expenses or participant list on closed games
- Retroactive editing of game metadata (title, chip rate, currency)
- Player proposal/approval flow for expenses (direct-add is used instead)
- Guest-initiated expense creation (dealer acts on their behalf)
- Remove participant from lobby UI
- Blocking or reporting users
- Chat or messaging
- Payment tracking for settlement transfers
- Guest conversion to registered user
- Profile image upload
- Tournament mode or multi-table support

---

## Success criteria for Phase 4

1. Dealer can invite friends from both the lobby and active game screens
2. Users can delete all notifications in one action; invite modal is comfortable to use
3. When invited to a game while the app is open, a popup appears immediately with Accept/Decline
4. Dealer can edit buy-ins and final stacks on closed games; settlement recomputes automatically with a full audit trail
5. Any active participant can add side expenses; dealer retains edit/delete authority over all expenses
6. All changes broadcast in real time and notifications are delivered correctly
