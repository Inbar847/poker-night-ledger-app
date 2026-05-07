import React from 'react';
import { Pressable, View, StyleSheet, ViewStyle } from 'react-native';
import { tokens } from '@/theme';
import { shadows } from '@/theme';

type CardVariant = 'default' | 'prominent';
type CardPadding = 'compact' | 'comfortable' | 'none';

export interface CardProps {
  variant?: CardVariant;
  padding?: CardPadding;
  onPress?: () => void;
  style?: ViewStyle;
  children: React.ReactNode;
}

const paddingMap: Record<CardPadding, number> = {
  compact: tokens.spacing.base,
  comfortable: tokens.spacing.lg,
  none: 0,
};

export function Card({
  variant = 'default',
  padding = 'compact',
  onPress,
  style,
  children,
}: CardProps) {
  const isProminent = variant === 'prominent';
  const cardStyle: ViewStyle[] = [
    styles.base,
    {
      padding: paddingMap[padding],
      borderRadius: isProminent ? tokens.radius.xl : tokens.radius.lg,
    },
    isProminent ? shadows.card : undefined,
    !isProminent ? styles.border : undefined,
    style,
  ].filter(Boolean) as ViewStyle[];

  if (onPress) {
    return (
      <Pressable
        onPress={onPress}
        style={({ pressed }) => [
          ...cardStyle,
          { opacity: pressed ? 0.85 : 1 },
        ]}
        accessibilityRole="button"
      >
        {children}
      </Pressable>
    );
  }

  return <View style={cardStyle}>{children}</View>;
}

const styles = StyleSheet.create({
  base: {
    backgroundColor: tokens.color.bg.elevated,
  },
  border: {
    borderWidth: 1,
    borderColor: tokens.color.border.default,
  },
});
