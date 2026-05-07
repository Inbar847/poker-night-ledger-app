import React from 'react';
import { View, StyleSheet } from 'react-native';
import { tokens } from '@/theme';

export interface DividerProps {
  subtle?: boolean;
  spacing?: number;
}

export function Divider({ subtle = false, spacing = 0 }: DividerProps) {
  return (
    <View
      style={[
        styles.divider,
        {
          backgroundColor: subtle
            ? tokens.color.border.subtle
            : tokens.color.border.default,
          marginVertical: spacing,
        },
      ]}
    />
  );
}

const styles = StyleSheet.create({
  divider: {
    height: 1,
    width: '100%',
  },
});
