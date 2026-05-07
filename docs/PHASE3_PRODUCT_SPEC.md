# PHASE3_PRODUCT_SPEC.md

# Phase 3 — Game lifecycle, invitation rework, and behavior fixes

This document extends `PRODUCT_SPEC.md` and `PHASE2_PRODUCT_SPEC.md` for post-Phase-2 development.  
**Do not modify PRODUCT_SPEC.md or PHASE2_PRODUCT_SPEC.md.** All MVP and Phase 2 behavior is preserved unless this document explicitly overrides it.

---

## Phase 3 goal

Fix critical UX bugs around notifications and game closing, rework the game invitation flow to use a pending accept/decline model tied to the friends system, and introduce early cash-out and participant lifecycle statuses so that games reflect real-world scenarios where players leave before the end.

---

## What is preserved from MVP and Phase 2

- Guest participant support (no changes)
- Dealer-only buy-in control (no changes — extended with early cash-out nuance)
- WebSocket realtime for live games (extended with new events)
- Personal statistics for registered users (no changes)
- Settlement engine and audit trail (no changes to calculation logic)
- Game states: lobby → active → closed (no changes)
- Invite link / token join flow (preserved alongside new invitation model)
- Friends system, user search, public profiles (no changes)
- Friend leaderboard (no changes)
- Buy-in smart autofill (no changes)

---

## P0 — Critical behavior fixes

---

### Fix 1 — Notification badge must reflect unread count only

**Current behavior:** The notification badge may show a count that does not match the true unread notification count (e.g. it counts all notifications, or does not decrement when notifications are read).

**Expected behavior:**
- The badge displays the exact count of notifications where `read = false`
- When a notification is marked as read (individually or via mark-all), the badge decrements immediately
- A badge count of 0 hides the badge entirely

---

### Fix 2 — Entering the notifications screen clears the badge

**Current behavior:** Opening the notifications screen does not automatically mark notifications as read or clear the badge.

**Expected behavior:**
- When the user navigates to the notifications screen, call `POST /notifications/read-all` automatically
- The badge count resets to 0 immediately upon entering the screen
- New notifications arriving while on the screen do not auto-mark as read — they appear as unread items that increment the badge if the user navigates away and returns

---

### Fix 3 — Close game blocked if final stacks are missing

**Current behavior:** The dealer can close a game even if some participants do not have a final chip count recorded. This produces an incomplete settlement.

**Expected behavior:**
- The `POST /games/{game_id}/close` endpoint validates that every participant who requires a final stack has one recorded
- If any are missing, the endpoint returns an error (HTTP 400) with a clear list of participants who still need final stacks
- The mobile close-game UI shows the error and lists the missing participants by display name

**Rules for who requires a final stack:**
- All participants with status `active` require a final stack
- Participants with status `left_early` already have a final stack (recorded at cash-out time) — they pass validation
- Participants with status `removed_before_start` do not require a final stack — they are excluded from settlement entirely

**Note:** Until participant lifecycle statuses are implemented (Feature 7), all participants are implicitly `active` and all require final stacks.

---

### Fix 4 — Dealer sees a clear error listing missing participants

This is the UX complement to Fix 3.

**Expected behavior:**
- When the close-game request fails due to missing final stacks, the response includes:
  - `missing_final_stacks`: array of `{participant_id, display_name}`
- The mobile app renders this list clearly, e.g. "Cannot close game. The following players still need final chip counts: Alice, Bob, Guest 1"
- The dealer can then navigate to enter the missing values before retrying

---

## P1 — Core feature changes

---

### Feature 5 — Friend-only game invitations

**Phase 2 behavior (overridden):** The dealer could search any registered user and invite them. The invited user was added to participants immediately.

**Phase 3 behavior:**
- The dealer can only invite users who are accepted friends
- The invite flow searches only the dealer's accepted friends list, not all users
- This applies to the in-game lobby invite flow; the invite-link/token flow is unchanged (anyone with the link can still join)

---

### Feature 6 — Pending game invitation model

**Phase 2 behavior (overridden):** Inviting a user via the lobby immediately added them as a participant.

**Phase 3 behavior:**
- Inviting a friend creates a **pending game invitation** record (not a participant)
- The invited user is NOT added to participants until they explicitly accept

**Game invitation states:**
- `pending` — invitation sent, awaiting response
- `accepted` — user accepted and was added as a participant
- `declined` — user declined the invitation

**Rules:**
- A user cannot be invited to the same game twice (guard against duplicate pending invitations)
- Declining an invitation does not notify the dealer
- An invitation to a game that has already started or closed is still valid — the user can accept and join a running game (same as the current invite-link behavior)

---

### Feature 7 — Notification and accept/decline for game invitations

**Flow:**
1. Dealer taps "Invite Friend" in the game lobby
2. Selects a friend from the friends list
3. A pending game invitation is created
4. Invited user receives a `game_invitation` notification
5. Tapping the notification shows game details + Accept / Decline buttons
6. Accept: user becomes a participant, dealer sees the update
7. Decline: invitation is marked as declined, no further action

**Acceptance criteria:**
- Invited user receives a notification immediately
- Accepting adds the user as a registered participant
- Declining does not create any additional notifications

---

### Feature 8 — Dealer sees pending invitation state in lobby

**Expected behavior:**
- The game lobby shows a section for pending invitations alongside the participants list
- Each pending invitation shows the invited friend's display name and a "Pending" badge
- When the invited user accepts, the pending invitation disappears and they appear in the participants list
- When the invited user declines, the pending invitation disappears silently

---

### Feature 9 — Realtime updates for invitation acceptance

**Expected behavior:**
- When an invited user accepts a game invitation, a WebSocket event is broadcast to the game room
- All connected clients (including the dealer) see the new participant appear in real time
- New event type: `game.invitation_accepted`

---

### Feature 10 — Early cash-out (leave early)

A player can leave the game early and cash out without being fully removed from the game. Their financial records remain intact for settlement.

**Flow:**
1. During an active game, a player decides to leave early
2. The player enters their own final chip count (their cash-out value)
3. The system records their final stack and marks them as `left_early`
4. The player's buy-ins, expenses, and final stack are all preserved
5. At settlement time, they are included in the calculation normally

**Rules:**
- Only the player themselves can initiate their own early cash-out
- The dealer can review and edit the early cash-out final stack value if needed (dealer retains ledger authority)
- A player who has left early cannot add more buy-ins or be assigned new expenses
- A player who has left early can still view the game (read-only)
- Early cash-out is only available during an active game

---

### Feature 11 — Participant lifecycle statuses

Extend the participant model with a `status` field:

| Status | Meaning |
|---|---|
| `active` | Currently in the game (default) |
| `left_early` | Cashed out early; included in settlement |
| `removed_before_start` | Removed from lobby before game started; excluded from settlement |

**Rules:**
- Default status for all new participants is `active`
- `left_early` is set when a player cashes out early during an active game
- `removed_before_start` is set when a participant is removed from the lobby before the game starts (future consideration — for Phase 3, this status exists in the model but the "remove from lobby" UI may be deferred)
- Settlement includes `active` and `left_early` participants, but excludes `removed_before_start`
- The close-game validation (Fix 3) uses these statuses to determine who needs a final stack

---

### Feature 12 — Player-entered early final stack vs dealer-controlled global entry

**Permissions clarification:**
- During an active game, a player can enter **only their own** final chip count as part of the early cash-out flow (Feature 10)
- The global "enter final chip counts for all participants" flow remains **dealer-only** — only the dealer can bulk-enter or edit chip counts for active players at game end
- The dealer can review and override any early cash-out value if they believe it is incorrect

---

### Feature 13 — Settlement transfer notifications

After a game is closed and settlement is computed, notify registered users who owe money.

**Flow:**
1. Game is closed and settlement transfers are generated
2. For each transfer where the `from_participant` is a registered user:
   - Create a notification of type `settlement_owed`
   - Notification data includes: game title, recipient display name, amount, currency
3. The notification message renders as: "You owe [display_name] [amount] [currency] from [game_title]"

**Rules:**
- Only users who **owe** money (debtors) receive a notification — creditors do not
- Guests cannot receive notifications (no user account)
- One notification per transfer (a user may receive multiple if they owe multiple people)

---

## New notification types

| Type | Trigger | Recipient |
|---|---|---|
| `settlement_owed` | Game closed with outgoing transfer | Debtor (registered user) |

All existing notification types from Phase 2 are preserved unchanged.

---

## Permissions model additions

| Action | Who can do it |
|---|---|
| Invite friend to game | Dealer only (friends-only) |
| Accept/decline game invitation | Invited user only |
| Enter own early cash-out | Player themselves (active game) |
| Edit early cash-out value | Dealer only |
| Enter global final chip counts | Dealer only |
| Close game | Dealer only (blocked if stacks missing) |

---

## Out of scope for Phase 3

- Push notifications (APNs / FCM)
- Remove participant from lobby UI (status exists but UI deferred)
- Blocking or reporting users
- Chat or messaging
- Payment tracking for settlement transfers
- Guest conversion to registered user
- Profile image upload
- Tournament mode or multi-table support

---

## Success criteria for Phase 3

1. Notification badge always shows correct unread count; entering notifications screen clears it
2. Dealer cannot close a game with missing final stacks; error clearly lists who is missing
3. Dealer invites only friends; invitation creates a pending record, not an immediate participant
4. Invited user can accept or decline; only accept adds them to the game
5. A player can cash out early and their result is included in settlement
6. After game close, debtors receive a notification telling them who to pay
