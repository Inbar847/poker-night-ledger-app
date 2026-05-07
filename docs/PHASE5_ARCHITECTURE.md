# PHASE5_ARCHITECTURE.md

# Phase 5 Architecture — Frontend redesign and design system

This document extends `ARCHITECTURE.md`, `PHASE2_ARCHITECTURE.md`, `PHASE3_ARCHITECTURE.md`, and `PHASE4_ARCHITECTURE.md` for the frontend redesign phase.  
**Do not modify earlier architecture documents.** All prior architecture is preserved. Phase 5 changes **only** the mobile app's visual layer.

---

## Stack changes

No new frameworks or major dependencies are introduced.

Additions (all within the existing React Native + Expo + TypeScript stack):

| Addition | Purpose |
|---|---|
| `expo-haptics` | Haptic feedback on primary actions |
| `expo-linear-gradient` (if not already present) | Subtle background gradients on auth screens |

No backend dependencies change. No database migrations. No new API endpoints.

---

## Backend changes

**None.** Phase 5 is a pure frontend phase. All API contracts, endpoints, services, models, and realtime events are untouched.

---

## Mobile architecture changes

### New directory structure

```text
mobile/src/
├── theme/                          # NEW — design system foundation
│   ├── tokens.ts                   # Color, spacing, radius, typography tokens
│   ├── typography.ts               # Text style presets
│   ├── shadows.ts                  # Shadow/elevation presets
│   └── index.ts                    # Re-exports
├── components/                     # RESTRUCTURED — shared primitive components
│   ├── primitives/                 # NEW — base-level building blocks
│   │   ├── Text.tsx                # Themed text with variant prop
│   │   ├── Button.tsx              # Primary, secondary, ghost, destructive variants
│   │   ├── Card.tsx                # Themed card container
│   │   ├── Input.tsx               # Themed text input
│   │   ├── Badge.tsx               # Status/count badges
│   │   ├── Avatar.tsx              # User avatar with fallback
│   │   ├── Divider.tsx             # Themed horizontal divider
│   │   ├── Spacer.tsx              # Consistent spacing component
│   │   └── index.ts                # Re-exports
│   ├── layout/                     # NEW — screen structure components
│   │   ├── Screen.tsx              # Base screen wrapper (safe area, bg color, scroll)
│   │   ├── ScreenHeader.tsx        # Consistent screen header
│   │   ├── Section.tsx             # Titled content section
│   │   ├── Row.tsx                 # Horizontal layout row
│   │   └── index.ts
│   ├── feedback/                   # NEW — loading/error/empty states
│   │   ├── Skeleton.tsx            # Skeleton loading placeholders
│   │   ├── EmptyState.tsx          # Empty list/screen state
│   │   ├── ErrorState.tsx          # Error with retry
│   │   ├── Toast.tsx               # Transient feedback messages
│   │   └── index.ts
│   ├── data-display/               # NEW — domain-specific display components
│   │   ├── MoneyAmount.tsx         # Formatted currency with +/- coloring
│   │   ├── ChipCount.tsx           # Formatted chip count display
│   │   ├── StatCard.tsx            # Stat value + label card
│   │   ├── ParticipantRow.tsx      # Player row with avatar, name, amount
│   │   ├── TransferRow.tsx         # "A pays B $X" settlement row
│   │   ├── GameCard.tsx            # Game summary card for lists
│   │   └── index.ts
│   ├── forms/                      # NEW — form-specific components
│   │   ├── FormField.tsx           # Label + input + error wrapper
│   │   ├── NumericInput.tsx        # Large numeric entry for money/chips
│   │   ├── SelectField.tsx         # Selection input
│   │   ├── SearchInput.tsx         # Search/filter input
│   │   └── index.ts
│   ├── overlays/                   # NEW — modal and sheet components
│   │   ├── BottomSheet.tsx         # Slide-up sheet modal
│   │   ├── Modal.tsx               # Centered modal
│   │   ├── ConfirmDialog.tsx       # Confirmation dialog
│   │   └── index.ts
│   └── index.ts                    # Master re-export
├── features/                       # EXISTING — feature modules (screens rebuilt)
├── hooks/                          # EXISTING — unchanged
├── lib/                            # EXISTING — unchanged
├── services/                       # EXISTING — unchanged
├── store/                          # EXISTING — unchanged
└── types/                          # EXISTING — unchanged
```

### What changes vs. what stays

| Layer | Changes? | Details |
|---|---|---|
| `src/theme/` | **New** | Design tokens, typography presets, shadow presets |
| `src/components/primitives/` | **New** | Shared base components replacing per-screen styled elements |
| `src/components/layout/` | **New** | Screen structure wrappers |
| `src/components/feedback/` | **New** | Loading/error/empty state components |
| `src/components/data-display/` | **New** | Domain display components (money, chips, transfers) |
| `src/components/forms/` | **New** | Form field components |
| `src/components/overlays/` | **New** | Modal and sheet components |
| `src/features/*/` | **Rebuilt** | Every feature screen is rebuilt using shared components. Data hooks, services, stores, and types are NOT changed. |
| `src/hooks/` | Unchanged | All data hooks (useGameSocket, usePersonalSocket, etc.) remain |
| `src/services/` | Unchanged | All API service modules remain |
| `src/store/` | Unchanged | All Zustand stores remain |
| `src/types/` | Unchanged | All TypeScript types remain |
| `src/lib/` | Unchanged | Query keys, utils remain |
| `app/` (Expo Router) | **Visual only** | Route files are updated to use new components. Route paths do not change. |

---

## Design token system

### Token file: `src/theme/tokens.ts`

Exports a frozen `tokens` object with these namespaces:

```ts
export const tokens = {
  color: {
    bg: {
      primary: '#1A1A2E',
      elevated: '#232340',
      surface: '#2A2A4A',
    },
    accent: {
      primary: '#2ECC71',
      muted: '#1A8F4A',
    },
    text: {
      primary: '#F0F0F5',
      secondary: '#8888A0',
      muted: '#55556A',
    },
    semantic: {
      positive: '#2ECC71',
      negative: '#E74C6F',
      warning: '#F39C12',
    },
    border: {
      default: '#333355',
      subtle: '#2A2A45',
    },
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 12,
    base: 16,
    lg: 20,
    xl: 24,
    '2xl': 32,
    '3xl': 40,
    '4xl': 48,
    '5xl': 64,
  },
  radius: {
    sm: 6,
    md: 10,
    lg: 12,
    xl: 16,
  },
  size: {
    touchTarget: 44,
    listItemStandard: 60,
    listItemRich: 76,
    buttonHeight: 48,
    inputHeight: 48,
    avatarSm: 32,
    avatarMd: 40,
    avatarLg: 56,
  },
} as const;
```

### Typography file: `src/theme/typography.ts`

Exports named text style presets:

```ts
export const typography = {
  h1: { fontSize: 28, fontWeight: '700', lineHeight: 34 },
  h2: { fontSize: 22, fontWeight: '700', lineHeight: 28 },
  h3: { fontSize: 18, fontWeight: '600', lineHeight: 24 },
  body: { fontSize: 16, fontWeight: '400', lineHeight: 22 },
  bodyBold: { fontSize: 16, fontWeight: '600', lineHeight: 22 },
  caption: { fontSize: 13, fontWeight: '400', lineHeight: 18 },
  captionBold: { fontSize: 13, fontWeight: '600', lineHeight: 18 },
  numeric: { fontSize: 20, fontWeight: '700', lineHeight: 26, fontVariant: ['tabular-nums'] },
  numericLarge: { fontSize: 28, fontWeight: '700', lineHeight: 34, fontVariant: ['tabular-nums'] },
  numericSmall: { fontSize: 16, fontWeight: '600', lineHeight: 22, fontVariant: ['tabular-nums'] },
  button: { fontSize: 16, fontWeight: '600', lineHeight: 22 },
  buttonSmall: { fontSize: 14, fontWeight: '600', lineHeight: 20 },
} as const;
```

### Shadow file: `src/theme/shadows.ts`

```ts
export const shadows = {
  card: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 3,
  },
  elevated: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 5,
  },
} as const;
```

---

## Shared component specifications

### Primitives

#### `Text`
- Props: `variant` (maps to typography preset), `color` (maps to token), `align`, `numberOfLines`
- Default variant: `body`, default color: `text.primary`
- All text in the app must use this component — no raw `<Text>` from React Native

#### `Button`
- Props: `variant` ('primary' | 'secondary' | 'ghost' | 'destructive'), `size` ('md' | 'lg'), `loading`, `disabled`, `onPress`, `label`, `icon`
- Primary: emerald bg, white text
- Secondary: `bg.surface` bg, `text.primary` text, border
- Ghost: transparent bg, accent text
- Destructive: `semantic.negative` bg, white text
- All buttons: 12px radius, 48px height (md) or 56px height (lg), minimum 44px touch target

#### `Card`
- Props: `variant` ('default' | 'prominent'), `padding` ('compact' | 'comfortable'), `onPress` (optional)
- Default: `bg.elevated` bg, 1px `border.default` border, 12px radius
- Prominent: `bg.elevated` bg, 16px radius, card shadow
- Pressable variant adds subtle opacity feedback

#### `Input`
- Props: `label`, `value`, `onChangeText`, `placeholder`, `error`, `keyboardType`, `secureTextEntry`
- `bg.surface` background, 10px radius, 48px height
- Error state: `semantic.negative` border + error text below
- Label above input in `text.secondary` color

#### `Avatar`
- Props: `uri`, `name` (for fallback initials), `size` ('sm' | 'md' | 'lg')
- Circular, bg fallback with initials when no image
- Sizes: 32px, 40px, 56px

#### `Badge`
- Props: `count`, `variant` ('accent' | 'warning' | 'neutral')
- Small pill with count. Used for notification counts, pending invitations.

#### `MoneyAmount`
- Props: `amount` (number), `currency` (string), `size` ('sm' | 'md' | 'lg'), `showSign` (boolean)
- Positive: emerald color, optional "+" prefix
- Negative: coral color, "−" prefix
- Zero: `text.secondary` color
- Uses `numeric` / `numericLarge` / `numericSmall` typography
- Tabular-lining numerals for column alignment

#### `ChipCount`
- Props: `chips` (number), `size` ('sm' | 'md' | 'lg')
- Same numeric formatting as MoneyAmount but without currency symbol
- Neutral color (text.primary) unless used in a gain/loss context

#### `ParticipantRow`
- Props: `participant`, `trailingContent` (ReactNode for amounts/actions), `onPress`
- Avatar + display name + role badge (dealer/guest) + trailing content
- 60–76px height, clear touch target

#### `TransferRow`
- Props: `from` (name), `to` (name), `amount`, `currency`
- "From → To" with amount prominently displayed
- Used in settlement screen for the transfer list

### Layout

#### `Screen`
- Props: `scrollable` (boolean), `padded` (boolean), `header` (ReactNode)
- Wraps content in SafeAreaView with `bg.primary` background
- Optional ScrollView wrapper
- Handles keyboard avoidance for form screens

#### `ScreenHeader`
- Props: `title`, `leftAction`, `rightAction`
- Consistent header bar across all screens
- Title in `h3` typography

#### `Section`
- Props: `title`, `subtitle`, `action` (optional right-side action link)
- Groups content with a titled header
- Used throughout dashboard and detail screens

### Feedback

#### `Skeleton`
- Animated placeholder blocks matching the shape of the content they replace
- Used on all list screens during initial load
- No spinners anywhere in the app (skeleton or empty state only)

#### `EmptyState`
- Props: `title`, `description`, `action` (optional CTA button)
- Centered layout for empty lists/screens
- Soft, non-alarming appearance

#### `ErrorState`
- Props: `message`, `onRetry`
- Error display with retry button
- Used when API calls fail

### Forms

#### `NumericInput`
- Props: `label`, `value`, `onChangeText`, `prefix` (e.g., "$"), `suffix` (e.g., "chips")
- Extra-large font for easy entry of money/chip values
- Numeric keyboard by default

#### `FormField`
- Props: `label`, `error`, `children`
- Standard wrapper: label above, error below, children in the middle

### Overlays

#### `BottomSheet`
- Props: `visible`, `onDismiss`, `title`, `height` ('auto' | '50%' | '60%' | '80%')
- Slide-up from bottom
- Drag handle at top
- Backdrop press to dismiss (when no unsaved data)

#### `ConfirmDialog`
- Props: `visible`, `title`, `message`, `confirmLabel`, `confirmVariant`, `onConfirm`, `onCancel`
- Centered modal for destructive action confirmations
- Confirm button uses the specified variant (usually 'destructive')

---

## Screen rebuild approach

Each screen rebuild follows this pattern:

1. **Read the existing screen file** to understand its data flow, hooks, queries, mutations, and navigation
2. **Do not change** any data hooks, service calls, query keys, store usage, or navigation paths
3. **Replace** the JSX and StyleSheet with shared components from `src/components/`
4. **Replace** all hardcoded colors, spacing, and font sizes with design tokens from `src/theme/`
5. **Verify** that every user interaction (press, submit, navigate, refresh) still works identically
6. **Add** skeleton loading states where spinners previously existed
7. **Add** empty states where blank screens previously existed

### Screen-to-stage mapping

| Stage | Screens |
|---|---|
| 34 | Welcome, Login, Register |
| 35 | App shell (tab bar, layout), Home/Dashboard |
| 36 | Game Lobby (dealer + player views), Create Game |
| 37 | Live Game Dashboard (dealer + player views) |
| 38 | Buy-in entry, Expense entry, Final Stacks entry |
| 39 | Settlement screen, Transfer list, Audit trail |
| 40 | Profile, Stats, History, Notifications, Game Details |
| 41 | Consistency pass, spacing/alignment QA, edge cases |

---

## Testing approach for Phase 5

### What to test

- **Visual regression:** manually compare before/after screenshots for every screen
- **Interaction parity:** every button, form submission, navigation action, and realtime update must work identically to before
- **Token compliance:** no hardcoded colors, spacing, or typography in any screen file
- **Component reuse:** no one-off styled components for elements covered by the shared library
- **Responsive layout:** test on iPhone SE (small), iPhone 15 (standard), iPhone 15 Pro Max (large)
- **Loading states:** skeleton screens appear during data fetch
- **Error states:** error display with retry works
- **Empty states:** appropriate empty state when lists are empty

### What NOT to test in Phase 5

- Backend logic (unchanged)
- API contracts (unchanged)
- Settlement calculations (unchanged)
- Permission enforcement (unchanged)
- WebSocket events (unchanged)

---

## Migration strategy

Phase 5 is **not** a big-bang rewrite. Screens are rebuilt one stage at a time:

1. **Stage 32** creates the theme and token system
2. **Stage 33** creates the shared component library
3. **Stages 34–40** rebuild screens one group at a time, each stage producing a fully functional app
4. **Stage 41** is a consistency pass ensuring everything aligns

At every stage boundary, the app must be fully functional. No "half-redesigned" state should persist — each stage completes its screens fully before moving on.

Existing feature module structure (`src/features/`) is preserved. Screen files within features are rebuilt in place. No file renames, no route changes, no service refactors.
