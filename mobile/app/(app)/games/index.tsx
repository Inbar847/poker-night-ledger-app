/**
 * Dashboard / home screen — lists the current user's games.
 *
 * Dealer: can create a new game.
 * Anyone: can join via an invite token.
 * Tap a game card to open the game screen.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Stack, useRouter } from "expo-router";
import { Alert, FlatList, StyleSheet, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import {
  Text,
  Button,
  Section,
  Spacer,
  Skeleton,
  EmptyState,
  ErrorState,
  GameCard,
  SwipeableGameRow,
  BottomTabBar,
  Card,
  Badge,
  FeltBackground,
} from "@/components";
import { useUnreadCount } from "@/hooks/useNotifications";
import { queryKeys } from "@/lib/queryKeys";
import * as gameService from "@/services/gameService";
import * as userService from "@/services/userService";
import { useAuthStore } from "@/store/authStore";
import { tokens } from "@/theme";
import type { Game } from "@/types/game";

/** Format ISO date to a short readable string. */
function formatDate(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

/** Skeleton loading state matching the dashboard layout. */
function DashboardSkeleton({ topInset }: { topInset: number }) {
  return (
    <View style={[styles.content, { paddingTop: topInset + tokens.spacing.lg }]}>
      {/* Greeting skeleton */}
      <Skeleton width={180} height={28} />
      <Spacer size="2xl" />

      {/* Active game card skeleton */}
      <Skeleton width={100} height={18} />
      <Spacer size="md" />
      <Skeleton height={100} radius={tokens.radius.xl} />
      <Spacer size="2xl" />

      {/* Quick actions skeleton */}
      <View style={styles.actionRow}>
        <View style={styles.actionHalf}>
          <Skeleton height={tokens.size.buttonMd} radius={tokens.radius.lg} />
        </View>
        <View style={styles.actionHalf}>
          <Skeleton height={tokens.size.buttonMd} radius={tokens.radius.lg} />
        </View>
      </View>
      <Spacer size="2xl" />

      {/* Recent games skeleton */}
      <Skeleton width={120} height={18} />
      <Spacer size="md" />
      <Skeleton height={80} radius={tokens.radius.lg} />
      <Spacer size="md" />
      <Skeleton height={80} radius={tokens.radius.lg} />
    </View>
  );
}

export default function DashboardScreen() {
  const router = useRouter();
  const userId = useAuthStore((s) => s.userId) ?? "";

  const {
    data: games,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: queryKeys.games(userId),
    queryFn: gameService.listGames,
  });

  const { data: me } = useQuery({
    queryKey: queryKeys.me(userId),
    queryFn: userService.getMe,
    staleTime: 5 * 60_000,
  });

  const queryClient = useQueryClient();
  const insets = useSafeAreaInsets();

  const hideMutation = useMutation({
    mutationFn: (gameId: string) => gameService.hideGame(gameId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.games(userId) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.history(userId) });
    },
    onError: (err) => {
      Alert.alert(
        "Error",
        err instanceof Error ? err.message : "Failed to hide game",
      );
    },
  });

  const handleHideGame = (gameId: string, title: string) => {
    hideMutation.mutate(gameId);
  };

  const { data: unreadData } = useUnreadCount();
  const unreadCount = unreadData?.count ?? 0;

  // Split games into active/lobby and recent closed
  const activeGame = games?.find(
    (g) => g.status === "active" || g.status === "lobby"
  );
  const recentGames = games
    ?.filter((g) => g.status === "closed")
    .slice(0, 5);

  const greeting = me?.full_name
    ? `Hey, ${me.full_name.split(" ")[0]}`
    : "Welcome back";

  const handleTabPress = (key: string) => {
    if (key === "home") return; // already here
    if (key === "profile") router.push("/profile");
    if (key === "notifications") router.push("/notifications");
  };

  const renderDashboard = () => {
    if (isLoading) {
      return <DashboardSkeleton topInset={insets.top} />;
    }

    if (error) {
      return (
        <ErrorState
          message="Failed to load games"
          onRetry={() => void refetch()}
        />
      );
    }

    return (
      <FlatList
        data={recentGames ?? []}
        keyExtractor={(g) => g.id}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={[
          styles.listContent,
          { paddingTop: insets.top + tokens.spacing.lg },
        ]}
        ListHeaderComponent={
          <>
            {/* Greeting */}
            <Text variant="h1">{greeting}</Text>
            <Spacer size="xl" />

            {/* Active Game Section */}
            {activeGame && (
              <Section title="Live Game">
                <SwipeableGameRow
                  disabled={activeGame.status === "active"}
                  onHide={() => handleHideGame(activeGame.id, activeGame.title)}
                >
                  <Card
                    variant="prominent"
                    padding="comfortable"
                    onPress={() => router.push(`/games/${activeGame.id}`)}
                  >
                    <View style={styles.activeCardHeader}>
                      <Text variant="bodyBold" numberOfLines={1} style={styles.flex}>
                        {activeGame.title}
                      </Text>
                      <Badge
                        label={activeGame.status === "active" ? "LIVE" : "Lobby"}
                        variant={activeGame.status === "active" ? "accent" : "warning"}
                      />
                    </View>
                    <Spacer size="sm" />
                    <Text variant="caption" color="secondary">
                      {parseFloat(activeGame.chip_cash_rate).toFixed(4)}{" "}
                      {activeGame.currency} / chip
                    </Text>
                    <Spacer size="sm" />
                    <Text variant="caption" color="muted">
                      Tap to continue
                    </Text>
                  </Card>
                </SwipeableGameRow>
                <Spacer size="xl" />
              </Section>
            )}

            {/* Quick Actions */}
            <View style={styles.actionRow}>
              <View style={styles.actionHalf}>
                <Button
                  label="Create Game"
                  variant="primary"
                  fullWidth
                  onPress={() => router.push("/games/create")}
                />
              </View>
              <View style={styles.actionHalf}>
                <Button
                  label="Join Game"
                  variant="secondary"
                  fullWidth
                  onPress={() => router.push("/games/join")}
                />
              </View>
            </View>
            <Spacer size="2xl" />

            {/* Recent Games Section header */}
            {(recentGames?.length ?? 0) > 0 && (
              <Section
                title="Recent"
                action={
                  <Button
                    label="See All"
                    variant="ghost"
                    size="md"
                    onPress={() => router.push("/history")}
                  />
                }
              >
                <View />
              </Section>
            )}
          </>
        }
        renderItem={({ item }) => (
          <View style={styles.gameCardWrapper}>
            <SwipeableGameRow
              onHide={() => handleHideGame(item.id, item.title)}
            >
              <GameCard
                title={item.title}
                date={formatDate(item.created_at)}
                status={item.status}
                currency={item.currency}
                onPress={() => router.push(`/games/${item.id}`)}
              />
            </SwipeableGameRow>
          </View>
        )}
        ListEmptyComponent={
          !activeGame ? (
            <EmptyState
              title="No games yet"
              description="Create your first poker night"
              action={{
                label: "Create Game",
                onPress: () => router.push("/games/create"),
              }}
            />
          ) : null
        }
      />
    );
  };

  return (
    <FeltBackground>
      <Stack.Screen options={{ headerShown: false }} />

      <View style={styles.main}>{renderDashboard()}</View>

      <BottomTabBar
        activeTab="home"
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
  content: {
    flex: 1,
    paddingHorizontal: tokens.spacing.lg,
    paddingTop: tokens.spacing['2xl'],
  },
  listContent: {
    paddingHorizontal: tokens.spacing.lg,
    paddingBottom: tokens.spacing['2xl'],
    flexGrow: 1,
  },
  activeCardHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: tokens.spacing.sm,
  },
  flex: {
    flex: 1,
  },
  actionRow: {
    flexDirection: "row",
    gap: tokens.spacing.md,
  },
  actionHalf: {
    flex: 1,
  },
  gameCardWrapper: {
    marginBottom: tokens.spacing.md,
  },
});
