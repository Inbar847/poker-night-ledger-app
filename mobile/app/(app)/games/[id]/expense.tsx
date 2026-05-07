/**
 * Expense entry screen — any active participant.
 *
 * Fields: title, total_amount, paid_by participant, split_among participants.
 * Non-dealers are locked to themselves as payer (backend enforces this).
 * The dealer can select any participant as payer.
 * Splits are computed as equal shares among selected participants only.
 * The remainder (from integer division) goes to the first selected participant,
 * ensuring the split sum equals total_amount exactly.
 *
 * On success: go back (game screen refreshes via WS event).
 */

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Stack, useLocalSearchParams, useRouter } from "expo-router";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Pressable, StyleSheet, View } from "react-native";
import { z } from "zod";

import {
  Text,
  Button,
  Card,
  Badge,
  Spacer,
  Divider,
  Screen,
  Section,
  Row,
  Input,
  FormField,
  NumericInput,
  SelectField,
  Skeleton,
  MoneyAmount,
  currencySymbol,
} from "@/components";

import { queryKeys } from "@/lib/queryKeys";
import * as gameService from "@/services/gameService";
import * as ledgerService from "@/services/ledgerService";
import { useAuthStore } from "@/store/authStore";
import { tokens } from "@/theme";
import type { Participant } from "@/types/game";

const schema = z.object({
  title: z.string().min(1, "Title is required").max(255),
  total_amount: z
    .string()
    .min(1, "Amount is required")
    .refine((v) => parseFloat(v) > 0, "Must be greater than 0"),
});

type FormValues = z.infer<typeof schema>;

/**
 * Compute equal splits for the given participants.
 * Uses integer cent arithmetic to avoid floating-point drift.
 * Remainder (from floor division) goes to the first participant.
 */
function computeEqualSplits(
  participants: Participant[],
  totalAmountStr: string,
): { participant_id: string; share_amount: string }[] {
  const n = participants.length;
  if (n === 0) return [];
  const totalCents = Math.round(parseFloat(totalAmountStr) * 100);
  const baseCents = Math.floor(totalCents / n);
  const remainderCents = totalCents - baseCents * n;
  return participants.map((p, i) => ({
    participant_id: p.id,
    share_amount: ((baseCents + (i === 0 ? remainderCents : 0)) / 100).toFixed(
      2,
    ),
  }));
}

export default function ExpenseScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();

  const userId = useAuthStore((s) => s.userId) ?? "";

  const [paidBy, setPaidBy] = useState<string | null>(null);
  // IDs of participants included in the split. Initialised to all once loaded.
  const [splitIds, setSplitIds] = useState<Set<string>>(new Set());

  const { data: game } = useQuery({
    queryKey: queryKeys.game(id),
    queryFn: () => gameService.getGame(id),
    enabled: !!id,
  });

  const { data: participants = [], isLoading: participantsLoading } = useQuery({
    queryKey: queryKeys.participants(id),
    queryFn: () => gameService.getParticipants(id),
    enabled: !!id,
  });

  const isDealer = !!(game && userId && game.dealer_user_id === userId);
  const myParticipant = participants.find((p) => p.user_id === userId);

  // Default: include everyone in the split once participants are loaded.
  // For non-dealers, auto-set paidBy to self.
  useEffect(() => {
    if (participants.length > 0 && splitIds.size === 0) {
      setSplitIds(new Set(participants.map((p) => p.id)));
    }
    if (!isDealer && myParticipant && !paidBy) {
      setPaidBy(myParticipant.id);
    }
  }, [participants, isDealer, myParticipant]); // eslint-disable-line react-hooks/exhaustive-deps

  function toggleSplitId(participantId: string) {
    setSplitIds((prev) => {
      const next = new Set(prev);
      if (next.has(participantId)) {
        next.delete(participantId);
      } else {
        next.add(participantId);
      }
      return next;
    });
  }

  const selectedParticipants = participants.filter((p) => splitIds.has(p.id));

  const mutation = useMutation({
    mutationFn: (values: FormValues) => {
      const splits = computeEqualSplits(selectedParticipants, values.total_amount);
      return ledgerService.createExpense(id, {
        title: values.title,
        total_amount: parseFloat(values.total_amount).toFixed(2),
        paid_by_participant_id: paidBy!,
        splits,
      });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.expenses(id) });
      router.back();
    },
  });

  const {
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { title: "", total_amount: "" },
  });

  const title = watch("title");
  const total = watch("total_amount");

  // Preview splits when both total and selected participants are available
  const previewSplits =
    total && parseFloat(total) > 0 && selectedParticipants.length > 0
      ? computeEqualSplits(selectedParticipants, total)
      : [];

  const canSubmit = !!paidBy && selectedParticipants.length > 0 && !mutation.isPending;

  // Participant options for SelectField
  const participantOptions = participants.map((p) => ({
    label: p.display_name,
    value: p.id,
  }));

  return (
    <>
      <Stack.Screen options={{ title: "Add Expense" }} />
      <Screen scrollable keyboardAvoiding>
        <Spacer size="base" />

        {/* Error banner */}
        {mutation.error ? (
          <>
            <Card variant="default" padding="compact" style={styles.errorBanner}>
              <Text variant="body" color="negative">
                {mutation.error instanceof Error
                  ? mutation.error.message
                  : "Failed to add expense"}
              </Text>
            </Card>
            <Spacer size="base" />
          </>
        ) : null}

        {/* Title */}
        <FormField label="Expense title" error={errors.title?.message}>
          <Input
            placeholder="Pizza, drinks, etc."
            value={title}
            onChangeText={(v) =>
              setValue("title", v, { shouldValidate: true })
            }
            error={errors.title?.message}
          />
        </FormField>

        {/* Total amount */}
        <FormField label="Total amount" error={errors.total_amount?.message}>
          <NumericInput
            value={total}
            onChangeText={(v) =>
              setValue("total_amount", v, { shouldValidate: true })
            }
            prefix={currencySymbol(game?.currency ?? "ILS")}
            placeholder="40.00"
            decimal
            error={errors.total_amount?.message}
          />
        </FormField>

        {/* Paid by */}
        <Section title="Paid by">
          {participantsLoading ? (
            <Skeleton height={tokens.size.touchTarget} radius={tokens.radius.lg} />
          ) : isDealer ? (
            <SelectField
              options={participantOptions}
              value={paidBy ?? ""}
              onSelect={setPaidBy}
            />
          ) : (
            <Card variant="default" padding="compact">
              <Row gap="sm" align="center">
                <Badge label="You" variant="accent" />
                <Text variant="bodyBold">
                  {myParticipant?.display_name ?? "You"}
                </Text>
              </Row>
            </Card>
          )}
        </Section>

        {/* Split among */}
        <Section
          title="Split among"
          subtitle={`${selectedParticipants.length} selected`}
        >
          {participantsLoading ? (
            <Skeleton height={tokens.size.touchTarget} radius={tokens.radius.lg} />
          ) : (
            <View style={styles.splitChipRow}>
              {participants.map((p) => {
                const included = splitIds.has(p.id);
                return (
                  <Pressable
                    key={p.id}
                    style={[
                      styles.splitChip,
                      included && styles.splitChipIncluded,
                    ]}
                    onPress={() => toggleSplitId(p.id)}
                    accessibilityRole="checkbox"
                    accessibilityState={{ checked: included }}
                  >
                    <Text
                      variant="captionBold"
                      color={included ? "white" : "secondary"}
                    >
                      {included ? "✓ " : ""}{p.display_name}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          )}
          {selectedParticipants.length === 0 ? (
            <Text variant="caption" color="negative" style={styles.splitError}>
              Select at least one participant to split the expense
            </Text>
          ) : null}
        </Section>

        {/* Split preview */}
        {previewSplits.length > 0 ? (
          <Section title="Split preview">
            <Card variant="default" padding="compact">
              <Text variant="caption" color="secondary" style={styles.splitPreviewHeader}>
                Equal split among {selectedParticipants.length}{" "}
                {selectedParticipants.length === 1 ? "participant" : "participants"}
              </Text>
              <Spacer size="sm" />
              {previewSplits.map((s, idx) => {
                const name =
                  participants.find((p) => p.id === s.participant_id)
                    ?.display_name ?? "Unknown";
                return (
                  <View key={s.participant_id}>
                    {idx > 0 && <Divider subtle />}
                    <View style={styles.splitRow}>
                      <Text variant="body" numberOfLines={1} style={styles.splitName}>
                        {name}
                      </Text>
                      <MoneyAmount
                        amount={parseFloat(s.share_amount)}
                        currency={game?.currency ?? "ILS"}
                        size="sm"
                      />
                    </View>
                  </View>
                );
              })}
            </Card>
          </Section>
        ) : null}

        <Spacer size="md" />

        {/* Submit */}
        <Button
          label="Add Expense"
          variant="primary"
          size="lg"
          fullWidth
          loading={mutation.isPending}
          disabled={!canSubmit}
          onPress={handleSubmit((v) => mutation.mutate(v))}
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
  splitChipRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: tokens.spacing.sm,
  },
  splitChip: {
    paddingHorizontal: tokens.spacing.base,
    paddingVertical: tokens.spacing.sm,
    borderRadius: tokens.radius.lg,
    backgroundColor: tokens.color.bg.surface,
    borderWidth: 1,
    borderColor: tokens.color.border.default,
    minHeight: tokens.size.touchTarget,
    justifyContent: "center",
    alignItems: "center",
  },
  splitChipIncluded: {
    backgroundColor: tokens.color.accent.muted,
    borderColor: tokens.color.accent.primary,
  },
  splitError: {
    marginTop: tokens.spacing.xs,
  },
  splitPreviewHeader: {
    marginBottom: tokens.spacing.xs,
  },
  splitRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: tokens.spacing.sm,
  },
  splitName: {
    flex: 1,
  },
});
