/**
 * AppDialog — themed presentational dialog used by the dialog provider.
 *
 * Renders inside React Native's `Modal` primitive so it sits above the entire
 * navigator on both native and web. All visual values come from theme tokens.
 */

import React from "react";
import { Modal as RNModal, Pressable, StyleSheet, View } from "react-native";

import { Button } from "../primitives/Button";
import { Spacer } from "../primitives/Spacer";
import { Text } from "../primitives/Text";
import { shadows, tokens } from "@/theme";
import type { DialogVariant } from "@/lib/dialogController";

export interface AppDialogProps {
  visible: boolean;
  title: string;
  message: string;
  mode: "confirm" | "notify";
  confirmLabel?: string;
  cancelLabel?: string;
  destructive?: boolean;
  variant?: DialogVariant;
  onConfirm: () => void;
  onCancel: () => void;
}

const titleColorByVariant: Record<DialogVariant, "primary" | "negative" | "positive" | "warning" | "accent"> = {
  default: "primary",
  destructive: "negative",
  info: "accent",
  error: "negative",
  success: "positive",
};

export function AppDialog({
  visible,
  title,
  message,
  mode,
  confirmLabel,
  cancelLabel = "Cancel",
  destructive = false,
  variant = "default",
  onConfirm,
  onCancel,
}: AppDialogProps) {
  const effectiveDestructive = destructive || variant === "destructive";
  const titleColor = titleColorByVariant[variant];
  const resolvedConfirmLabel =
    confirmLabel ?? (mode === "confirm" ? "Confirm" : "OK");

  return (
    <RNModal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onCancel}
      // Web a11y hint
      accessibilityViewIsModal
    >
      <Pressable
        style={styles.backdrop}
        onPress={mode === "confirm" ? onCancel : onConfirm}
        accessibilityRole="button"
        accessibilityLabel="Dismiss dialog"
      >
        {/* Inner Pressable swallows taps so backdrop dismissal only triggers
            on actual backdrop clicks, not on clicks inside the card. */}
        <Pressable
          style={[styles.card, shadows.elevated]}
          onPress={() => {}}
          accessibilityRole="alert"
        >
          <Text variant="h3" align="center" color={titleColor}>
            {title}
          </Text>
          <Spacer size="sm" />
          <Text variant="body" align="center" color="secondary">
            {message}
          </Text>
          <Spacer size="xl" />

          {mode === "confirm" ? (
            <View style={styles.row}>
              <View style={styles.btnFlex}>
                <Button
                  label={cancelLabel}
                  variant="secondary"
                  onPress={onCancel}
                  fullWidth
                />
              </View>
              <View style={styles.btnFlex}>
                <Button
                  label={resolvedConfirmLabel}
                  variant={effectiveDestructive ? "destructive" : "primary"}
                  onPress={onConfirm}
                  fullWidth
                />
              </View>
            </View>
          ) : (
            <Button
              label={resolvedConfirmLabel}
              variant="primary"
              onPress={onConfirm}
              fullWidth
            />
          )}
        </Pressable>
      </Pressable>
    </RNModal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.6)",
    justifyContent: "center",
    alignItems: "center",
    padding: tokens.spacing.xl,
  },
  card: {
    backgroundColor: tokens.color.bg.elevated,
    borderRadius: tokens.radius.xl,
    padding: tokens.spacing.xl,
    width: "100%",
    maxWidth: 360,
    borderWidth: 1,
    borderColor: tokens.color.border.default,
  },
  row: {
    flexDirection: "row",
    gap: tokens.spacing.md,
  },
  btnFlex: {
    flex: 1,
  },
});
