/**
 * TanStack Query hooks for the friends system.
 *
 * All mutations invalidate relevant query keys so the UI updates automatically
 * after an accept, decline, or remove.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "@/lib/queryKeys";
import * as friendsService from "@/services/friendsService";

// ---------------------------------------------------------------------------
// Query hooks — read-only data fetching
// ---------------------------------------------------------------------------

/** List of accepted friends for the current user. */
export function useFriends() {
  return useQuery({
    queryKey: queryKeys.friends,
    queryFn: friendsService.getFriends,
    staleTime: 30_000,
  });
}

/** Pending incoming friend requests (enriched with requester user info). */
export function useIncomingFriendRequests() {
  return useQuery({
    queryKey: queryKeys.friendRequestsIncoming,
    queryFn: friendsService.getIncomingRequests,
    staleTime: 30_000,
  });
}

/** Pending outgoing friend requests (enriched with addressee user info). */
export function useOutgoingFriendRequests() {
  return useQuery({
    queryKey: queryKeys.friendRequestsOutgoing,
    queryFn: friendsService.getOutgoingRequests,
    staleTime: 30_000,
  });
}

/**
 * Friendship status between the current user and a specific target user.
 * Used by PublicProfileScreen to show the correct Add Friend / Pending / Friends button.
 */
export function useFriendshipStatus(targetUserId: string) {
  return useQuery({
    queryKey: queryKeys.friendshipStatus(targetUserId),
    queryFn: () => friendsService.getFriendshipStatus(targetUserId),
    staleTime: 15_000,
    enabled: !!targetUserId,
  });
}

// ---------------------------------------------------------------------------
// Mutation hooks — state-changing operations
// ---------------------------------------------------------------------------

function useFriendsMutationBase() {
  const queryClient = useQueryClient();

  function invalidateAll() {
    queryClient.invalidateQueries({ queryKey: queryKeys.friends });
    queryClient.invalidateQueries({ queryKey: queryKeys.friendRequestsIncoming });
    queryClient.invalidateQueries({ queryKey: queryKeys.friendRequestsOutgoing });
  }

  return { invalidateAll, queryClient };
}

/** Send a friend request to another user. Invalidates status for the target. */
export function useSendFriendRequest(targetUserId?: string) {
  const { invalidateAll, queryClient } = useFriendsMutationBase();

  return useMutation({
    mutationFn: (addresseeUserId: string) =>
      friendsService.sendFriendRequest(addresseeUserId),
    onSuccess: () => {
      invalidateAll();
      if (targetUserId) {
        queryClient.invalidateQueries({
          queryKey: queryKeys.friendshipStatus(targetUserId),
        });
      }
    },
  });
}

/** Accept an incoming friend request. */
export function useAcceptFriendRequest() {
  const { invalidateAll, queryClient } = useFriendsMutationBase();

  return useMutation({
    mutationFn: (friendshipId: string) =>
      friendsService.acceptFriendRequest(friendshipId),
    onSuccess: () => {
      invalidateAll();
      // Also invalidate any cached friendship status for the relevant user
      queryClient.invalidateQueries({ queryKey: ["friends", "status"] });
    },
  });
}

/** Decline an incoming friend request. */
export function useDeclineFriendRequest() {
  const { invalidateAll } = useFriendsMutationBase();

  return useMutation({
    mutationFn: (friendshipId: string) =>
      friendsService.declineFriendRequest(friendshipId),
    onSuccess: invalidateAll,
  });
}

/** Unfriend — remove an accepted friendship. */
export function useRemoveFriend(targetUserId?: string) {
  const { invalidateAll, queryClient } = useFriendsMutationBase();

  return useMutation({
    mutationFn: (friendshipId: string) =>
      friendsService.removeFriend(friendshipId),
    onSuccess: () => {
      invalidateAll();
      if (targetUserId) {
        queryClient.invalidateQueries({
          queryKey: queryKeys.friendshipStatus(targetUserId),
        });
      }
    },
  });
}
