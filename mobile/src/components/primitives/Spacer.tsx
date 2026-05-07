import React from 'react';
import { View } from 'react-native';
import { tokens } from '@/theme';

type SpacingKey = keyof typeof tokens.spacing;

export interface SpacerProps {
  size?: SpacingKey;
  horizontal?: boolean;
}

export function Spacer({ size = 'base', horizontal = false }: SpacerProps) {
  const value = tokens.spacing[size];

  return (
    <View
      style={
        horizontal
          ? { width: value, height: 1 }
          : { height: value, width: 1 }
      }
    />
  );
}
