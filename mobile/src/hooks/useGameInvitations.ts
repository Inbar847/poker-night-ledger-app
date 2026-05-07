/**
 * TanStack Query hooks for game invitations.
 *
 * useGameInvitations     — pending invitations for a game (dealer lobby view)
 * usePendingInvitations  — pending invitations for the current user
 * useCreateInvitation    — dealer invites a friend
 * useAcceptInvitation    — invited user accepts
 * useDeclineInvitation   — invited user declines
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "@/lib/queryKeys";
import * as gameInvitationService from "@/services/gameInvitationService";

/** Pending invitations for a game (dealer view). */
export function useGameInvitations(gameId: string) {
  return useQuery({
    queryKey: queryKeys.gameInvitations(gameId),
    queryFn: () => gameInvitationService.listGameInvitations(gameId),
    enabled: !!gameId,
    staleTime: 15_000,
  });
}

/** Pending invitations for the current user. */
export function usePendingInvitations() {
  return useQuery({
    queryKey: queryKeys.pendingInvitations,
    queryFn: gameInvitationService.listPendingInvitations,
    staleTime: 30_000,
  });
}

/** Dealer invites a friend to a game. */
export function useCreateInvitation(gameId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (invitedUserId: string) =>
      gameInvitationService.createInvitation(gameId, invitedUserId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.gameInvitations(gameId),
      });
    },
  });
}

/** Invited user accepts an invitation. */
export function useAcceptInvitation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      gameId,
      invitationId,
    }: {
      gameId: string;
      invitationId: string;
    }) => gameInvitationService.acceptInvitation(gameId, invitationId),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.pendingInvitations,
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.participants(variables.gameId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.gameInvitations(variables.gameId),
      });
    },
  });
}

/** Invited user declines an invitation. */
export function useDeclineInvitation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      gameId,
      invitationId,
    }: {
      gameId: string;
      invitationId: string;
    }) => gameInvitationService.declineInvitation(gameId, invitationId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.pendingInvitations,
      });
    },
  });
}
