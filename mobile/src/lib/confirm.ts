/**
 * Cross-platform confirm/notify helpers.
 *
 * Primary path: route requests through the `AppDialogProvider` mounted at the
 * app root, which renders a themed in-app dialog on both native and web.
 *
 * Fallback path: if no provider is mounted (preview tooling, jest, or before
 * the React tree has finished mounting), fall back to `Alert.alert` on native
 * and `window.confirm` / `window.alert` on web. These ugly system dialogs are
 * intentionally last-resort only so a missing provider never silently
 * swallows a user-facing message.
 */

import { Alert, Platform } from "react-native";

import {
  type DialogVariant,
  getDialogPresenter,
} from "./dialogController";

export interface ConfirmOptions {
  confirmLabel?: string;
  cancelLabel?: string;
  destructive?: boolean;
  variant?: DialogVariant;
}

export interface NotifyOptions {
  okLabel?: string;
  variant?: DialogVariant;
}

/**
 * Ask the user to confirm an action.
 * Resolves with `true` if confirmed, `false` if cancelled/dismissed.
 */
export function confirmAsync(
  title: string,
  message: string,
  options?: ConfirmOptions,
): Promise<boolean> {
  const presenter = getDialogPresenter();
  if (presenter) {
    return presenter({
      mode: "confirm",
      title,
      message,
      confirmLabel: options?.confirmLabel,
      cancelLabel: options?.cancelLabel,
      destructive: options?.destructive,
      variant: options?.variant,
    });
  }
  return platformConfirmFallback(title, message, options);
}

/**
 * Show a one-button informational/error message.
 * Resolves once the user dismisses it.
 */
export function notifyAsync(
  title: string,
  message: string,
  options?: NotifyOptions,
): Promise<void> {
  const presenter = getDialogPresenter();
  if (presenter) {
    return presenter({
      mode: "notify",
      title,
      message,
      confirmLabel: options?.okLabel,
      variant: options?.variant,
    }).then(() => undefined);
  }
  return platformNotifyFallback(title, message, options);
}

// ---------------------------------------------------------------------------
// Fallbacks — only reached when the AppDialogProvider is not mounted.
// ---------------------------------------------------------------------------

function platformConfirmFallback(
  title: string,
  message: string,
  options?: ConfirmOptions,
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
    Alert.alert(
      title,
      message,
      [
        { text: cancelLabel, style: "cancel", onPress: () => resolve(false) },
        {
          text: confirmLabel,
          style: options?.destructive ? "destructive" : "default",
          onPress: () => resolve(true),
        },
      ],
      { onDismiss: () => resolve(false) },
    );
  });
}

function platformNotifyFallback(
  title: string,
  message: string,
  options?: NotifyOptions,
): Promise<void> {
  const okLabel = options?.okLabel ?? "OK";

  if (Platform.OS === "web") {
    if (typeof window !== "undefined" && typeof window.alert === "function") {
      window.alert(`${title}\n\n${message}`);
    }
    return Promise.resolve();
  }

  return new Promise<void>((resolve) => {
    Alert.alert(title, message, [{ text: okLabel, onPress: () => resolve() }], {
      onDismiss: () => resolve(),
    });
  });
}
