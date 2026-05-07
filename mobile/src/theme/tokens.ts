/**
 * Design tokens for Poker Night Ledger.
 *
 * Every visual value in the app (color, spacing, radius, sizing) must come
 * from this file. No hardcoded values in screens or components.
 */

export const tokens = {
  color: {
    bg: {
      /** Main screen background — deep poker-felt green */
      primary: '#12352C',
      /** Cards, sheets, modals — sits above primary */
      elevated: '#1A3D34',
      /** Inputs, interactive surfaces — the most forward layer */
      surface: '#21473C',
    },
    /** Felt background gradient stops — used by FeltBackground component */
    felt: {
      /** Lightest area — nearly identical to primary; matte = no bright spots */
      highlight: '#143A30',
      /** Shadow areas — edges and bottom */
      shadow: '#0A2C23',
      /** Micro-grain opacity (0–1) — visible matte textile grain */
      grainOpacity: 0.09,
    },
    accent: {
      /** Primary CTA buttons, positive values, active tab — premium emerald */
      primary: '#22A55A',
      /** Pressed state for primary buttons, secondary accent */
      muted: '#177840',
    },
    text: {
      /** Primary readable text — headings, body, names */
      primary: '#F0F0F5',
      /** Secondary text — captions, timestamps, helper text */
      secondary: '#8DA69E',
      /** Tertiary text — disabled labels, placeholders */
      muted: '#4A6B62',
    },
    semantic: {
      /** Winnings, positive balances, success — premium emerald */
      positive: '#22A55A',
      /** Losses, negative balances, destructive actions, errors — deep muted burgundy-red */
      negative: '#C43D5C',
      /** Alerts, pending states, caution */
      warning: '#F39C12',
    },
    border: {
      /** Standard card and element borders */
      default: '#2A4F44',
      /** Faint separators, dividers between list items */
      subtle: '#1E3F36',
    },
    /** Pure white — for text on accent/semantic backgrounds */
    white: '#FFFFFF',
  },

  /** Spacing scale — base unit 4px. All spacing must use these values. */
  spacing: {
    /** 4px — tight internal gaps (icon-to-label inside a button) */
    xs: 4,
    /** 8px — compact gaps (badge-to-text, inline elements) */
    sm: 8,
    /** 12px — standard gaps (elements in a row, icon-to-label) */
    md: 12,
    /** 16px — default padding (card compact, screen horizontal min) */
    base: 16,
    /** 20px — comfortable padding (card comfortable, screen horizontal preferred) */
    lg: 20,
    /** 24px — section separation (between cards, between sections) */
    xl: 24,
    /** 32px — large separation (between major screen sections) */
    '2xl': 32,
    /** 40px — generous separation (auth screen vertical spacing) */
    '3xl': 40,
    /** 48px — very large separation (hero element to content) */
    '4xl': 48,
    /** 64px — maximum separation (auth screen top padding) */
    '5xl': 64,
  },

  /** Border radius scale */
  radius: {
    /** 6px — small elements (badges, tags) */
    sm: 6,
    /** 10px — inputs, small buttons */
    md: 10,
    /** 12px — standard cards, standard buttons */
    lg: 12,
    /** 16px — prominent cards, bottom sheets, modals */
    xl: 16,
  },

  /** Sizing constants for consistent layout */
  size: {
    /** Minimum iOS touch target — 44px */
    touchTarget: 44,
    /** Standard list item height — 60px */
    listItemStandard: 60,
    /** Rich list item height — 76px */
    listItemRich: 76,
    /** Standard button height (md) — 48px */
    buttonMd: 48,
    /** Large button height (lg) — 56px */
    buttonLg: 56,
    /** Standard input height — 48px */
    inputHeight: 48,
    /** Numeric input min height — 64px */
    numericInputHeight: 64,
    /** Small avatar — 32px */
    avatarSm: 32,
    /** Medium avatar — 40px */
    avatarMd: 40,
    /** Large avatar — 56px */
    avatarLg: 56,
    /** Tab bar icon — 24px */
    iconStandard: 24,
    /** Inline icon — 20px */
    iconInline: 20,
    /** Navigation icon — 28px */
    iconNav: 28,
    /** Bottom sheet drag handle width — 36px */
    dragHandleWidth: 36,
    /** Bottom sheet drag handle height — 4px */
    dragHandleHeight: 4,
  },
} as const;

/** TypeScript type for the full token tree */
export type Tokens = typeof tokens;
