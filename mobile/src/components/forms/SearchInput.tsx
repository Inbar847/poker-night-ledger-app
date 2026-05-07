import React from 'react';
import { TextInput, View, StyleSheet } from 'react-native';
import { tokens } from '@/theme';
import { typography } from '@/theme';
import { Text } from '../primitives/Text';

export interface SearchInputProps {
  value: string;
  onChangeText: (text: string) => void;
  placeholder?: string;
  icon?: React.ReactNode;
}

export function SearchInput({
  value,
  onChangeText,
  placeholder = 'Search...',
  icon,
}: SearchInputProps) {
  return (
    <View style={styles.container}>
      {icon ?? (
        <Text variant="body" color="muted" style={styles.icon}>
          {'\u{1F50D}'}
        </Text>
      )}
      <TextInput
        style={styles.input}
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor={tokens.color.text.muted}
        autoCapitalize="none"
        autoCorrect={false}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: tokens.color.bg.surface,
    borderRadius: tokens.radius.md,
    height: tokens.size.inputHeight,
    paddingHorizontal: tokens.spacing.md,
    borderWidth: 1,
    borderColor: tokens.color.border.default,
  },
  icon: {
    marginRight: tokens.spacing.sm,
  },
  input: {
    flex: 1,
    color: tokens.color.text.primary,
    fontSize: typography.body.fontSize,
    fontWeight: typography.body.fontWeight,
  },
});
