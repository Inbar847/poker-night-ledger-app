/**
 * Route: /public-profile/[userId]
 *
 * Thin shell that reads the userId from the URL and delegates to PublicProfileScreen.
 */

import { useLocalSearchParams } from "expo-router";
import { View } from "react-native";

import PublicProfileScreen from "@/features/profile/PublicProfileScreen";

export default function PublicProfileRoute() {
  const { userId } = useLocalSearchParams<{ userId: string }>();

  return (
    <View style={{ flex: 1 }}>
      <PublicProfileScreen userId={userId} />
    </View>
  );
}
