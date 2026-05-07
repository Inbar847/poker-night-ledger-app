/**
 * Stats service — API calls for history and personal statistics.
 * Keeps raw fetch logic out of screens.
 */

import { apiClient } from "@/lib/apiClient";
import type { Settlement } from "@/types/game";
import type { GameHistoryItem, UserStats } from "@/types/stats";

/** Closed games the current user participated in, most recent first. */
export async function getHistory(): Promise<GameHistoryItem[]> {
  return apiClient.get<GameHistoryItem[]>("/history/games");
}

/**
 * Full settlement view for a single historical (closed) game.
 * Reuses the same Settlement shape as the live settlement endpoint.
 */
export async function getHistoryGame(gameId: string): Promise<Settlement> {
  return apiClient.get<Settlement>(`/history/games/${gameId}`);
}

/** Personal aggregated statistics for the current user. */
export async function getStats(): Promise<UserStats> {
  return apiClient.get<UserStats>("/stats/me");
}
