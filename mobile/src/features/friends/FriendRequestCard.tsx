/**
 * FriendRequestCard — displays a single incoming friend request with
 * Accept and Decline action buttons.
 *
 * Used inside FriendsScreen's "Requests" tab.
 */

import { ActivityIndicator, StyleSheet, View } from "react-native";

import {
  Avatar,
  Button,
  Card,
  Row,
  Text,
} from "@/components";
import { useAcceptFriendRequest, useDeclineFriendRequest } from "@/hooks/useFriends";
import { tokens } from "@/theme";
import type { IncomingRequestEntry } from "@/types/friendship";

interface FriendRequestCardProps {
  request: IncomingRequestEntry;
}

export default function FriendRequestCard({ request }: FriendRequestCardProps) {
  const accept = useAcceptFriendRequest();
  const decline = useDeclineFriendRequest();

  const isPending = accept.isPending || decline.isPending;
  const name = request.requester.full_name ?? "Unknown Player";

  return (
    <Card variant="default" padding="compact">
      <Row align="center" gap="md">
        <Avatar
          uri={request.requester.profile_image_url}
          name={name}
          size="md"
        />

        <View style={styles.info}>
          <Text variant="bodyBold" numberOfLines={1}>{name}</Text>
          <Text variant="caption" color="secondary">Wants to be your friend</Text>
        </View>

        <View style={styles.actions}>
          {isPending ? (
            <ActivityIndicator color={tokens.color.accent.primary} />
          ) : (
            <>
              <Button
                label="Accept"
                variant="primary"
                size="md"
                onPress={() => accept.mutate(request.id)}
                disabled={isPending}
              />
              <Button
                label="Decline"
                variant="secondary"
                size="md"
                onPress={() => decline.mutate(request.id)}
                disabled={isPending}
              />
            </>
          )}
        </View>
      </Row>
    </Card>
  );
}

const styles = StyleSheet.create({
  info: {
    flex: 1,
  },
  actions: {
    flexDirection: "row",
    gap: tokens.spacing.sm,
  },
});
