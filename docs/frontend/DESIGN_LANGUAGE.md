# DESIGN_LANGUAGE.md

# Poker Night Ledger — Design Language Specification

This document defines the complete visual and interaction language for Poker Night Ledger. Every screen in the app must conform to this specification. When in doubt about a design decision, return to this document.

---

## 1. Brand identity

### Who we are
A premium social utility for adults who host poker nights. We manage real money among friends. We are organized, confident, and slightly dramatic when it matters.

### Who we are not
- Not a casino or gambling app
- Not a gaming product with achievements and XP
- Not a fintech dashboard with charts and KPIs
- Not a social media app with feeds and reactions

### Mood words
Premium. Confident. Warm. Organized. Subtle. Adult. Personal. Effortless.

### Anti-mood words
Flashy. Neon. Loud. Gamified. Cheap. Cartoonish. Corporate. Cold.

---

## 2. Color system

### Background palette

The app lives in **warm dark charcoal** — not pure black, not cold gray.

| Token | Value | Usage |
|---|---|---|
| `bg.primary` | `#1A1A2E` | Main screen background. The default canvas. |
| `bg.elevated` | `#232340` | Cards, modals, bottom sheets. Sits above the primary background. |
| `bg.surface` | `#2A2A4A` | Inputs, interactive surfaces, pressed states. The most forward layer. |

Why charcoal instead of black:
- Pure black (#000) is cold and screen-like. Charcoal has warmth and depth.
- The slight purple-navy undertone (`#1A1A2E`) adds richness without being obviously colored.
- It creates natural elevation layers: primary → elevated → surface provides depth without heavy shadows.

### Accent palette

**Emerald green** is the primary accent — evoking the felt of a poker table without being literal.

| Token | Value | Usage |
|---|---|---|
| `accent.primary` | `#2ECC71` | Primary CTA buttons, positive values, active tab highlight, success states |
| `accent.muted` | `#1A8F4A` | Pressed state for primary buttons, secondary accent contexts |

Rules for emerald:
- Use sparingly. Emerald is the signal color — if everything is green, nothing is.
- Primary CTA buttons are emerald. Secondary buttons are not.
- Positive money values use emerald. All other text does not.
- Active tab indicator is emerald. Inactive tabs are muted gray.
- Never use emerald for backgrounds larger than a button (no green screens, no green cards).

### Text palette

| Token | Value | Usage |
|---|---|---|
| `text.primary` | `#F0F0F5` | Primary readable text. Headings, body, names, labels. |
| `text.secondary` | `#8888A0` | Secondary text. Captions, timestamps, helper text, inactive labels. |
| `text.muted` | `#55556A` | Tertiary text. Disabled labels, placeholders, decorative text. |

### Semantic palette

| Token | Value | Usage |
|---|---|---|
| `semantic.positive` | `#2ECC71` | Winnings, positive balances, success messages |
| `semantic.negative` | `#E74C6F` | Losses, negative balances, destructive buttons, error messages |
| `semantic.warning` | `#F39C12` | Alerts, pending states, caution indicators |

### Border palette

| Token | Value | Usage |
|---|---|---|
| `border.default` | `#333355` | Standard card and element borders |
| `border.subtle` | `#2A2A45` | Faint separators, dividers between list items |

### Absolute color prohibitions

These colors and effects must **never** appear in the app:

- Neon green, electric blue, hot pink, saturated yellow
- Glowing or pulsing effects
- Gradients on interactive elements (buttons, inputs, cards)
- White backgrounds (no screen, card, or modal may have a white or light background)
- Pure black (#000000) as a background (use charcoal tokens)
- Any color that would be at home in a slot machine, arcade, or casino lobby

Permitted gradient use:
- Subtle, dark gradients on non-interactive decorative backgrounds (auth screens only)
- Direction: top-to-bottom or radial from center
- Colors: must be within the charcoal range (e.g., `#1A1A2E` → `#12121E`)

---

## 3. Typography

### Font family

**System font only.** San Francisco on iOS.

No custom fonts, no Google Fonts, no icon fonts for text. The system font is premium, readable, and zero-cost in bundle size and load time.

### Type scale

| Preset | Size | Weight | Line height | Usage |
|---|---|---|---|---|
| `h1` | 28px | Bold (700) | 34px | Screen titles, welcome headings |
| `h2` | 22px | Bold (700) | 28px | Section titles, card headings |
| `h3` | 18px | Semibold (600) | 24px | Subsection titles, screen headers |
| `body` | 16px | Regular (400) | 22px | Default body text, descriptions |
| `bodyBold` | 16px | Semibold (600) | 22px | Emphasized body, names in lists |
| `caption` | 13px | Regular (400) | 18px | Timestamps, helper text, footnotes |
| `captionBold` | 13px | Semibold (600) | 18px | Labels on cards, status badges |
| `button` | 16px | Semibold (600) | 22px | Button labels |
| `buttonSmall` | 14px | Semibold (600) | 20px | Small button labels, text links |

### Numeric type scale

Money and chip values get their own type scale with **tabular-lining numerals** (`fontVariant: ['tabular-nums']`). This ensures:
- Digits are monospaced, so columns of numbers align perfectly
- The "1" is the same width as "8", so totals don't shift when values change

| Preset | Size | Weight | Line height | Usage |
|---|---|---|---|---|
| `numeric` | 20px | Bold (700) | 26px | Standard money/chip values in lists and cards |
| `numericLarge` | 28px | Bold (700) | 34px | Hero values — net result, total buy-in, settlement amount |
| `numericSmall` | 16px | Semibold (600) | 22px | Inline numeric values, secondary amounts |

### Typography rules

1. **Maximum 3–4 type sizes per screen.** If a screen uses more than four sizes, it's too complex.
2. **Headings are bold. Labels are semibold. Body is regular.** Do not use light (300) or thin (100) weights.
3. **All money/chip values use numeric presets.** Never use a body text style for a dollar amount.
4. **Positive amounts:** emerald (`semantic.positive`), optional "+" prefix
5. **Negative amounts:** coral (`semantic.negative`), "−" prefix (not hyphen — use minus sign U+2212)
6. **Zero amounts:** `text.secondary` color, no prefix
7. **Currency symbols** are the same size as the number they accompany (not superscript, not smaller).
8. **No ALL CAPS** except for very short labels (2–3 words max) where it aids scannability. Never for sentences or paragraphs.

---

## 4. Spacing system

### Base unit: 4px

Every spacing value in the app is a multiple of 4px. No arbitrary values.

| Token | Value | Typical usage |
|---|---|---|
| `xs` | 4px | Tight internal gaps (icon-to-label within a button) |
| `sm` | 8px | Compact gaps (between badge and text, between inline elements) |
| `md` | 12px | Standard gaps (between elements in a row, between icon and label) |
| `base` | 16px | Default padding (card padding compact, screen horizontal margin) |
| `lg` | 20px | Comfortable padding (card padding comfortable, screen horizontal margin preferred) |
| `xl` | 24px | Section separation (gap between cards, between sections) |
| `2xl` | 32px | Large separation (gap between major screen sections) |
| `3xl` | 40px | Generous separation (auth screen vertical spacing) |
| `4xl` | 48px | Very large separation (between hero element and content) |
| `5xl` | 64px | Maximum separation (auth screen top padding) |

### Layout constants

| Property | Value | Notes |
|---|---|---|
| Screen horizontal padding | 16–20px | 16px minimum, 20px preferred |
| Card padding (compact) | 16px | Used for list item cards |
| Card padding (comfortable) | 20px | Used for standalone cards, dashboard cards |
| Section gap | 24px | Vertical gap between screen sections |
| Card gap | 12–16px | Vertical gap between cards in a list |
| List item gap | 1px (border) or 8px | List items separated by subtle border or small gap |

### Spacing rules

1. **Never use hardcoded pixel values.** Always reference a spacing token.
2. **Horizontal padding is consistent across the entire screen** — cards, sections, and loose text all align to the same edge.
3. **Vertical rhythm uses the scale monotonically** — tighter gaps inside components, wider gaps between components, widest gaps between sections.
4. **Do not use negative margins** for alignment hacks. Fix the layout instead.
5. **Auth screens use more generous spacing** (lg through 5xl) than in-app screens (sm through 2xl).

---

## 5. Elevation and depth

Depth is created through **background color steps**, not through heavy shadows.

| Level | Background | Shadow | Usage |
|---|---|---|---|
| 0 — Base | `bg.primary` | None | Screen background |
| 1 — Elevated | `bg.elevated` | `card` shadow | Cards, list items, bottom sheets |
| 2 — Surface | `bg.surface` | None | Inputs, interactive surfaces within cards |
| 3 — Overlay | `bg.elevated` | `elevated` shadow | Modals, dialogs, popups |

### Shadow presets

| Preset | Properties | Usage |
|---|---|---|
| `card` | `{ shadowColor: '#000', shadowOffset: {0, 2}, shadowOpacity: 0.15, shadowRadius: 4, elevation: 3 }` | Standard cards |
| `elevated` | `{ shadowColor: '#000', shadowOffset: {0, 4}, shadowOpacity: 0.2, shadowRadius: 8, elevation: 5 }` | Modals, floating elements |

### Depth rules

1. **Maximum 3 depth levels visible on any screen.** Background + cards + maybe an overlay.
2. **No frosted glass or blur effects.** Overlays use solid backgrounds.
3. **No drop shadows heavier than the `elevated` preset.** If you need more prominence, use size and color, not shadow.
4. **Cards use 1px `border.default` border** for definition. Shadow is supplementary, not primary.

---

## 6. Border radius

| Token | Value | Usage |
|---|---|---|
| `sm` | 6px | Small elements (badges, tags) |
| `md` | 10px | Inputs, small buttons |
| `lg` | 12px | Standard cards, standard buttons |
| `xl` | 16px | Prominent cards, bottom sheets, modals |

### Radius rules

1. **All corners of a given element use the same radius.** No mixed-radius corners.
2. **Nested elements use a smaller radius** than their container (if card is 12px, internal elements are 10px or less).
3. **Avatars are fully circular** (borderRadius = size / 2).
4. **No sharp corners (0px radius)** on any visible element except full-width dividers.

---

## 7. Iconography

- **Icon set:** Use `@expo/vector-icons` (Ionicons or MaterialCommunityIcons) for standard UI icons
- **Icon size:** 20px for inline, 24px for standard, 28px for navigation
- **Icon color:** Matches the text color of its context (primary, secondary, or accent)
- **No custom icon assets.** No poker-specific icons (no card suits, no chip icons, no dice).
- **Icons are functional, not decorative.** Every icon accompanies an action or label. No purely decorative icons.

---

## 8. Animation and motion

### Permitted motion

- **Screen transitions:** Simple fade or slide, 200–300ms duration
- **Sheet/modal entry:** Slide up from bottom, 250ms, ease-out
- **Sheet/modal exit:** Slide down, 200ms, ease-in
- **Skeleton shimmer:** Subtle left-to-right shimmer on loading placeholders
- **Press feedback:** Opacity reduction to 0.7 on press, 100ms
- **List item entry:** Simple fade-in on mount, 150ms (for real-time additions)

### Prohibited motion

- Bouncing or spring physics (no springy animations)
- Parallax scrolling
- Confetti, particles, or celebration effects
- Pulsing, glowing, or breathing effects
- Complex gesture-driven animations
- Any animation longer than 400ms
- Any animation that blocks user interaction

### Reduced motion

When the system `prefers-reduced-motion` setting is enabled:
- Skeleton shimmer becomes a static gray block
- Screen transitions become instant (0ms)
- Sheet/modal appear instantly without slide
- All other animations are disabled
- Functionality is unchanged

---

## 9. Screen composition patterns

### Standard in-app screen

```
┌──────────────────────────────┐
│ [Safe area top]              │
│ ScreenHeader: title + actions│
├──────────────────────────────┤
│                              │
│ [Screen content]             │
│  ├── Section (title)         │
│  │   ├── Card / Row          │
│  │   ├── Card / Row          │
│  │   └── Card / Row          │
│  ├── Spacer (xl)             │
│  ├── Section (title)         │
│  │   ├── Card / Row          │
│  │   └── Card / Row          │
│  └── ...                     │
│                              │
│ [Safe area bottom]           │
├──────────────────────────────┤
│ Tab bar (if app shell)       │
└──────────────────────────────┘
```

### Auth screen

```
┌──────────────────────────────┐
│ [Gradient or textured bg]    │
│                              │
│          [Spacer 5xl]        │
│                              │
│      Brand / Welcome text    │
│         (h1, centered)       │
│                              │
│          [Spacer 3xl]        │
│                              │
│      [Input fields]          │
│      [Input fields]          │
│                              │
│          [Spacer xl]         │
│                              │
│    [ Primary CTA button ]    │
│                              │
│     Secondary text link      │
│                              │
│ [Safe area bottom]           │
└──────────────────────────────┘
```

### Data entry bottom sheet

```
┌──────────────────────────────┐
│ [Backdrop — semi-transparent]│
│                              │
│                              │
├──────────────────────────────┤
│  [Drag handle]               │
│  Sheet title (h3)            │
│  ──────────────────────      │
│  FormField (label + input)   │
│  FormField (label + input)   │
│  [Spacer xl]                 │
│  [ Save button — primary ]   │
│  [Safe area bottom]          │
└──────────────────────────────┘
```

---

## 10. Poker-specific design rules

The app references poker through **color, rhythm, and context** — never through literal poker imagery.

### Do
- Use emerald green as the accent color (felt-table energy)
- Use warm dark charcoal as the canvas (evening atmosphere)
- Make numeric values prominent (the "chips on the table" feeling)
- Make the settlement feel like a moment of resolution (the "end of the night" feeling)
- Use warm, personal social elements (names, avatars, real relationships)

### Do not
- Show playing cards, card suits (♠♥♦♣), or card backs anywhere
- Show poker chips, chip stacks, or chip icons
- Show dice, roulette wheels, or any casino equipment
- Use casino-style fonts (western, serif, art deco)
- Use red-and-black as a color pairing
- Use gold or metallic colors
- Play sounds or audio of any kind
- Use terms like "jackpot," "all-in," or "royal flush" in UI text (unless the user named their game that)

---

## 11. Responsive considerations

### Device size targets

| Category | Example | Screen width | Notes |
|---|---|---|---|
| Small | iPhone SE, iPhone 13 mini | 320–375pt | Tightest layout. Verify nothing clips or overflows. |
| Standard | iPhone 15, iPhone 14 | 390–393pt | Primary design target. |
| Large | iPhone 15 Pro Max, iPhone 14 Plus | 428–430pt | Most generous. Verify nothing looks too spread out. |

### Responsive rules

1. **Horizontal padding stays constant** (16–20px) across all sizes. Content width grows/shrinks naturally.
2. **Text does not resize** across device sizes. The type scale is fixed.
3. **Cards are full-width minus horizontal padding.** No multi-column card layouts on phone.
4. **Touch targets remain 44px minimum** on all sizes.
5. **Long text truncates with ellipsis** rather than wrapping into unexpected layouts.
6. **Numbers never truncate.** Money amounts and chip counts are always fully visible.
7. **Safe areas are respected** on all edges: notch, home indicator, and status bar.
