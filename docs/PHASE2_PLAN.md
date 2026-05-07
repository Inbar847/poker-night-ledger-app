# PHASE2_PLAN.md

This file is the execution roadmap for **Phase 2** of Poker Night Ledger.  
Claude must implement **one stage at a time** and stop after the requested stage.

Read `PHASE2_PRODUCT_SPEC.md` and `PHASE2_ARCHITECTURE.md` before implementing any stage.  
The MVP stages (0–9) in `PLAN.md` are complete and must not be regressed.

---

# Stage 10 — Account switch cache fix

## Goal
Fix the known bug (KI-001) where switching accounts leaves stale profile/games/history/stats data on screen.

## Scope
- mobile only — no backend changes required

## Deliverables
- `logout()` in `authStore.ts` calls `queryClient.clear()` before navigating to login
- `login()` success path calls `queryClient.clear()` before navigating into the app shell
- All user-scoped query keys verified to include `user_id` so cross-user cache hits are structurally impossible
- Manual QA: log in as User A → browse profile/history → log out → log in as User B → confirm all screens show User B's data immediately

## Files likely to change
- `mobile/src/store/authStore.ts`
- `mobile/src/lib/queryKeys.ts`
- Any screen or hook that constructs a user-scoped query key without including `user_id`

## Acceptance criteria
- No stale data visible after account switch in manual testing
- Query key audit confirms all user-scoped keys are scoped by user ID

## Stop boundary
Fix only the cache/auth wiring. Do not add new screens or services.

---

# Stage 11 — Friends system: backend

## Goal
Build the server-side friends system: data model, service, and API endpoints.

## Deliverables
- `friendships` table + Alembic migration
- `FriendshipStatus` enum: `pending`, `accepted`, `declined`
- `friendship` SQLAlchemy model
- `friendship` Pydantic schemas: request/response
- `friendship_service.py`:
  - `send_request(requester_id, addressee_id)`
  - `accept_request(friendship_id, caller_id)`
  - `decline_request(friendship_id, caller_id)`
  - `list_friends(user_id)` — accepted, both directions
  - `list_incoming_requests(user_id)`
  - `list_outgoing_requests(user_id)`
  - `are_friends(user_id_a, user_id_b)` — boolean, used by privacy checks
  - `remove_friend(friendship_id, caller_id)`
- Router `app/api/routers/friends.py`
- Backend tests for friendship lifecycle and permission guards

## Suggested endpoints
```
POST   /friends/request
POST   /friends/{friendship_id}/accept
POST   /friends/{friendship_id}/decline
GET    /friends
GET    /friends/requests/incoming
GET    /friends/requests/outgoing
DELETE /friends/{friendship_id}
```

## Acceptance criteria
- All friendship state transitions work correctly
- Duplicate request guard enforced
- Self-request rejected
- Only the addressee can accept/decline
- Only participants can remove the friendship
- Tests cover all edge cases

## Stop boundary
No mobile UI. No notification side-effects yet (added in Stage 13).

---

# Stage 12 — User search and public profiles: backend + mobile

## Goal
Allow users to search for others by name/email and view a public profile with friend-gated statistics.

## Deliverables

### Backend
- `GET /users/search?q=...` endpoint (returns id, full_name, profile_image_url only — no email leak)
- `GET /users/{user_id}/profile` endpoint — returns public profile fields
- `GET /users/{user_id}/stats` endpoint — returns full stats if caller is a friend or self; returns public-only stats (games played) otherwise
- Extend `stats_service` to accept `viewer_user_id` for privacy decisions
- Backend tests for privacy gating

### Mobile
- `UserSearchInput` component — reusable debounced search that calls `/users/search`
- `PublicProfileScreen` — shows display name, profile image, games played; shows full stats block if friend or self; shows locked/placeholder block if not friend
- New service: `userService.searchUsers(q)`, `userService.getPublicProfile(userId)`, `userService.getUserStats(userId)`
- New query keys for search and public profile

## Files likely to change/add

**Backend:**
- `app/api/routers/users.py` (extend)
- `app/services/user_service.py` (extend)
- `app/services/stats_service.py` (extend)
- `app/schemas/users.py` (add public profile response schema)
- `tests/test_users.py`

**Mobile:**
- `mobile/src/components/UserSearchInput.tsx`
- `mobile/src/features/profile/PublicProfileScreen.tsx`
- `mobile/src/services/userService.ts` (extend)
- `mobile/src/lib/queryKeys.ts` (extend)
- App router: add route for `public-profile/[userId]`

## Acceptance criteria
- Authenticated user can search by name and see results
- Non-friend sees only games-played stat on another user's profile
- Friend (or self) sees full stats
- No sensitive fields (email, password) exposed in search or public profile responses

## Stop boundary
No friends UI screens yet (those come in Stage 13). No invite-user UI (Stage 14).

---

# Stage 13 — Friends system: mobile UI + notification side-effects

## Goal
Build the mobile friends experience and wire notification creation into friendship events.

## Deliverables

### Mobile
- `FriendsScreen` — tabs: Friends list / Incoming requests
- `FriendRequestCard` component — accept / decline actions
- "Add Friend" button on `PublicProfileScreen` (from Stage 12)
- Navigate to `PublicProfileScreen` from friends list entries
- Outgoing pending state shown when request already sent
- Hook: `useFriends`, `useFriendRequests`

### Backend — notification side-effects
- When `accept_request` succeeds: create `friend_request_accepted` notification for the requester
- When `send_request` succeeds: create `friend_request_received` notification for the addressee
- `notification_service.py` created here (minimal: create, used later for more triggers)
- `notifications` table + Alembic migration
- `Notification` SQLAlchemy model and Pydantic schemas
- No full notification screen yet — just the creation side-effects

## Files likely to change/add

**Backend:**
- `app/models/notification.py`
- `app/services/notification_service.py`
- `app/services/friendship_service.py` (extend with notification calls)
- Alembic migration for `notifications` table

**Mobile:**
- `mobile/src/features/friends/FriendsScreen.tsx`
- `mobile/src/features/friends/FriendRequestCard.tsx`
- `mobile/src/services/friendsService.ts`
- `mobile/src/hooks/useFriends.ts`
- App router: add `/friends` route

## Acceptance criteria
- User can see friends list and incoming requests
- Accept/decline works from the mobile app
- Accepted friend appears in friends list immediately
- Sending or accepting a request creates the correct notification record in the DB (verified via test or direct query)

## Stop boundary
No notification screen UI yet (Stage 15). No invite-user UI (Stage 14). No leaderboard yet (Stage 16).

---

# Stage 14 — Invite registered user from game lobby (mobile UI)

## Goal
Close the gap from KI-002: give dealers a UI to find and invite a registered user from the game lobby.

## Deliverables
- "Invite Player" button in the game lobby screen (dealer view only)
- Tapping it opens a modal/sheet with `UserSearchInput` (from Stage 12)
- Selecting a user calls `POST /games/{game_id}/invite-user` (existing endpoint)
- On success: invited user is added to participants list; a `game_invitation` notification is created for them
- Add `game_invitation` notification creation side-effect in the backend invite-user endpoint

## Files likely to change/add

**Backend:**
- `app/api/routers/games.py` — add notification side-effect call on invite-user success
- `app/services/notification_service.py` (extend)

**Mobile:**
- `mobile/app/(app)/games/[gameId]/lobby.tsx` (extend — add invite button, dealer-only guard)
- `mobile/src/components/InvitePlayerModal.tsx`

## Acceptance criteria
- Dealer sees an "Invite Player" button in lobby; regular participants do not
- Searching and selecting a user fires the invite endpoint
- Invited user appears in participant list
- `game_invitation` notification is created for the invited user (verified via test)

## Stop boundary
No changes to buy-in flows. No notification screen UI yet.

---

# Stage 15 — Buy-in smart autofill

## Goal
When a dealer enters a buy-in, autofill the complementary field (cash ↔ chips) using the game's `chip_cash_rate`.

## Scope
- mobile only — no backend changes required

## Deliverables
- Buy-in entry form (dealer view) updated:
  - Entering cash amount → chips auto-calculated: `floor(cash / chip_cash_rate)`
  - Entering chips amount → cash auto-calculated: `chips * chip_cash_rate`
  - Either field can still be manually overridden (autofill does not lock the field)
- `chip_cash_rate` sourced from the already-loaded active game context
- Explicit rounding: cash → chips uses `Math.floor`; chips → cash uses simple multiply

## Files likely to change
- Buy-in entry screen / form component (location depends on Stage 7 implementation)
- Any validation schema for the buy-in form (Zod schema)

## Acceptance criteria
- Entering cash fills chips correctly (floored)
- Entering chips fills cash correctly
- Overriding either field after autofill works without fighting the autofill
- Edge cases: chip_cash_rate of 0 must not divide by zero (show validation error)

## Stop boundary
No backend changes. No changes to settlement engine.

---

# Stage 16 — In-app notifications: screen and full event wiring

## Goal
Build the full notifications screen and complete all remaining notification side-effects.

## Deliverables

### Backend — remaining notification side-effects
- `POST /games/{game_id}/start` → create `game_started` notification for all participants
- `POST /games/{game_id}/close` → create `game_closed` notification for all participants
- All 5 notification types now being created where appropriate

### Backend — notification read API
- `GET /notifications` — list for current user, newest-first
- `GET /notifications/unread-count`
- `POST /notifications/{id}/read`
- `POST /notifications/read-all`
- Router: `app/api/routers/notifications.py`
- Backend tests for read/unread flows

### Mobile
- Notifications tab or icon in the app shell with unread badge count
- `NotificationsScreen` — list of notifications, newest-first
- `NotificationItem` component — tapping navigates to relevant context
- `notificationsService.ts`
- `useNotifications` hook (with polling or focus-refetch)
- Unread count refetched on app focus

## Files likely to change/add

**Backend:**
- `app/api/routers/notifications.py`
- `app/api/routers/games.py` (extend start/close with notification calls)
- `app/services/notification_service.py` (extend)
- `tests/test_notifications.py`

**Mobile:**
- `mobile/src/features/notifications/NotificationsScreen.tsx`
- `mobile/src/features/notifications/NotificationItem.tsx`
- `mobile/src/services/notificationsService.ts`
- `mobile/src/hooks/useNotifications.ts`
- `mobile/app/_layout.tsx` (add notifications tab/icon + badge)

## Acceptance criteria
- Unread badge count updates correctly
- All 5 notification types appear in the list
- Tapping a notification navigates to the right place
- Mark-as-read works individually and for all

## Stop boundary
No push notifications (APNs/FCM). No leaderboard yet.

---

# Stage 17 — Friend leaderboard and social stats

## Goal
Let users see how they compare to their accepted friends.

## Deliverables

### Backend
- `GET /social/leaderboard` — returns current user + all accepted friends with their stats, sorted by net result descending
- Extend `stats_service` to batch-compute stats for a list of user IDs
- `app/api/routers/social.py`
- Backend tests for leaderboard ordering and friend-scope isolation

### Mobile
- `LeaderboardScreen` — ranked list of self + friends
- Rank indicator, name, profile image, net result, win rate
- Sort toggle: net result / win rate / games played
- Entry point from profile or a new Social tab

## Files likely to change/add

**Backend:**
- `app/api/routers/social.py`
- `app/services/stats_service.py` (extend)
- `tests/test_social.py`

**Mobile:**
- `mobile/src/features/social/LeaderboardScreen.tsx`
- `mobile/src/services/socialService.ts`
- App router: add leaderboard route

## Acceptance criteria
- Leaderboard shows only accepted friends + self
- User with no friends sees only themselves
- Stats are consistent with what the personal stats screen shows
- Sort toggle works

## Stop boundary
No global/public leaderboard. No cross-user data exposed beyond accepted friends.

---

# Phase 2 stage execution rules

For every Phase 2 stage Claude must:

1. Read `PHASE2_PRODUCT_SPEC.md` and `PHASE2_ARCHITECTURE.md` before starting.
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
Do not regress any MVP behavior (Stages 0–9).
