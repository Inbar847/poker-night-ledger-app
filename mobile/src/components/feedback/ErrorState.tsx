import React from 'react';
import { View, StyleSheet } from 'react-native';
import { tokens } from '@/theme';
import { Text } from '../primitives/Text';
import { Button } from '../primitives/Button';
import { Spacer } from '../primitives/Spacer';

export interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({
  message = 'Something went wrong',
  onRetry,
}: ErrorStateProps) {
  return (
    <View style={styles.container}>
      <Text variant="h3" color="negative" align="center">
        Error
      </Text>
      <Spacer size="sm" />
      <Text variant="body" color="secondary" align="center">
        {message}
      </Text>
      {onRetry && (
        <>
          <Spacer size="xl" />
          <Button label="Try Again" variant="secondary" onPress={onRetry} />
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
