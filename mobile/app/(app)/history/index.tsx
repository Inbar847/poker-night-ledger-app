/**
 * History screen — lists the current user's closed games, most recent first.
 *
 * Tap a game card to open the historical settlement detail.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Stack, useRouter } from "expo-router";
import {
  Alert,
  FlatList,
  RefreshControl,
  StyleSheet,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import {
  EmptyState,
  ErrorState,
  FeltBackground,
  GameCard,
  SwipeableGameRow,
  Skeleton,
  Spacer,
  Text,
} from "@/components";
import * as gameService from "@/services/gameService";
import { queryKeys } from "@/lib/queryKeys";
import * as statsService from "@/services/statsService";
import { useAuthStore } from "@/store/authStore";
import { tokens } from "@/theme";
import type { GameHistoryItem } from "@/types/stats";

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

function HistorySkeleton() {
  return (
    <View style={styles.skeletonContainer}>
      <Skeleton width={140} height={18} />
      <Spacer size="md" />
      {[1, 2, 3, 4, 5].map((i) => (
        <View key={i}>
          <Skeleton height={80} radius={tokens.radius.lg} />
          <Spacer size="md" />
        </View>
      ))}
    </View>
  );
}

export default function HistoryScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const userId = useAuthStore((s) => s.userId) ?? "";

  const { data: items, isLoading, error, refetch, isRefetching } = useQuery({
    queryKey: queryKeys.history(userId),
    queryFn: statsService.getHistory,
  });

  const hideMutation = useMutation({
    mutationFn: (gameId: string) => gameService.hideGame(gameId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.history(userId) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.games(userId) });
    },
    onError: (err) => {
      Alert.alert(
        "Error",
        err instanceof Error ? err.message : "Failed to hide game",
      );
    },
  });

  const gameCount = items?.length ?? 0;

  return (
    <FeltBackground>
      <Stack.Screen options={{ title: "My History" }} />

      {isLoading ? (
        <HistorySkeleton />
      ) : error ? (
        <ErrorState
          message="Failed to load history"
          onRetry={() => void refetch()}
        />
      ) : (
        <FlatList
          data={items}
          keyExtractor={(g) => g.game_id}
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={isRefetching}
              onRefresh={refetch}
              tintColor={tokens.color.accent.primary}
            />
          }
          ListHeaderComponent={
            gameCount > 0 ? (
              <View style={styles.listHeader}>
                <Text variant="caption" color="secondary">
                  {gameCount} completed {gameCount === 1 ? "game" : "games"}
                </Text>
                <Spacer size="base" />
              </View>
            ) : null
          }
          renderItem={({ item }) => {
            const net =
              item.net_balance != null ? parseFloat(item.net_balance) : null;

            return (
              <View style={styles.cardWrapper}>
                <SwipeableGameRow
                  onHide={() => hideMutation.mutate(item.game_id)}
                >
                  <GameCard
                    title={item.title}
                    date={formatDate(item.closed_at)}
                    status="closed"
                    netResult={net ?? undefined}
                    currency={item.currency}
                    onPress={() => router.push(`/history/${item.game_id}`)}
                  />
                </SwipeableGameRow>
              </View>
            );
          }}
          ListEmptyComponent={
            <EmptyState
              title="No completed games yet"
              description="Closed games will appear here"
            />
          }
        />
      )}
    </FeltBackground>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  listContent: {
    padding: tokens.spacing.lg,
    paddingBottom: tokens.spacing["4xl"],
    flexGrow: 1,
  },
  listHeader: {
    marginBottom: tokens.spacing.xs,
  },
  cardWrapper: {
    marginBottom: tokens.spacing.md,
  },
  skeletonContainer: {
    padding: tokens.spacing.lg,
  },
});
