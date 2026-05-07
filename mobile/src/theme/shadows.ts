import { ViewStyle } from 'react-native';

/**
 * Shadow / elevation presets for Poker Night Ledger.
 *
 * Depth is created primarily through background color steps (tokens.color.bg),
 * not heavy shadows. These presets are supplementary.
 *
 * Rules:
 * - Maximum 3 depth levels visible on any screen.
 * - No frosted glass or blur effects.
 * - No shadows heavier than the `elevated` preset.
 * - Cards use 1px border for primary definition; shadow is supplementary.
 */

type ShadowPreset = Pick<
  ViewStyle,
  'shadowColor' | 'shadowOffset' | 'shadowOpacity' | 'shadowRadius' | 'elevation'
>;

/** Standard card shadow */
const card: ShadowPreset = {
  shadowColor: '#000',
  shadowOffset: { width: 0, height: 2 },
  shadowOpacity: 0.15,
  shadowRadius: 4,
  elevation: 3,
};

/** Elevated shadow — modals, floating elements */
const elevated: ShadowPreset = {
  shadowColor: '#000',
  shadowOffset: { width: 0, height: 4 },
  shadowOpacity: 0.2,
  shadowRadius: 8,
  elevation: 5,
};

/** No shadow — base level elements */
const none: ShadowPreset = {
  shadowColor: 'transparent',
  shadowOffset: { width: 0, height: 0 },
  shadowOpacity: 0,
  shadowRadius: 0,
  elevation: 0,
};

export const shadows = {
  card,
  elevated,
  none,
} as const;

export type ShadowVariant = keyof typeof shadows;
export type Shadows = typeof shadows;
