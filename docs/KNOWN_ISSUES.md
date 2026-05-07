# KNOWN_ISSUES.md

Known bugs and technical debt discovered during or after MVP development.  
Issues here are candidates for Phase 2 fixes. Do not modify MVP behavior to address these unless the fix is in scope for the active stage.

---

## KI-001 — Account switch does not reliably reset user-scoped state

**Severity:** High → **RESOLVED in Phase 2 Stage 10**  
**Affected area:** Mobile — auth, profile, my-games, history, stats  
**Discovered:** Post Stage 9 QA

### Symptom

When a user logs out and a different user logs in on the same device, the new session sometimes displays stale data from the previous session:
- Profile screen shows the previous user's name/image
- My Games list contains the previous user's games
- History and stats reflect the previous user's records

### Root cause (suspected)

TanStack Query caches server state keyed by query keys. On logout, the cache is not fully cleared, so when the new user's queries fire, stale cached responses from the prior session are served before the refetch completes — or the refetch never triggers because the query key did not change.

Additionally, Zustand's auth store may be updating the token correctly while leaving TanStack Query's `queryClient` cache intact with prior user data.

### Expected behavior

On logout (or on any auth state change that results in a different `user_id`), all user-scoped query cache entries must be invalidated or cleared before the new user's screens render.

### Fix approach (to be implemented in Stage 10)

1. Call `queryClient.clear()` (or `queryClient.invalidateQueries()` for user-scoped keys) inside the logout handler in the auth store, before navigating to the login screen.
2. Ensure the login success handler also clears stale cache from any prior session before the new user's screens mount.
3. Verify that all user-scoped query keys include the `user_id` or rely on auth token rotation so they cannot accidentally serve cross-user data.
4. Add a manual QA test: log in as User A, browse profile and history, log out, log in as User B — confirm all screens show User B's data immediately.

### Fix implemented (Stage 10)

1. `queryClient` extracted to `mobile/src/lib/queryClient.ts` (singleton module)
2. `clearAuth()` calls `queryClient.clear()` before wiping tokens — handles logout and token-expiry paths
3. `login.tsx` and `register.tsx` call `queryClient.clear()` before `setTokens()` — belt-and-suspenders for the new-session case
4. `userId` added to the auth store, decoded from the JWT `sub` claim via `extractUserId()`
5. User-identity-scoped query keys (`me`, `games`, `history`, `stats`) now include `userId` as a parameter — structurally prevents cross-user cache hits even if `clear()` is missed

### References
- Auth store: `mobile/src/store/authStore.ts`
- Query keys: `mobile/src/lib/queryKeys.ts`
- Query client: `mobile/src/lib/queryClient.ts`
- API client: `mobile/src/lib/apiClient.ts`

---

## KI-002 — Invite registered user from game lobby has no mobile UI

**Severity:** Medium  
**Affected area:** Mobile — game lobby  
**Discovered:** Stage 7 implementation gap

### Symptom

The backend endpoint `POST /games/{game_id}/invite-user` exists and is tested (Stage 2), but the mobile game lobby screen has no UI to search for and invite a registered user by name or email.

Dealers can only add guests from the lobby screen; inviting a registered user requires out-of-band sharing of the invite link/token.

### Fix approach (to be implemented in Stage 14)

Build a user search flow accessible from the game lobby: dealer searches by name/email, selects a user, and the app calls the existing invite endpoint.

---
