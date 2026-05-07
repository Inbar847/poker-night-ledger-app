# PHASE2_PRODUCT_SPEC.md

# Phase 2 — Social, UX polish, and notifications

This document extends `PRODUCT_SPEC.md` for post-MVP development.  
**Do not modify PRODUCT_SPEC.md.** All MVP behavior is preserved unless this document explicitly overrides it.

---

## Phase 2 goal

Extend Poker Night Ledger from a single-user financial tool into a lightweight social poker platform:
- fix known UX correctness bugs from the MVP
- allow players to build a social graph of poker friends
- let dealers invite known friends directly from the game lobby
- surface friend-scoped statistics and a friends leaderboard
- deliver timely in-app notifications for social and game events

---

## What is preserved from MVP

- Guest participant support (no changes)
- Dealer-only buy-in control (no changes)
- WebSocket realtime for live games (no changes)
- Personal statistics for registered users (extended, not replaced)
- Settlement engine and audit trail (no changes)
- Game states: lobby → active → closed (no changes)
- Invite link / token join flow (no changes)

---

## New personas

### 4) Social Player
A registered user who actively uses the friends system.

Primary goals:
- build a friends list from regular poker partners
- see how friends compare across games
- quickly invite a known friend to a new game
- be notified when something relevant happens

---

## New features and flows

---

### Feature 1 — Account switch cache correctness (bug fix)

See `KNOWN_ISSUES.md` KI-001.

**Flow: Switch accounts**
1. User A is logged in and has browsed profile, games, history
2. User A logs out
3. User B logs in on the same device
4. All screens (profile, my games, history, stats) immediately show User B's data

**Acceptance criteria**
- No stale data from a prior session appears on any screen after a new login
- Applies both to: logout → login, and to forced re-auth (token expiry)

---

### Feature 2 — Friends system

Users can establish a mutual friendship with other registered users.

**Friendship states:**
- `pending` — request sent, not yet accepted
- `accepted` — mutual friendship
- `declined` — request was declined (non-visible to requester; can re-request after cooldown — out of scope for MVP Phase 2, just block re-request for now)
- `blocked` — future consideration; out of scope for Phase 2

**Rules:**
- Friendship is mutual (A and B are both friends once accepted)
- A user can have multiple pending outgoing requests simultaneously
- A user can receive multiple pending incoming requests simultaneously
- Declining a request does not notify the requester
- A user cannot send a duplicate request if one is already pending or accepted

**Flow: Send friend request**
1. User opens another user's public profile
2. Taps "Add Friend"
3. A pending friend request is created
4. Recipient receives an in-app notification (Feature 7)

**Flow: Accept / decline request**
1. User opens notifications or friends screen
2. Sees incoming request from a known user
3. Taps Accept or Decline
4. If accepted: both users now see each other in their friends list, requester gets a notification

**Flow: View friends list**
1. User opens Friends screen
2. Sees list of accepted friends with their display name and profile image
3. Can tap any friend to view their public profile

---

### Feature 3 — User search and public profile view

**User search:**
- Search by full name or partial email match
- Returns a list of registered users (no guests)
- Results are visible to any authenticated user

**Public profile:**
- Any authenticated user can view another user's public profile
- Public profile shows:
  - display name
  - profile image
  - total games played (always visible)
  - detailed stats (win rate, cumulative P&L, etc.) — **visible only to accepted friends**
- Non-friends see a locked/placeholder block where friend-only stats would appear

**Privacy rule:** Statistics are personal for MVP. Phase 2 extends this: stats are visible to accepted friends only. Stats remain hidden from non-friends and unauthenticated users.

---

### Feature 4 — Invite registered user from mobile game lobby

Close the gap from `KNOWN_ISSUES.md` KI-002.

**Flow:**
1. Dealer opens the game lobby
2. Taps "Invite Player"
3. Sees a search field — searches by name or email
4. Selects a user from results
5. App calls the existing `POST /games/{game_id}/invite-user` endpoint
6. Invited user receives an in-app notification (Feature 7)

**Note:** The backend endpoint already exists from Stage 2. This stage adds only the mobile UI.

---

### Feature 5 — Buy-in smart autofill

When a dealer enters a buy-in, either the cash amount or chips amount can be entered first, and the other field auto-calculates using the game's `chip_cash_rate`.

**Rules:**
- If dealer enters cash → chips = cash / chip_cash_rate (rounded to nearest whole chip)
- If dealer enters chips → cash = chips * chip_cash_rate
- Either field can still be manually overridden after autofill
- chip_cash_rate comes from the game record already loaded in the active game context
- Rounding must be explicit: cash → chips rounds down (floor), to avoid giving more chips than paid for

**No backend changes required.** This is a pure mobile UX improvement.

---

### Feature 6 — In-app notifications

Users receive notifications for social and game events.

**Notification triggers:**
| Event | Recipient |
|---|---|
| Friend request received | Target user |
| Friend request accepted | Requester |
| Invited to a game | Invited user |
| Game started (participant) | All participants |
| Game closed (participant) | All participants |

**Notification behavior:**
- Notifications are stored in the database (persistent, not ephemeral)
- Unread count badge on a Notifications tab/icon
- Notifications screen lists all notifications newest-first
- Tapping a notification navigates to the relevant context (game, friend profile, etc.)
- Notifications can be marked as read individually or all-at-once
- Push notifications (APNs/FCM) are **out of scope for Phase 2** — in-app only

**Notification types (enum):**
- `friend_request_received`
- `friend_request_accepted`
- `game_invitation`
- `game_started`
- `game_closed`

---

### Feature 7 — Friend-only leaderboard and social stats

After the friends system and privacy model are in place, surface a friend-scoped leaderboard.

**Leaderboard:**
- Shows only accepted friends (plus the current user)
- Default sort: cumulative net result (descending)
- Secondary sort options: win rate, games played
- No global/public leaderboard

**Social stats on public profile (friend-visible):**
- All stats already computed by the MVP stats service
- Filtered to: games played together (optional enhancement), overall career stats

**Rules:**
- Leaderboard is only visible to the user for their own friends — never public
- Stats visibility follows the same friend-only rule from Feature 3

---

## Permissions model additions

| Action | Who can do it |
|---|---|
| Send friend request | Any authenticated user |
| Accept/decline request | Recipient only |
| View friend list | Owner only |
| View public profile (basic) | Any authenticated user |
| View friend-only stats | Accepted friends only |
| Search users | Any authenticated user |
| View notifications | Owner only |
| Mark notifications read | Owner only |
| View friend leaderboard | Any authenticated user (own friends only) |

---

## Out of scope for Phase 2

- Push notifications (APNs / FCM)
- Blocking users
- Reporting users
- Chat or messaging
- Public leaderboard (beyond friends)
- Payment tracking for settlement transfers
- Guest conversion to registered user
- Profile image upload (still URL-only as per MVP)

---

## Success criteria for Phase 2

1. Account switching never shows stale data from a prior session
2. A user can find a friend, send a request, and have it accepted — all from the app
3. A dealer can invite a registered user to a game directly from the lobby
4. Friend-only stats are not visible to non-friends
5. Users receive in-app notifications for social and game events
6. A user can see how they rank among their friends
