/**
 * PublicProfileScreen — view another user's public profile.
 *
 * Shows:
 *  - Avatar (image or initials fallback)
 *  - Display name
 *  - Games played (always visible)
 *  - Full stats block → when viewer is self or an accepted friend (is_friend_access: true)
 *  - Locked placeholder → when viewer is not a friend (is_friend_access: false)
 *  - Friendship action button (Add Friend / Pending / Friends / Accept):
 *      not_friends      → "Add Friend" button → sends request
 *      pending_outgoing → "Request Sent" label (disabled)
 *      pending_incoming → "Accept Request" button → accepts request
 *      friends          → "Friends" label + unfriend option
 *
 * The privacy gate is enforced on the backend. This screen simply renders what
 * the API returns in UserStatsView.is_friend_access.
 */

import { useQuery } from "@tanstack/react-query";
import { ActivityIndicator, Alert, Image, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import {
  useAcceptFriendRequest,
  useFriendshipStatus,
  useRemoveFriend,
  useSendFriendRequest,
} from "@/hooks/useFriends";
import { queryKeys } from "@/lib/queryKeys";
import { getPublicProfile, getUserStats } from "@/services/userService";
import { useAuthStore } from "@/store/authStore";
import { tokens } from "@/theme";

interface PublicProfileScreenProps {
  userId: string;
}

// ---------------------------------------------------------------------------
// Friendship action button
// ---------------------------------------------------------------------------

function FriendshipButton({ userId }: { userId: string }) {
  const { data: statusData, isLoading } = useFriendshipStatus(userId);
  const sendRequest = useSendFriendRequest(userId);
  const acceptRequest = useAcceptFriendRequest();
  const removeFriend = useRemoveFriend(userId);

  if (isLoading) {
    return <ActivityIndicator color={tokens.color.accent.primary} style={{ marginBottom: 20 }} />;
  }

  const status = statusData?.status ?? "not_friends";
  const friendshipId = statusData?.friendship_id ?? null;

  const isMutating =
    sendRequest.isPending || acceptRequest.isPending || removeFriend.isPending;

  if (status === "not_friends") {
    return (
      <Pressable
        style={[styles.friendBtn, styles.addFriendBtn, isMutating && styles.btnDisabled]}
        onPress={() => sendRequest.mutate(userId)}
        disabled={isMutating}
      >
        {isMutating ? (
          <ActivityIndicator color={tokens.color.white} size="small" />
        ) : (
          <Text style={styles.friendBtnText}>Add Friend</Text>
        )}
      </Pressable>
    );
  }

  if (status === "pending_outgoing") {
    return (
      <View style={[styles.friendBtn, styles.pendingBtn]}>
        <Text style={styles.pendingBtnText}>Request Sent</Text>
      </View>
    );
  }

  if (status === "pending_incoming") {
    return (
      <Pressable
        style={[styles.friendBtn, styles.acceptBtn, isMutating && styles.btnDisabled]}
        onPress={() => friendshipId && acceptRequest.mutate(friendshipId)}
        disabled={isMutating || !friendshipId}
      >
        {isMutating ? (
          <ActivityIndicator color={tokens.color.white} size="small" />
        ) : (
          <Text style={styles.friendBtnText}>Accept Request</Text>
        )}
      </Pressable>
    );
  }

  // status === "friends"
  return (
    <Pressable
      style={[styles.friendBtn, styles.friendsBtn]}
      onPress={() => {
        Alert.alert("Unfriend", "Remove this player from your friends?", [
          { text: "Cancel", style: "cancel" },
          {
            text: "Unfriend",
            style: "destructive",
            onPress: () => friendshipId && removeFriend.mutate(friendshipId),
          },
        ]);
      }}
      disabled={isMutating}
    >
      <Text style={styles.friendsBtnText}>Friends ✓</Text>
    </Pressable>
  );
}

// ---------------------------------------------------------------------------
// Main screen
// ---------------------------------------------------------------------------

export default function PublicProfileScreen({ userId }: PublicProfileScreenProps) {
  const currentUserId = useAuthStore((s) => s.userId);
  const isSelf = currentUserId === userId;

  const {
    data: profile,
    isLoading: profileLoading,
    error: profileError,
  } = useQuery({
    queryKey: queryKeys.publicProfile(userId),
    queryFn: () => getPublicProfile(userId),
    staleTime: 30_000,
  });

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: queryKeys.userStats(userId),
    queryFn: () => getUserStats(userId),
    enabled: !!profile,
    staleTime: 30_000,
  });

  if (profileLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator color={tokens.color.accent.primary} />
      </View>
    );
  }

  if (profileError || !profile) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorText}>User not found.</Text>
      </View>
    );
  }

  const displayName = profile.full_name ?? "Unknown Player";
  const initials = displayName.charAt(0).toUpperCase();

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Avatar */}
      <View style={styles.avatarSection}>
        {profile.profile_image_url ? (
          <Image source={{ uri: profile.profile_image_url }} style={styles.avatarImage} />
        ) : (
          <View style={styles.avatarFallback}>
            <Text style={styles.avatarInitials}>{initials}</Text>
          </View>
        )}
        <Text style={styles.displayName}>{displayName}</Text>
      </View>

      {/* Friendship button — only shown when viewing another user's profile */}
      {!isSelf && <FriendshipButton userId={userId} />}

      {/* Stats section */}
      {statsLoading ? (
        <ActivityIndicator color={tokens.color.accent.primary} style={{ marginTop: 24 }} />
      ) : stats ? (
        <View style={styles.statsSection}>
          {/* Always-visible stat */}
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{stats.total_games_played}</Text>
            <Text style={styles.statLabel}>Games Played</Text>
          </View>

          {stats.is_friend_access ? (
            /* Full stats block */
            <>
              <View style={styles.statRow}>
                <View style={styles.statCard}>
                  <Text style={styles.statValue}>{stats.total_games_hosted ?? 0}</Text>
                  <Text style={styles.statLabel}>Games Hosted</Text>
                </View>
                <View style={styles.statCard}>
                  <Text style={styles.statValue}>
                    {stats.win_rate != null ? `${(stats.win_rate * 100).toFixed(0)}%` : "—"}
                  </Text>
                  <Text style={styles.statLabel}>Win Rate</Text>
                </View>
              </View>

              <View style={styles.netCard}>
                <Text style={styles.netLabel}>Cumulative Net</Text>
                <Text
                  style={[
                    styles.netValue,
                    stats.cumulative_net != null && parseFloat(stats.cumulative_net) >= 0
                      ? styles.positive
                      : styles.negative,
                  ]}
                >
                  {stats.cumulative_net != null
                    ? `${parseFloat(stats.cumulative_net) >= 0 ? "+" : ""}${parseFloat(stats.cumulative_net).toFixed(2)}`
                    : "—"}
                </Text>
              </View>

              {stats.average_net != null && (
                <View style={styles.metaRow}>
                  <Text style={styles.metaLabel}>Average per game</Text>
                  <Text
                    style={[
                      styles.metaValue,
                      parseFloat(stats.average_net) >= 0 ? styles.positive : styles.negative,
                    ]}
                  >
                    {`${parseFloat(stats.average_net) >= 0 ? "+" : ""}${parseFloat(stats.average_net).toFixed(2)}`}
                  </Text>
                </View>
              )}

              {stats.profitable_games != null && stats.games_with_result != null && (
                <View style={styles.metaRow}>
                  <Text style={styles.metaLabel}>Profitable games</Text>
                  <Text style={styles.metaValue}>
                    {stats.profitable_games} / {stats.games_with_result}
                  </Text>
                </View>
              )}
            </>
          ) : (
            /* Locked placeholder for non-friends */
            <View style={styles.lockedBlock}>
              <Text style={styles.lockIcon}>🔒</Text>
              <Text style={styles.lockedTitle}>Friend-only stats</Text>
              <Text style={styles.lockedSubtitle}>
                Add this player as a friend to see their full statistics.
              </Text>
            </View>
          )}
        </View>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: tokens.color.bg.primary },
  content: { padding: tokens.spacing.lg },
  centered: { flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: tokens.color.bg.primary },
  errorText: { color: tokens.color.semantic.negative, fontSize: 16 },

  avatarSection: { alignItems: "center", marginBottom: tokens.spacing.base },
  avatarImage: { width: 96, height: 96, borderRadius: 48, marginBottom: tokens.spacing.md },
  avatarFallback: {
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: tokens.color.accent.primary,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: tokens.spacing.md,
  },
  avatarInitials: { color: tokens.color.white, fontSize: 40, fontWeight: "700" },
  displayName: { color: tokens.color.text.primary, fontSize: 22, fontWeight: "700" },

  // Friendship button styles
  friendBtn: {
    borderRadius: tokens.radius.md,
    paddingVertical: 10,
    paddingHorizontal: 20,
    alignItems: "center",
    alignSelf: "center",
    marginBottom: tokens.spacing.lg,
    minWidth: 160,
  },
  addFriendBtn: { backgroundColor: tokens.color.accent.primary },
  pendingBtn: { backgroundColor: tokens.color.bg.surface },
  acceptBtn: { backgroundColor: tokens.color.semantic.positive },
  friendsBtn: { backgroundColor: tokens.color.bg.elevated, borderWidth: 1, borderColor: tokens.color.border.default },
  friendBtnText: { color: tokens.color.white, fontSize: 15, fontWeight: "600" },
  pendingBtnText: { color: tokens.color.text.muted, fontSize: 15 },
  friendsBtnText: { color: tokens.color.text.secondary, fontSize: 15 },
  btnDisabled: { opacity: 0.6 },

  statsSection: { gap: tokens.spacing.md },
  statRow: { flexDirection: "row", gap: tokens.spacing.md },
  statCard: {
    flex: 1,
    backgroundColor: tokens.color.bg.elevated,
    borderRadius: tokens.radius.md,
    padding: tokens.spacing.base,
    alignItems: "center",
  },
  statValue: { color: tokens.color.text.primary, fontSize: 26, fontWeight: "700" },
  statLabel: { color: tokens.color.text.secondary, fontSize: 12, marginTop: 4 },

  netCard: {
    backgroundColor: tokens.color.bg.elevated,
    borderRadius: tokens.radius.md,
    padding: tokens.spacing.base,
    alignItems: "center",
  },
  netLabel: { color: tokens.color.text.secondary, fontSize: 13, marginBottom: 4 },
  netValue: { fontSize: 28, fontWeight: "700" },
  positive: { color: tokens.color.semantic.positive },
  negative: { color: tokens.color.semantic.negative },

  metaRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    backgroundColor: tokens.color.bg.elevated,
    borderRadius: tokens.radius.md,
    paddingHorizontal: tokens.spacing.base,
    paddingVertical: 10,
  },
  metaLabel: { color: tokens.color.text.secondary, fontSize: 14 },
  metaValue: { color: tokens.color.text.primary, fontSize: 14, fontWeight: "600" },

  lockedBlock: {
    backgroundColor: tokens.color.bg.elevated,
    borderRadius: tokens.radius.md,
    padding: 28,
    alignItems: "center",
    gap: tokens.spacing.sm,
    marginTop: tokens.spacing.sm,
  },
  lockIcon: { fontSize: 36 },
  lockedTitle: { color: tokens.color.text.primary, fontSize: 16, fontWeight: "700" },
  lockedSubtitle: { color: tokens.color.text.secondary, fontSize: 13, textAlign: "center", lineHeight: 20 },
});
