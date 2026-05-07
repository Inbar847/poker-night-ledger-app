# PHASE2_ARCHITECTURE.md

# Phase 2 Architecture

This document extends `ARCHITECTURE.md` for post-MVP development.  
**Do not modify ARCHITECTURE.md.** All MVP architecture is preserved unless this document explicitly overrides it.

---

## Stack additions

No new framework dependencies are required for Phase 2.  
All additions fit within the existing FastAPI + SQLAlchemy + React Native + Expo stack.

---

## New database models

All schema changes must go through Alembic migrations.

---

### 9) friendships

Represents a directed friend request that becomes a mutual relationship on acceptance.

Suggested fields:
- `id`
- `requester_user_id` (FK → users.id)
- `addressee_user_id` (FK → users.id)
- `status` — enum: `pending`, `accepted`, `declined`
- `created_at`
- `updated_at`

Rules:
- unique constraint on `(requester_user_id, addressee_user_id)` — one record per ordered pair
- `(A→B)` and `(B→A)` are distinct rows; only one should exist at a time
- accepted friendship is mutual: query for friends must check both directions
- a user cannot be both requester and addressee

Indexes:
- `(addressee_user_id, status)` — for incoming request queries
- `(requester_user_id, status)` — for outgoing request queries

---

### 10) notifications

Represents a persistent in-app notification for a user.

Suggested fields:
- `id`
- `user_id` (FK → users.id) — the recipient
- `type` — enum: `friend_request_received`, `friend_request_accepted`, `game_invitation`, `game_started`, `game_closed`
- `read` — boolean, default false
- `data` — JSONB — structured payload (e.g. `{from_user_id, game_id, friendship_id}`)
- `created_at`

Rules:
- notifications are append-only; they are never mutated except to mark `read = true`
- `data` field payload shape is defined per `type`

Indexes:
- `(user_id, read, created_at DESC)` — primary read path for the notifications list

---

## New backend services

### friendship service

Responsibilities:
- send friend request (enforce no duplicate, no self-request)
- accept / decline request (requester must not be the caller)
- list friends (accepted, both directions)
- list incoming pending requests
- list outgoing pending requests
- check friendship status between two users (for privacy decisions)

### notification service

Responsibilities:
- create notification record for a recipient
- list notifications for authenticated user (newest-first, paginated)
- mark one notification as read
- mark all notifications as read
- return unread count

Called by: friendship service, game/participant service (on game_started, game_closed, invite-user)

### user search service

Responsibilities:
- search users by full_name (case-insensitive, partial match) or email prefix
- exclude the requesting user from results
- return public-safe user fields only (no password_hash, no refresh tokens)

### stats service (extended)

The existing stats service is extended to support:
- computing stats for another user (used by public profile endpoint)
- accepting a `viewer_user_id` to determine whether to return full stats or public-only stats
- computing friend leaderboard: fetch all accepted friends, compute each one's stats, return ranked list

---

## New API endpoints

### Friends

```
POST   /friends/request              — send a friend request
POST   /friends/{friendship_id}/accept   — accept an incoming request
POST   /friends/{friendship_id}/decline  — decline an incoming request
GET    /friends                      — list accepted friends
GET    /friends/requests/incoming    — list pending incoming requests
GET    /friends/requests/outgoing    — list pending outgoing requests
DELETE /friends/{friendship_id}      — remove a friend (unfriend)
```

### User search and public profiles

```
GET    /users/search?q=...           — search users by name or email prefix
GET    /users/{user_id}/profile      — get public profile for a user
GET    /users/{user_id}/stats        — get stats for a user (friend-gated)
```

### Notifications

```
GET    /notifications                — list notifications for current user
GET    /notifications/unread-count   — get unread notification count
POST   /notifications/{id}/read      — mark a single notification as read
POST   /notifications/read-all       — mark all notifications as read
```

### Social stats / leaderboard

```
GET    /social/leaderboard           — friend leaderboard for current user
```

---

## Changes to existing endpoints

### `GET /users/me`
No change. Still returns full profile for authenticated user only.

### `POST /games/{game_id}/invite-user`
No backend change. This endpoint already exists (Stage 2). Phase 2 adds a notification side-effect: when a user is successfully invited, a `game_invitation` notification is created for them.

### `POST /games/{game_id}/start`
Add side effect: create `game_started` notification for all game participants.

### `POST /games/{game_id}/close`
Add side effect: create `game_closed` notification for all game participants.

---

## Privacy enforcement pattern

Stats visibility is enforced in the stats service, not in the router.

```
get_user_stats(target_user_id, viewer_user_id):
    if viewer_user_id == target_user_id:
        return full stats
    if friendship_service.are_friends(viewer_user_id, target_user_id):
        return full stats
    return public_only_stats  # only total games played
```

This pattern keeps authorization logic out of route handlers.

---

## New mobile modules

### `src/features/friends/`
- `friendsService.ts` — API calls for friend requests, list, search
- `useFriends.ts` — TanStack Query hooks
- `FriendsScreen.tsx` — friends list + incoming requests
- `FriendRequestCard.tsx` — component for accept/decline

### `src/features/notifications/`
- `notificationsService.ts` — API calls
- `useNotifications.ts` — TanStack Query hooks + unread count
- `NotificationsScreen.tsx`
- `NotificationItem.tsx`

### `src/features/profile/` (extended)
- `PublicProfileScreen.tsx` — public-facing profile view
- Add friend-only stats block with locked state for non-friends

### `src/features/social/`
- `LeaderboardScreen.tsx` — friend leaderboard

### `src/components/UserSearchInput.tsx`
Reusable search input that calls `/users/search` and returns selectable results.  
Used in: invite player flow (game lobby), send friend request flow.

---

## Account switch cache fix

### Problem
TanStack Query cache is not cleared on logout, causing stale data to bleed into a new session.

### Fix pattern

In `authStore.ts`, the `logout()` action must call:
```ts
queryClient.clear()
```
before navigating away from the authenticated shell.

In `login()` success handler, call:
```ts
queryClient.clear()
```
before navigating into the authenticated shell, to guard against any residual cache from a prior session.

The `queryClient` instance must be accessible from the auth store. Recommended approach: pass `queryClient` as a parameter to the logout/login action, or expose a `clearCache()` helper that screens/hooks can call as part of the auth transition.

### Query key discipline
All user-scoped queries must use query keys that include the authenticated user's ID so that if cache clearing is missed, a different user's ID will naturally miss the cache rather than returning wrong data:
```ts
// Good
[queryKeys.userProfile, userId]
[queryKeys.myGames, userId]

// Risky (avoid)
[queryKeys.userProfile]   // could be shared across users
```

---

## New query keys

Add to `queryKeys.ts`:
```ts
friends: 'friends',
friendRequests: 'friendRequests',
notifications: 'notifications',
notificationsUnread: 'notificationsUnread',
userSearch: 'userSearch',
publicProfile: 'publicProfile',
userStats: 'userStats',
leaderboard: 'leaderboard',
```

---

## Realtime additions (notifications)

Notification delivery currently uses the database poll model (client fetches on mount and on focus). WebSocket push for notifications is **not required for Phase 2**.

If real-time notification badges are desired without polling, the existing WebSocket game-room channel can be extended to include a personal user channel (`user.{user_id}`). This is optional and deferred.

---

## Testing additions

New backend test coverage required:
- friendship lifecycle (request → accept, request → decline, duplicate guard, self-request guard)
- friendship privacy: stats endpoint returns restricted data to non-friends
- notification creation side effects on game_started, game_closed, invite-user
- notification read/unread flows
- user search: no password fields leaked, requester excluded from results
- friend leaderboard: only includes accepted friends

New mobile QA flows:
- account switch shows fresh data (KI-001 regression test)
- friend request → accept → appears in friends list
- invite user from game lobby calls correct endpoint
- notifications screen shows and dismisses items correctly
