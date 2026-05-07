/**
 * Edit Buy-Ins screen — dealer-only retroactive editing of buy-ins on closed games.
 *
 * Lists all existing buy-ins with edit/delete options.
 * Provides an "Add Buy-In" form at the bottom.
 * Each edit triggers re-settlement on the backend.
 */

import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery } from "@tanstack/react-query";
import { Stack, useLocalSearchParams, useRouter } from "expo-router";
import { useState } from "react";
import { useForm } from "react-hook-form";
import {
  Alert,
  Pressable,
  StyleSheet,
  View,
} from "react-native";
import { z } from "zod";

import {
  Screen,
  Section,
  Card,
  Text,
  Button,
  Spacer,
  Divider,
  Row,
  Badge,
  Skeleton,
  NumericInput,
  currencySymbol,
} from "@/components";

import {
  useCreateClosedBuyIn,
  useDeleteClosedBuyIn,
  useUpdateClosedBuyIn,
} from "@/features/game-edits/useGameEdits";
import { cashToChips, chipsToCash } from "@/lib/buyInAutofill";
import { queryKeys } from "@/lib/queryKeys";
import * as gameService from "@/services/gameService";
import * as ledgerService from "@/services/ledgerService";
import { tokens } from "@/theme";
import type { BuyIn, BuyInType, Participant } from "@/types/game";

// ---------------------------------------------------------------------------
// Inline edit form for a single buy-in
// ---------------------------------------------------------------------------

function EditBuyInRow({
  buyIn,
  participantName,
  currency,
  chipCashRate,
  gameId,
}: {
  buyIn: BuyIn;
  participantName: string;
  currency: string;
  chipCashRate: number;
  gameId: string;
}) {
  const [editing, setEditing] = useState(false);
  const [cashVal, setCashVal] = useState(
    parseFloat(buyIn.cash_amount).toFixed(2),
  );
  const [chipsVal, setChipsVal] = useState(
    parseFloat(buyIn.chips_amount).toFixed(2),
  );

  const updateMutation = useUpdateClosedBuyIn(gameId);
  const deleteMutation = useDeleteClosedBuyIn(gameId);

  function handleCashChange(v: string) {
    setCashVal(v);
    if (chipCashRate > 0) {
      const cash = parseFloat(v);
      if (!isNaN(cash) && cash > 0) {
        setChipsVal(String(cashToChips(cash, chipCashRate)));
      }
    }
  }

  function handleChipsChange(v: string) {
    setChipsVal(v);
    if (chipCashRate > 0) {
      const chips = parseFloat(v);
      if (!isNaN(chips) && chips >= 0) {
        setCashVal(chipsToCash(chips, chipCashRate).toFixed(2));
      }
    }
  }

  function handleSave() {
    const cash = parseFloat(cashVal);
    const chips = parseFloat(chipsVal);
    if (isNaN(cash) || cash <= 0) {
      Alert.alert("Invalid", "Cash amount must be greater than 0");
      return;
    }
    if (isNaN(chips) || chips < 0) {
      Alert.alert("Invalid", "Chips amount must be 0 or greater");
      return;
    }
    updateMutation.mutate(
      {
        buyInId: buyIn.id,
        data: {
          cash_amount: cash.toFixed(2),
          chips_amount: chips.toFixed(2),
        },
      },
      {
        onSuccess: () => setEditing(false),
        onError: (err) =>
          Alert.alert(
            "Error",
            err instanceof Error ? err.message : "Failed to update",
          ),
      },
    );
  }

  function handleDelete() {
    Alert.alert(
      "Delete Buy-In",
      `Delete ${participantName}'s ${buyIn.buy_in_type} buy-in of ${currencySymbol(currency)}${parseFloat(buyIn.cash_amount).toFixed(2)}?`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: () =>
            deleteMutation.mutate(buyIn.id, {
              onError: (err) =>
                Alert.alert(
                  "Error",
                  err instanceof Error ? err.message : "Failed to delete",
                ),
            }),
        },
      ],
    );
  }

  const isPending = updateMutation.isPending || deleteMutation.isPending;

  if (editing) {
    return (
      <Card style={[rowStyles.card, rowStyles.cardEditing]}>
        <Row justify="between" align="center">
          <Text variant="bodyBold">{participantName}</Text>
          <Badge
            label={buyIn.buy_in_type}
            variant="neutral"
          />
        </Row>

        <Spacer size="md" />
        <View style={rowStyles.inputRow}>
          <View style={rowStyles.inputField}>
            <NumericInput
              value={cashVal}
              onChangeText={handleCashChange}
              prefix={currencySymbol(currency)}
              decimal
            />
          </View>
          <View style={rowStyles.inputField}>
            <NumericInput
              value={chipsVal}
              onChangeText={handleChipsChange}
              suffix="chips"
              decimal
            />
          </View>
        </View>

        <Spacer size="md" />
        <Row gap="sm">
          <View style={rowStyles.actionFlex}>
            <Button
              label="Save"
              variant="primary"
              fullWidth
              loading={updateMutation.isPending}
              disabled={isPending}
              onPress={handleSave}
            />
          </View>
          <View style={rowStyles.actionFlex}>
            <Button
              label="Cancel"
              variant="secondary"
              fullWidth
              onPress={() => setEditing(false)}
            />
          </View>
        </Row>
      </Card>
    );
  }

  return (
    <Card style={rowStyles.card}>
      <Row justify="between" align="center">
        <View style={rowStyles.nameColumn}>
          <Row gap="sm" align="center">
            <Text variant="bodyBold" numberOfLines={1}>
              {participantName}
            </Text>
            <Badge label={buyIn.buy_in_type} variant="neutral" />
          </Row>
          <Spacer size="xs" />
          <Text variant="caption" color="secondary">
            {currencySymbol(currency)}{parseFloat(buyIn.cash_amount).toFixed(2)} —{" "}
            {parseFloat(buyIn.chips_amount).toFixed(0)} chips
          </Text>
        </View>
        <Row gap="sm">
          <Button
            label="Edit"
            variant="secondary"
            onPress={() => setEditing(true)}
          />
          <Button
            label="Del"
            variant="destructive"
            disabled={deleteMutation.isPending}
            onPress={handleDelete}
          />
        </Row>
      </Row>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Add new buy-in form
// ---------------------------------------------------------------------------

const addSchema = z.object({
  cash_amount: z
    .string()
    .min(1, "Required")
    .refine((v) => parseFloat(v) > 0, "Must be > 0"),
  chips_amount: z
    .string()
    .min(1, "Required")
    .refine((v) => parseFloat(v) >= 0, "Must be >= 0"),
});

type AddFormValues = z.infer<typeof addSchema>;

const BUY_IN_TYPES: BuyInType[] = ["initial", "rebuy", "addon"];

function AddBuyInForm({
  gameId,
  participants,
  chipCashRate,
}: {
  gameId: string;
  participants: Participant[];
  chipCashRate: number;
}) {
  const [selectedParticipant, setSelectedParticipant] = useState<string | null>(
    null,
  );
  const [buyInType, setBuyInType] = useState<BuyInType>("rebuy");
  const createMutation = useCreateClosedBuyIn(gameId);

  const {
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors },
  } = useForm<AddFormValues>({
    resolver: zodResolver(addSchema),
    defaultValues: { cash_amount: "", chips_amount: "" },
  });

  const cashAmount = watch("cash_amount");
  const chipsAmount = watch("chips_amount");

  function handleCashChange(v: string) {
    setValue("cash_amount", v, { shouldValidate: true });
    if (chipCashRate > 0) {
      const cash = parseFloat(v);
      if (!isNaN(cash) && cash > 0) {
        setValue("chips_amount", String(cashToChips(cash, chipCashRate)), {
          shouldValidate: true,
        });
      }
    }
  }

  function handleChipsChange(v: string) {
    setValue("chips_amount", v, { shouldValidate: true });
    if (chipCashRate > 0) {
      const chips = parseFloat(v);
      if (!isNaN(chips) && chips >= 0) {
        setValue("cash_amount", chipsToCash(chips, chipCashRate).toFixed(2), {
          shouldValidate: true,
        });
      }
    }
  }

  function onSubmit(values: AddFormValues) {
    if (!selectedParticipant) return;
    createMutation.mutate(
      {
        participant_id: selectedParticipant,
        cash_amount: parseFloat(values.cash_amount).toFixed(2),
        chips_amount: parseFloat(values.chips_amount).toFixed(2),
        buy_in_type: buyInType,
      },
      {
        onSuccess: () => {
          reset();
          setSelectedParticipant(null);
        },
        onError: (err) =>
          Alert.alert(
            "Error",
            err instanceof Error ? err.message : "Failed to add buy-in",
          ),
      },
    );
  }

  return (
    <View>
      <Section title="Add Buy-In">
        <Text variant="captionBold" color="secondary">
          Participant
        </Text>
        <Spacer size="sm" />
        <View style={addStyles.chipRow}>
          {participants.map((p) => (
            <Pressable
              key={p.id}
              style={[
                addStyles.chip,
                selectedParticipant === p.id && addStyles.chipSelected,
              ]}
              onPress={() => setSelectedParticipant(p.id)}
            >
              <Text
                variant="caption"
                color={selectedParticipant === p.id ? "white" : "secondary"}
                style={
                  selectedParticipant === p.id ? { fontWeight: "600" } : undefined
                }
              >
                {p.display_name}
              </Text>
            </Pressable>
          ))}
        </View>

        <Spacer size="md" />
        <Text variant="captionBold" color="secondary">
          Type
        </Text>
        <Spacer size="sm" />
        <View style={addStyles.chipRow}>
          {BUY_IN_TYPES.map((t) => (
            <Pressable
              key={t}
              style={[
                addStyles.chip,
                buyInType === t && addStyles.chipSelected,
              ]}
              onPress={() => setBuyInType(t)}
            >
              <Text
                variant="caption"
                color={buyInType === t ? "white" : "secondary"}
                style={buyInType === t ? { fontWeight: "600" } : undefined}
              >
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </Text>
            </Pressable>
          ))}
        </View>

        <Spacer size="md" />
        <View style={rowStyles.inputRow}>
          <View style={rowStyles.inputField}>
            <NumericInput
              value={cashAmount}
              onChangeText={handleCashChange}
              prefix={currencySymbol(currency)}
              placeholder="50.00"
              decimal
              error={errors.cash_amount?.message}
            />
          </View>
          <View style={rowStyles.inputField}>
            <NumericInput
              value={chipsAmount}
              onChangeText={handleChipsChange}
              suffix="chips"
              placeholder="5000"
              decimal
              error={errors.chips_amount?.message}
            />
          </View>
        </View>

        <Spacer size="base" />
        <Button
          label="Add Buy-In"
          variant="primary"
          fullWidth
          loading={createMutation.isPending}
          disabled={!selectedParticipant || createMutation.isPending}
          onPress={handleSubmit(onSubmit)}
        />
      </Section>
    </View>
  );
}

// ---------------------------------------------------------------------------
// Main screen
// ---------------------------------------------------------------------------

export default function EditBuyInsScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();

  const { data: game } = useQuery({
    queryKey: queryKeys.game(id),
    queryFn: () => gameService.getGame(id),
    enabled: !!id,
  });

  const { data: participants = [] } = useQuery({
    queryKey: queryKeys.participants(id),
    queryFn: () => gameService.getParticipants(id),
    enabled: !!id,
  });

  const { data: buyIns = [], isLoading } = useQuery({
    queryKey: queryKeys.buyIns(id),
    queryFn: () => ledgerService.listBuyIns(id),
    enabled: !!id,
  });

  const participantMap = Object.fromEntries(
    participants.map((p) => [p.id, p.display_name]),
  );

  const chipCashRate = game ? parseFloat(game.chip_cash_rate) : 0;
  const currency = game?.currency ?? "";

  return (
    <>
      <Stack.Screen options={{ title: "Edit Buy-Ins" }} />
      <Screen scrollable keyboardAvoiding>
        <Spacer size="base" />

        {/* Info banner */}
        <Card style={bannerStyles.info}>
          <Text variant="caption" color="secondary" style={bannerStyles.text}>
            Editing buy-ins on a closed game. Each change triggers automatic
            re-settlement and notifies all participants.
          </Text>
        </Card>

        <Spacer size="lg" />

        {/* Existing buy-ins */}
        <Section title="Existing Buy-Ins">
          {isLoading ? (
            <View style={{ gap: tokens.spacing.md }}>
              {[1, 2, 3].map((i) => (
                <Skeleton
                  key={i}
                  width="100%"
                  height={72}
                  radius={tokens.radius.lg}
                />
              ))}
            </View>
          ) : buyIns.length === 0 ? (
            <Text variant="body" color="muted">
              No buy-ins recorded.
            </Text>
          ) : (
            buyIns.map((b) => (
              <EditBuyInRow
                key={b.id}
                buyIn={b}
                participantName={participantMap[b.participant_id] ?? "Unknown"}
                currency={currency}
                chipCashRate={chipCashRate}
                gameId={id}
              />
            ))
          )}
        </Section>

        <Divider spacing={tokens.spacing.lg} />

        {/* Add form */}
        <AddBuyInForm
          gameId={id}
          participants={participants}
          chipCashRate={chipCashRate}
        />

        <Spacer size="lg" />
        <Button
          label="Done"
          variant="secondary"
          fullWidth
          onPress={() => router.back()}
        />

        <Spacer size="4xl" />
      </Screen>
    </>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const bannerStyles = StyleSheet.create({
  info: {
    borderLeftWidth: 3,
    borderLeftColor: tokens.color.accent.primary,
  },
  text: {
    // lineHeight inherited from Text variant="caption"
  },
});

const rowStyles = StyleSheet.create({
  card: {
    marginBottom: tokens.spacing.md,
  },
  cardEditing: {
    borderWidth: 1,
    borderColor: tokens.color.accent.primary,
  },
  nameColumn: {
    flex: 1,
    marginRight: tokens.spacing.md,
  },
  inputRow: {
    flexDirection: "row",
    gap: tokens.spacing.md,
  },
  inputField: {
    flex: 1,
  },
  actionFlex: {
    flex: 1,
  },
});

const addStyles = StyleSheet.create({
  chipRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: tokens.spacing.sm,
  },
  chip: {
    borderWidth: 1,
    borderColor: tokens.color.border.default,
    borderRadius: tokens.radius.xl,
    paddingHorizontal: tokens.spacing.base,
    paddingVertical: tokens.spacing.sm,
    minHeight: tokens.size.touchTarget,
    justifyContent: "center",
  },
  chipSelected: {
    backgroundColor: tokens.color.accent.primary,
    borderColor: tokens.color.accent.primary,
  },
});
