/**
 * Historical game detail screen.
 *
 * Displays the settlement summary for a single closed game from history.
 * Shows participant balances and the who-pays-whom transfer list.
 * Read-only — no mutations possible on a closed game.
 */

import { useQuery } from "@tanstack/react-query";
import { Stack, useLocalSearchParams } from "expo-router";
import {
  RefreshControl,
  ScrollView,
  StyleSheet,
  View,
} from "react-native";

import {
  Badge,
  Card,
  Divider,
  EmptyState,
  ErrorState,
  MoneyAmount,
  Row,
  Section,
  Skeleton,
  Spacer,
  Text,
  TransferRow,
  currencySymbol,
} from "@/components";
import { queryKeys } from "@/lib/queryKeys";
import * as statsService from "@/services/statsService";
import { tokens } from "@/theme";
import type { ParticipantBalance, Transfer } from "@/types/game";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function parseVal(val: string | null | undefined): number {
  if (val == null) return 0;
  return parseFloat(val);
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function BalanceCard({
  balance,
  currency,
}: {
  balance: ParticipantBalance;
  currency: string;
}) {
  const net = balance.net_balance != null ? parseFloat(balance.net_balance) : null;

  return (
    <Card variant="default" padding="comfortable" style={styles.balanceCard}>
      <Row justify="between" align="center">
        <Text variant="bodyBold" numberOfLines={1} style={styles.flex}>
          {balance.display_name}
        </Text>
        {net != null ? (
          <MoneyAmount amount={net} currency={currency} size="md" showSign />
        ) : (
          <Text variant="numeric" color="secondary">{"\u2014"}</Text>
        )}
      </Row>

      <Spacer size="sm" />
      <Divider subtle />
      <Spacer size="sm" />

      <Row justify="between" align="center">
        <Text variant="caption" color="secondary">Buy-ins</Text>
        <MoneyAmount
          amount={parseVal(balance.total_buy_ins)}
          currency={currency}
          size="sm"
        />
      </Row>
      <Spacer size="xs" />
      <Row justify="between" align="center">
        <Text variant="caption" color="secondary">Chip value</Text>
        {balance.final_chip_cash_value != null ? (
          <MoneyAmount
            amount={parseVal(balance.final_chip_cash_value)}
            currency={currency}
            size="sm"
          />
        ) : (
          <Text variant="numericSmall" color="secondary">{"\u2014"}</Text>
        )}
      </Row>
      <Spacer size="xs" />
      <Row justify="between" align="center">
        <Text variant="caption" color="secondary">Expense balance</Text>
        <MoneyAmount
          amount={parseVal(balance.expense_balance)}
          currency={currency}
          size="sm"
        />
      </Row>
    </Card>
  );
}

function DetailSkeleton() {
  return (
    <View style={styles.skeletonContainer}>
      {/* Chip rate */}
      <Skeleton width={180} height={14} />
      <Spacer size="xl" />

      {/* Transfers section */}
      <Skeleton width={140} height={18} />
      <Spacer size="md" />
      <Skeleton height={120} radius={tokens.radius.xl} />
      <Spacer size="xl" />

      {/* Balances section */}
      <Skeleton width={140} height={18} />
      <Spacer size="md" />
      <Skeleton height={140} radius={tokens.radius.lg} />
      <Spacer size="md" />
      <Skeleton height={140} radius={tokens.radius.lg} />
    </View>
  );
}

// ---------------------------------------------------------------------------
// Main screen
// ---------------------------------------------------------------------------

export default function HistoryGameScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();

  const {
    data: settlement,
    isLoading,
    error,
    refetch,
    isRefetching,
  } = useQuery({
    queryKey: queryKeys.historyGame(id),
    queryFn: () => statsService.getHistoryGame(id),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <View style={styles.container}>
        <Stack.Screen options={{ title: "Game Detail" }} />
        <DetailSkeleton />
      </View>
    );
  }

  if (error || !settlement) {
    return (
      <View style={styles.container}>
        <Stack.Screen options={{ title: "Game Detail" }} />
        <ErrorState
          message="Failed to load game"
          onRetry={() => void refetch()}
        />
      </View>
    );
  }

  const { currency, balances, transfers, is_complete } = settlement;

  return (
    <View style={styles.container}>
      <Stack.Screen options={{ title: "Game Detail" }} />
      <ScrollView
        style={styles.flex}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={isRefetching}
            onRefresh={refetch}
            tintColor={tokens.color.accent.primary}
          />
        }
      >
        {/* Game info header */}
        <Row gap="md" align="center">
          <Text variant="caption" color="secondary">
            Chip rate: {parseFloat(settlement.chip_cash_rate).toFixed(4)} {currencySymbol(currency)} / chip
          </Text>
          <Badge
            label={is_complete ? "Complete" : "Incomplete"}
            variant={is_complete ? "accent" : "warning"}
          />
        </Row>

        <Spacer size="lg" />

        {/* Warning banner */}
        {!is_complete && (
          <>
            <Card variant="default" padding="compact" style={styles.warningBanner}>
              <Text variant="caption" color="warning">
                Settlement incomplete — one or more final stacks are missing.
              </Text>
            </Card>
            <Spacer size="lg" />
          </>
        )}

        {/* Transfers (hero section) */}
        {is_complete && transfers.length > 0 && (
          <Section title="Who Pays Whom">
            <Card variant="prominent" padding="compact">
              {transfers.map((t, i) => (
                <View key={i}>
                  {i > 0 && <Divider subtle />}
                  <TransferRow
                    fromName={t.from_display_name}
                    toName={t.to_display_name}
                    amount={parseFloat(t.amount)}
                    currency={currency}
                  />
                </View>
              ))}
            </Card>
          </Section>
        )}

        {is_complete && transfers.length === 0 && (
          <Section title="Transfers">
            <Card variant="default" padding="comfortable">
              <Text variant="body" color="secondary" align="center">
                All balances are settled — no transfers needed.
              </Text>
            </Card>
          </Section>
        )}

        {/* Final Balances */}
        <Section
          title="Final Balances"
          subtitle={`${balances.length} ${balances.length === 1 ? "player" : "players"}`}
        >
          {balances.map((b) => (
            <BalanceCard key={b.participant_id} balance={b} currency={currency} />
          ))}
        </Section>

        <Spacer size="4xl" />
      </ScrollView>
    </View>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: tokens.color.bg.primary,
  },
  flex: {
    flex: 1,
  },
  scrollContent: {
    padding: tokens.spacing.lg,
    paddingBottom: tokens.spacing["4xl"],
  },
  skeletonContainer: {
    padding: tokens.spacing.lg,
  },
  balanceCard: {
    marginBottom: tokens.spacing.md,
  },
  warningBanner: {
    borderLeftWidth: 3,
    borderLeftColor: tokens.color.semantic.warning,
  },
});
