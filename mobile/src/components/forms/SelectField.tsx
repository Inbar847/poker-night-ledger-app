import React from 'react';
import { Pressable, View, StyleSheet, ScrollView } from 'react-native';
import { tokens } from '@/theme';
import { Text } from '../primitives/Text';

export interface SelectOption {
  label: string;
  value: string;
}

export interface SelectFieldProps {
  label?: string;
  options: SelectOption[];
  value: string;
  onSelect: (value: string) => void;
  error?: string;
}

export function SelectField({
  label,
  options,
  value,
  onSelect,
  error,
}: SelectFieldProps) {
  return (
    <View>
      {label && (
        <Text variant="caption" color="secondary" style={styles.label}>
          {label}
        </Text>
      )}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.options}
      >
        {options.map((option) => {
          const selected = option.value === value;
          return (
            <Pressable
              key={option.value}
              onPress={() => onSelect(option.value)}
              style={[
                styles.option,
                selected && styles.optionSelected,
              ]}
              accessibilityRole="button"
              accessibilityState={{ selected }}
            >
              <Text
                variant="captionBold"
                color={selected ? 'white' : 'secondary'}
                style={selected ? { color: tokens.color.white } : undefined}
              >
                {option.label}
              </Text>
            </Pressable>
          );
        })}
      </ScrollView>
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
  options: {
    flexDirection: 'row',
    gap: tokens.spacing.sm,
  },
  option: {
    paddingHorizontal: tokens.spacing.base,
    paddingVertical: tokens.spacing.sm,
    borderRadius: tokens.radius.lg,
    backgroundColor: tokens.color.bg.surface,
    borderWidth: 1,
    borderColor: tokens.color.border.default,
    minHeight: tokens.size.touchTarget,
    justifyContent: 'center',
    alignItems: 'center',
  },
  optionSelected: {
    backgroundColor: tokens.color.accent.primary,
    borderColor: tokens.color.accent.primary,
  },
  error: {
    marginTop: tokens.spacing.xs,
  },
});
