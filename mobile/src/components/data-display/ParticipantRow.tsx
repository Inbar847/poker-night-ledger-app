import React from 'react';
import { Pressable, View, StyleSheet } from 'react-native';
import { tokens } from '@/theme';
import { Text } from '../primitives/Text';
import { Avatar } from '../primitives/Avatar';
import { Badge } from '../primitives/Badge';

export interface ParticipantRowProps {
  name: string;
  avatarUri?: string | null;
  role?: 'dealer' | 'guest' | null;
  highlighted?: boolean;
  trailingContent?: React.ReactNode;
  onPress?: () => void;
}

export function ParticipantRow({
  name,
  avatarUri,
  role,
  highlighted = false,
  trailingContent,
  onPress,
}: ParticipantRowProps) {
  const content = (
    <View style={[styles.container, highlighted && styles.highlighted]}>
      <Avatar uri={avatarUri} name={name} size="md" />
      <View style={styles.info}>
        <View style={styles.nameRow}>
          <Text variant="bodyBold" numberOfLines={1} style={styles.name}>
            {name}
          </Text>
          {role === 'dealer' && <Badge label="Dealer" variant="accent" />}
          {role === 'guest' && <Badge label="Guest" variant="neutral" />}
        </View>
      </View>
      {trailingContent && <View style={styles.trailing}>{trailingContent}</View>}
    </View>
  );

  if (onPress) {
    return (
      <Pressable
        onPress={onPress}
        style={({ pressed }) => ({ opacity: pressed ? 0.7 : 1 })}
        accessibilityRole="button"
      >
        {content}
      </Pressable>
    );
  }

  return content;
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: tokens.spacing.md,
    paddingHorizontal: tokens.spacing.base,
    minHeight: tokens.size.listItemStandard,
    gap: tokens.spacing.md,
  },
  highlighted: {
    backgroundColor: tokens.color.bg.surface,
    borderRadius: tokens.radius.lg,
  },
  info: {
    flex: 1,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: tokens.spacing.sm,
  },
  name: {
    flexShrink: 1,
  },
  trailing: {
    marginLeft: tokens.spacing.sm,
  },
});
