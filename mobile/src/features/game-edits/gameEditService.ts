/**
 * Game edit service — retroactive editing of closed games.
 *
 * Talks to the /games/{gameId}/edits/* endpoints added in Stage 28.
 */

import { apiClient } from "@/lib/apiClient";
import type {
  BuyIn,
  ClosedGameBuyInCreate,
  ClosedGameBuyInUpdate,
  ClosedGameFinalStackUpdate,
  FinalStack,
  GameEdit,
} from "@/types/game";

export async function listEdits(gameId: string): Promise<GameEdit[]> {
  return apiClient.get<GameEdit[]>(`/games/${gameId}/edits`);
}

export async function createBuyIn(
  gameId: string,
  data: ClosedGameBuyInCreate,
): Promise<BuyIn> {
  return apiClient.post<BuyIn>(`/games/${gameId}/edits/buy-ins`, data);
}

export async function updateBuyIn(
  gameId: string,
  buyInId: string,
  data: ClosedGameBuyInUpdate,
): Promise<BuyIn> {
  return apiClient.patch<BuyIn>(
    `/games/${gameId}/edits/buy-ins/${buyInId}`,
    data,
  );
}

export async function deleteBuyIn(
  gameId: string,
  buyInId: string,
): Promise<void> {
  return apiClient.delete(`/games/${gameId}/edits/buy-ins/${buyInId}`);
}

export async function updateFinalStack(
  gameId: string,
  participantId: string,
  data: ClosedGameFinalStackUpdate,
): Promise<FinalStack> {
  return apiClient.patch<FinalStack>(
    `/games/${gameId}/edits/final-stacks/${participantId}`,
    data,
  );
}
