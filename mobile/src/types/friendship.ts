/**
 * Friendship domain types for the mobile client.
 *
 * These mirror the Pydantic schemas from backend/app/schemas/friendship.py.
 */

/** The friendship state between the current user and a target user. */
export type FriendshipUIStatus =
  | "not_friends"
  | "pending_outgoing"
  | "pending_incoming"
  | "friends";

/** Returned by GET /friends/status/{user_id} */
export interface FriendshipStatusResponse {
  status: FriendshipUIStatus;
  friendship_id: string | null;
}

/** Raw friendship record (used for accept/decline/remove) */
export interface FriendshipResponse {
  id: string;
  requester_user_id: string;
  addressee_user_id: string;
  status: "pending" | "accepted" | "declined";
  created_at: string;
  updated_at: string;
}

/** Public user info embedded in friend entries */
export interface FriendUserInfo {
  id: string;
  full_name: string | null;
  profile_image_url: string | null;
}

/** One entry in the accepted friends list (GET /friends) */
export interface FriendEntry {
  friendship_id: string;
  friend: FriendUserInfo;
  since: string;
}

/** Enriched incoming request (GET /friends/requests/incoming) */
export interface IncomingRequestEntry {
  id: string;
  requester: FriendUserInfo;
  status: "pending";
  created_at: string;
}

/** Enriched outgoing request (GET /friends/requests/outgoing) */
export interface OutgoingRequestEntry {
  id: string;
  addressee: FriendUserInfo;
  status: "pending";
  created_at: string;
}
