import { TextStyle } from 'react-native';

/**
 * Typography presets for Poker Night Ledger.
 *
 * Rules:
 * - System font only (San Francisco on iOS).
 * - All money/chip values use numeric presets with tabular-lining numerals.
 * - Maximum 3-4 type sizes per screen.
 * - Headings are bold, labels are semibold, body is regular.
 */

export const typography = {
  /** 28px bold — screen titles, welcome headings */
  h1: {
    fontSize: 28,
    fontWeight: '700' as TextStyle['fontWeight'],
    lineHeight: 34,
  },

  /** 22px bold — section titles, card headings */
  h2: {
    fontSize: 22,
    fontWeight: '700' as TextStyle['fontWeight'],
    lineHeight: 28,
  },

  /** 18px semibold — subsection titles, screen headers */
  h3: {
    fontSize: 18,
    fontWeight: '600' as TextStyle['fontWeight'],
    lineHeight: 24,
  },

  /** 16px regular — default body text, descriptions */
  body: {
    fontSize: 16,
    fontWeight: '400' as TextStyle['fontWeight'],
    lineHeight: 22,
  },

  /** 16px semibold — emphasized body, names in lists */
  bodyBold: {
    fontSize: 16,
    fontWeight: '600' as TextStyle['fontWeight'],
    lineHeight: 22,
  },

  /** 13px regular — timestamps, helper text, footnotes */
  caption: {
    fontSize: 13,
    fontWeight: '400' as TextStyle['fontWeight'],
    lineHeight: 18,
  },

  /** 13px semibold — labels on cards, status badges */
  captionBold: {
    fontSize: 13,
    fontWeight: '600' as TextStyle['fontWeight'],
    lineHeight: 18,
  },

  /** 16px semibold — button labels */
  button: {
    fontSize: 16,
    fontWeight: '600' as TextStyle['fontWeight'],
    lineHeight: 22,
  },

  /** 14px semibold — small button labels, text links */
  buttonSmall: {
    fontSize: 14,
    fontWeight: '600' as TextStyle['fontWeight'],
    lineHeight: 20,
  },

  /** 20px bold tabular — standard money/chip values in lists and cards */
  numeric: {
    fontSize: 20,
    fontWeight: '700' as TextStyle['fontWeight'],
    lineHeight: 26,
    fontVariant: ['tabular-nums'] as TextStyle['fontVariant'],
  },

  /** 28px bold tabular — hero values: net result, total buy-in, settlement */
  numericLarge: {
    fontSize: 28,
    fontWeight: '700' as TextStyle['fontWeight'],
    lineHeight: 34,
    fontVariant: ['tabular-nums'] as TextStyle['fontVariant'],
  },

  /** 16px semibold tabular — inline numeric values, secondary amounts */
  numericSmall: {
    fontSize: 16,
    fontWeight: '600' as TextStyle['fontWeight'],
    lineHeight: 22,
    fontVariant: ['tabular-nums'] as TextStyle['fontVariant'],
  },
} as const;

/** Union of all typography variant names */
export type TypographyVariant = keyof typeof typography;

/** TypeScript type for the full typography map */
export type Typography = typeof typography;
