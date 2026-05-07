/**
 * LeaderboardScreen — Stage 17.
 *
 * Displays the current user + accepted friends ranked by:
 *   - Default: cumulative net result (descending)
 *   - Toggle: win rate (descending)
 *   - Toggle: games played (descending)
 *
 * Only the authenticated user's own friends are ever visible here.
 * Non-friend data is never leaked: the backend enforces this.
 */

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { useState } from "react";
import {
  FlatList,
  Pressable,
  StyleSheet,
  View,
} from "react-native";

import {
  Avatar,
  Card,
  EmptyState,
  ErrorState,
  FeltBackground,
  Row,
  Skeleton,
  Spacer,
  Text,
  MoneyAmount,
} from "@/components";
import { queryKeys } from "@/lib/queryKeys";
import * as socialService from "@/services/socialService";
import type { LeaderboardEntry } from "@/services/socialService";
import { tokens } from "@/theme";

// ---------------------------------------------------------------------------
// Sort types
// ---------------------------------------------------------------------------

type SortKey = "net" | "win_rate" | "games_played";

const SORT_OPTIONS: { key: SortKey; label: string }[] = [
  { key: "net", label: "Net result" },
  { key: "win_rate", label: "Win rate" },
  { key: "games_played", label: "Games played" },
];

// ---------------------------------------------------------------------------
// Sorting helper
// ---------------------------------------------------------------------------

function sortEntries(
  entries: LeaderboardEntry[],
  sortKey: SortKey
): LeaderboardEntry[] {
  const copy = [...entries];

  copy.sort((a, b) => {
    if (sortKey === "net") {
      const diff =
        parseFloat(b.cumulative_net) - parseFloat(a.cumulative_net);
      if (diff !== 0) return diff;
      const wrDiff = (b.win_rate ?? -1) - (a.win_rate ?? -1);
      if (wrDiff !== 0) return wrDiff;
      return b.total_games_played - a.total_games_played;
    }
    if (sortKey === "win_rate") {
      const wrDiff = (b.win_rate ?? -1) - (a.win_rate ?? -1);
      if (wrDiff !== 0) return wrDiff;
      return (
        parseFloat(b.cumulative_net) - parseFloat(a.cumulative_net)
      );
    }
    // games_played
    const gpDiff = b.total_games_played - a.total_games_played;
    if (gpDiff !== 0) return gpDiff;
    return parseFloat(b.cumulative_net) - parseFloat(a.cumulative_net);
  });

  return copy.map((e, i) => ({ ...e, rank: i + 1 }));
}

// ---------------------------------------------------------------------------
// Rank badge colors
// ---------------------------------------------------------------------------

const RANK_COLORS: Record<number, string> = {
  1: "#F1C40F",
  2: "#A0AEB8",
  3: "#CD7F32",
};

// ---------------------------------------------------------------------------
// LeaderboardRow
// ---------------------------------------------------------------------------

function LeaderboardRow({
  entry,
  sortKey,
}: {
  entry: LeaderboardEntry;
  sortKey: SortKey;
}) {
  const router = useRouter();
  const net = parseFloat(entry.cumulative_net);
  const winRateStr =
    entry.win_rate != null
      ? `${(entry.win_rate * 100).toFixed(0)}%`
      : "\u2014";

  const rankBg = RANK_COLORS[entry.rank ?? 0] ?? tokens.color.text.muted;

  const handlePress = () => {
    if (!entry.is_self) {
      router.push(`/public-profile/${entry.user_id}`);
    }
  };

  return (
    <Card
      variant={entry.is_self ? "prominent" : "default"}
      padding="compact"
      onPress={handlePress}
      style={entry.is_self ? styles.selfCard : undefined}
    >
      <Row align="center" gap="md">
        {/* Rank */}
        <View style={[styles.rankBadge, { backgroundColor: rankBg }]}>
          <Text
            variant="captionBold"
            style={styles.rankText}
          >
            {entry.rank}
          </Text>
        </View>

        {/* Avatar */}
        <Avatar
          uri={entry.profile_image_url}
          name={entry.full_name ?? "?"}
          size="md"
        />

        {/* Name + meta */}
        <View style={styles.nameBlock}>
          <Text variant="bodyBold" numberOfLines={1}>
            {entry.full_name ?? "Unknown"}
            {entry.is_self ? " (you)" : ""}
          </Text>
          <Text variant="caption" color="muted">
            {entry.total_games_played} game
            {entry.total_games_played !== 1 ? "s" : ""}
          </Text>
        </View>

        {/* Primary stat */}
        <View style={styles.statBlock}>
          {sortKey === "net" && (
            entry.games_with_result > 0 ? (
              <MoneyAmount amount={net} size="sm" showSign />
            ) : (
              <Text variant="body" color="muted">{"\u2014"}</Text>
            )
          )}
          {sortKey === "win_rate" && (
            <Text variant="numeric" color="primary">
              {winRateStr}
            </Text>
          )}
          {sortKey === "games_played" && (
            <Text variant="numeric" color="primary">
              {entry.total_games_played}
            </Text>
          )}
          <Text variant="caption" color="muted">
            {sortKey === "net"
              ? "net"
              : sortKey === "win_rate"
              ? "win rate"
              : "played"}
          </Text>
        </View>
      </Row>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Loading skeleton
// ---------------------------------------------------------------------------

function LeaderboardSkeleton() {
  return (
    <View style={styles.skeletonContainer}>
      <Skeleton width={200} height={16} />
      <Spacer size="lg" />
      {[1, 2, 3, 4, 5].map((i) => (
        <View key={i}>
          <Skeleton height={64} radius={tokens.radius.lg} />
          <Spacer size="md" />
        </View>
      ))}
    </View>
  );
}

// ---------------------------------------------------------------------------
// Main screen
// ---------------------------------------------------------------------------

export default function LeaderboardScreen() {
  const [sortKey, setSortKey] = useState<SortKey>("net");

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: queryKeys.leaderboard,
    queryFn: socialService.getLeaderboard,
  });

  if (isLoading) {
    return (
      <FeltBackground>
        <LeaderboardSkeleton />
      </FeltBackground>
    );
  }

  if (error || !data) {
    return (
      <FeltBackground>
        <ErrorState
          message="Failed to load leaderboard"
          onRetry={() => void refetch()}
        />
      </FeltBackground>
    );
  }

  const sorted = sortEntries(data.entries, sortKey);

  return (
    <FeltBackground>
      {/* Sort toggle */}
      <View style={styles.sortRow}>
        {SORT_OPTIONS.map((opt) => {
          const active = sortKey === opt.key;
          return (
            <Pressable
              key={opt.key}
              style={[
                styles.sortBtn,
                active && styles.sortBtnActive,
              ]}
              onPress={() => setSortKey(opt.key)}
            >
              <Text
                variant="captionBold"
                color={active ? "white" : "secondary"}
              >
                {opt.label}
              </Text>
            </Pressable>
          );
        })}
      </View>

      {sorted.length === 0 ? (
        <EmptyState
          title="No data available"
          description="Play some games with friends to see rankings"
        />
      ) : (
        <FlatList
          data={sorted}
          keyExtractor={(e) => e.user_id}
          renderItem={({ item }) => (
            <View style={styles.rowWrapper}>
              <LeaderboardRow entry={item} sortKey={sortKey} />
            </View>
          )}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
        />
      )}

      <Text variant="caption" color="muted" align="center" style={styles.privacyNote}>
        Only your accepted friends are included
      </Text>
    </FeltBackground>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const styles = StyleSheet.create({
  // Sort toggle
  sortRow: {
    flexDirection: "row",
    paddingHorizontal: tokens.spacing.lg,
    paddingVertical: tokens.spacing.md,
    gap: tokens.spacing.sm,
  },
  sortBtn: {
    flex: 1,
    paddingVertical: tokens.spacing.sm,
    borderRadius: tokens.radius.md,
    backgroundColor: tokens.color.bg.elevated,
    alignItems: "center",
    borderWidth: 1,
    borderColor: tokens.color.border.subtle,
  },
  sortBtnActive: {
    backgroundColor: tokens.color.accent.primary,
    borderColor: tokens.color.accent.primary,
  },

  // List
  list: {
    paddingHorizontal: tokens.spacing.lg,
    paddingBottom: tokens.spacing["2xl"],
  },
  rowWrapper: {
    marginBottom: tokens.spacing.sm,
  },

  // Row internals
  selfCard: {
    borderWidth: 1,
    borderColor: tokens.color.accent.primary,
  },
  rankBadge: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
  },
  rankText: {
    color: tokens.color.bg.primary,
    fontSize: 13,
  },
  nameBlock: {
    flex: 1,
  },
  statBlock: {
    alignItems: "flex-end",
  },

  // Privacy footer
  privacyNote: {
    paddingBottom: tokens.spacing.md,
  },

  // Skeleton
  skeletonContainer: {
    flex: 1,
    padding: tokens.spacing.lg,
    paddingTop: tokens.spacing["2xl"],
  },
});
