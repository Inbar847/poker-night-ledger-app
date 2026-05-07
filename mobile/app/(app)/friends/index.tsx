/**
 * Route: /friends
 *
 * Thin shell that mounts FriendsScreen with the correct header title.
 */

import { Stack } from "expo-router";
import { View } from "react-native";

import FriendsScreen from "@/features/friends/FriendsScreen";

export default function FriendsRoute() {
  return (
    <View style={{ flex: 1 }}>
      <Stack.Screen options={{ title: "Friends" }} />
      <FriendsScreen />
    </View>
  );
}
