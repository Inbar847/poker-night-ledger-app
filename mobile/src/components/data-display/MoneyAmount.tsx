import React from 'react';
import { tokens } from '@/theme';
import { Text } from '../primitives/Text';
import { TypographyVariant } from '@/theme';

type MoneySize = 'sm' | 'md' | 'lg';

export interface MoneyAmountProps {
  amount: number;
  currency?: string;
  size?: MoneySize;
  showSign?: boolean;
}

const sizeToVariant: Record<MoneySize, TypographyVariant> = {
  sm: 'numericSmall',
  md: 'numeric',
  lg: 'numericLarge',
};

function getColor(amount: number): 'positive' | 'negative' | 'secondary' {
  if (amount > 0) return 'positive';
  if (amount < 0) return 'negative';
  return 'secondary';
}

function formatNumber(value: number): string {
  const abs = Math.abs(value);
  const hasDecimals = abs % 1 !== 0;
  return abs.toLocaleString('en-US', {
    minimumFractionDigits: hasDecimals ? 2 : 0,
    maximumFractionDigits: hasDecimals ? 2 : 0,
  });
}

/** Map currency codes / symbols to display symbols. */
const symbolMap: Record<string, string> = {
  ILS: '₪',
  NIS: '₪',
  '₪': '₪',
  USD: '$',
  '$': '$',
  EUR: '€',
  '€': '€',
  GBP: '£',
  '£': '£',
};

/** Resolve a currency code or symbol to its display symbol. Falls back to the input. */
export function currencySymbol(currency: string): string {
  return symbolMap[currency] ?? currency;
}

/** Currencies whose symbol goes before the number */
const prefixCurrencies = new Set(['$', '₪', '€', '£', 'ILS', 'NIS', 'USD', 'EUR', 'GBP']);

export function MoneyAmount({
  amount,
  currency = 'ILS',
  size = 'md',
  showSign = false,
}: MoneyAmountProps) {
  const color = getColor(amount);
  const variant = sizeToVariant[size];

  // Unicode minus (U+2212) for negative, "+" for positive
  let sign = '';
  if (amount < 0) sign = '\u2212';
  else if (amount > 0 && showSign) sign = '+';

  const formatted = formatNumber(amount);
  const sym = currencySymbol(currency);
  const isPrefix = prefixCurrencies.has(currency);
  const display = isPrefix
    ? `${sign}${sym}${formatted}`
    : `${sign}${formatted} ${sym}`;

  return (
    <Text variant={variant} color={color} accessibilityLabel={`${amount} ${currency}`}>
      {display}
    </Text>
  );
}
