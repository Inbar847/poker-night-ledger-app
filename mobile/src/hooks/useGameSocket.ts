/**
 * WebSocket hook for real-time game room updates.
 *
 * Connects to ws://<host>/ws/games/{gameId}?token=<access_token>
 * and invalidates the relevant TanStack Query caches when events arrive.
 *
 * Reconnect strategy:
 *   - Exponential backoff starting at 1 s, capped at 30 s, with random jitter.
 *   - Up to 10 reconnect attempts, then stops (navigating away and back resets).
 *   - Returns a `reconnecting` flag so the game screen can show a banner.
 *   - On successful reconnect, TanStack Query refetches stale queries automatically.
 *
 * Events are NOT replayed on reconnect. If the hook unmounts and remounts,
 * callers should re-fetch game state via the REST API (TanStack Query does
 * this automatically when the component remounts, unless the cache is fresh).
 */

import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { WS_URL } from "@/lib/config";
import { queryKeys } from "@/lib/queryKeys";
import { useAuthStore } from "@/store/authStore";

const MAX_RETRIES = 10;
const BASE_DELAY_MS = 1_000;
const MAX_DELAY_MS = 30_000;

function backoffDelay(attempt: number): number {
  const exponential = Math.min(BASE_DELAY_MS * 2 ** attempt, MAX_DELAY_MS);
  // Add 0–25 % random jitter to avoid thundering herd
  const jitter = exponential * 0.25 * Math.random();
  return exponential + jitter;
}

export function useGameSocket(gameId: string): { reconnecting: boolean } {
  const queryClient = useQueryClient();
  const accessToken = useAuthStore((s) => s.accessToken);
  const [reconnecting, setReconnecting] = useState(false);

  // Refs survive re-renders without triggering effect re-runs
  const wsRef = useRef<WebSocket | null>(null);
  const retriesRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const unmountedRef = useRef(false);

  useEffect(() => {
    unmountedRef.current = false;

    if (!accessToken || !gameId) return;

    function handleMessage(event: MessageEvent) {
      try {
        const msg = JSON.parse(event.data as string) as { type: string };
        const { type } = msg;

        if (
          type === "game.participant_joined" ||
          type === "game.started" ||
          type === "game.closed" ||
          type === "game.invitation_accepted" ||
          type === "game.participant_status_changed"
        ) {
          void queryClient.invalidateQueries({
            queryKey: queryKeys.game(gameId),
          });
          void queryClient.invalidateQueries({
            queryKey: queryKeys.participants(gameId),
          });
        }

        if (
          type === "buyin.created" ||
          type === "buyin.updated" ||
          type === "buyin.deleted"
        ) {
          void queryClient.invalidateQueries({
            queryKey: queryKeys.buyIns(gameId),
          });
        }

        if (
          type === "expense.created" ||
          type === "expense.updated" ||
          type === "expense.deleted"
        ) {
          void queryClient.invalidateQueries({
            queryKey: queryKeys.expenses(gameId),
          });
        }

        if (type === "final_stack.updated") {
          void queryClient.invalidateQueries({
            queryKey: queryKeys.finalStacks(gameId),
          });
        }

        if (type === "settlement.updated") {
          void queryClient.invalidateQueries({
            queryKey: queryKeys.settlement(gameId),
          });
          void queryClient.invalidateQueries({
            queryKey: queryKeys.game(gameId),
          });
        }
      } catch {
        // Ignore parse errors — server may send control messages
      }
    }

    function connect() {
      if (unmountedRef.current) return;

      const url = `${WS_URL}/ws/games/${gameId}?token=${accessToken}`;
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (unmountedRef.current) {
          ws.close();
          return;
        }
        retriesRef.current = 0;
        setReconnecting(false);

        // Invalidate all game-scoped queries to pick up any missed events
        void queryClient.invalidateQueries({ queryKey: queryKeys.game(gameId) });
        void queryClient.invalidateQueries({ queryKey: queryKeys.participants(gameId) });
        void queryClient.invalidateQueries({ queryKey: queryKeys.buyIns(gameId) });
        void queryClient.invalidateQueries({ queryKey: queryKeys.expenses(gameId) });
        void queryClient.invalidateQueries({ queryKey: queryKeys.finalStacks(gameId) });
        void queryClient.invalidateQueries({ queryKey: queryKeys.settlement(gameId) });
      };

      ws.onmessage = handleMessage;

      ws.onclose = () => {
        if (unmountedRef.current) return;
        scheduleReconnect();
      };

      ws.onerror = () => {
        // onclose will fire after onerror — reconnect logic lives there
      };
    }

    function scheduleReconnect() {
      if (unmountedRef.current) return;
      if (retriesRef.current >= MAX_RETRIES) {
        setReconnecting(false);
        return;
      }

      setReconnecting(true);
      const delay = backoffDelay(retriesRef.current);
      retriesRef.current += 1;
      timerRef.current = setTimeout(connect, delay);
    }

    connect();

    return () => {
      unmountedRef.current = true;
      if (timerRef.current != null) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      if (wsRef.current) {
        wsRef.current.onclose = null; // prevent reconnect on intentional close
        wsRef.current.close();
        wsRef.current = null;
      }
      setReconnecting(false);
    };
  }, [accessToken, gameId, queryClient]);

  return { reconnecting };
}
