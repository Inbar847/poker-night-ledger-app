/**
 * NotificationItem — renders a single notification row.
 *
 * Unread notifications are visually distinct (bold text + accent dot + elevated bg).
 * Tapping calls onPress(notification) — the parent handles navigation
 * and mark-as-read so this component stays pure/presentational.
 *
 * For game_invitation notifications with an invitation_id, renders
 * inline Accept/Decline buttons when the invitation is still pending.
 */

import { useState } from "react";
import { Pressable, StyleSheet, View } from "react-native";

import { Badge, Button, Row, Spacer, Text, currencySymbol } from "@/components";
import {
  useAcceptInvitation,
  useDeclineInvitation,
} from "@/hooks/useGameInvitations";
import { tokens } from "@/theme";
import type { AppNotification, NotificationType } from "@/types/notification";

// ---------------------------------------------------------------------------
// Human-readable labels for each notification type
// ---------------------------------------------------------------------------

const NOTIFICATION_LABELS: Record<NotificationType, string> = {
  friend_request_received: "You received a friend request",
  friend_request_accepted: "Your friend request was accepted",
  game_invitation: "You were invited to a game",
  game_started: "A game you are in has started",
  game_closed: "A game you were in has closed",
  settlement_owed: "Settlement payment due",
  game_resettled: "Settlement updated",
};

// ---------------------------------------------------------------------------
// Notification type to badge variant mapping
// ---------------------------------------------------------------------------

function getTypeBadge(type: NotificationType): { label: string; variant: "accent" | "warning" | "neutral" } | null {
  switch (type) {
    case "settlement_owed":
      return { label: "Payment", variant: "warning" };
    case "game_resettled":
      return { label: "Updated", variant: "accent" };
    case "game_invitation":
      return { label: "Invite", variant: "accent" };
    default:
      return null;
  }
}

// ---------------------------------------------------------------------------
// Relative time formatter (no external dependency)
// ---------------------------------------------------------------------------

function timeAgo(isoString: string): string {
  const diffMs = Date.now() - new Date(isoString).getTime();
  const mins = Math.floor(diffMs / 60_000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface NotificationItemProps {
  notification: AppNotification;
  onPress: (notification: AppNotification) => void;
}

export default function NotificationItem({
  notification,
  onPress,
}: NotificationItemProps) {
  const data = notification.data;

  // Build the label, guarding against null/missing data fields
  let label: string;
  if (
    notification.type === "settlement_owed" &&
    data?.to_display_name &&
    data?.amount &&
    data?.currency &&
    data?.game_title
  ) {
    label = `You owe ${data.to_display_name} ${currencySymbol(data.currency)}${data.amount} from ${data.game_title}`;
  } else if (notification.type === "game_resettled" && data?.game_title) {
    label = `Settlement updated for ${data.game_title}`;
  } else {
    label = NOTIFICATION_LABELS[notification.type] ?? notification.type;
  }

  const gameTitle = data?.game_title;
  const isGameInvitation =
    notification.type === "game_invitation" &&
    data?.invitation_id &&
    data?.game_id;

  const typeBadge = getTypeBadge(notification.type);

  return (
    <Pressable
      style={({ pressed }) => [
        styles.row,
        !notification.read && styles.rowUnread,
        pressed && styles.rowPressed,
      ]}
      onPress={() => onPress(notification)}
    >
      {/* Unread indicator */}
      <View style={styles.dotContainer}>
        {!notification.read ? (
          <View style={styles.dot} />
        ) : (
          <View style={styles.dotPlaceholder} />
        )}
      </View>

      <View style={styles.content}>
        {/* Top row: label + optional badge */}
        <View style={styles.labelRow}>
          <Text
            variant={notification.read ? "body" : "bodyBold"}
            color={notification.read ? "secondary" : "primary"}
            numberOfLines={2}
            style={styles.labelText}
          >
            {notification.type !== "settlement_owed" && gameTitle
              ? `${label}: ${gameTitle}`
              : label}
          </Text>
          {typeBadge && (
            <Badge
              label={typeBadge.label}
              variant={typeBadge.variant}
            />
          )}
        </View>

        <Spacer size="xs" />

        <Text variant="caption" color="muted">
          {timeAgo(notification.created_at)}
        </Text>

        {isGameInvitation && (
          <>
            <Spacer size="md" />
            <InvitationActions
              gameId={data!.game_id!}
              invitationId={data!.invitation_id!}
            />
          </>
        )}
      </View>
    </Pressable>
  );
}

// ---------------------------------------------------------------------------
// Inline accept/decline for game invitations
// ---------------------------------------------------------------------------

function InvitationActions({
  gameId,
  invitationId,
}: {
  gameId: string;
  invitationId: string;
}) {
  const [resolved, setResolved] = useState<"accepted" | "declined" | null>(null);
  const acceptMutation = useAcceptInvitation();
  const declineMutation = useDeclineInvitation();

  const isPending = acceptMutation.isPending || declineMutation.isPending;

  if (resolved === "accepted") {
    return (
      <Text variant="captionBold" color="positive">
        Accepted
      </Text>
    );
  }
  if (resolved === "declined") {
    return (
      <Text variant="caption" color="secondary">
        Declined
      </Text>
    );
  }

  return (
    <Row gap="sm">
      <Button
        label="Accept"
        variant="primary"
        size="md"
        loading={acceptMutation.isPending}
        disabled={isPending}
        onPress={() =>
          acceptMutation.mutate(
            { gameId, invitationId },
            { onSuccess: () => setResolved("accepted") },
          )
        }
      />
      <Button
        label="Decline"
        variant="secondary"
        size="md"
        loading={declineMutation.isPending}
        disabled={isPending}
        onPress={() =>
          declineMutation.mutate(
            { gameId, invitationId },
            { onSuccess: () => setResolved("declined") },
          )
        }
      />
    </Row>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    alignItems: "flex-start",
    paddingHorizontal: tokens.spacing.lg,
    paddingVertical: tokens.spacing.base,
    borderBottomWidth: 1,
    borderBottomColor: tokens.color.border.subtle,
    backgroundColor: tokens.color.bg.primary,
  },
  rowUnread: {
    backgroundColor: tokens.color.bg.elevated,
  },
  rowPressed: {
    opacity: 0.75,
  },
  dotContainer: {
    width: tokens.spacing.md,
    alignItems: "center",
    marginRight: tokens.spacing.md,
    marginTop: tokens.spacing.xs + 2,
  },
  dot: {
    width: tokens.spacing.sm,
    height: tokens.spacing.sm,
    borderRadius: tokens.spacing.xs,
    backgroundColor: tokens.color.accent.primary,
  },
  dotPlaceholder: {
    width: tokens.spacing.sm,
    height: tokens.spacing.sm,
  },
  content: {
    flex: 1,
  },
  labelRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: tokens.spacing.sm,
  },
  labelText: {
    flex: 1,
  },
});
