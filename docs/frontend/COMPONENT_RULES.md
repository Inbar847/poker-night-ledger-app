# COMPONENT_RULES.md

# Poker Night Ledger — Component Library Rules

This document defines the rules for building, using, and maintaining the shared component library. Every developer (human or AI) modifying the mobile app must follow these rules.

---

## 1. Component hierarchy

Components are organized into layers. Higher layers may depend on lower layers. Lower layers must never import from higher layers.

```
Layer 4: Screens (app/ route files, src/features/ screen components)
  ↓ uses
Layer 3: Domain components (data-display/, overlays/)
  ↓ uses
Layer 2: Composite components (layout/, feedback/, forms/)
  ↓ uses
Layer 1: Primitives (primitives/)
  ↓ uses
Layer 0: Theme (theme/)
```

### Import rules

| From → To | Allowed? |
|---|---|
| Screen → any component layer | Yes |
| Domain component → primitives, layout, feedback, forms, theme | Yes |
| Composite component → primitives, theme | Yes |
| Primitive → theme only | Yes |
| Any component → screen | **No** |
| Lower layer → higher layer | **No** |
| Any component → services, hooks, stores | **No** (components are pure presentation) |

### The one exception

`ParticipantRow`, `TransferRow`, and `GameCard` are domain components that render domain data. They accept **already-fetched data** as props — they do not call hooks or services themselves. The screen passes data down.

---

## 2. Component design rules

### 2a. Every component consumes design tokens

No component may contain hardcoded colors, spacing, font sizes, or border radii. All values come from `src/theme/tokens.ts`, `typography.ts`, or `shadows.ts`.

**Correct:**
```tsx
import { tokens } from '@/theme';

const styles = StyleSheet.create({
  container: {
    backgroundColor: tokens.color.bg.elevated,
    padding: tokens.spacing.base,
    borderRadius: tokens.radius.lg,
  },
});
```

**Incorrect:**
```tsx
const styles = StyleSheet.create({
  container: {
    backgroundColor: '#232340',  // hardcoded
    padding: 16,                  // hardcoded
    borderRadius: 12,             // hardcoded
  },
});
```

### 2b. Components are pure presentation

Shared components must not:
- Call API services or fetch data
- Read from Zustand stores directly
- Use TanStack Query hooks
- Perform navigation (except via `onPress` callback props)
- Contain business logic

They receive data and callbacks via props. The screen/feature module is responsible for data fetching and logic.

### 2c. Components use typed props

Every component exports a TypeScript interface for its props.

```tsx
interface ButtonProps {
  label: string;
  variant?: 'primary' | 'secondary' | 'ghost' | 'destructive';
  size?: 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  icon?: React.ReactNode;
  onPress: () => void;
}
```

Use union types for variants, not booleans (`variant: 'primary'` not `isPrimary: true`).

### 2d. Components have sensible defaults

Every optional prop has a clear default so the component works with minimal configuration.

```tsx
export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  ...
}: ButtonProps) { ... }
```

### 2e. No internal state for display-only data

Components that only display data should not maintain internal state. They render what they receive.

Components that manage ephemeral UI state (e.g., modal visibility, input focus) may use `useState` for that narrow purpose.

---

## 3. Screen rebuild rules

### 3a. Screens are rebuilt in place

When redesigning a screen, modify the existing file. Do not create a new file and delete the old one. This preserves:
- Expo Router route structure
- Import relationships
- Git history

### 3b. Data layer is untouched

When rebuilding a screen's JSX, do not change:
- Hook calls (`useQuery`, `useMutation`, `useGameSocket`, etc.)
- Service imports or API call patterns
- Zustand store usage
- Query key references
- Navigation calls (router.push, router.back, etc.)
- Form validation logic
- Permission checks

The data layer was built in Phases 1–4 and is stable. Phase 5 changes only what the user sees.

### 3c. Replace all inline styles with themed components

Before:
```tsx
<View style={{ backgroundColor: '#fff', padding: 20, borderRadius: 8 }}>
  <Text style={{ fontSize: 18, fontWeight: 'bold', color: '#333' }}>
    {game.title}
  </Text>
</View>
```

After:
```tsx
<Card variant="default" padding="comfortable">
  <Text variant="h3">{game.title}</Text>
</Card>
```

### 3d. Replace all custom loading indicators with Skeleton

Before:
```tsx
if (isLoading) return <ActivityIndicator />;
```

After:
```tsx
if (isLoading) return <GameListSkeleton />;
```

Where `GameListSkeleton` is a screen-specific arrangement of `<Skeleton>` blocks matching the shape of the loaded content.

### 3e. Add empty states

Every list screen must handle the empty case:

```tsx
if (data.length === 0) {
  return <EmptyState title="No games yet" description="Create your first poker night" action={{ label: 'Create Game', onPress: handleCreate }} />;
}
```

### 3f. Add error states

Every screen that fetches data must handle the error case:

```tsx
if (isError) {
  return <ErrorState message="Failed to load games" onRetry={refetch} />;
}
```

---

## 4. Specific component specifications

### 4a. Button

| Variant | Background | Text | Border | Usage |
|---|---|---|---|---|
| `primary` | `accent.primary` | `#FFFFFF` | none | Main CTA — one per screen section max |
| `secondary` | `bg.surface` | `text.primary` | `border.default` | Secondary actions |
| `ghost` | transparent | `accent.primary` | none | Tertiary actions, text links |
| `destructive` | `semantic.negative` | `#FFFFFF` | none | Delete, remove, destructive actions |

Sizes:
- `md`: 48px height, `button` typography
- `lg`: 56px height, `button` typography (used on auth screens)

States:
- `disabled`: 50% opacity, press disabled
- `loading`: label replaced with small spinner, press disabled
- `pressed`: opacity 0.7 for 100ms

Rules:
- Maximum one `primary` button visible per screen section. If there are two equally important actions, one must be `secondary`.
- Button labels are short: 1–3 words. No sentences on buttons.
- Destructive buttons are never the default/first option. They require deliberate selection.

### 4b. Card

| Variant | Background | Border | Radius | Shadow | Usage |
|---|---|---|---|---|---|
| `default` | `bg.elevated` | 1px `border.default` | `lg` (12px) | `card` | Standard list items, info cards |
| `prominent` | `bg.elevated` | none | `xl` (16px) | `card` | Dashboard hero card, featured items |

Pressable behavior:
- If `onPress` is provided, the card is wrapped in `Pressable`
- Press feedback: opacity 0.85 for the duration of the press
- No scale transforms, no color changes on press

### 4c. MoneyAmount

This is the most important display component in the app. Money must always be readable.

| Prop | Purpose |
|---|---|
| `amount` | Numeric value |
| `currency` | Currency string (e.g., "ILS", "$") |
| `size` | 'sm' → `numericSmall`, 'md' → `numeric`, 'lg' → `numericLarge` |
| `showSign` | Whether to show +/− prefix |

Color logic:
- `amount > 0`: `semantic.positive` (emerald)
- `amount < 0`: `semantic.negative` (coral)
- `amount === 0`: `text.secondary`

Formatting:
- Thousands separator: comma (1,000 not 1000)
- Decimal places: 0 for whole numbers, 2 if the value has cents
- Negative sign: Unicode minus "−" (U+2212), not hyphen "-"
- Positive sign: "+" when `showSign` is true
- Currency placement: prefix ("$100") or suffix ("100 ILS") based on currency

### 4d. ParticipantRow

| Element | Position | Style |
|---|---|---|
| Avatar | Left | `avatarMd` (40px), circular |
| Display name | Center-left | `bodyBold` typography |
| Role badge | After name | Small pill: "Dealer" or "Guest" in `captionBold` |
| Trailing content | Right | ReactNode — typically MoneyAmount or action button |

Height: 60–76px depending on content.
The entire row is pressable if `onPress` is provided.

### 4e. TransferRow

The settlement transfer display. This is the hero element of the settlement screen.

Layout: `[From name] → [To name]  [Amount]`

| Element | Style |
|---|---|
| From name | `bodyBold`, `text.primary` |
| Arrow | "→" in `text.secondary` |
| To name | `bodyBold`, `text.primary` |
| Amount | `numeric` or `numericLarge`, `semantic.negative` (it's money owed) |

### 4f. NumericInput

Designed for fast money/chip entry by a dealer who may be distracted.

| Property | Value |
|---|---|
| Font size | 28px+ (numericLarge) for the input value |
| Keyboard | `numeric` or `decimal-pad` |
| Height | 64px minimum |
| Prefix/suffix | Displayed inside the input (e.g., "$" prefix, "chips" suffix) in `text.secondary` |
| Background | `bg.surface` |
| Focus state | `accent.primary` border |

### 4g. BottomSheet

| Property | Value |
|---|---|
| Background | `bg.elevated` |
| Border radius | `xl` (16px) on top corners, 0 on bottom |
| Drag handle | Centered pill, 36x4px, `border.default` color |
| Backdrop | Semi-transparent black, 40% opacity |
| Backdrop press | Dismisses sheet (unless `preventDismiss` is set) |
| Max height | 80% of screen |
| Configurable heights | 'auto', '50%', '60%', '80%' |

---

## 5. Do / don't checklist for screen implementation

### Do

- [ ] Import all visual components from `@/components`
- [ ] Import all token values from `@/theme`
- [ ] Use `<Screen>` wrapper for every route
- [ ] Use `<Text variant="...">` for all text
- [ ] Use `<Button variant="...">` for all buttons
- [ ] Use `<Card>` for all card-like containers
- [ ] Use `<MoneyAmount>` for all currency displays
- [ ] Use `<ChipCount>` for all chip count displays
- [ ] Use `<Skeleton>` for loading states
- [ ] Use `<EmptyState>` for empty lists
- [ ] Use `<ErrorState>` for failed data fetches
- [ ] Use `<ConfirmDialog>` for destructive actions
- [ ] Test on small (SE), standard (15), and large (Pro Max) screens

### Don't

- [ ] Hardcode any color value (`#ffffff`, `'red'`, etc.)
- [ ] Hardcode any spacing value (`padding: 20`, `margin: 10`)
- [ ] Hardcode any font size (`fontSize: 18`)
- [ ] Use raw `<Text>` from React Native
- [ ] Use raw `<TextInput>` from React Native
- [ ] Use `<ActivityIndicator>` (use Skeleton instead)
- [ ] Use `<TouchableOpacity>` directly (use Button or Card onPress)
- [ ] Create new one-off styled components for patterns the library covers
- [ ] Add new colors not in the token system
- [ ] Modify data hooks, services, stores, or types

---

## 6. Adding new components

If a screen needs a component pattern not covered by the existing library:

1. **Check first:** Is this pattern truly reusable across 2+ screens? If not, it belongs in the screen file, not the component library.
2. **Check second:** Can it be composed from existing primitives? A `Section` + `Card` + `ParticipantRow` combination may be sufficient.
3. **If truly new:** Create it in the appropriate subdirectory, following all rules in this document.
4. **Export it** from the subdirectory's `index.ts` and the master `src/components/index.ts`.
5. **Document it** with a TypeScript prop interface and inline JSDoc if the usage is non-obvious.

Do not create "utility" components that wrap a single primitive with a few props preset. That's not abstraction — it's indirection.
