/**
 * Game invitation service — API calls for the pending invitation flow.
 */

import { apiClient } from "@/lib/apiClient";
import type { GameInvitation } from "@/types/gameInvitation";

/** Dealer invites a friend to a game. Creates a pending invitation. */
export async function createInvitation(
  gameId: string,
  invitedUserId: string,
): Promise<GameInvitation> {
  return apiClient.post<GameInvitation>(`/games/${gameId}/invitations`, {
    invited_user_id: invitedUserId,
  });
}

/** List pending invitations for a game (dealer view). */
export async function listGameInvitations(
  gameId: string,
): Promise<GameInvitation[]> {
  return apiClient.get<GameInvitation[]>(`/games/${gameId}/invitations`);
}

/** Accept a game invitation (invited user). */
export async function acceptInvitation(
  gameId: string,
  invitationId: string,
): Promise<GameInvitation> {
  return apiClient.post<GameInvitation>(
    `/games/${gameId}/invitations/${invitationId}/accept`,
  );
}

/** Decline a game invitation (invited user). */
export async function declineInvitation(
  gameId: string,
  invitationId: string,
): Promise<GameInvitation> {
  return apiClient.post<GameInvitation>(
    `/games/${gameId}/invitations/${invitationId}/decline`,
  );
}

/** List pending invitations for the current user. */
export async function listPendingInvitations(): Promise<GameInvitation[]> {
  return apiClient.get<GameInvitation[]>("/invitations/pending");
}
