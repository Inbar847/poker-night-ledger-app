import React, { useState } from 'react';
import {
  TextInput,
  View,
  StyleSheet,
  TextInputProps,
} from 'react-native';
import { tokens } from '@/theme';
import { typography } from '@/theme';
import { Text } from './Text';

export interface InputProps extends Omit<TextInputProps, 'style'> {
  label?: string;
  error?: string;
  containerStyle?: object;
}

export function Input({
  label,
  error,
  containerStyle,
  ...rest
}: InputProps) {
  const [focused, setFocused] = useState(false);

  const borderColor = error
    ? tokens.color.semantic.negative
    : focused
      ? tokens.color.accent.primary
      : tokens.color.border.default;

  return (
    <View style={containerStyle}>
      {label && (
        <Text variant="caption" color="secondary" style={styles.label}>
          {label}
        </Text>
      )}
      <TextInput
        style={[
          styles.input,
          { borderColor },
        ]}
        placeholderTextColor={tokens.color.text.muted}
        onFocus={(e) => {
          setFocused(true);
          rest.onFocus?.(e);
        }}
        onBlur={(e) => {
          setFocused(false);
          rest.onBlur?.(e);
        }}
        {...rest}
      />
      {error && (
        <Text variant="caption" color="negative" style={styles.error}>
          {error}
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  label: {
    marginBottom: tokens.spacing.xs,
  },
  input: {
    backgroundColor: tokens.color.bg.surface,
    borderWidth: 1,
    borderRadius: tokens.radius.md,
    height: tokens.size.inputHeight,
    paddingHorizontal: tokens.spacing.base,
    color: tokens.color.text.primary,
    fontSize: typography.body.fontSize,
    fontWeight: typography.body.fontWeight,
  },
  error: {
    marginTop: tokens.spacing.xs,
  },
});
