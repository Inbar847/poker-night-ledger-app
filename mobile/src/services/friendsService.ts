/**
 * Friends service — API calls for the friends system.
 *
 * All calls go through apiClient so Authorization header + token refresh
 * are handled automatically.
 */

import { apiClient } from "@/lib/apiClient";
import type {
  FriendEntry,
  FriendshipResponse,
  FriendshipStatusResponse,
  IncomingRequestEntry,
  OutgoingRequestEntry,
} from "@/types/friendship";

/** Send a friend request to another user. */
export async function sendFriendRequest(addresseeUserId: string): Promise<FriendshipResponse> {
  return apiClient.post<FriendshipResponse>("/friends/request", {
    addressee_user_id: addresseeUserId,
  });
}

/** Accept an incoming friend request. */
export async function acceptFriendRequest(friendshipId: string): Promise<FriendshipResponse> {
  return apiClient.post<FriendshipResponse>(`/friends/${friendshipId}/accept`, {});
}

/** Decline an incoming friend request. */
export async function declineFriendRequest(friendshipId: string): Promise<FriendshipResponse> {
  return apiClient.post<FriendshipResponse>(`/friends/${friendshipId}/decline`, {});
}

/** Remove an accepted friendship (unfriend). */
export async function removeFriend(friendshipId: string): Promise<void> {
  return apiClient.delete<void>(`/friends/${friendshipId}`);
}

/** Fetch the current user's accepted friends list. */
export async function getFriends(): Promise<FriendEntry[]> {
  return apiClient.get<FriendEntry[]>("/friends");
}

/** Fetch pending incoming friend requests (enriched with requester info). */
export async function getIncomingRequests(): Promise<IncomingRequestEntry[]> {
  return apiClient.get<IncomingRequestEntry[]>("/friends/requests/incoming");
}

/** Fetch pending outgoing friend requests (enriched with addressee info). */
export async function getOutgoingRequests(): Promise<OutgoingRequestEntry[]> {
  return apiClient.get<OutgoingRequestEntry[]>("/friends/requests/outgoing");
}

/**
 * Get friendship status between the current user and a target user.
 * Returns one of: not_friends | pending_outgoing | pending_incoming | friends
 */
export async function getFriendshipStatus(
  userId: string
): Promise<FriendshipStatusResponse> {
  return apiClient.get<FriendshipStatusResponse>(`/friends/status/${userId}`);
}
