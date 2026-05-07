import React from 'react';
import { Text as RNText, TextProps as RNTextProps, StyleSheet } from 'react-native';
import { typography, TypographyVariant } from '@/theme';
import { tokens } from '@/theme';

type TextColor =
  | 'primary'
  | 'secondary'
  | 'muted'
  | 'accent'
  | 'positive'
  | 'negative'
  | 'warning'
  | 'white';

const colorMap: Record<TextColor, string> = {
  primary: tokens.color.text.primary,
  secondary: tokens.color.text.secondary,
  muted: tokens.color.text.muted,
  accent: tokens.color.accent.primary,
  positive: tokens.color.semantic.positive,
  negative: tokens.color.semantic.negative,
  warning: tokens.color.semantic.warning,
  white: tokens.color.white,
};

export interface TextProps extends RNTextProps {
  variant?: TypographyVariant;
  color?: TextColor;
  align?: 'left' | 'center' | 'right';
  children: React.ReactNode;
}

export function Text({
  variant = 'body',
  color = 'primary',
  align,
  style,
  children,
  ...rest
}: TextProps) {
  return (
    <RNText
      style={[
        typography[variant],
        { color: colorMap[color] },
        align ? { textAlign: align } : undefined,
        style,
      ]}
      {...rest}
    >
      {children}
    </RNText>
  );
}
