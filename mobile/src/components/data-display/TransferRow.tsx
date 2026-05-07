import React from 'react';
import { View, StyleSheet } from 'react-native';
import { tokens } from '@/theme';
import { Text } from '../primitives/Text';
import { MoneyAmount } from './MoneyAmount';

export interface TransferRowProps {
  fromName: string;
  toName: string;
  amount: number;
  currency?: string;
}

export function TransferRow({
  fromName,
  toName,
  amount,
  currency = 'ILS',
}: TransferRowProps) {
  return (
    <View style={styles.container}>
      <View style={styles.names}>
        <Text variant="bodyBold" numberOfLines={1} style={styles.name}>
          {fromName}
        </Text>
        <Text variant="body" color="secondary" style={styles.arrow}>
          {'\u2192'}
        </Text>
        <Text variant="bodyBold" numberOfLines={1} style={styles.name}>
          {toName}
        </Text>
      </View>
      <MoneyAmount amount={-Math.abs(amount)} currency={currency} size="md" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: tokens.spacing.md,
    paddingHorizontal: tokens.spacing.base,
    minHeight: tokens.size.listItemStandard,
  },
  names: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: tokens.spacing.sm,
    marginRight: tokens.spacing.md,
  },
  name: {
    flexShrink: 1,
  },
  arrow: {
    flexShrink: 0,
  },
});
