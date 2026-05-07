/**
 * Social service — Stage 17.
 *
 * Handles the friend leaderboard endpoint.
 */

import { apiClient } from "@/lib/apiClient";

export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  full_name: string | null;
  profile_image_url: string | null;
  total_games_played: number;
  games_with_result: number;
  /** Decimal string, e.g. "12.50" */
  cumulative_net: string;
  /** 0.0–1.0 or null if no games with result */
  win_rate: number | null;
  is_self: boolean;
}

export interface LeaderboardResponse {
  entries: LeaderboardEntry[];
}

/** Fetch the friend leaderboard for the current user. */
export async function getLeaderboard(): Promise<LeaderboardResponse> {
  return apiClient.get<LeaderboardResponse>("/social/leaderboard");
}
