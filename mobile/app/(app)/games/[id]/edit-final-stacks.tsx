/**
 * Edit Final Stacks screen — dealer-only retroactive editing on closed games.
 *
 * Lists all participants with their current final chip count.
 * Dealer can tap to edit each final stack value.
 * Each edit triggers re-settlement on the backend.
 */

import { useQuery } from "@tanstack/react-query";
import { Stack, useLocalSearchParams, useRouter } from "expo-router";
import { useState } from "react";
import { Alert, StyleSheet, View } from "react-native";

import {
  Screen,
  Section,
  Card,
  Text,
  Button,
  Spacer,
  Row,
  Skeleton,
  NumericInput,
} from "@/components";

import { useUpdateClosedFinalStack } from "@/features/game-edits/useGameEdits";
import { queryKeys } from "@/lib/queryKeys";
import * as gameService from "@/services/gameService";
import * as ledgerService from "@/services/ledgerService";
import { tokens } from "@/theme";
import type { FinalStack, Participant } from "@/types/game";

// ---------------------------------------------------------------------------
// Editable row for a single participant's final stack
// ---------------------------------------------------------------------------

function FinalStackRow({
  participant,
  finalStack,
  currency,
  chipCashRate,
  gameId,
}: {
  participant: Participant;
  finalStack: FinalStack | undefined;
  currency: string;
  chipCashRate: number;
  gameId: string;
}) {
  const [editing, setEditing] = useState(false);
  const [chipsVal, setChipsVal] = useState(
    finalStack ? parseFloat(finalStack.chips_amount).toFixed(0) : "0",
  );
  const updateMutation = useUpdateClosedFinalStack(gameId);

  const cashValue =
    finalStack && chipCashRate > 0
      ? (parseFloat(finalStack.chips_amount) * chipCashRate).toFixed(2)
      : null;

  function handleSave() {
    const chips = parseFloat(chipsVal);
    if (isNaN(chips) || chips < 0) {
      Alert.alert("Invalid", "Chips amount must be 0 or greater");
      return;
    }
    updateMutation.mutate(
      {
        participantId: participant.id,
        data: { chips_amount: chips.toFixed(2) },
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

  if (editing) {
    return (
      <Card style={[cardStyles.card, cardStyles.cardEditing]}>
        <Text variant="bodyBold">{participant.display_name}</Text>

        <Spacer size="md" />
        <NumericInput
          value={chipsVal}
          onChangeText={setChipsVal}
          suffix="chips"
          placeholder="0"
          decimal
        />

        <Spacer size="md" />
        <Row gap="sm">
          <View style={cardStyles.actionFlex}>
            <Button
              label="Save"
              variant="primary"
              fullWidth
              loading={updateMutation.isPending}
              disabled={updateMutation.isPending}
              onPress={handleSave}
            />
          </View>
          <View style={cardStyles.actionFlex}>
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
    <Card style={cardStyles.card} onPress={() => setEditing(true)}>
      <Row justify="between" align="center">
        <Text variant="bodyBold" numberOfLines={1} style={cardStyles.name}>
          {participant.display_name}
        </Text>
        <Button label="Edit" variant="secondary" onPress={() => setEditing(true)} />
      </Row>

      <Spacer size="xs" />
      <Text variant="body" color="secondary">
        {finalStack
          ? `${parseFloat(finalStack.chips_amount).toFixed(0)} chips`
          : "No final stack"}
      </Text>
      {cashValue != null && (
        <Text variant="caption" color="muted">
          = {currency} {cashValue}
        </Text>
      )}
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Main screen
// ---------------------------------------------------------------------------

export default function EditFinalStacksScreen() {
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

  const { data: finalStacks = [], isLoading } = useQuery({
    queryKey: queryKeys.finalStacks(id),
    queryFn: () => ledgerService.listFinalStacks(id),
    enabled: !!id,
  });

  const chipCashRate = game ? parseFloat(game.chip_cash_rate) : 0;
  const currency = game?.currency ?? "";

  const finalStackMap = Object.fromEntries(
    finalStacks.map((fs) => [fs.participant_id, fs]),
  );

  return (
    <>
      <Stack.Screen options={{ title: "Edit Final Stacks" }} />
      <Screen scrollable keyboardAvoiding>
        <Spacer size="base" />

        {/* Info banner */}
        <Card style={bannerStyles.info}>
          <Text variant="caption" color="secondary" style={bannerStyles.text}>
            Editing final chip counts on a closed game. Each change triggers
            automatic re-settlement and notifies all participants.
          </Text>
        </Card>

        <Spacer size="lg" />

        <Section title="Final Stacks">
          {isLoading ? (
            <View style={{ gap: tokens.spacing.md }}>
              {[1, 2, 3].map((i) => (
                <Skeleton
                  key={i}
                  width="100%"
                  height={80}
                  radius={tokens.radius.lg}
                />
              ))}
            </View>
          ) : (
            participants.map((p) => (
              <FinalStackRow
                key={p.id}
                participant={p}
                finalStack={finalStackMap[p.id]}
                currency={currency}
                chipCashRate={chipCashRate}
                gameId={id}
              />
            ))
          )}
        </Section>

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

const cardStyles = StyleSheet.create({
  card: {
    marginBottom: tokens.spacing.md,
  },
  cardEditing: {
    borderWidth: 1,
    borderColor: tokens.color.accent.primary,
  },
  name: {
    flex: 1,
    marginRight: tokens.spacing.md,
  },
  actionFlex: {
    flex: 1,
  },
});
