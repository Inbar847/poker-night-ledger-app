/**
 * Centralised TanStack Query key definitions.
 * Import from here so key shape stays consistent across hooks and mutations.
 *
 * User-identity-scoped keys (me, games, history, stats) require a `userId`
 * parameter. This ensures that cached data from one user cannot be served to
 * a different user even if queryClient.clear() were somehow skipped. Screens
 * behind the auth guard always have a non-null userId from the auth store.
 *
 * Game-scoped keys (game, participants, buyIns, etc.) are keyed by game ID
 * only — they are access-controlled server-side and are not identity-specific.
 */
export const queryKeys = {
  /** Current authenticated user — scoped by userId for cross-session safety. */
  me: (userId: string) => ["users", "me", userId] as const,

  /** All games for the current user — scoped by userId. */
  games: (userId: string) => ["games", "user", userId] as const,

  /** Single game by ID */
  game: (id: string) => ["games", id] as const,

  /** Participants list for a game */
  participants: (gameId: string) => ["games", gameId, "participants"] as const,

  /** Buy-ins list for a game */
  buyIns: (gameId: string) => ["games", gameId, "buy-ins"] as const,

  /** Expenses list for a game */
  expenses: (gameId: string) => ["games", gameId, "expenses"] as const,

  /** Final stacks list for a game */
  finalStacks: (gameId: string) => ["games", gameId, "final-stacks"] as const,

  /** Settlement for a game */
  settlement: (gameId: string) => ["games", gameId, "settlement"] as const,

  /** History list (closed games) — scoped by userId. */
  history: (userId: string) => ["history", "games", "user", userId] as const,

  /** Settlement detail for one historical game */
  historyGame: (id: string) => ["history", "games", id] as const,

  /** Personal stats for the current user — scoped by userId. */
  stats: (userId: string) => ["stats", "me", userId] as const,

  /** User search results — scoped by query string. */
  userSearch: (q: string) => ["users", "search", q] as const,

  /** Public profile for any user — keyed by target user ID. */
  publicProfile: (userId: string) => ["users", "profile", userId] as const,

  /** Stats view for any user — keyed by target user ID. */
  userStats: (userId: string) => ["users", "stats", userId] as const,

  /** Accepted friends list for the current user. */
  friends: ["friends"] as const,

  /** Incoming pending friend requests. */
  friendRequestsIncoming: ["friends", "requests", "incoming"] as const,

  /** Outgoing pending friend requests. */
  friendRequestsOutgoing: ["friends", "requests", "outgoing"] as const,

  /** Friendship status between current user and a specific target. */
  friendshipStatus: (targetUserId: string) =>
    ["friends", "status", targetUserId] as const,

  /** Notifications list for the current user. */
  notifications: ["notifications"] as const,

  /** Unread notification count for the current user. */
  notificationsUnread: ["notifications", "unread-count"] as const,

  /** Friend leaderboard for the current user. */
  leaderboard: ["social", "leaderboard"] as const,

  /** Pending game invitations for a specific game (dealer view). */
  gameInvitations: (gameId: string) =>
    ["games", gameId, "invitations"] as const,

  /** Pending game invitations for the current user. */
  pendingInvitations: ["invitations", "pending"] as const,

  /** Audit trail (game edits) for a closed game. */
  gameEdits: (gameId: string) => ["games", gameId, "edits"] as const,
};
