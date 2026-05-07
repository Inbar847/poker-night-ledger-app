import React from 'react';
import { View, StyleSheet } from 'react-native';
import { tokens } from '@/theme';
import { Text } from '../primitives/Text';
import { Card } from '../primitives/Card';
import { Badge } from '../primitives/Badge';
import { MoneyAmount } from './MoneyAmount';

type GameStatus = 'lobby' | 'active' | 'closed';

export interface GameCardProps {
  title: string;
  date: string;
  status: GameStatus;
  playerCount?: number;
  netResult?: number;
  currency?: string;
  onPress?: () => void;
}

const statusBadge: Record<GameStatus, { label: string; variant: 'accent' | 'warning' | 'neutral' }> = {
  lobby: { label: 'Lobby', variant: 'warning' },
  active: { label: 'LIVE', variant: 'accent' },
  closed: { label: 'Closed', variant: 'neutral' },
};

export function GameCard({
  title,
  date,
  status,
  playerCount,
  netResult,
  currency = 'ILS',
  onPress,
}: GameCardProps) {
  const badge = statusBadge[status];

  return (
    <Card
      variant={status === 'active' ? 'prominent' : 'default'}
      padding="comfortable"
      onPress={onPress}
    >
      <View style={styles.header}>
        <Text variant="bodyBold" numberOfLines={1} style={styles.title}>
          {title}
        </Text>
        <Badge label={badge.label} variant={badge.variant} />
      </View>
      <View style={styles.details}>
        <Text variant="caption" color="secondary">
          {date}
          {playerCount != null ? ` \u00B7 ${playerCount} players` : ''}
        </Text>
        {netResult != null && (
          <MoneyAmount amount={netResult} currency={currency} size="sm" showSign />
        )}
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: tokens.spacing.sm,
  },
  title: {
    flex: 1,
  },
  details: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: tokens.spacing.sm,
  },
});
