/**
 * Final stacks entry screen — dealer only.
 *
 * Shows all participants with a chips_amount input for each.
 * "Save All" calls PUT /games/:id/final-stacks/:participantId for each
 * participant that has a value entered. Participants with empty input are skipped.
 *
 * On success: go back (game screen refreshes via WS events).
 */

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Stack, useLocalSearchParams, useRouter } from "expo-router";
import { useMemo, useState } from "react";
import { Alert, StyleSheet, View } from "react-native";

import {
  Text,
  Button,
  Card,
  Spacer,
  Divider,
  Screen,
  Section,
  Row,
  Avatar,
  NumericInput,
  Skeleton,
  ChipCount,
  currencySymbol,
} from "@/components";

import { queryKeys } from "@/lib/queryKeys";
import * as gameService from "@/services/gameService";
import * as ledgerService from "@/services/ledgerService";
import { tokens } from "@/theme";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Format a cash value with currency symbol. */
function formatCash(value: number, currency: string): string {
  return `${currencySymbol(currency)}${Math.abs(value).toFixed(2)}`;
}

// ---------------------------------------------------------------------------
// Loading skeleton
// ---------------------------------------------------------------------------

function FinalStacksSkeleton() {
  return (
    <Screen scrollable>
      <Spacer size="base" />
      <Skeleton width={240} height={20} />
      <Spacer size="xl" />
      {[1, 2, 3].map((i) => (
        <View key={i} style={skeletonStyles.row}>
          <Skeleton circle height={tokens.size.avatarMd} />
          <View style={skeletonStyles.rowContent}>
            <Skeleton width={100} height={16} />
            <Spacer size="sm" />
            <Skeleton height={tokens.size.numericInputHeight} radius={tokens.radius.md} />
          </View>
        </View>
      ))}
      <Spacer size="xl" />
      <Skeleton height={tokens.size.buttonLg} radius={tokens.radius.lg} />
    </Screen>
  );
}

const skeletonStyles = StyleSheet.create({
  row: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: tokens.spacing.md,
    marginBottom: tokens.spacing.lg,
  },
  rowContent: {
    flex: 1,
  },
});

// ---------------------------------------------------------------------------
// Main screen
// ---------------------------------------------------------------------------

export default function FinalStacksScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data: game } = useQuery({
    queryKey: queryKeys.game(id),
    queryFn: () => gameService.getGame(id),
    enabled: !!id,
  });

  const { data: participants = [], isLoading } = useQuery({
    queryKey: queryKeys.participants(id),
    queryFn: () => gameService.getParticipants(id),
    enabled: !!id,
  });

  const { data: existingStacks = [] } = useQuery({
    queryKey: queryKeys.finalStacks(id),
    queryFn: () => ledgerService.listFinalStacks(id),
    enabled: !!id,
  });

  const { data: buyIns = [] } = useQuery({
    queryKey: queryKeys.buyIns(id),
    queryFn: () => ledgerService.listBuyIns(id),
    enabled: !!id,
  });

  const chipCashRate = game ? parseFloat(game.chip_cash_rate) : 0;
  const currency = game?.currency ?? "ILS";

  // Total chips distributed via buy-ins (all participants)
  const totalChipsBoughtIn = useMemo(
    () => buyIns.reduce((sum, b) => sum + parseFloat(b.chips_amount), 0),
    [buyIns],
  );

  // Chips already accounted for by left_early participants with saved final stacks
  // (these are not editable on this screen — they cashed out earlier)
  const leftEarlyChips = useMemo(() => {
    const leftEarlyIds = new Set(
      participants.filter((p) => p.status === "left_early").map((p) => p.id),
    );
    return existingStacks
      .filter((s) => leftEarlyIds.has(s.participant_id))
      .reduce((sum, s) => sum + parseFloat(s.chips_amount), 0);
  }, [participants, existingStacks]);

  // Build initial chip values from existing stacks
  const existingMap = Object.fromEntries(
    existingStacks.map((s) => [s.participant_id, s.chips_amount]),
  );

  // Local state: participantId → chips string
  const [chips, setChips] = useState<Record<string, string>>(() =>
    Object.fromEntries(
      participants.map((p) => [p.id, existingMap[p.id] ?? ""]),
    ),
  );

  // Re-init when participants/stacks load
  // (useEffect not needed — initial state captures whatever loaded first;
  //  we rely on component re-rendering after both queries resolve)

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const queryClient_ = useQueryClient();

  const handleSave = async () => {
    const entries = participants.filter(
      (p) => chips[p.id] !== undefined && chips[p.id].trim() !== "",
    );

    if (entries.length === 0) {
      Alert.alert("No chips entered", "Enter chip counts for at least one participant.");
      return;
    }

    // Validate all entered values
    const invalid = entries.find((p) => {
      const v = parseFloat(chips[p.id] ?? "");
      return isNaN(v) || v < 0;
    });
    if (invalid) {
      setError("Chip counts must be 0 or greater.");
      return;
    }

    setSaving(true);
    setError(null);
    try {
      await Promise.all(
        entries.map((p) =>
          ledgerService.upsertFinalStack(id, p.id, {
            chips_amount: parseFloat(chips[p.id]).toFixed(2),
          }),
        ),
      );
      void queryClient_.invalidateQueries({
        queryKey: queryKeys.finalStacks(id),
      });
      router.back();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to save final stacks",
      );
    } finally {
      setSaving(false);
    }
  };

  // Compute chip total for entered values (on this screen)
  const totalChipsEntered = participants.reduce((sum, p) => {
    const val = parseFloat(chips[p.id] ?? "");
    return sum + (isNaN(val) ? 0 : val);
  }, 0);
  const filledCount = participants.filter(
    (p) => chips[p.id] !== undefined && chips[p.id].trim() !== "",
  ).length;

  // Chips remaining = total bought in − left-early chips − currently entered chips
  const chipsRemaining = totalChipsBoughtIn - leftEarlyChips - totalChipsEntered;

  if (isLoading) {
    return (
      <>
        <Stack.Screen options={{ title: "Final Chip Counts" }} />
        <FinalStacksSkeleton />
      </>
    );
  }

  return (
    <>
      <Stack.Screen options={{ title: "Final Chip Counts" }} />
      <Screen scrollable keyboardAvoiding>
        <Spacer size="base" />

        <Text variant="body" color="secondary">
          Enter the final chip count for each participant. Leave blank to skip.
        </Text>

        <Spacer size="base" />

        {/* Chips remaining at the table */}
        {totalChipsBoughtIn > 0 && (
          <>
            <Card variant="default" padding="comfortable" style={styles.remainingCard}>
              <Row justify="between" align="center">
                <Text variant="bodyBold" color="secondary">
                  Chips remaining at the table
                </Text>
                <ChipCount chips={chipsRemaining} size="md" />
              </Row>
              {chipCashRate > 0 && (
                <>
                  <Spacer size="xs" />
                  <Text variant="caption" color="muted" style={styles.alignRight}>
                    ≈ {formatCash(chipsRemaining * chipCashRate, currency)}
                  </Text>
                </>
              )}
            </Card>
            <Spacer size="base" />
          </>
        )}

        <Spacer size="sm" />

        {/* Error banner */}
        {error ? (
          <>
            <Card variant="default" padding="compact" style={styles.errorBanner}>
              <Text variant="body" color="negative">{error}</Text>
            </Card>
            <Spacer size="base" />
          </>
        ) : null}

        {/* Participant chip entries */}
        <Card variant="default" padding="none">
          {participants.map((p, idx) => (
            <View key={p.id}>
              {idx > 0 && <Divider subtle />}
              <View style={styles.participantEntry}>
                <Row gap="md" align="center" style={styles.participantHeader}>
                  <Avatar name={p.display_name} size="md" />
                  <Text variant="bodyBold" numberOfLines={1} style={styles.participantName}>
                    {p.display_name}
                  </Text>
                  {p.status === "left_early" && (
                    <Text variant="caption" color="warning">Left early</Text>
                  )}
                </Row>
                <View style={styles.chipInputWrapper}>
                  <NumericInput
                    value={chips[p.id] ?? ""}
                    onChangeText={(v) =>
                      setChips((prev) => ({ ...prev, [p.id]: v }))
                    }
                    suffix="chips"
                    placeholder="0"
                    decimal
                  />
                  {chipCashRate > 0 && (chips[p.id] ?? "").trim() !== "" && (
                    <Text variant="caption" color="muted" style={styles.cashEquivalent}>
                      ≈ {formatCash(parseFloat(chips[p.id] || "0") * chipCashRate, currency)}
                    </Text>
                  )}
                </View>
              </View>
            </View>
          ))}
        </Card>

        <Spacer size="xl" />

        {/* Chip total summary */}
        {filledCount > 0 && (
          <>
            <Card variant="default" padding="comfortable" style={styles.totalCard}>
              <Row justify="between" align="center">
                <Text variant="bodyBold" color="secondary">Total entered</Text>
                <ChipCount chips={totalChipsEntered} size="md" />
              </Row>
              <Spacer size="xs" />
              <Text variant="caption" color="muted">
                {filledCount} of {participants.length} participants filled
              </Text>
            </Card>
            <Spacer size="xl" />
          </>
        )}

        {/* Save */}
        <Button
          label="Save All"
          variant="primary"
          size="lg"
          fullWidth
          loading={saving}
          disabled={saving}
          onPress={() => void handleSave()}
        />

        <Spacer size="4xl" />
      </Screen>
    </>
  );
}

const styles = StyleSheet.create({
  errorBanner: {
    borderWidth: 1,
    borderColor: tokens.color.semantic.negative,
  },
  participantEntry: {
    paddingHorizontal: tokens.spacing.base,
    paddingVertical: tokens.spacing.md,
  },
  participantHeader: {
    marginBottom: tokens.spacing.sm,
  },
  participantName: {
    flex: 1,
  },
  chipInputWrapper: {
    paddingLeft: tokens.size.avatarMd + tokens.spacing.md,
  },
  cashEquivalent: {
    marginTop: tokens.spacing.xs,
    paddingLeft: tokens.spacing.sm,
  },
  remainingCard: {
    borderWidth: 1,
    borderColor: tokens.color.border.default,
  },
  alignRight: {
    textAlign: "right" as const,
  },
  totalCard: {
    borderWidth: 1,
    borderColor: tokens.color.border.default,
  },
});
