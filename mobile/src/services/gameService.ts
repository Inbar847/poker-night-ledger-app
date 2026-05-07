/**
 * Game service — API calls for games and participants.
 * Keeps raw fetch logic out of screens.
 */

import { apiClient } from "@/lib/apiClient";
import type {
  CloseGameResult,
  CreateGameRequest,
  Game,
  Participant,
  ShortagePreview,
  ShortageResolutionRequired,
  ShortageStrategy,
} from "@/types/game";

/**
 * Type guard: returns true when the close endpoint responded with a
 * "shortage resolution required" payload rather than a closed GameResponse.
 */
export function isShortageResolutionRequired(
  result: CloseGameResult,
): result is ShortageResolutionRequired {
  return (
    "requires_shortage_resolution" in result &&
    result.requires_shortage_resolution === true
  );
}

export async function listGames(): Promise<Game[]> {
  return apiClient.get<Game[]>("/games");
}

export async function getGame(gameId: string): Promise<Game> {
  return apiClient.get<Game>(`/games/${gameId}`);
}

export async function createGame(data: CreateGameRequest): Promise<Game> {
  return apiClient.post<Game>("/games", data);
}

export async function startGame(gameId: string): Promise<Game> {
  return apiClient.post<Game>(`/games/${gameId}/start`);
}

/**
 * Attempt to close a game.
 *
 * - No strategy supplied:
 *   - No shortage → game closes, returns GameResponse (CloseGameResult narrows to Game).
 *   - Shortage detected → returns ShortageResolutionRequired (HTTP 200, game NOT closed).
 *     The caller should show the strategy modal and re-call with a strategy.
 * - Strategy supplied: applies shortage distribution, closes game, returns GameResponse.
 */
export async function closeGame(
  gameId: string,
  shortageStrategy?: ShortageStrategy,
): Promise<CloseGameResult> {
  const body: { shortage_strategy?: ShortageStrategy } = {};
  if (shortageStrategy) body.shortage_strategy = shortageStrategy;
  return apiClient.post<CloseGameResult>(`/games/${gameId}/close`, body);
}

/** Check whether the current settlement has a shortage before closing. */
export async function getShortagePreview(gameId: string): Promise<ShortagePreview> {
  return apiClient.get<ShortagePreview>(`/games/${gameId}/shortage-preview`);
}

export async function getParticipants(gameId: string): Promise<Participant[]> {
  return apiClient.get<Participant[]>(`/games/${gameId}/participants`);
}

export async function joinByToken(token: string): Promise<Participant> {
  return apiClient.post<Participant>("/games/join-by-token", { token });
}

export async function generateInviteLink(
  gameId: string,
): Promise<{ game_id: string; invite_token: string }> {
  return apiClient.post<{ game_id: string; invite_token: string }>(
    `/games/${gameId}/invite-link`,
  );
}

export async function addGuest(
  gameId: string,
  guest_name: string,
): Promise<Participant> {
  return apiClient.post<Participant>(`/games/${gameId}/guests`, { guest_name });
}

/** Player cashes out early — enters their own final chip count. */
export async function cashOut(
  gameId: string,
  chipsAmount: string,
): Promise<{ participant_id: string; chips_amount: string; status: string }> {
  return apiClient.post<{
    participant_id: string;
    chips_amount: string;
    status: string;
  }>(`/games/${gameId}/cashout`, { chips_amount: chipsAmount });
}

/** Hide a game from the current user's lists (user-specific, not deletion). */
export async function hideGame(gameId: string): Promise<void> {
  await apiClient.post<void>(`/games/${gameId}/hide`, {});
}

export async function inviteUser(
  gameId: string,
  userId: string,
): Promise<Participant> {
  return apiClient.post<Participant>(`/games/${gameId}/invite-user`, {
    user_id: userId,
  });
}
