/**
 * Buy-in entry screen — dealer only.
 *
 * Select a participant, enter cash_amount or chips_amount, and buy_in_type.
 * Smart autofill: editing one amount field auto-calculates the other using
 * the game's chip_cash_rate.
 *
 *   cash  → chips : Math.floor(cash / chip_cash_rate)
 *   chips → cash  : chips * chip_cash_rate
 *
 * Either field can be manually overridden — "last edited" always drives.
 * A subtle "← auto" label marks the autofilled field.
 * chip_cash_rate = 0 disables autofill and shows a warning.
 *
 * On success: go back (the game screen refreshes via WS event).
 */

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Stack, useLocalSearchParams, useRouter } from "expo-router";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { StyleSheet, View } from "react-native";
import { z } from "zod";

import {
  Text,
  Button,
  Card,
  Badge,
  Spacer,
  Screen,
  Section,
  Row,
  FormField,
  NumericInput,
  SelectField,
  Skeleton,
  currencySymbol,
} from "@/components";

import { cashToChips, chipsToCash } from "@/lib/buyInAutofill";
import { queryKeys } from "@/lib/queryKeys";
import * as gameService from "@/services/gameService";
import * as ledgerService from "@/services/ledgerService";
import { tokens } from "@/theme";
import type { BuyInType } from "@/types/game";

const BUY_IN_TYPES: BuyInType[] = ["initial", "rebuy", "addon"];

const buyInTypeOptions = BUY_IN_TYPES.map((t) => ({
  label: t.charAt(0).toUpperCase() + t.slice(1),
  value: t,
}));

const schema = z.object({
  cash_amount: z
    .string()
    .min(1, "Cash amount is required")
    .refine((v) => parseFloat(v) > 0, "Must be greater than 0"),
  chips_amount: z
    .string()
    .min(1, "Chips amount is required")
    .refine((v) => parseFloat(v) >= 0, "Must be 0 or greater"),
});

type FormValues = z.infer<typeof schema>;

/** Which field the dealer last typed in — determines the autofill direction. */
type EditedField = "cash" | "chips" | null;

export default function BuyInScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();

  const [selectedParticipant, setSelectedParticipant] = useState<string | null>(
    null,
  );
  const [buyInType, setBuyInType] = useState<BuyInType>("initial");
  // Tracks which field the dealer last edited so we know which label to mark "← auto".
  const [lastEdited, setLastEdited] = useState<EditedField>(null);

  // Game data — serves from cache (already loaded in parent game screen).
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

  // Parse rate once so helpers have a number to work with.
  const chipCashRate = game ? parseFloat(game.chip_cash_rate) : null;
  const rateIsZero = chipCashRate !== null && chipCashRate === 0;

  const mutation = useMutation({
    mutationFn: (values: FormValues) =>
      ledgerService.createBuyIn(id, {
        participant_id: selectedParticipant!,
        cash_amount: parseFloat(values.cash_amount).toFixed(2),
        chips_amount: parseFloat(values.chips_amount).toFixed(2),
        buy_in_type: buyInType,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.buyIns(id) });
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
    defaultValues: { cash_amount: "", chips_amount: "" },
  });

  const cashAmount = watch("cash_amount");
  const chipsAmount = watch("chips_amount");

  // ---------------------------------------------------------------------------
  // Autofill handlers — "last editor wins"
  // RHF's setValue() does NOT fire onChangeText, so there is no circular loop.
  // ---------------------------------------------------------------------------

  function handleCashChange(v: string) {
    setValue("cash_amount", v, { shouldValidate: true });
    setLastEdited("cash");

    if (rateIsZero || chipCashRate === null) return;

    const cash = parseFloat(v);
    if (!isNaN(cash) && cash > 0) {
      const chips = cashToChips(cash, chipCashRate);
      setValue("chips_amount", String(chips), { shouldValidate: true });
    }
  }

  function handleChipsChange(v: string) {
    setValue("chips_amount", v, { shouldValidate: true });
    setLastEdited("chips");

    if (rateIsZero || chipCashRate === null) return;

    const chips = parseFloat(v);
    if (!isNaN(chips) && chips >= 0) {
      const cash = chipsToCash(chips, chipCashRate);
      setValue("cash_amount", cash.toFixed(2), { shouldValidate: true });
    }
  }

  // Build participant options for SelectField
  const participantOptions = participants.map((p) => ({
    label: p.display_name,
    value: p.id,
  }));

  return (
    <>
      <Stack.Screen options={{ title: "Add Buy-in" }} />
      <Screen scrollable keyboardAvoiding>
        <Spacer size="base" />

        {/* Error banner */}
        {mutation.error ? (
          <>
            <Card variant="default" padding="compact" style={styles.errorBanner}>
              <Text variant="body" color="negative">
                {mutation.error instanceof Error
                  ? mutation.error.message
                  : "Failed to add buy-in"}
              </Text>
            </Card>
            <Spacer size="base" />
          </>
        ) : null}

        {/* Zero rate warning */}
        {rateIsZero ? (
          <>
            <Card variant="default" padding="compact" style={styles.warningBanner}>
              <Text variant="caption" color="warning">
                chip_cash_rate is 0 — autofill is disabled. Enter both amounts manually.
              </Text>
            </Card>
            <Spacer size="base" />
          </>
        ) : null}

        {/* Participant selector */}
        <Section title="Participant">
          {participantsLoading ? (
            <Skeleton height={tokens.size.touchTarget} radius={tokens.radius.lg} />
          ) : (
            <SelectField
              options={participantOptions}
              value={selectedParticipant ?? ""}
              onSelect={setSelectedParticipant}
              error={!selectedParticipant ? undefined : undefined}
            />
          )}
        </Section>

        {/* Buy-in type */}
        <Section title="Type">
          <SelectField
            options={buyInTypeOptions}
            value={buyInType}
            onSelect={(v) => setBuyInType(v as BuyInType)}
          />
        </Section>

        {/* Cash amount */}
        <FormField
          label={
            lastEdited === "chips" && chipsAmount !== "" && cashAmount !== ""
              ? "Cash amount  ← auto"
              : "Cash amount"
          }
          error={errors.cash_amount?.message}
        >
          <NumericInput
            value={cashAmount}
            onChangeText={handleCashChange}
            prefix={currencySymbol(game?.currency ?? "ILS")}
            placeholder="50.00"
            decimal
            error={errors.cash_amount?.message}
          />
        </FormField>

        {/* Chips amount */}
        <FormField
          label={
            lastEdited === "cash" && cashAmount !== "" && chipsAmount !== ""
              ? "Chips amount  ← auto"
              : "Chips amount"
          }
          error={errors.chips_amount?.message}
        >
          <NumericInput
            value={chipsAmount}
            onChangeText={handleChipsChange}
            suffix="chips"
            placeholder="5000"
            decimal
            error={errors.chips_amount?.message}
          />
        </FormField>

        <Spacer size="lg" />

        {/* Submit */}
        <Button
          label="Add Buy-in"
          variant="primary"
          size="lg"
          fullWidth
          loading={mutation.isPending}
          disabled={!selectedParticipant || mutation.isPending}
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
  warningBanner: {
    borderWidth: 1,
    borderColor: tokens.color.semantic.warning,
  },
});
