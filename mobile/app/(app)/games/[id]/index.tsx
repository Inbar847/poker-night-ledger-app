/**
 * Main game screen — adapts to game status (lobby / active / closed).
 *
 * Lobby:  participant list, dealer can add guests, generate invite link, start game.
 * Active: buy-ins summary, expenses summary, dealer entry buttons, close game.
 * Closed: settlement button, read-only summary.
 *
 * WebSocket is connected the entire time this screen is mounted.
 * Mutations invalidate queries; WebSocket events independently invalidate on
 * updates from other clients, so live updates work for all participants.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Stack, useLocalSearchParams, useRouter } from "expo-router";
import { useState } from "react";
import {
  Alert,
  Modal,
  Pressable,
  StyleSheet,
  View,
} from "react-native";
import * as Clipboard from "expo-clipboard";
import { ApiError } from "@/lib/apiClient";
import type { Game, MissingFinalStack, ShortageStrategy } from "@/types/game";

import {
  Text,
  Button,
  Card,
  Badge,
  Input,
  Spacer,
  Divider,
  Screen,
  Section,
  Row,
  ParticipantRow,
  MoneyAmount,
  Skeleton,
  EmptyState,
  ErrorState,
  currencySymbol,
} from "@/components";

import CashoutModal from "@/features/cashout/CashoutModal";
import InviteFriendModal from "@/features/invitations/InviteFriendModal";
import { useGameInvitations } from "@/hooks/useGameInvitations";
import { useGameSocket } from "@/hooks/useGameSocket";
import { queryKeys } from "@/lib/queryKeys";
import * as gameService from "@/services/gameService";
import * as ledgerService from "@/services/ledgerService";
import * as userService from "@/services/userService";
import { useAuthStore } from "@/store/authStore";
import { tokens } from "@/theme";
import type { BuyIn, Expense, Participant } from "@/types/game";
import type { GameInvitation } from "@/types/gameInvitation";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function totalBuyInsForParticipant(
  buyIns: BuyIn[],
  participantId: string,
): number {
  const totalCents = buyIns
    .filter((b) => b.participant_id === participantId)
    .reduce((sum, b) => sum + Math.round(parseFloat(b.cash_amount) * 100), 0);
  return totalCents / 100;
}

function getParticipantRole(
  p: Participant,
): "dealer" | "guest" | null {
  if (p.role_in_game === "dealer") return "dealer";
  if (p.participant_type === "guest") return "guest";
  return null;
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function BuyInRow({
  buyIn,
  participantName,
  currency,
}: {
  buyIn: BuyIn;
  participantName: string;
  currency: string;
}) {
  return (
    <View style={subStyles.ledgerRow}>
      <Text variant="body" numberOfLines={1} style={subStyles.ledgerFlex}>
        {participantName}
      </Text>
      <Badge
        label={buyIn.buy_in_type === "initial" ? "Initial" : "Re-buy"}
        variant="neutral"
      />
      <MoneyAmount amount={parseFloat(buyIn.cash_amount)} currency={currency} size="sm" />
    </View>
  );
}

function ExpenseRow({
  expense,
  currency,
  canDelete,
  onDelete,
}: {
  expense: Expense;
  currency: string;
  canDelete: boolean;
  onDelete: (expenseId: string) => void;
}) {
  return (
    <View style={subStyles.ledgerRow}>
      <Text variant="body" numberOfLines={1} style={subStyles.ledgerFlex}>
        {expense.title}
      </Text>
      <MoneyAmount amount={parseFloat(expense.total_amount)} currency={currency} size="sm" />
      {canDelete ? (
        <Pressable
          style={subStyles.deleteBtn}
          hitSlop={8}
          onPress={() =>
            Alert.alert(
              "Delete Expense",
              `Delete "${expense.title}"?`,
              [
                { text: "Cancel", style: "cancel" },
                {
                  text: "Delete",
                  style: "destructive",
                  onPress: () => onDelete(expense.id),
                },
              ],
            )
          }
        >
          <Text variant="captionBold" color="negative">✕</Text>
        </Pressable>
      ) : null}
    </View>
  );
}

// ---------------------------------------------------------------------------
// Add guest inline form
// ---------------------------------------------------------------------------

function AddGuestForm({
  gameId,
  onDone,
}: {
  gameId: string;
  onDone: () => void;
}) {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");

  const mutation = useMutation({
    mutationFn: () => gameService.addGuest(gameId, name.trim()),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.participants(gameId),
      });
      setName("");
      onDone();
    },
  });

  return (
    <View style={subStyles.inlineForm}>
      <View style={subStyles.inlineInputWrapper}>
        <Input
          placeholder="Guest name"
          value={name}
          onChangeText={setName}
        />
      </View>
      <Button
        label="Add"
        variant="primary"
        size="md"
        loading={mutation.isPending}
        disabled={!name.trim() || mutation.isPending}
        onPress={() => mutation.mutate()}
      />
      <Button
        label="Cancel"
        variant="ghost"
        size="md"
        onPress={onDone}
      />
    </View>
  );
}

// ---------------------------------------------------------------------------
// Shortage modal
// ---------------------------------------------------------------------------

function ShortageModal({
  visible,
  shortageAmount,
  currency,
  isPending,
  onChoose,
  onCancel,
}: {
  visible: boolean;
  shortageAmount: string;
  currency: string;
  isPending: boolean;
  onChoose: (strategy: ShortageStrategy) => void;
  onCancel: () => void;
}) {
  const amt = parseFloat(shortageAmount).toFixed(2);

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onCancel}
    >
      <View style={shortageStyles.overlay}>
        <Card variant="prominent" padding="comfortable" style={shortageStyles.sheet}>
          <Text variant="h3">Settlement Shortage</Text>
          <Spacer size="md" />
          <Text variant="body" color="secondary">
            There is a shortage of {currency} {amt} in the pot.{"\n"}
            Choose how to distribute it among participants.
          </Text>
          <Spacer size="lg" />

          <Pressable
            style={[shortageStyles.option, isPending && shortageStyles.optionDisabled]}
            disabled={isPending}
            onPress={() => onChoose("proportional_winners")}
          >
            <Text variant="bodyBold" color="primary">Proportional (recommended)</Text>
            <Spacer size="xs" />
            <Text variant="caption" color="secondary">
              Only winners absorb the shortage, proportional to their winnings.
            </Text>
          </Pressable>

          <Spacer size="sm" />

          <Pressable
            style={[shortageStyles.option, isPending && shortageStyles.optionDisabled]}
            disabled={isPending}
            onPress={() => onChoose("equal_all")}
          >
            <Text variant="bodyBold" color="primary">Equal split</Text>
            <Spacer size="xs" />
            <Text variant="caption" color="secondary">
              All participants absorb an equal share of the shortage.
            </Text>
          </Pressable>

          <Spacer size="base" />
          <Button
            label="Cancel"
            variant="ghost"
            onPress={onCancel}
            disabled={isPending}
          />
        </Card>
      </View>
    </Modal>
  );
}

// ---------------------------------------------------------------------------
// Skeleton for loading state
// ---------------------------------------------------------------------------

function GameScreenSkeleton() {
  return (
    <Screen scrollable>
      <Spacer size="base" />
      {/* Status row skeleton */}
      <Row gap="md" align="center">
        <Skeleton width={60} height={22} radius={tokens.radius.sm} />
        <Skeleton width={140} height={16} />
      </Row>
      <Spacer size="lg" />
      {/* Hero totals card skeleton */}
      <Skeleton height={100} radius={tokens.radius.xl} />
      <Spacer size="xl" />
      {/* Player list skeleton */}
      <Skeleton width={80} height={20} />
      <Spacer size="md" />
      <Skeleton height={tokens.size.listItemStandard} radius={tokens.radius.lg} />
      <Spacer size="sm" />
      <Skeleton height={tokens.size.listItemStandard} radius={tokens.radius.lg} />
      <Spacer size="sm" />
      <Skeleton height={tokens.size.listItemStandard} radius={tokens.radius.lg} />
      <Spacer size="xl" />
      {/* Action buttons skeleton */}
      <Row gap="md">
        <View style={subStyles.flexOne}>
          <Skeleton height={tokens.size.buttonLg} radius={tokens.radius.lg} />
        </View>
        <View style={subStyles.flexOne}>
          <Skeleton height={tokens.size.buttonLg} radius={tokens.radius.lg} />
        </View>
      </Row>
    </Screen>
  );
}

// ---------------------------------------------------------------------------
// Main screen
// ---------------------------------------------------------------------------

export default function GameScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const userId = useAuthStore((s) => s.userId) ?? "";

  // Live updates
  const { reconnecting } = useGameSocket(id);

  const [showAddGuest, setShowAddGuest] = useState(false);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showCashoutModal, setShowCashoutModal] = useState(false);
  const [shortageModal, setShortageModal] = useState<{
    visible: boolean;
    amount: string;
  }>({ visible: false, amount: "0" });
  const [generatedToken, setGeneratedToken] = useState<string | null>(null);
  const [tokenCopied, setTokenCopied] = useState(false);

  // Queries
  const {
    data: game,
    isLoading: gameLoading,
    error: gameError,
    refetch: refetchGame,
  } = useQuery({
    queryKey: queryKeys.game(id),
    queryFn: () => gameService.getGame(id),
    enabled: !!id,
  });

  const { data: participants = [] } = useQuery({
    queryKey: queryKeys.participants(id),
    queryFn: () => gameService.getParticipants(id),
    enabled: !!id,
  });

  const { data: buyIns = [] } = useQuery({
    queryKey: queryKeys.buyIns(id),
    queryFn: () => ledgerService.listBuyIns(id),
    enabled: !!id && game?.status === "active",
  });

  const { data: expenses = [] } = useQuery({
    queryKey: queryKeys.expenses(id),
    queryFn: () => ledgerService.listExpenses(id),
    enabled: !!id && game?.status === "active",
  });

  const { data: me } = useQuery({
    queryKey: queryKeys.me(userId),
    queryFn: userService.getMe,
  });

  // Pending invitations for the game lobby (dealer view)
  const { data: pendingInvitations = [] } = useGameInvitations(id);

  // The current user is the dealer if their user_id matches game.dealer_user_id.
  const isDealer = !!(me && game && me.id === game.dealer_user_id);

  // Find the current user's participant record for status checks
  const myParticipant = participants.find((p) => p.user_id === me?.id);
  const canCashOut =
    !isDealer &&
    game?.status === "active" &&
    myParticipant?.status === "active";

  // Build a map of participant id → display_name for quick lookup in buy-in rows
  const participantMap = Object.fromEntries(
    participants.map((p) => [p.id, p.display_name]),
  );

  // ---------------------------------------------------------------------------
  // Mutations
  // ---------------------------------------------------------------------------

  const startMutation = useMutation({
    mutationFn: () => gameService.startGame(id),
    onSuccess: (updated) => {
      queryClient.setQueryData(queryKeys.game(id), updated);
      void queryClient.invalidateQueries({ queryKey: queryKeys.games(userId) });
    },
    onError: (err) => {
      Alert.alert(
        "Error",
        err instanceof Error ? err.message : "Failed to start game",
      );
    },
  });

  const closeMutation = useMutation({
    mutationFn: (strategy?: ShortageStrategy) =>
      gameService.closeGame(id, strategy),
    onSuccess: (result) => {
      setShortageModal({ visible: false, amount: "0" });
      if ("status" in result && (result as Game).status === "closed") {
        queryClient.setQueryData(queryKeys.game(id), result);
      }
      void queryClient.invalidateQueries({ queryKey: queryKeys.games(userId) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.game(id) });
    },
    onError: (err) => {
      setShortageModal({ visible: false, amount: "0" });

      if (err instanceof ApiError && err.data?.missing_final_stacks) {
        const missing = err.data.missing_final_stacks as MissingFinalStack[];
        const names = missing.map((m) => m.display_name).join(", ");
        Alert.alert(
          "Cannot Close Game",
          `Missing final chip counts for:\n${names}`,
        );
        return;
      }

      Alert.alert(
        "Error",
        err instanceof Error ? err.message : "Failed to close game",
      );
    },
  });

  async function handleCloseGame() {
    Alert.alert(
      "Close Game",
      "Close the game and generate settlement? This cannot be undone.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Close",
          style: "destructive",
          onPress: async () => {
            try {
              const preview = await gameService.getShortagePreview(id);
              if (preview.has_shortage) {
                setShortageModal({
                  visible: true,
                  amount: preview.shortage_amount,
                });
              } else {
                closeMutation.mutate(undefined);
              }
            } catch {
              closeMutation.mutate(undefined);
            }
          },
        },
      ],
    );
  }

  const inviteMutation = useMutation({
    mutationFn: () => gameService.generateInviteLink(id),
    onSuccess: (data) => {
      setGeneratedToken(data.invite_token);
      setTokenCopied(false);
    },
    onError: (err) => {
      Alert.alert(
        "Error",
        err instanceof Error ? err.message : "Failed to generate invite link",
      );
    },
  });

  // Only show the token after the user explicitly generates it
  const inviteTokenDisplay = generatedToken;

  const handleCopyToken = async () => {
    if (!inviteTokenDisplay) return;
    await Clipboard.setStringAsync(inviteTokenDisplay);
    setTokenCopied(true);
    setTimeout(() => setTokenCopied(false), 2000);
  };

  const deleteExpenseMutation = useMutation({
    mutationFn: (expenseId: string) => ledgerService.deleteExpense(id, expenseId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.expenses(id) });
    },
    onError: (err) => {
      Alert.alert(
        "Error",
        err instanceof Error ? err.message : "Failed to delete expense",
      );
    },
  });

  // ---------------------------------------------------------------------------
  // Loading / error states
  // ---------------------------------------------------------------------------

  if (gameLoading) {
    return (
      <>
        <Stack.Screen options={{ title: "Game" }} />
        <GameScreenSkeleton />
      </>
    );
  }

  if (gameError || !game) {
    return (
      <>
        <Stack.Screen options={{ title: "Game" }} />
        <Screen>
          <ErrorState
            message="Failed to load game"
            onRetry={() => void refetchGame()}
          />
        </Screen>
      </>
    );
  }

  // ---------------------------------------------------------------------------
  // Computed values
  // ---------------------------------------------------------------------------

  const totalBuyIns =
    buyIns.reduce((sum, b) => sum + Math.round(parseFloat(b.cash_amount) * 100), 0) / 100;
  const totalChips =
    buyIns.reduce((sum, b) => sum + Math.round(parseFloat(b.chips_amount) * 100), 0) / 100;
  const totalExpenses =
    expenses.reduce((sum, e) => sum + Math.round(parseFloat(e.total_amount) * 100), 0) / 100;

  // Count active participants (not left_early)
  const activePlayerCount = participants.filter(
    (p) => p.status === "active",
  ).length;

  // ---------------------------------------------------------------------------
  // Render — Active game (dealer + player views)
  // ---------------------------------------------------------------------------

  function renderActiveGame() {
    return (
      <>
        {/* ── Hero totals card ─────────────────────────────────── */}
        <Card variant="prominent" padding="comfortable" style={activeStyles.heroCard}>
          <Text variant="caption" color="secondary">
            Total Pot
          </Text>
          <Spacer size="xs" />
          <MoneyAmount amount={totalBuyIns} currency={game!.currency} size="lg" />
          {totalChips > 0 && (
            <>
              <Spacer size="xs" />
              <Text variant="caption" color="muted">
                {totalChips.toLocaleString()} chips
              </Text>
            </>
          )}
          <Spacer size="sm" />
          <Row gap="md" align="center">
            <Text variant="caption" color="muted">
              {activePlayerCount} active player{activePlayerCount !== 1 ? "s" : ""}
            </Text>
            {totalExpenses > 0 && (
              <>
                <Text variant="caption" color="muted">·</Text>
                <Text variant="caption" color="muted">
                  {game!.currency} {totalExpenses.toFixed(2)} expenses
                </Text>
              </>
            )}
          </Row>
        </Card>

        <Spacer size="xl" />

        {/* ── Dealer quick actions ─────────────────────────────── */}
        {isDealer && (
          <>
            <Row gap="md" style={activeStyles.quickActions}>
              <View style={subStyles.flexOne}>
                <Button
                  label="Add Buy-In"
                  variant="primary"
                  size="lg"
                  fullWidth
                  onPress={() => router.push(`/games/${id}/buy-in`)}
                />
              </View>
              <View style={subStyles.flexOne}>
                <Button
                  label="Add Expense"
                  variant="secondary"
                  size="lg"
                  fullWidth
                  onPress={() => router.push(`/games/${id}/expense`)}
                />
              </View>
            </Row>
            <Spacer size="xl" />
          </>
        )}

        {/* ── Player: Add Expense only ─────────────────────────── */}
        {!isDealer && myParticipant?.status === "active" && (
          <>
            <Button
              label="Add Expense"
              variant="secondary"
              size="lg"
              fullWidth
              onPress={() => router.push(`/games/${id}/expense`)}
            />
            <Spacer size="xl" />
          </>
        )}

        {/* ── Players section ──────────────────────────────────── */}
        <Section title="Players" subtitle={`${participants.length} at the table`}>
          {participants.length === 0 ? (
            <EmptyState
              title="No players yet"
              description="Invite friends or add guests to get started"
            />
          ) : (
            <Card variant="default" padding="none">
              {participants.map((p, idx) => {
                const pBuyInTotal = totalBuyInsForParticipant(buyIns, p.id);
                return (
                  <View key={p.id}>
                    {idx > 0 && <Divider subtle />}
                    <ParticipantRow
                      name={p.display_name}
                      role={getParticipantRole(p)}
                      highlighted={p.user_id === me?.id}
                      trailingContent={
                        <Row gap="sm" align="center">
                          {p.status === "left_early" && (
                            <Badge label="Left Early" variant="warning" />
                          )}
                          {pBuyInTotal > 0 && (
                            <MoneyAmount
                              amount={pBuyInTotal}
                              currency={game!.currency}
                              size="sm"
                            />
                          )}
                        </Row>
                      }
                    />
                  </View>
                );
              })}
            </Card>
          )}
        </Section>

        {/* Pending invitations (dealer view) */}
        {isDealer && pendingInvitations.length > 0 && (
          <Section title="Pending Invitations">
            <Card variant="default" padding="none">
              {pendingInvitations.map((inv: GameInvitation, idx: number) => (
                <View key={inv.id}>
                  {idx > 0 && <Divider subtle />}
                  <ParticipantRow
                    name={inv.invited_user_display_name}
                    trailingContent={<Badge label="Pending" variant="warning" />}
                  />
                </View>
              ))}
            </Card>
          </Section>
        )}

        {/* Dealer: add guest + invite friend */}
        {isDealer && (
          <View style={activeStyles.managePlayersSection}>
            {showAddGuest ? (
              <AddGuestForm
                gameId={id}
                onDone={() => setShowAddGuest(false)}
              />
            ) : (
              <Row gap="md">
                <View style={subStyles.flexOne}>
                  <Button
                    label="Add Guest"
                    variant="ghost"
                    fullWidth
                    onPress={() => setShowAddGuest(true)}
                  />
                </View>
                <View style={subStyles.flexOne}>
                  <Button
                    label="Invite Friend"
                    variant="ghost"
                    fullWidth
                    onPress={() => setShowInviteModal(true)}
                  />
                </View>
              </Row>
            )}
          </View>
        )}

        {/* ── Buy-ins detail ───────────────────────────────────── */}
        {buyIns.length > 0 && (
          <Section
            title="Buy-in History"
            subtitle={`${buyIns.length} transaction${buyIns.length !== 1 ? "s" : ""}`}
          >
            <Card variant="default" padding="compact">
              {buyIns.map((b, idx) => (
                <View key={b.id}>
                  {idx > 0 && <Divider subtle />}
                  <BuyInRow
                    buyIn={b}
                    participantName={
                      participantMap[b.participant_id] ?? "Unknown"
                    }
                    currency={game!.currency}
                  />
                </View>
              ))}
            </Card>
          </Section>
        )}

        {/* ── Expenses detail ──────────────────────────────────── */}
        {expenses.length > 0 && (
          <Section
            title="Expenses"
            subtitle={`${currencySymbol(game!.currency)} ${totalExpenses.toFixed(2)} total`}
          >
            <Card variant="default" padding="compact">
              {expenses.map((e, idx) => (
                <View key={e.id}>
                  {idx > 0 && <Divider subtle />}
                  <ExpenseRow
                    expense={e}
                    currency={game!.currency}
                    canDelete={
                      isDealer || e.created_by_user_id === me?.id
                    }
                    onDelete={(eid) => deleteExpenseMutation.mutate(eid)}
                  />
                </View>
              ))}
            </Card>
          </Section>
        )}

        {/* ── Player: Cash Out ─────────────────────────────────── */}
        {canCashOut && (
          <View style={activeStyles.cashOutSection}>
            <Button
              label="Leave Early / Cash Out"
              variant="destructive"
              size="lg"
              fullWidth
              onPress={() => setShowCashoutModal(true)}
            />
          </View>
        )}

        {/* Player left early — read-only notice */}
        {!isDealer && myParticipant?.status === "left_early" && (
          <Card variant="default" padding="comfortable" style={activeStyles.leftEarlyCard}>
            <Text variant="body" color="secondary">
              You have cashed out. Your result is recorded and will be
              included in the final settlement.
            </Text>
          </Card>
        )}

        {/* ── Dealer: game management ──────────────────────────── */}
        {isDealer && (
          <View style={activeStyles.dealerGameSection}>
            <Divider spacing={tokens.spacing.md} />
            <Section title="Game Management">
              <Button
                label="Enter Final Chip Counts"
                variant="secondary"
                size="lg"
                fullWidth
                onPress={() => router.push(`/games/${id}/final-stacks`)}
              />
              <Spacer size="md" />
              <Button
                label="Close Game"
                variant="destructive"
                size="lg"
                fullWidth
                loading={closeMutation.isPending}
                disabled={closeMutation.isPending}
                onPress={() => void handleCloseGame()}
              />
            </Section>
          </View>
        )}
      </>
    );
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <>
      <Stack.Screen options={{ title: game.title }} />
      <Screen scrollable>
        {/* Reconnecting banner */}
        {reconnecting && (
          <Card variant="default" padding="compact" style={styles.reconnectBanner}>
            <Row gap="sm" align="center">
              <Badge label="Reconnecting" variant="warning" />
              <Text variant="caption" color="secondary">
                Restoring live updates…
              </Text>
            </Row>
          </Card>
        )}

        {/* Game header */}
        <View style={styles.gameHeader}>
          <Badge
            label={game.status.toUpperCase()}
            variant={
              game.status === "active"
                ? "accent"
                : game.status === "lobby"
                  ? "warning"
                  : "neutral"
            }
          />
          <Text variant="caption" color="secondary">
            {parseFloat(game.chip_cash_rate).toFixed(4)} {game.currency} / chip
          </Text>
        </View>

        <Spacer size="base" />

        {/* ------------------------------------------------------------- */}
        {/* Active game — redesigned live dashboard                       */}
        {/* ------------------------------------------------------------- */}
        {game.status === "active" && renderActiveGame()}

        {/* ------------------------------------------------------------- */}
        {/* Lobby + Closed — unchanged                                    */}
        {/* ------------------------------------------------------------- */}

        {/* Participants section (lobby + closed only — active has its own) */}
        {game.status !== "active" && (
          <Section title={`Players (${participants.length})`}>
            {participants.length === 0 ? (
              <EmptyState
                title="No players yet"
                description="Invite friends or add guests to get started"
              />
            ) : (
              <Card variant="default" padding="none">
                {participants.map((p, idx) => (
                  <View key={p.id}>
                    {idx > 0 && <Divider subtle />}
                    <ParticipantRow
                      name={p.display_name}
                      role={getParticipantRole(p)}
                      highlighted={p.user_id === me?.id}
                      trailingContent={
                        <>
                          {p.status === "left_early" && (
                            <Badge label="Left Early" variant="warning" />
                          )}
                        </>
                      }
                    />
                  </View>
                ))}
              </Card>
            )}
          </Section>
        )}

        {/* Pending invitations (lobby — dealer view) */}
        {game.status !== "active" && isDealer && game.status !== "closed" && pendingInvitations.length > 0 && (
          <Section title="Pending Invitations">
            <Card variant="default" padding="none">
              {pendingInvitations.map((inv: GameInvitation, idx: number) => (
                <View key={inv.id}>
                  {idx > 0 && <Divider subtle />}
                  <ParticipantRow
                    name={inv.invited_user_display_name}
                    trailingContent={<Badge label="Pending" variant="warning" />}
                  />
                </View>
              ))}
            </Card>
          </Section>
        )}

        {/* Dealer: add guest + invite friend (lobby only now — active has its own) */}
        {game.status === "lobby" && isDealer && (
          <View style={styles.dealerControls}>
            {showAddGuest ? (
              <AddGuestForm
                gameId={id}
                onDone={() => setShowAddGuest(false)}
              />
            ) : (
              <Button
                label="Add Guest"
                variant="secondary"
                fullWidth
                onPress={() => setShowAddGuest(true)}
              />
            )}
            <Spacer size="sm" />
            <Button
              label="Invite Friend"
              variant="secondary"
              fullWidth
              onPress={() => setShowInviteModal(true)}
            />
          </View>
        )}

        {/* ------------------------------------------------------------- */}
        {/* Lobby actions (dealer only)                                    */}
        {/* ------------------------------------------------------------- */}
        {game.status === "lobby" && isDealer && (
          <View style={styles.lobbyActions}>
            <Divider spacing={tokens.spacing.lg} />
            <Section title="Dealer Actions">
              <Button
                label={generatedToken ? "Regenerate Invite Token" : "Generate Invite Token"}
                variant="ghost"
                fullWidth
                loading={inviteMutation.isPending}
                disabled={inviteMutation.isPending}
                onPress={() => inviteMutation.mutate()}
              />
              {inviteTokenDisplay && (
                <>
                  <Spacer size="sm" />
                  <Card variant="default" padding="compact">
                    <Text variant="caption" color="secondary">
                      Invite Token
                    </Text>
                    <Spacer size="xs" />
                    <View style={styles.tokenRow}>
                      <Text
                        variant="body"
                        numberOfLines={1}
                        style={styles.tokenText}
                      >
                        {inviteTokenDisplay}
                      </Text>
                      <Pressable
                        style={styles.copyButton}
                        hitSlop={8}
                        onPress={() => void handleCopyToken()}
                      >
                        <Text
                          variant="captionBold"
                          color={tokenCopied ? "positive" : "accent"}
                        >
                          {tokenCopied ? "Copied!" : "Copy"}
                        </Text>
                      </Pressable>
                    </View>
                  </Card>
                </>
              )}
              <Spacer size="md" />
              <Button
                label="Start Game"
                variant="primary"
                size="lg"
                fullWidth
                loading={startMutation.isPending}
                disabled={startMutation.isPending}
                onPress={() => {
                  Alert.alert("Start Game", "Start the game now?", [
                    { text: "Cancel", style: "cancel" },
                    {
                      text: "Start",
                      onPress: () => startMutation.mutate(),
                    },
                  ]);
                }}
              />
            </Section>
          </View>
        )}

        {/* Lobby — player view: waiting message */}
        {game.status === "lobby" && !isDealer && (
          <View style={styles.waitingSection}>
            <Divider spacing={tokens.spacing.lg} />
            <Text variant="body" color="secondary" align="center">
              Waiting for the dealer to start the game…
            </Text>
          </View>
        )}

        {/* ------------------------------------------------------------- */}
        {/* Closed game — settlement + dealer edit actions                 */}
        {/* ------------------------------------------------------------- */}
        {game.status === "closed" && (
          <View style={styles.actionSection}>
            <Divider spacing={tokens.spacing.lg} />
            <Button
              label="View Settlement"
              variant="primary"
              size="lg"
              fullWidth
              onPress={() => router.push(`/games/${id}/settlement`)}
            />

            {isDealer && (
              <>
                <Spacer size="xl" />
                <Section title="Edit Closed Game">
                  <Button
                    label="Edit Buy-Ins"
                    variant="secondary"
                    fullWidth
                    onPress={() => router.push(`/games/${id}/edit-buyins`)}
                  />
                  <Spacer size="sm" />
                  <Button
                    label="Edit Final Stacks"
                    variant="secondary"
                    fullWidth
                    onPress={() => router.push(`/games/${id}/edit-final-stacks`)}
                  />
                </Section>
              </>
            )}

            <Spacer size="base" />
            <Button
              label="View Edit History"
              variant="ghost"
              fullWidth
              onPress={() => router.push(`/games/${id}/edit-history`)}
            />
          </View>
        )}

        <Spacer size="4xl" />
      </Screen>

      {/* Shortage resolution modal */}
      <ShortageModal
        visible={shortageModal.visible}
        shortageAmount={shortageModal.amount}
        currency={game?.currency ?? ""}
        isPending={closeMutation.isPending}
        onChoose={(strategy) => closeMutation.mutate(strategy)}
        onCancel={() => setShortageModal({ visible: false, amount: "0" })}
      />

      {/* Cash out modal — player-only */}
      <CashoutModal
        visible={showCashoutModal}
        gameId={id}
        currency={game?.currency ?? ""}
        chipCashRate={game?.chip_cash_rate ?? "0"}
        onSuccess={() => {
          setShowCashoutModal(false);
          void queryClient.invalidateQueries({
            queryKey: queryKeys.participants(id),
          });
        }}
        onClose={() => setShowCashoutModal(false)}
      />

      {/* Invite friend modal — dealer-only */}
      <InviteFriendModal
        visible={showInviteModal}
        gameId={id}
        onSuccess={() => {
          void queryClient.invalidateQueries({
            queryKey: queryKeys.gameInvitations(id),
          });
          setShowInviteModal(false);
        }}
        onClose={() => setShowInviteModal(false)}
      />
    </>
  );
}

// ---------------------------------------------------------------------------
// Styles — shared (lobby, closed, header)
// ---------------------------------------------------------------------------

const styles = StyleSheet.create({
  reconnectBanner: {
    marginBottom: tokens.spacing.md,
  },
  gameHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: tokens.spacing.md,
    paddingHorizontal: tokens.spacing.lg,
  },
  dealerControls: {
    paddingHorizontal: tokens.spacing.lg,
    marginBottom: tokens.spacing.base,
  },
  lobbyActions: {
    paddingHorizontal: tokens.spacing.lg,
  },
  waitingSection: {
    paddingHorizontal: tokens.spacing.lg,
    paddingBottom: tokens.spacing.xl,
  },
  actionSection: {
    paddingHorizontal: tokens.spacing.lg,
  },
  tokenRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: tokens.spacing.sm,
  },
  tokenText: {
    flex: 1,
    fontFamily: "monospace",
    fontSize: 13,
  },
  copyButton: {
    paddingVertical: tokens.spacing.xs,
    paddingHorizontal: tokens.spacing.md,
    borderRadius: tokens.radius.sm,
    backgroundColor: tokens.color.bg.surface,
    minWidth: tokens.size.touchTarget,
    alignItems: "center" as const,
  },
});

// ---------------------------------------------------------------------------
// Styles — active game dashboard
// ---------------------------------------------------------------------------

const activeStyles = StyleSheet.create({
  heroCard: {
    alignItems: "center" as const,
    borderWidth: 1,
    borderColor: tokens.color.border.subtle,
  },
  quickActions: {
    // Row gap handles spacing between buttons
  },
  managePlayersSection: {
    marginBottom: tokens.spacing.xl,
  },
  cashOutSection: {
    marginBottom: tokens.spacing.xl,
  },
  leftEarlyCard: {
    borderWidth: 1,
    borderColor: tokens.color.semantic.warning,
    marginBottom: tokens.spacing.xl,
  },
  dealerGameSection: {
    marginTop: tokens.spacing.md,
  },
});

// ---------------------------------------------------------------------------
// Styles — sub-components
// ---------------------------------------------------------------------------

const subStyles = StyleSheet.create({
  ledgerRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: tokens.spacing.md,
    gap: tokens.spacing.sm,
  },
  ledgerFlex: {
    flex: 1,
  },
  deleteBtn: {
    padding: tokens.spacing.xs,
    marginLeft: tokens.spacing.xs,
    minWidth: tokens.size.touchTarget,
    minHeight: tokens.size.touchTarget,
    alignItems: "center" as const,
    justifyContent: "center" as const,
  },
  inlineForm: {
    flexDirection: "row",
    gap: tokens.spacing.sm,
    alignItems: "center",
    marginBottom: tokens.spacing.sm,
  },
  inlineInputWrapper: {
    flex: 1,
  },
  flexOne: {
    flex: 1,
  },
});

const shortageStyles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.7)",
    alignItems: "center",
    justifyContent: "center",
    padding: tokens.spacing.xl,
  },
  sheet: {
    width: "100%",
  },
  option: {
    backgroundColor: tokens.color.bg.surface,
    borderRadius: tokens.radius.md,
    padding: tokens.spacing.base,
    marginBottom: tokens.spacing.sm,
    borderWidth: 1,
    borderColor: tokens.color.border.default,
  },
  optionDisabled: { opacity: 0.5 },
});
