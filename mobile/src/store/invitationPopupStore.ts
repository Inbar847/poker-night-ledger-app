/**
 * Zustand store for the live invitation popup — Stage 26.
 *
 * The personal WebSocket hook writes to this store when a
 * `user.game_invitation` event arrives. The InvitationPopup component
 * reads from it.
 *
 * Duplicate suppression: dismissed invitation IDs are tracked in a Set
 * so the same invitation never triggers a second popup.
 */

import { create } from "zustand";

export interface PendingInvitation {
  invitationId: string;
  gameId: string;
  gameTitle: string;
  inviterName: string;
}

interface InvitationPopupState {
  /** The invitation currently shown (or queued to show) in the popup. */
  pendingInvitation: PendingInvitation | null;

  /** Show the popup for an invitation. No-op if already dismissed. */
  showPopup: (data: PendingInvitation) => void;

  /** Clear the popup (after accept, decline, or dismiss). */
  clearPopup: () => void;

  /** Reset dismissed set (call on logout so next user starts fresh). */
  resetDismissed: () => void;
}

/** Invitation IDs that have already been shown and acted on / dismissed. */
const _dismissed = new Set<string>();

export const useInvitationPopupStore = create<InvitationPopupState>(
  (set) => ({
    pendingInvitation: null,

    showPopup: (data) => {
      if (_dismissed.has(data.invitationId)) return;
      _dismissed.add(data.invitationId);
      set({ pendingInvitation: data });
    },

    clearPopup: () => {
      set({ pendingInvitation: null });
    },

    resetDismissed: () => {
      _dismissed.clear();
      set({ pendingInvitation: null });
    },
  })
);
