/**
 * NotificationsScreen — full list of in-app notifications for the current user.
 *
 * Features:
 * - Newest-first list with unread indicator dot on unread items
 * - "Mark all as read" button at the top when unread items exist
 * - Pull-to-refresh
 * - Empty state
 * - Tapping a notification: marks it as read + navigates to relevant context
 *
 * Navigation targets:
 *   friend_request_received | friend_request_accepted → /friends
 *   game_invitation | game_started | game_closed      → /games/{game_id}
 */

import { useRouter } from "expo-router";
import { useCallback } from "react";
import {
  FlatList,
  RefreshControl,
  StyleSheet,
  View,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import {
  Button,
  Divider,
  EmptyState,
  Row,
  Skeleton,
  Spacer,
  Text,
} from "@/components";
import NotificationItem from "@/features/notifications/NotificationItem";
import {
  useDeleteAllNotifications,
  useMarkAllRead,
  useMarkNotificationRead,
  useNotifications,
  useUnreadCount,
} from "@/hooks/useNotifications";
import { tokens } from "@/theme";
import type { AppNotification } from "@/types/notification";

function NotificationsSkeleton({ topInset }: { topInset: number }) {
  return (
    <View style={[styles.skeletonContainer, { paddingTop: topInset + tokens.spacing.base }]}>
      <Skeleton width={160} height={28} />
      <Spacer size="xl" />
      {[1, 2, 3, 4, 5].map((i) => (
        <View key={i}>
          <Skeleton height={72} radius={tokens.radius.lg} />
          <Spacer size="sm" />
        </View>
      ))}
    </View>
  );
}

export default function NotificationsScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();

  const { data: notifications = [], isLoading, refetch, isRefetching } = useNotifications();
  const { data: unreadData } = useUnreadCount();
  const markRead = useMarkNotificationRead();
  const markAll = useMarkAllRead();
  const deleteAll = useDeleteAllNotifications();

  const unreadCount = unreadData?.count ?? 0;

  // Auto-mark all as read when the screen gains focus.
  useFocusEffect(
    useCallback(() => {
      if (unreadCount > 0) {
        markAll.mutate();
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []),
  );

  function handlePress(notification: AppNotification) {
    if (!notification.read) {
      markRead.mutate(notification.id);
    }

    const gameId = notification.data?.game_id;

    if (
      notification.type === "settlement_owed" ||
      notification.type === "game_resettled"
    ) {
      if (gameId) {
        router.push(`/games/${gameId}/settlement` as never);
      }
    } else if (
      notification.type === "game_invitation" ||
      notification.type === "game_started" ||
      notification.type === "game_closed"
    ) {
      if (gameId) {
        router.push(`/games/${gameId}` as never);
      }
    } else if (
      notification.type === "friend_request_received" ||
      notification.type === "friend_request_accepted"
    ) {
      router.push("/friends" as never);
    }
  }

  if (isLoading) {
    return <NotificationsSkeleton topInset={insets.top} />;
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top + tokens.spacing.base }]}>
      {/* Header */}
      <View style={styles.headerRow}>
        <Text variant="h1">Notifications</Text>
      </View>

      {/* Actions bar */}
      {(unreadCount > 0 || notifications.length > 0) && (
        <>
          <View style={styles.actionsBar}>
            <Text variant="caption" color="secondary">
              {unreadCount > 0 ? `${unreadCount} unread` : `${notifications.length} notifications`}
            </Text>
            <Row gap="sm">
              {unreadCount > 0 && (
                <Button
                  label={markAll.isPending ? "Marking\u2026" : "Mark all read"}
                  variant="ghost"
                  size="md"
                  disabled={markAll.isPending}
                  onPress={() => markAll.mutate()}
                />
              )}
              <Button
                label={deleteAll.isPending ? "Deleting\u2026" : "Delete All"}
                variant="ghost"
                size="md"
                disabled={deleteAll.isPending}
                onPress={() => deleteAll.mutate()}
              />
            </Row>
          </View>
          <Divider subtle />
        </>
      )}

      {/* List */}
      <FlatList
        data={notifications}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <NotificationItem notification={item} onPress={handlePress} />
        )}
        refreshControl={
          <RefreshControl
            refreshing={isRefetching}
            onRefresh={refetch}
            tintColor={tokens.color.accent.primary}
          />
        }
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.listContent}
        ListEmptyComponent={
          <EmptyState
            title="All caught up"
            description="No notifications yet"
          />
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  headerRow: {
    paddingHorizontal: tokens.spacing.lg,
    paddingBottom: tokens.spacing.md,
  },
  actionsBar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: tokens.spacing.lg,
    paddingBottom: tokens.spacing.sm,
  },
  listContent: {
    flexGrow: 1,
    paddingBottom: tokens.spacing["2xl"],
  },
  skeletonContainer: {
    paddingHorizontal: tokens.spacing.lg,
  },
});
