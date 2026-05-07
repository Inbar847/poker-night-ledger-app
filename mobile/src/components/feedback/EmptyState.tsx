import React from 'react';
import { View, StyleSheet } from 'react-native';
import { tokens } from '@/theme';
import { Text } from '../primitives/Text';
import { Button } from '../primitives/Button';
import { Spacer } from '../primitives/Spacer';

export interface EmptyStateProps {
  title: string;
  description?: string;
  action?: {
    label: string;
    onPress: () => void;
  };
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <View style={styles.container}>
      <Text variant="h3" color="secondary" align="center">
        {title}
      </Text>
      {description && (
        <>
          <Spacer size="sm" />
          <Text variant="body" color="muted" align="center">
            {description}
          </Text>
        </>
      )}
      {action && (
        <>
          <Spacer size="xl" />
          <Button
            label={action.label}
            variant="primary"
            onPress={action.onPress}
          />
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: tokens.spacing['2xl'],
    paddingVertical: tokens.spacing['4xl'],
  },
});
