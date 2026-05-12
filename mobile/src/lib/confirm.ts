/**
 * Cross-platform confirm/notify helpers.
 *
 * React Native's `Alert.alert` is iOS/Android only — on `react-native-web` it
 * is a no-op, which silently breaks any flow that wraps a mutation inside an
 * Alert confirm or surfaces errors via Alert. Use these helpers anywhere a
 * confirmation or a one-button message dialog is needed.
 */

import { Alert, Platform } from "react-native";

/**
 * Ask the user to confirm an action.
 * Resolves with `true` if confirmed, `false` if cancelled/dismissed.
 */
export function confirmAsync(
  title: string,
  message: string,
  options?: { confirmLabel?: string; cancelLabel?: string; destructive?: boolean },
): Promise<boolean> {
  const confirmLabel = options?.confirmLabel ?? "OK";
  const cancelLabel = options?.cancelLabel ?? "Cancel";

  if (Platform.OS === "web") {
    const ok =
      typeof window !== "undefined" && typeof window.confirm === "function"
        ? window.confirm(`${title}\n\n${message}`)
        : true;
    return Promise.resolve(ok);
  }

  return new Promise<boolean>((resolve) => {
    Alert.alert(title, message, [
      { text: cancelLabel, style: "cancel", onPress: () => resolve(false) },
      {
        text: confirmLabel,
        style: options?.destructive ? "destructive" : "default",
        onPress: () => resolve(true),
      },
    ], { onDismiss: () => resolve(false) });
  });
}

/**
 * Show a one-button informational/error message.
 * Resolves once the user dismisses it.
 */
export function notifyAsync(title: string, message: string): Promise<void> {
  if (Platform.OS === "web") {
    if (typeof window !== "undefined" && typeof window.alert === "function") {
      window.alert(`${title}\n\n${message}`);
    }
    return Promise.resolve();
  }

  return new Promise<void>((resolve) => {
    Alert.alert(title, message, [{ text: "OK", onPress: () => resolve() }], {
      onDismiss: () => resolve(),
    });
  });
}
