import React, { useEffect, useRef } from 'react';
import { Animated, StyleSheet, ViewStyle } from 'react-native';
import { tokens } from '@/theme';
import { shadows } from '@/theme';
import { Text } from '../primitives/Text';

type ToastVariant = 'success' | 'error' | 'info';

export interface ToastProps {
  message: string;
  variant?: ToastVariant;
  visible: boolean;
  duration?: number;
  onDismiss?: () => void;
}

const variantColors: Record<ToastVariant, string> = {
  success: tokens.color.semantic.positive,
  error: tokens.color.semantic.negative,
  info: tokens.color.text.secondary,
};

export function Toast({
  message,
  variant = 'info',
  visible,
  duration = 3000,
  onDismiss,
}: ToastProps) {
  const opacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (visible) {
      Animated.timing(opacity, {
        toValue: 1,
        duration: 200,
        useNativeDriver: true,
      }).start();

      if (onDismiss && duration > 0) {
        const timer = setTimeout(() => {
          Animated.timing(opacity, {
            toValue: 0,
            duration: 200,
            useNativeDriver: true,
          }).start(() => onDismiss());
        }, duration);
        return () => clearTimeout(timer);
      }
    } else {
      Animated.timing(opacity, {
        toValue: 0,
        duration: 200,
        useNativeDriver: true,
      }).start();
    }
  }, [visible, duration, onDismiss, opacity]);

  if (!visible) return null;

  return (
    <Animated.View
      style={[
        styles.container,
        shadows.elevated,
        {
          opacity,
          borderLeftColor: variantColors[variant],
        },
      ]}
    >
      <Text variant="bodyBold" color="primary">
        {message}
      </Text>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: tokens.spacing['5xl'],
    left: tokens.spacing.lg,
    right: tokens.spacing.lg,
    backgroundColor: tokens.color.bg.elevated,
    borderRadius: tokens.radius.lg,
    padding: tokens.spacing.base,
    borderLeftWidth: 3,
  },
});
