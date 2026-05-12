/**
 * Imperative bridge between the `confirmAsync` / `notifyAsync` helpers and the
 * `AppDialogProvider` mounted at the app root.
 *
 * The helpers must be callable from anywhere (non-React contexts, mutation
 * callbacks, module top-level code), so a hook-based API would not work.
 * `AppDialogProvider` registers a presenter on mount; the helpers route
 * requests through it. If no provider is mounted (e.g. preview tooling or
 * tests) the helpers fall back to `window.confirm` / `window.alert`.
 */

export type DialogVariant =
  | "default"
  | "destructive"
  | "info"
  | "error"
  | "success";

export interface DialogRequest {
  title: string;
  message: string;
  mode: "confirm" | "notify";
  confirmLabel?: string;
  cancelLabel?: string;
  destructive?: boolean;
  variant?: DialogVariant;
}

export type DialogPresenter = (req: DialogRequest) => Promise<boolean>;

let _presenter: DialogPresenter | null = null;

/** Called by `AppDialogProvider` on mount and unmount. */
export function registerDialogPresenter(p: DialogPresenter | null): void {
  _presenter = p;
}

/**
 * Returns the active presenter, or null if no provider is currently mounted.
 * Callers use the null return value to fall back to a platform dialog.
 */
export function getDialogPresenter(): DialogPresenter | null {
  return _presenter;
}
