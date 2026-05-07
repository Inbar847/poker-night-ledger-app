/**
 * InviteFriendModal — dealer-only modal for inviting an accepted friend to a game.
 *
 * Replaces the old user-search invite flow.
 * Shows only the dealer's accepted friends list. Tapping a friend sends
 * a pending game invitation (they must accept before joining).
 *
 * Phase 4 Stage 25: increased height, client-side search filter.
 * Phase 5 Stage 36: restyled with shared component library and design tokens.
 */

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import {
  FlatList,
  Modal,
  Pressable,
  StyleSheet,
  View,
} from "react-native";

import {
  Text,
  Badge,
  Spacer,
  Divider,
  Skeleton,
  EmptyState,
  SearchInput,
  Avatar,
} from "@/components";

import { useCreateInvitation } from "@/hooks/useGameInvitations";
import { queryKeys } from "@/lib/queryKeys";
import * as friendsService from "@/services/friendsService";
import { tokens } from "@/theme";
import type { FriendEntry } from "@/types/friendship";

interface InviteFriendModalProps {
  visible: boolean;
  gameId: string;
  onSuccess: () => void;
  onClose: () => void;
}

export default function InviteFriendModal({
  visible,
  gameId,
  onSuccess,
  onClose,
}: InviteFriendModalProps) {
  const [filter, setFilter] = useState("");

  const { data: friends = [], isLoading } = useQuery({
    queryKey: queryKeys.friends,
    queryFn: friendsService.getFriends,
    enabled: visible,
  });

  const filteredFriends = useMemo(() => {
    if (!filter.trim()) return friends;
    const needle = filter.trim().toLowerCase();
    return friends.filter((f) =>
      (f.friend.full_name ?? "").toLowerCase().includes(needle),
    );
  }, [friends, filter]);

  const createInvitation = useCreateInvitation(gameId);

  function handleSelect(friend: FriendEntry) {
    createInvitation.reset();
    createInvitation.mutate(friend.friend.id, {
      onSuccess: () => {
        onSuccess();
      },
    });
  }

  function handleClose() {
    createInvitation.reset();
    setFilter("");
    onClose();
  }

  const errorMessage = createInvitation.isError
    ? createInvitation.error instanceof Error
      ? createInvitation.error.message
      : "Failed to invite friend."
    : null;

  return (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={handleClose}
    >
      {/* Backdrop fills top 35% so the sheet gets at least 65% */}
      <Pressable style={styles.backdrop} onPress={handleClose} />

      <View style={styles.sheet}>
        {/* Drag handle */}
        <View style={styles.dragHandle} />

        <View style={styles.header}>
          <Text variant="h3">Invite Friend</Text>
          <Pressable
            onPress={handleClose}
            hitSlop={12}
            style={styles.closeBtn}
          >
            <Text variant="body" color="secondary">✕</Text>
          </Pressable>
        </View>

        <Spacer size="sm" />
        <SearchInput
          value={filter}
          onChangeText={setFilter}
          placeholder="Search friends..."
        />
        <Spacer size="md" />

        {isLoading ? (
          <View style={styles.loadingContainer}>
            <Skeleton height={tokens.size.listItemStandard} />
            <Spacer size="sm" />
            <Skeleton height={tokens.size.listItemStandard} />
            <Spacer size="sm" />
            <Skeleton height={tokens.size.listItemStandard} />
          </View>
        ) : friends.length === 0 ? (
          <EmptyState
            title="No friends yet"
            description="Add friends first to invite them to games."
          />
        ) : filteredFriends.length === 0 ? (
          <EmptyState
            title="No friends found"
            description="Try a different search term."
          />
        ) : (
          <FlatList
            data={filteredFriends}
            keyExtractor={(item) => item.friendship_id}
            style={styles.list}
            keyboardShouldPersistTaps="handled"
            ItemSeparatorComponent={() => <Divider subtle />}
            renderItem={({ item }) => (
              <Pressable
                style={({ pressed }) => [
                  styles.friendRow,
                  pressed && styles.friendRowPressed,
                ]}
                onPress={() => handleSelect(item)}
                disabled={createInvitation.isPending}
              >
                <Avatar name={item.friend.full_name ?? "?"} size="md" />
                <Text variant="bodyBold" style={styles.friendName}>
                  {item.friend.full_name ?? "Unknown"}
                </Text>
              </Pressable>
            )}
          />
        )}

        {/* Status feedback */}
        {createInvitation.isPending && (
          <View style={styles.statusRow}>
            <Badge label="Sending..." variant="neutral" />
          </View>
        )}

        {createInvitation.isSuccess && (
          <View style={styles.statusRow}>
            <Badge label="Invitation sent!" variant="accent" />
          </View>
        )}

        {errorMessage && (
          <View style={styles.statusRow}>
            <Text variant="caption" color="negative">{errorMessage}</Text>
          </View>
        )}
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 35,
    backgroundColor: "rgba(0,0,0,0.5)",
  },
  sheet: {
    flex: 65,
    backgroundColor: tokens.color.bg.elevated,
    borderTopLeftRadius: tokens.radius.xl,
    borderTopRightRadius: tokens.radius.xl,
    paddingHorizontal: tokens.spacing.lg,
    paddingBottom: tokens.spacing['3xl'],
  },
  dragHandle: {
    alignSelf: "center",
    width: tokens.size.dragHandleWidth,
    height: tokens.size.dragHandleHeight,
    backgroundColor: tokens.color.border.default,
    borderRadius: tokens.size.dragHandleHeight / 2,
    marginTop: tokens.spacing.md,
    marginBottom: tokens.spacing.base,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  closeBtn: {
    padding: tokens.spacing.xs,
  },
  loadingContainer: {
    paddingVertical: tokens.spacing.base,
  },
  list: {
    flex: 1,
  },
  friendRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: tokens.spacing.md,
    paddingVertical: tokens.spacing.md,
    paddingHorizontal: tokens.spacing.sm,
    minHeight: tokens.size.listItemStandard,
  },
  friendRowPressed: {
    opacity: 0.7,
  },
  friendName: {
    flex: 1,
  },
  statusRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: tokens.spacing.sm,
    marginTop: tokens.spacing.md,
  },
});
