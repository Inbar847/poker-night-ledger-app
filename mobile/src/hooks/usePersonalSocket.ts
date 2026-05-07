/**
 * Personal WebSocket hook for user-level realtime events — Stage 26.
 *
 * Connects to ws://<host>/ws/user?token=<access_token> and listens for
 * events targeting the authenticated user (e.g. game invitation popups).
 *
 * Follows the same reconnect strategy as useGameSocket:
 *   - Exponential backoff starting at 1 s, capped at 30 s, with jitter.
 *   - Up to 10 reconnect attempts, then stops.
 *
 * Initialize this hook once in the authenticated app shell so it stays
 * alive across screen navigations.
 */

import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { WS_URL } from "@/lib/config";
import { queryKeys } from "@/lib/queryKeys";
import { useAuthStore } from "@/store/authStore";
import { useInvitationPopupStore } from "@/store/invitationPopupStore";

const MAX_RETRIES = 10;
const BASE_DELAY_MS = 1_000;
const MAX_DELAY_MS = 30_000;

function backoffDelay(attempt: number): number {
  const exponential = Math.min(BASE_DELAY_MS * 2 ** attempt, MAX_DELAY_MS);
  const jitter = exponential * 0.25 * Math.random();
  return exponential + jitter;
}

export function usePersonalSocket(): void {
  const accessToken = useAuthStore((s) => s.accessToken);
  const queryClient = useQueryClient();
  const showPopup = useInvitationPopupStore((s) => s.showPopup);

  const wsRef = useRef<WebSocket | null>(null);
  const retriesRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const unmountedRef = useRef(false);

  useEffect(() => {
    unmountedRef.current = false;

    if (!accessToken) return;

    function handleMessage(event: MessageEvent) {
      try {
        const msg = JSON.parse(event.data as string) as {
          type: string;
          payload?: {
            invitation_id?: string;
            game_id?: string;
            game_title?: string;
            inviter_name?: string;
          };
        };

        if (msg.type === "user.game_invitation" && msg.payload) {
          const { invitation_id, game_id, game_title, inviter_name } =
            msg.payload;
          if (invitation_id && game_id && game_title && inviter_name) {
            showPopup({
              invitationId: invitation_id,
              gameId: game_id,
              gameTitle: game_title,
              inviterName: inviter_name,
            });

            // Also invalidate pending invitations so the list stays in sync
            void queryClient.invalidateQueries({
              queryKey: queryKeys.pendingInvitations,
            });
            void queryClient.invalidateQueries({
              queryKey: queryKeys.notifications,
            });
            void queryClient.invalidateQueries({
              queryKey: queryKeys.notificationsUnread,
            });
          }
        }
      } catch {
        // Ignore parse errors
      }
    }

    function connect() {
      if (unmountedRef.current) return;

      const url = `${WS_URL}/ws/user?token=${accessToken}`;
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (unmountedRef.current) {
          ws.close();
          return;
        }
        retriesRef.current = 0;
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
      if (retriesRef.current >= MAX_RETRIES) return;

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
    };
  }, [accessToken, queryClient, showPopup]);
}
