/**
 * AppDialogProvider — mounts a single themed `AppDialog` at the app root and
 * registers an imperative presenter so `confirmAsync` / `notifyAsync` can
 * trigger dialogs from anywhere (mutation callbacks, plain async functions,
 * non-React code).
 *
 * Concurrent requests are serialised by a FIFO queue so that back-to-back
 * errors are not dropped on the floor.
 */

import React, { useEffect, useRef, useState } from "react";

import {
  type DialogRequest,
  registerDialogPresenter,
} from "@/lib/dialogController";
import { AppDialog } from "./AppDialog";

interface PendingDialog {
  req: DialogRequest;
  resolve: (result: boolean) => void;
}

const ANIMATION_GAP_MS = 150;

export function AppDialogProvider({ children }: { children: React.ReactNode }) {
  const [current, setCurrent] = useState<PendingDialog | null>(null);
  const currentRef = useRef<PendingDialog | null>(null);
  const queueRef = useRef<PendingDialog[]>([]);

  // Keep the ref in sync so the imperative presenter, which closes over
  // initial state, can always read the latest visible dialog.
  useEffect(() => {
    currentRef.current = current;
  }, [current]);

  useEffect(() => {
    const presenter = (req: DialogRequest): Promise<boolean> =>
      new Promise<boolean>((resolve) => {
        const item: PendingDialog = { req, resolve };
        if (currentRef.current == null) {
          currentRef.current = item;
          setCurrent(item);
        } else {
          queueRef.current.push(item);
        }
      });

    registerDialogPresenter(presenter);
    return () => {
      registerDialogPresenter(null);
      // Reject any in-flight requests as cancelled so promises don't hang.
      if (currentRef.current) currentRef.current.resolve(false);
      for (const q of queueRef.current) q.resolve(false);
      currentRef.current = null;
      queueRef.current = [];
    };
  }, []);

  const resolveCurrent = (result: boolean) => {
    const cur = currentRef.current;
    if (cur) cur.resolve(result);
    const next = queueRef.current.shift() ?? null;
    currentRef.current = next;
    setCurrent(null);
    if (next) {
      // Brief gap so the modal animation can complete before re-opening,
      // avoiding flicker on both native and web.
      setTimeout(() => setCurrent(next), ANIMATION_GAP_MS);
    }
  };

  const visible = current != null;

  return (
    <>
      {children}
      <AppDialog
        visible={visible}
        title={current?.req.title ?? ""}
        message={current?.req.message ?? ""}
        mode={current?.req.mode ?? "notify"}
        confirmLabel={current?.req.confirmLabel}
        cancelLabel={current?.req.cancelLabel}
        destructive={current?.req.destructive}
        variant={current?.req.variant}
        onConfirm={() => resolveCurrent(true)}
        onCancel={() => resolveCurrent(false)}
      />
    </>
  );
}
