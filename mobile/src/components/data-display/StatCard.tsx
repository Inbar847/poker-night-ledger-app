import React from 'react';
import { View, StyleSheet } from 'react-native';
import { tokens } from '@/theme';
import { Text } from '../primitives/Text';
import { Card } from '../primitives/Card';

export interface StatCardProps {
  label: string;
  value: string;
  valueColor?: 'primary' | 'positive' | 'negative' | 'secondary';
}

export function StatCard({ label, value, valueColor = 'primary' }: StatCardProps) {
  return (
    <Card variant="default" padding="comfortable">
      <View style={styles.content}>
        <Text variant="numeric" color={valueColor}>
          {value}
        </Text>
        <Text variant="caption" color="secondary" style={styles.label}>
          {label}
        </Text>
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  content: {
    alignItems: 'center',
    gap: tokens.spacing.xs,
  },
  label: {
    textAlign: 'center',
  },
});
