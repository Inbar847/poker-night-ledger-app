import React from 'react';
import { View, StyleSheet } from 'react-native';
import { tokens } from '@/theme';
import { Text } from './Text';

type BadgeVariant = 'accent' | 'warning' | 'neutral';

export interface BadgeProps {
  label: string;
  variant?: BadgeVariant;
}

const variantColors: Record<BadgeVariant, { bg: string; text: string }> = {
  accent: {
    bg: tokens.color.accent.muted,
    text: tokens.color.white,
  },
  warning: {
    bg: tokens.color.semantic.warning,
    text: tokens.color.white,
  },
  neutral: {
    bg: tokens.color.bg.surface,
    text: tokens.color.text.secondary,
  },
};

export function Badge({ label, variant = 'neutral' }: BadgeProps) {
  const colors = variantColors[variant];

  return (
    <View style={[styles.badge, { backgroundColor: colors.bg }]}>
      <Text variant="captionBold" style={{ color: colors.text }}>
        {label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: tokens.spacing.sm,
    paddingVertical: tokens.spacing.xs / 2,
    borderRadius: tokens.radius.sm,
    alignSelf: 'flex-start',
  },
});
