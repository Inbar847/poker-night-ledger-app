/**
 * Settlement screen — available to all participants once game is closed.
 *
 * Shows:
 *  - Per-participant balance breakdown (buy-ins, poker result, expense balance, net)
 *  - Optimized transfer list (who pays whom) — hero element
 *  - Warning banner if any participant is missing a final stack
 *  - Dealer retroactive edit entry points for closed games
 */

import { useQuery } from "@tanstack/react-query";
import { Stack, useLocalSearchParams, useRouter } from "expo-router";
import { Pressable, StyleSheet, View } from "react-native";

import {
  Screen,
  ScreenHeader,
  Section,
  Card,
  Text,
  MoneyAmount,
  TransferRow,
  Badge,
  Button,
  Divider,
  Spacer,
  Skeleton,
  EmptyState,
  ErrorState,
  Row,
  currencySymbol,
} from "@/components";

import { queryKeys } from "@/lib/queryKeys";
import * as gameService from "@/services/gameService";
import * as settlementService from "@/services/settlementService";
import * as userService from "@/services/userService";
import { useAuthStore } from "@/store/authStore";
import { tokens } from "@/theme";
import type { ParticipantBalance, Transfer } from "@/types/game";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function parseNum(v: string | null | undefined): number {
  if (v == null) return 0;
  const n = parseFloat(v);
  return isNaN(n) ? 0 : n;
}

// ---------------------------------------------------------------------------
// Loading skeleton
// ---------------------------------------------------------------------------

function SettlementSkeleton() {
  return (
    <Screen scrollable>
      <Spacer size="base" />
      {/* Transfer hero skeleton */}
      <Skeleton width={160} height={20} />
      <Spacer size="md" />
      {[1, 2, 3].map((i) => (
        <View key={i} style={skeletonStyles.transferRow}>
          <Skeleton width={80} height={16} />
          <Skeleton width={24} height={16} />
          <Skeleton width={80} height={16} />
          <View style={{ flex: 1 }} />
          <Skeleton width={60} height={20} />
        </View>
      ))}
      <Spacer size="2xl" />
      {/* Balance cards skeleton */}
      <Skeleton width={100} height={18} />
      <Spacer size="md" />
      {[1, 2, 3].map((i) => (
        <View key={i} style={{ marginBottom: tokens.spacing.md }}>
          <Skeleton width="100%" height={100} radius={tokens.radius.lg} />
        </View>
      ))}
    </Screen>
  );
}

// ---------------------------------------------------------------------------
// Balance detail row (within a participant card)
// ---------------------------------------------------------------------------

function DetailRow({
  label,
  amount,
  currency,
  colorOverride,
}: {
  label: string;
  amount: number;
  currency: string;
  colorOverride?: "warning";
}) {
  const color =
    colorOverride === "warning"
      ? "warning"
      : amount > 0
        ? "positive"
        : amount < 0
          ? "negative"
          : "secondary";

  return (
    <Row justify="between" style={detailStyles.row}>
      <Text variant="caption" color="secondary">
        {label}
      </Text>
      <MoneyAmount amount={amount} currency={currency} size="sm" showSign />
    </Row>
  );
}

// ---------------------------------------------------------------------------
// Participant balance card
// ---------------------------------------------------------------------------

function BalanceCard({
  balance,
  currency,
}: {
  balance: ParticipantBalance;
  currency: string;
}) {
  const displayNet = parseNum(balance.adjusted_net_balance ?? balance.net_balance);
  const totalBuyIns = parseNum(balance.total_buy_ins);
  const chipCashValue = balance.final_chip_cash_value != null
    ? parseNum(balance.final_chip_cash_value)
    : null;
  const expenseBalance = parseNum(balance.expense_balance);
  const shortageShare = parseNum(balance.shortage_share);

  return (
    <Card style={cardStyles.card}>
      <Row justify="between" align="center">
        <Text variant="bodyBold" numberOfLines={1} style={cardStyles.name}>
          {balance.display_name}
        </Text>
        <MoneyAmount amount={displayNet} currency={currency} size="md" showSign />
      </Row>

      <Spacer size="sm" />
      <Divider subtle />
      <Spacer size="sm" />

      <View style={cardStyles.details}>
        <DetailRow
          label="Buy-ins"
          amount={-totalBuyIns}
          currency={currency}
        />
        {chipCashValue != null ? (
          <DetailRow
            label="Chip cash value"
            amount={chipCashValue}
            currency={currency}
          />
        ) : (
          <Row justify="between" style={detailStyles.row}>
            <Text variant="caption" color="secondary">
              Final chips
            </Text>
            <Text variant="captionBold" color="muted">
              (missing)
            </Text>
          </Row>
        )}
        {expenseBalance !== 0 && (
          <DetailRow
            label="Expense balance"
            amount={expenseBalance}
            currency={currency}
          />
        )}
        {shortageShare > 0 && (
          <DetailRow
            label="Shortage absorbed"
            amount={-shortageShare}
            currency={currency}
            colorOverride="warning"
          />
        )}
      </View>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Transfer hero section
// ---------------------------------------------------------------------------

function TransferHero({
  transfers,
  currency,
}: {
  transfers: Transfer[];
  currency: string;
}) {
  if (transfers.length === 0) {
    return (
      <Card variant="prominent" padding="comfortable" style={heroStyles.card}>
        <Text variant="body" color="secondary" align="center">
          No transfers needed — everyone is settled.
        </Text>
      </Card>
    );
  }

  return (
    <Card variant="prominent" padding="none" style={heroStyles.card}>
      {transfers.map((t, i) => (
        <View key={i}>
          {i > 0 && <Divider subtle />}
          <TransferRow
            fromName={t.from_display_name}
            toName={t.to_display_name}
            amount={parseNum(t.amount)}
            currency={currency}
          />
        </View>
      ))}
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Main screen
// ---------------------------------------------------------------------------

export default function SettlementScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const userId = useAuthStore((s) => s.userId) ?? "";

  const {
    data: settlement,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: queryKeys.settlement(id),
    queryFn: () => settlementService.getSettlement(id),
    enabled: !!id,
  });

  const { data: game } = useQuery({
    queryKey: queryKeys.game(id),
    queryFn: () => gameService.getGame(id),
    enabled: !!id,
  });

  const { data: me } = useQuery({
    queryKey: queryKeys.me(userId),
    queryFn: userService.getMe,
  });

  const isDealer = !!(me && game && me.id === game.dealer_user_id);
  const isClosed = game?.status === "closed";

  // -- Loading --
  if (isLoading) {
    return (
      <>
        <Stack.Screen options={{ title: "Settlement" }} />
        <SettlementSkeleton />
      </>
    );
  }

  // -- Error --
  if (error || !settlement) {
    return (
      <>
        <Stack.Screen options={{ title: "Settlement" }} />
        <Screen>
          <ErrorState
            message="Failed to load settlement"
            onRetry={() => void refetch()}
          />
        </Screen>
      </>
    );
  }

  const { currency } = settlement;
  const chipCashRate = parseFloat(settlement.chip_cash_rate);
  const shortageAmount = parseNum(settlement.shortage_amount);

  // Separate winners and losers for visual grouping
  const winners = settlement.balances.filter(
    (b) => parseNum(b.adjusted_net_balance ?? b.net_balance) > 0,
  );
  const losers = settlement.balances.filter(
    (b) => parseNum(b.adjusted_net_balance ?? b.net_balance) <= 0,
  );

  return (
    <>
      <Stack.Screen options={{ title: "Settlement" }} />
      <Screen scrollable>
        <Spacer size="base" />

        {/* Chip-cash rate info */}
        <Row justify="start" gap="sm" style={layoutStyles.rateRow}>
          <Text variant="caption" color="secondary">
            Rate:
          </Text>
          <Text variant="captionBold" color="secondary">
            {chipCashRate.toFixed(4)} {currencySymbol(currency)} / chip
          </Text>
        </Row>

        <Spacer size="base" />

        {/* Incomplete warning */}
        {!settlement.is_complete && (
          <>
            <Card style={bannerStyles.warning}>
              <Row gap="sm" align="start">
                <Badge label="Incomplete" variant="warning" />
                <Text variant="caption" color="warning" style={bannerStyles.text}>
                  Some participants are missing final chip counts. Settlement is
                  incomplete — transfers are not yet available.
                </Text>
              </Row>
            </Card>
            <Spacer size="base" />
          </>
        )}

        {/* Shortage banner */}
        {shortageAmount > 0 && (
          <>
            <Card style={bannerStyles.shortage}>
              <Text variant="captionBold" color="warning">
                Shortage: {currencySymbol(currency)}{shortageAmount.toFixed(2)} absorbed
              </Text>
              <Spacer size="xs" />
              <Text variant="caption" color="secondary">
                Strategy:{" "}
                {settlement.shortage_strategy === "proportional_winners"
                  ? "Proportional (winners only)"
                  : "Equal split (all participants)"}
              </Text>
            </Card>
            <Spacer size="base" />
          </>
        )}

        {/* ============================================================= */}
        {/* HERO: Transfer list                                            */}
        {/* ============================================================= */}
        {settlement.is_complete && (
          <>
            <Section title="Who Pays Whom">
              <TransferHero
                transfers={settlement.transfers}
                currency={currency}
              />
            </Section>
            <Spacer size="md" />
          </>
        )}

        {/* ============================================================= */}
        {/* Winners                                                        */}
        {/* ============================================================= */}
        {winners.length > 0 && (
          <Section title="Winners">
            {winners.map((b) => (
              <BalanceCard
                key={b.participant_id}
                balance={b}
                currency={currency}
              />
            ))}
          </Section>
        )}

        {/* ============================================================= */}
        {/* Losers                                                         */}
        {/* ============================================================= */}
        {losers.length > 0 && (
          <Section title={winners.length > 0 ? "Losers" : "Balances"}>
            {losers.map((b) => (
              <BalanceCard
                key={b.participant_id}
                balance={b}
                currency={currency}
              />
            ))}
          </Section>
        )}

        {/* ============================================================= */}
        {/* Dealer retroactive edit actions                                */}
        {/* ============================================================= */}
        {isClosed && (
          <>
            <Divider spacing={tokens.spacing.lg} />

            {isDealer && (
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
                <Spacer size="lg" />
              </Section>
            )}

            <Button
              label="View Edit History"
              variant="ghost"
              fullWidth
              onPress={() => router.push(`/games/${id}/edit-history`)}
            />
          </>
        )}

        <Spacer size="4xl" />
      </Screen>
    </>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const skeletonStyles = StyleSheet.create({
  transferRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: tokens.spacing.sm,
    paddingVertical: tokens.spacing.md,
  },
});

const layoutStyles = StyleSheet.create({
  rateRow: {
    paddingHorizontal: tokens.spacing.xs,
  },
});

const bannerStyles = StyleSheet.create({
  warning: {
    borderLeftWidth: 3,
    borderLeftColor: tokens.color.semantic.warning,
  },
  shortage: {
    borderLeftWidth: 3,
    borderLeftColor: tokens.color.semantic.warning,
  },
  text: {
    flex: 1,
  },
});

const heroStyles = StyleSheet.create({
  card: {
    borderWidth: 1,
    borderColor: tokens.color.border.subtle,
  },
});

const cardStyles = StyleSheet.create({
  card: {
    marginBottom: tokens.spacing.md,
  },
  name: {
    flex: 1,
    marginRight: tokens.spacing.md,
  },
  details: {
    gap: tokens.spacing.xs,
  },
});

const detailStyles = StyleSheet.create({
  row: {
    paddingVertical: tokens.spacing.xs,
  },
});
