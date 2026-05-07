/**
 * Edit History screen — audit trail for retroactive edits on closed games.
 *
 * Read-only for all participants. Shows each edit chronologically with:
 *  - Who edited
 *  - What changed (edit type + before/after values)
 *  - When
 */

import { Stack, useLocalSearchParams } from "expo-router";
import { FlatList, RefreshControl, StyleSheet, View } from "react-native";

import {
  Screen,
  Text,
  Card,
  Badge,
  Spacer,
  Row,
  Divider,
  Skeleton,
  EmptyState,
} from "@/components";

import { useGameEdits } from "@/features/game-edits/useGameEdits";
import { tokens } from "@/theme";
import type { GameEdit, GameEditType } from "@/types/game";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const EDIT_TYPE_LABELS: Record<GameEditType, string> = {
  buyin_created: "Buy-in added",
  buyin_updated: "Buy-in updated",
  buyin_deleted: "Buy-in deleted",
  final_stack_updated: "Final stack updated",
};

const EDIT_TYPE_VARIANT: Record<GameEditType, "accent" | "warning" | "neutral"> = {
  buyin_created: "accent",
  buyin_updated: "neutral",
  buyin_deleted: "warning",
  final_stack_updated: "neutral",
};

function formatDate(isoString: string): string {
  const d = new Date(isoString);
  return d.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatValue(key: string, value: unknown): string {
  if (value == null) return "\u2014";
  if (typeof value === "number") return value.toFixed(2);
  if (typeof value === "string") {
    const n = parseFloat(value);
    if (!isNaN(n)) return n.toFixed(2);
    return value;
  }
  return String(value);
}

// ---------------------------------------------------------------------------
// Loading skeleton
// ---------------------------------------------------------------------------

function EditHistorySkeleton() {
  return (
    <Screen scrollable>
      <Spacer size="base" />
      <Skeleton width={120} height={16} />
      <Spacer size="lg" />
      {[1, 2, 3, 4].map((i) => (
        <View key={i} style={{ marginBottom: tokens.spacing.md }}>
          <Skeleton width="100%" height={100} radius={tokens.radius.lg} />
        </View>
      ))}
    </Screen>
  );
}

// ---------------------------------------------------------------------------
// Single edit entry
// ---------------------------------------------------------------------------

function EditEntry({ edit }: { edit: GameEdit }) {
  const label = EDIT_TYPE_LABELS[edit.edit_type] ?? edit.edit_type;
  const badgeVariant = EDIT_TYPE_VARIANT[edit.edit_type] ?? "neutral";

  // Determine which fields changed by comparing before/after
  const changedFields: { field: string; before: string; after: string }[] = [];

  if (edit.edit_type === "buyin_created" && edit.after_data) {
    if (edit.after_data.cash_amount != null)
      changedFields.push({
        field: "Cash",
        before: "\u2014",
        after: formatValue("cash", edit.after_data.cash_amount),
      });
    if (edit.after_data.chips_amount != null)
      changedFields.push({
        field: "Chips",
        before: "\u2014",
        after: formatValue("chips", edit.after_data.chips_amount),
      });
  } else if (edit.edit_type === "buyin_deleted" && edit.before_data) {
    if (edit.before_data.cash_amount != null)
      changedFields.push({
        field: "Cash",
        before: formatValue("cash", edit.before_data.cash_amount),
        after: "\u2014",
      });
    if (edit.before_data.chips_amount != null)
      changedFields.push({
        field: "Chips",
        before: formatValue("chips", edit.before_data.chips_amount),
        after: "\u2014",
      });
  } else if (edit.before_data && edit.after_data) {
    const allKeys = new Set([
      ...Object.keys(edit.before_data),
      ...Object.keys(edit.after_data),
    ]);
    for (const key of allKeys) {
      if (key.endsWith("_id") || key === "buy_in_type" || key.endsWith("_at"))
        continue;
      const before = edit.before_data[key];
      const after = edit.after_data[key];
      if (String(before) !== String(after)) {
        const fieldLabel = key
          .replace(/_/g, " ")
          .replace(/\b\w/g, (c) => c.toUpperCase());
        changedFields.push({
          field: fieldLabel,
          before: formatValue(key, before),
          after: formatValue(key, after),
        });
      }
    }
  }

  return (
    <Card style={entryStyles.card}>
      <Row justify="between" align="center">
        <Badge label={label} variant={badgeVariant} />
        <Text variant="caption" color="muted">
          {formatDate(edit.created_at)}
        </Text>
      </Row>

      <Spacer size="sm" />
      <Text variant="caption" color="secondary">
        by {edit.edited_by_display_name}
      </Text>

      {changedFields.length > 0 && (
        <>
          <Spacer size="sm" />
          <View style={entryStyles.changeBox}>
            {changedFields.map((change, i) => (
              <Row key={i} justify="start" gap="sm" align="center" wrap>
                <Text variant="captionBold" color="secondary">
                  {change.field}:
                </Text>
                <Text variant="caption" color="negative">
                  {change.before}
                </Text>
                <Text variant="caption" color="muted">
                  {"\u2192"}
                </Text>
                <Text variant="caption" color="positive">
                  {change.after}
                </Text>
              </Row>
            ))}
          </View>
        </>
      )}
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Main screen
// ---------------------------------------------------------------------------

export default function EditHistoryScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();

  const {
    data: edits = [],
    isLoading,
    refetch,
    isRefetching,
  } = useGameEdits(id);

  if (isLoading) {
    return (
      <>
        <Stack.Screen options={{ title: "Edit History" }} />
        <EditHistorySkeleton />
      </>
    );
  }

  return (
    <>
      <Stack.Screen options={{ title: "Edit History" }} />
      <FlatList
        data={edits}
        keyExtractor={(item) => item.id}
        style={listStyles.list}
        contentContainerStyle={listStyles.container}
        renderItem={({ item }) => <EditEntry edit={item} />}
        refreshControl={
          <RefreshControl
            refreshing={isRefetching}
            onRefresh={refetch}
            tintColor={tokens.color.accent.primary}
          />
        }
        ListHeaderComponent={
          edits.length > 0 ? (
            <View style={listStyles.header}>
              <Text variant="caption" color="secondary">
                {edits.length} edit{edits.length !== 1 ? "s" : ""} recorded
              </Text>
              <Spacer size="md" />
            </View>
          ) : null
        }
        ListEmptyComponent={
          <EmptyState
            title="No edits yet"
            description="No retroactive edits have been made to this game."
          />
        }
      />
    </>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const listStyles = StyleSheet.create({
  list: {
    flex: 1,
    backgroundColor: tokens.color.bg.primary,
  },
  container: {
    padding: tokens.spacing.lg,
    paddingBottom: tokens.spacing["4xl"],
  },
  header: {
    marginBottom: tokens.spacing.xs,
  },
});

const entryStyles = StyleSheet.create({
  card: {
    marginBottom: tokens.spacing.md,
  },
  changeBox: {
    backgroundColor: tokens.color.bg.primary,
    borderRadius: tokens.radius.sm,
    padding: tokens.spacing.md,
    gap: tokens.spacing.xs,
  },
});
