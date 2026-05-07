import React from 'react';
import { Text } from '../primitives/Text';
import { TypographyVariant } from '@/theme';

type ChipSize = 'sm' | 'md' | 'lg';

export interface ChipCountProps {
  chips: number;
  size?: ChipSize;
  showSign?: boolean;
}

const sizeToVariant: Record<ChipSize, TypographyVariant> = {
  sm: 'numericSmall',
  md: 'numeric',
  lg: 'numericLarge',
};

export function ChipCount({
  chips,
  size = 'md',
  showSign = false,
}: ChipCountProps) {
  const variant = sizeToVariant[size];
  const color = showSign && chips > 0 ? 'positive' : showSign && chips < 0 ? 'negative' : 'primary';

  let sign = '';
  if (chips < 0) sign = '\u2212';
  else if (chips > 0 && showSign) sign = '+';

  const formatted = Math.abs(chips).toLocaleString('en-US');

  return (
    <Text variant={variant} color={color} accessibilityLabel={`${chips} chips`}>
      {sign}{formatted}
    </Text>
  );
}
