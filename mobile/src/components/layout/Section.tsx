import React from 'react';
import { View, StyleSheet } from 'react-native';
import { tokens } from '@/theme';
import { Text } from '../primitives/Text';

export interface SectionProps {
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
}

export function Section({ title, subtitle, action, children }: SectionProps) {
  const hasHeader = title || action;

  return (
    <View style={styles.section}>
      {hasHeader && (
        <View style={styles.header}>
          <View style={styles.titles}>
            {title && <Text variant="h3">{title}</Text>}
            {subtitle && (
              <Text variant="caption" color="secondary">
                {subtitle}
              </Text>
            )}
          </View>
          {action && <View>{action}</View>}
        </View>
      )}
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  section: {
    marginBottom: tokens.spacing.xl,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: tokens.spacing.md,
  },
  titles: {
    flex: 1,
    gap: tokens.spacing.xs,
  },
});
