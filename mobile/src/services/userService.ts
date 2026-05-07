/**
 * User / profile service.
 *
 * Uses apiClient so Authorization header + token refresh are handled automatically.
 */

import { apiClient } from "@/lib/apiClient";
import type {
  PublicProfile,
  UpdateProfileRequest,
  User,
  UserSearchResult,
  UserStatsView,
} from "@/types/user";

/** Fetch the current authenticated user's profile. */
export async function getMe(): Promise<User> {
  return apiClient.get<User>("/users/me");
}

/** Partially update the current user's profile. */
export async function updateMe(data: UpdateProfileRequest): Promise<User> {
  return apiClient.patch<User>("/users/me", data);
}

/**
 * Search registered users by name (partial, case-insensitive).
 * Email is not searchable. Returns an empty array for queries shorter than 2 characters.
 */
export async function searchUsers(q: string): Promise<UserSearchResult[]> {
  if (q.trim().length < 2) return [];
  const encoded = encodeURIComponent(q.trim());
  return apiClient.get<UserSearchResult[]>(`/users/search?q=${encoded}`);
}

/** Fetch the public profile for any registered user. */
export async function getPublicProfile(userId: string): Promise<PublicProfile> {
  return apiClient.get<PublicProfile>(`/users/${userId}/profile`);
}

/**
 * Fetch stats for any registered user.
 * Returns full stats if the viewer is that user or an accepted friend;
 * otherwise returns only total_games_played with is_friend_access=false.
 */
export async function getUserStats(userId: string): Promise<UserStatsView> {
  return apiClient.get<UserStatsView>(`/users/${userId}/stats`);
}
