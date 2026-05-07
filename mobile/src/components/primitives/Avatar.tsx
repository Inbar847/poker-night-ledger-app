import React from 'react';
import { View, Image, StyleSheet } from 'react-native';
import { tokens } from '@/theme';
import { Text } from './Text';

type AvatarSize = 'sm' | 'md' | 'lg';

export interface AvatarProps {
  uri?: string | null;
  name: string;
  size?: AvatarSize;
}

const sizeMap: Record<AvatarSize, number> = {
  sm: tokens.size.avatarSm,
  md: tokens.size.avatarMd,
  lg: tokens.size.avatarLg,
};

function getInitials(name: string): string {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join('');
}

export function Avatar({ uri, name, size = 'md' }: AvatarProps) {
  const dim = sizeMap[size];
  const fontSize = size === 'sm' ? 12 : size === 'md' ? 14 : 20;

  if (uri) {
    return (
      <Image
        source={{ uri }}
        style={[
          styles.base,
          {
            width: dim,
            height: dim,
            borderRadius: dim / 2,
          },
        ]}
        accessibilityLabel={name}
      />
    );
  }

  return (
    <View
      style={[
        styles.base,
        styles.fallback,
        {
          width: dim,
          height: dim,
          borderRadius: dim / 2,
        },
      ]}
      accessibilityLabel={name}
    >
      <Text
        variant="captionBold"
        color="white"
        style={{ fontSize }}
      >
        {getInitials(name)}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  base: {
    overflow: 'hidden',
  },
  fallback: {
    backgroundColor: tokens.color.accent.muted,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
