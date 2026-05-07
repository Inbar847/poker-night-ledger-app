/**
 * Route: /notifications
 *
 * Top-level notifications screen with BottomTabBar.
 */

import { Stack, useRouter } from "expo-router";
import { StyleSheet, View } from "react-native";

import { BottomTabBar, FeltBackground } from "@/components";
import NotificationsScreen from "@/features/notifications/NotificationsScreen";
import { useUnreadCount } from "@/hooks/useNotifications";

export default function NotificationsRoute() {
  const router = useRouter();
  const { data: unreadData } = useUnreadCount();
  const unreadCount = unreadData?.count ?? 0;

  const handleTabPress = (key: string) => {
    if (key === "notifications") return; // already here
    if (key === "home") router.push("/games");
    if (key === "profile") router.push("/profile");
  };

  return (
    <FeltBackground>
      <Stack.Screen options={{ headerShown: false }} />
      <View style={styles.main}>
        <NotificationsScreen />
      </View>
      <BottomTabBar
        activeTab="notifications"
        onTabPress={handleTabPress}
        notificationCount={unreadCount}
      />
    </FeltBackground>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  main: {
    flex: 1,
  },
});
