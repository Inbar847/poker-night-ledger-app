/**
 * Settlement service — fetch settlement summary.
 */

import { apiClient } from "@/lib/apiClient";
import type { Settlement } from "@/types/game";

export async function getSettlement(gameId: string): Promise<Settlement> {
  return apiClient.get<Settlement>(`/games/${gameId}/settlement`);
}
