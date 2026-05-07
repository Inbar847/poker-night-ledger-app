/**
 * Leaderboard route — Stage 17.
 *
 * Thin route wrapper that sets the screen title and renders
 * LeaderboardScreen from the features layer.
 */

import { Stack } from "expo-router";

import LeaderboardScreen from "@/features/social/LeaderboardScreen";

export default function LeaderboardRoute() {
  return (
    <>
      <Stack.Screen options={{ title: "Friend Leaderboard" }} />
      <LeaderboardScreen />
    </>
  );
}
