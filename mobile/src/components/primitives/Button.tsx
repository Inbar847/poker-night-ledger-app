import React from 'react';
import {
  Pressable,
  ActivityIndicator,
  StyleSheet,
  ViewStyle,
  View,
} from 'react-native';
import { tokens } from '@/theme';
import { typography } from '@/theme';
import { Text } from './Text';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'destructive';
type ButtonSize = 'md' | 'lg';

export interface ButtonProps {
  label: string;
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
  icon?: React.ReactNode;
  onPress: () => void;
}

const variantStyles: Record<ButtonVariant, { bg: string; text: string; border?: string }> = {
  primary: {
    bg: tokens.color.accent.primary,
    text: tokens.color.white,
  },
  secondary: {
    bg: tokens.color.bg.surface,
    text: tokens.color.text.primary,
    border: tokens.color.border.default,
  },
  ghost: {
    bg: 'transparent',
    text: tokens.color.accent.primary,
  },
  destructive: {
    bg: tokens.color.semantic.negative,
    text: tokens.color.white,
  },
};

export function Button({
  label,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  fullWidth = false,
  icon,
  onPress,
}: ButtonProps) {
  const vs = variantStyles[variant];
  const height = size === 'lg' ? tokens.size.buttonLg : tokens.size.buttonMd;
  const isDisabled = disabled || loading;

  return (
    <Pressable
      onPress={onPress}
      disabled={isDisabled}
      style={({ pressed }) => [
        styles.base,
        {
          height,
          backgroundColor: vs.bg,
          borderRadius: tokens.radius.lg,
          opacity: isDisabled ? 0.5 : pressed ? 0.7 : 1,
          minWidth: tokens.size.touchTarget,
        },
        vs.border ? { borderWidth: 1, borderColor: vs.border } : undefined,
        fullWidth ? styles.fullWidth : undefined,
      ]}
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled: isDisabled }}
    >
      {loading ? (
        <ActivityIndicator
          size="small"
          color={vs.text}
        />
      ) : (
        <View style={styles.content}>
          {icon && <View style={styles.icon}>{icon}</View>}
          <Text
            variant={size === 'lg' ? 'button' : 'button'}
            color="white"
            style={{ color: vs.text }}
          >
            {label}
          </Text>
        </View>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: tokens.spacing.lg,
  },
  fullWidth: {
    width: '100%',
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: tokens.spacing.sm,
  },
  icon: {
    marginRight: tokens.spacing.xs,
  },
});
