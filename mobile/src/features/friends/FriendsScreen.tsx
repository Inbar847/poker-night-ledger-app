/**
 * FriendsScreen — shows two tabs:
 *  1. Friends      — list of accepted friends with navigation to their public profile
 *  2. Requests     — incoming pending friend requests with accept/decline actions
 *
 * Navigation: tapping a friend navigates to /public-profile/[userId].
 */

import { useRouter } from "expo-router";
import { useState } from "react";
import {
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  View,
} from "react-native";

import {
  Avatar,
  Card,
  EmptyState,
  FeltBackground,
  Row,
  Skeleton,
  Spacer,
  Text,
} from "@/components";
import FriendRequestCard from "@/features/friends/FriendRequestCard";
import { useFriends, useIncomingFriendRequests } from "@/hooks/useFriends";
import { tokens } from "@/theme";
import type { FriendEntry } from "@/types/friendship";

type Tab = "friends" | "requests";

// ---------------------------------------------------------------------------
// Friend list item
// ---------------------------------------------------------------------------

function FriendItem({ entry }: { entry: FriendEntry }) {
  const router = useRouter();
  const name = entry.friend.full_name ?? "Unknown Player";

  return (
    <Card
      variant="default"
      padding="compact"
      onPress={() => router.push(`/public-profile/${entry.friend.id}`)}
    >
      <Row align="center" gap="md">
        <Avatar
          uri={entry.friend.profile_image_url}
          name={name}
          size="md"
        />
        <View style={styles.nameBlock}>
          <Text variant="bodyBold" numberOfLines={1}>{name}</Text>
        </View>
        <Text variant="body" color="muted">{"\u203A"}</Text>
      </Row>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Loading skeleton
// ---------------------------------------------------------------------------

function FriendsSkeleton() {
  return (
    <View style={styles.skeletonContainer}>
      {[1, 2, 3, 4, 5].map((i) => (
        <View key={i}>
          <Skeleton height={60} radius={tokens.radius.lg} />
          <Spacer size="sm" />
        </View>
      ))}
    </View>
  );
}

// ---------------------------------------------------------------------------
// Main screen
// ---------------------------------------------------------------------------

export default function FriendsScreen() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<Tab>("friends");

  const friendsQuery = useFriends();
  const requestsQuery = useIncomingFriendRequests();

  const incomingCount = requestsQuery.data?.length ?? 0;

  const isLoading =
    activeTab === "friends" ? friendsQuery.isLoading : requestsQuery.isLoading;

  const isRefreshing =
    activeTab === "friends" ? friendsQuery.isFetching : requestsQuery.isFetching;

  function handleRefresh() {
    if (activeTab === "friends") {
      friendsQuery.refetch();
    } else {
      requestsQuery.refetch();
    }
  }

  return (
    <FeltBackground>
      {/* Find Players CTA */}
      <Card
        variant="default"
        padding="compact"
        onPress={() => router.push("/search")}
        style={styles.findPlayersCard}
      >
        <Row align="center" gap="sm">
          <Text variant="body" color="secondary">{"\uD83D\uDD0D"}</Text>
          <Text variant="bodyBold" color="primary">Find Players</Text>
        </Row>
      </Card>

      {/* Tab bar */}
      <View style={styles.tabBar}>
        <Pressable
          style={[styles.tab, activeTab === "friends" && styles.tabActive]}
          onPress={() => setActiveTab("friends")}
        >
          <Text
            variant="captionBold"
            color={activeTab === "friends" ? "primary" : "secondary"}
          >
            Friends {friendsQuery.data ? `(${friendsQuery.data.length})` : ""}
          </Text>
        </Pressable>

        <Pressable
          style={[styles.tab, activeTab === "requests" && styles.tabActive]}
          onPress={() => setActiveTab("requests")}
        >
          <Row align="center" gap="xs">
            <Text
              variant="captionBold"
              color={activeTab === "requests" ? "primary" : "secondary"}
            >
              Requests
            </Text>
            {incomingCount > 0 && (
              <View style={styles.badge}>
                <Text variant="captionBold" color="white" style={styles.badgeText}>
                  {incomingCount}
                </Text>
              </View>
            )}
          </Row>
        </Pressable>
      </View>

      {/* Content */}
      {isLoading ? (
        <FriendsSkeleton />
      ) : activeTab === "friends" ? (
        <FlatList
          data={friendsQuery.data ?? []}
          keyExtractor={(item) => item.friendship_id}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={isRefreshing}
              onRefresh={handleRefresh}
              tintColor={tokens.color.accent.primary}
            />
          }
          ListEmptyComponent={
            <EmptyState
              title="No friends yet"
              description="Search for players and send a friend request"
            />
          }
          renderItem={({ item }) => (
            <View style={styles.rowWrapper}>
              <FriendItem entry={item} />
            </View>
          )}
        />
      ) : (
        <FlatList
          data={requestsQuery.data ?? []}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={isRefreshing}
              onRefresh={handleRefresh}
              tintColor={tokens.color.accent.primary}
            />
          }
          ListEmptyComponent={
            <EmptyState
              title="No pending requests"
              description="Friend requests will appear here"
            />
          }
          renderItem={({ item }) => (
            <View style={styles.rowWrapper}>
              <FriendRequestCard request={item} />
            </View>
          )}
        />
      )}
    </FeltBackground>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const styles = StyleSheet.create({
  findPlayersCard: {
    marginHorizontal: tokens.spacing.lg,
    marginTop: tokens.spacing.md,
    marginBottom: tokens.spacing.sm,
  },
  tabBar: {
    flexDirection: "row",
    borderBottomWidth: 1,
    borderBottomColor: tokens.color.border.subtle,
    marginHorizontal: tokens.spacing.lg,
  },
  tab: {
    flex: 1,
    alignItems: "center",
    paddingVertical: tokens.spacing.md,
  },
  tabActive: {
    borderBottomWidth: 2,
    borderBottomColor: tokens.color.accent.primary,
  },
  badge: {
    backgroundColor: tokens.color.semantic.negative,
    borderRadius: tokens.spacing.sm,
    minWidth: 18,
    height: 18,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: tokens.spacing.xs,
  },
  badgeText: {
    fontSize: 11,
    lineHeight: 13,
  },
  list: {
    paddingHorizontal: tokens.spacing.lg,
    paddingTop: tokens.spacing.md,
    paddingBottom: tokens.spacing["2xl"],
    flexGrow: 1,
  },
  rowWrapper: {
    marginBottom: tokens.spacing.sm,
  },
  nameBlock: {
    flex: 1,
  },
  skeletonContainer: {
    flex: 1,
    padding: tokens.spacing.lg,
    paddingTop: tokens.spacing.md,
  },
});
