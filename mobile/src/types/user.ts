export interface User {
  id: string;
  email: string;
  full_name: string | null;
  phone: string | null;
  profile_image_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface UpdateProfileRequest {
  full_name?: string | null;
  phone?: string | null;
  profile_image_url?: string | null;
}

/** Public-safe user fields returned from /users/search */
export interface UserSearchResult {
  id: string;
  full_name: string | null;
  profile_image_url: string | null;
}

/** Public profile returned from /users/{user_id}/profile */
export interface PublicProfile {
  id: string;
  full_name: string | null;
  profile_image_url: string | null;
}

import type { RecentGameSummary } from "@/types/stats";

/**
 * Stats response from /users/{user_id}/stats.
 *
 * `is_friend_access` tells the UI whether to show full stats or a locked block.
 * Detailed fields are null when is_friend_access is false.
 */
export interface UserStatsView {
  is_friend_access: boolean;
  total_games_played: number;
  total_games_hosted: number | null;
  games_with_result: number | null;
  cumulative_net: string | null;
  average_net: string | null;
  profitable_games: number | null;
  win_rate: number | null;
  recent_games: RecentGameSummary[] | null;
}
