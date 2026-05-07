import React, { useState } from 'react';
import { TextInput, View, StyleSheet } from 'react-native';
import { tokens } from '@/theme';
import { typography } from '@/theme';
import { Text } from '../primitives/Text';

export interface NumericInputProps {
  label?: string;
  value: string;
  onChangeText: (text: string) => void;
  prefix?: string;
  suffix?: string;
  placeholder?: string;
  error?: string;
  decimal?: boolean;
}

export function NumericInput({
  label,
  value,
  onChangeText,
  prefix,
  suffix,
  placeholder = '0',
  error,
  decimal = false,
}: NumericInputProps) {
  const [focused, setFocused] = useState(false);

  const borderColor = error
    ? tokens.color.semantic.negative
    : focused
      ? tokens.color.accent.primary
      : tokens.color.border.default;

  return (
    <View>
      {label && (
        <Text variant="caption" color="secondary" style={styles.label}>
          {label}
        </Text>
      )}
      <View style={[styles.inputRow, { borderColor }]}>
        {prefix && (
          <Text variant="body" color="secondary" style={styles.affix}>
            {prefix}
          </Text>
        )}
        <TextInput
          style={styles.input}
          value={value}
          onChangeText={onChangeText}
          keyboardType={decimal ? 'decimal-pad' : 'number-pad'}
          placeholder={placeholder}
          placeholderTextColor={tokens.color.text.muted}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
        />
        {suffix && (
          <Text variant="body" color="secondary" style={styles.affix}>
            {suffix}
          </Text>
        )}
      </View>
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
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: tokens.color.bg.surface,
    borderWidth: 1,
    borderRadius: tokens.radius.md,
    minHeight: tokens.size.numericInputHeight,
    paddingHorizontal: tokens.spacing.base,
  },
  input: {
    flex: 1,
    color: tokens.color.text.primary,
    fontSize: typography.numericLarge.fontSize,
    fontWeight: typography.numericLarge.fontWeight,
    lineHeight: typography.numericLarge.lineHeight,
    paddingVertical: tokens.spacing.md,
  },
  affix: {
    marginHorizontal: tokens.spacing.xs,
  },
  error: {
    marginTop: tokens.spacing.xs,
  },
});
