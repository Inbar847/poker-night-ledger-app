/**
 * Live invitation popup — Stage 26.
 *
 * Rendered at the app shell level (above all screens) so it can appear
 * regardless of current navigation state. Shows game title, inviter name,
 * and Accept / Decline buttons.
 *
 * - Accept: calls accept endpoint, clears popup
 * - Decline: calls decline endpoint, clears popup
 * - Dismiss (backdrop tap): clears popup without acting (invitation stays pending)
 */

import { useState } from "react";
import {
  ActivityIndicator,
  Modal,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useRouter } from "expo-router";

import {
  useAcceptInvitation,
  useDeclineInvitation,
} from "@/hooks/useGameInvitations";
import { useInvitationPopupStore } from "@/store/invitationPopupStore";
import { tokens } from "@/theme";

export default function InvitationPopup() {
  const pendingInvitation = useInvitationPopupStore(
    (s) => s.pendingInvitation
  );
  const clearPopup = useInvitationPopupStore((s) => s.clearPopup);
  const router = useRouter();

  const acceptMutation = useAcceptInvitation();
  const declineMutation = useDeclineInvitation();

  const [loading, setLoading] = useState<"accept" | "decline" | null>(null);

  if (!pendingInvitation) return null;

  const { invitationId, gameId, gameTitle, inviterName } = pendingInvitation;

  const handleAccept = async () => {
    setLoading("accept");
    try {
      await acceptMutation.mutateAsync({ gameId, invitationId });
      clearPopup();
      router.push(`/games/${gameId}`);
    } catch {
      // If accept fails, just close the popup — user can retry from notifications
      clearPopup();
    } finally {
      setLoading(null);
    }
  };

  const handleDecline = async () => {
    setLoading("decline");
    try {
      await declineMutation.mutateAsync({ gameId, invitationId });
    } catch {
      // Silently handle — the invitation stays in its current state
    } finally {
      setLoading(null);
      clearPopup();
    }
  };

  const handleDismiss = () => {
    // Dismiss without acting — invitation remains pending in notifications
    clearPopup();
  };

  const busy = loading !== null;

  return (
    <Modal
      visible
      transparent
      animationType="fade"
      onRequestClose={handleDismiss}
    >
      <Pressable style={styles.backdrop} onPress={handleDismiss}>
        <Pressable style={styles.card} onPress={() => {}}>
          <Text style={styles.title}>Game Invitation</Text>
          <Text style={styles.body}>
            <Text style={styles.bold}>{inviterName}</Text> invited you to
          </Text>
          <Text style={styles.gameTitle}>{gameTitle}</Text>

          <View style={styles.buttons}>
            <Pressable
              style={[styles.btn, styles.declineBtn]}
              onPress={handleDecline}
              disabled={busy}
            >
              {loading === "decline" ? (
                <ActivityIndicator size="small" color={tokens.color.white} />
              ) : (
                <Text style={styles.btnText}>Decline</Text>
              )}
            </Pressable>
            <Pressable
              style={[styles.btn, styles.acceptBtn]}
              onPress={handleAccept}
              disabled={busy}
            >
              {loading === "accept" ? (
                <ActivityIndicator size="small" color={tokens.color.white} />
              ) : (
                <Text style={styles.btnText}>Accept</Text>
              )}
            </Pressable>
          </View>
        </Pressable>
      </Pressable>
    </Modal>
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
    maxWidth: 340,
    alignItems: "center",
    borderWidth: 1,
    borderColor: tokens.color.border.default,
  },
  title: {
    color: tokens.color.semantic.warning,
    fontSize: 18,
    fontWeight: "700",
    marginBottom: tokens.spacing.base,
  },
  body: {
    color: tokens.color.text.secondary,
    fontSize: 15,
    textAlign: "center",
    lineHeight: 22,
  },
  bold: {
    fontWeight: "700",
    color: tokens.color.text.primary,
  },
  gameTitle: {
    color: tokens.color.text.primary,
    fontSize: 17,
    fontWeight: "700",
    marginTop: 4,
    marginBottom: tokens.spacing.xl,
    textAlign: "center",
  },
  buttons: {
    flexDirection: "row",
    gap: tokens.spacing.md,
    width: "100%",
  },
  btn: {
    flex: 1,
    paddingVertical: tokens.spacing.md,
    borderRadius: tokens.radius.md,
    alignItems: "center",
    justifyContent: "center",
    minHeight: tokens.size.touchTarget,
  },
  acceptBtn: {
    backgroundColor: tokens.color.semantic.positive,
  },
  declineBtn: {
    backgroundColor: tokens.color.semantic.negative,
  },
  btnText: {
    color: tokens.color.white,
    fontSize: 15,
    fontWeight: "600",
  },
});
