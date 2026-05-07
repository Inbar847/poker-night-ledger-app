# AUDIT_REPORT.md

# Phase 5 — Current Mobile UI Audit

This document inventories every screen in the Poker Night Ledger mobile app, catalogs hardcoded style values, identifies repeated patterns, and provides a difficulty classification and execution ordering for the Phase 5 redesign.

**Audit date:** 2026-04-14
**Audit scope:** All files under `mobile/app/` and `mobile/src/features/` + `mobile/src/components/`

---

## 1. Summary

### Current state

The mobile app has **25 route files** and **8 feature/component files** containing UI. All screens use raw React Native primitives (`View`, `Text`, `TextInput`, `Pressable`, `Modal`, `ActivityIndicator`) with per-file `StyleSheet.create()` blocks. There is no shared design system, no theme file, no shared components for common patterns, and no design tokens.

### Key findings

1. **Zero shared components** for buttons, cards, inputs, or typography. Every screen defines its own.
2. **100% hardcoded colors** — every file has inline hex values. The same colors appear in 15+ files.
3. **100% hardcoded spacing** — padding, margin, and gap values are all raw numbers.
4. **100% hardcoded font sizes** — fontSize is a raw number in every style object.
5. **No avatars in most screens** — profile/friends screens have avatar logic, but game screens do not show participant avatars.
6. **No skeleton loading states** — every screen uses `<ActivityIndicator>` spinners.
7. **No empty state components** — empty states are inline `<Text>` elements with inconsistent styling.
8. **No error state components** — error handling is inline with inconsistent patterns.
9. **Primary accent color is `#e94560` (hot pink/red)** — this needs to change to emerald `#2ECC71` for primary CTAs per the design spec.
10. **No welcome/landing screen** — the app goes directly to login or the games list.
11. **No tab bar navigation** — uses a `Stack` navigator with a header-based nav. Phase 5 spec requires a bottom tab bar.
12. **Money/chip values use default proportional font** — no tabular-lining numerals anywhere.

---

## 2. Screen inventory

### Route files (`mobile/app/`)

| # | File | Purpose | Lines |
|---|---|---|---|
| 1 | `app/index.tsx` | Root redirect (auth check) | 25 |
| 2 | `app/_layout.tsx` | Root layout (QueryClient, auth bootstrap) | 41 |
| 3 | `app/auth/_layout.tsx` | Auth group layout | 22 |
| 4 | `app/auth/login.tsx` | Login screen | 192 |
| 5 | `app/auth/register.tsx` | Register screen | 216 |
| 6 | `app/(app)/_layout.tsx` | App shell (auth guard, header actions) | 139 |
| 7 | `app/(app)/games/index.tsx` | Dashboard / games list (home) | 201 |
| 8 | `app/(app)/games/create.tsx` | Create game form | 200 |
| 9 | `app/(app)/games/join.tsx` | Join game by token | 155 |
| 10 | `app/(app)/games/[id]/index.tsx` | Main game screen (lobby/active/closed) | 1135 |
| 11 | `app/(app)/games/[id]/buy-in.tsx` | Buy-in entry | 353 |
| 12 | `app/(app)/games/[id]/expense.tsx` | Expense entry | 390 |
| 13 | `app/(app)/games/[id]/final-stacks.tsx` | Final stacks entry | 214 |
| 14 | `app/(app)/games/[id]/settlement.tsx` | Settlement view | 355 |
| 15 | `app/(app)/games/[id]/edit-buyins.tsx` | Edit buy-ins (closed game) | 575 |
| 16 | `app/(app)/games/[id]/edit-final-stacks.tsx` | Edit final stacks (closed game) | 294 |
| 17 | `app/(app)/games/[id]/edit-history.tsx` | Audit trail | 254 |
| 18 | `app/(app)/profile.tsx` | Profile + stats + edit | 515 |
| 19 | `app/(app)/history/index.tsx` | Game history list | 175 |
| 20 | `app/(app)/history/[id].tsx` | Game detail (past) | 281 |
| 21 | `app/(app)/notifications/index.tsx` | Notifications route shell | 19 |
| 22 | `app/(app)/friends/index.tsx` | Friends route shell | 19 |
| 23 | `app/(app)/leaderboard/index.tsx` | Leaderboard route shell | 19 |
| 24 | `app/(app)/search/index.tsx` | Player search | 54 |
| 25 | `app/(app)/public-profile/[userId].tsx` | Public profile route shell | 20 |

### Feature/component files (`mobile/src/`)

| # | File | Purpose | Lines |
|---|---|---|---|
| 1 | `src/components/LoadingScreen.tsx` | Full-screen spinner | 18 |
| 2 | `src/components/UserSearchInput.tsx` | Debounced user search + results list | 192 |
| 3 | `src/features/notifications/NotificationsScreen.tsx` | Notification list + actions | 221 |
| 4 | `src/features/notifications/NotificationItem.tsx` | Single notification row | 274 |
| 5 | `src/features/friends/FriendsScreen.tsx` | Friends list + requests tabs | 297 |
| 6 | `src/features/friends/FriendRequestCard.tsx` | Friend request accept/decline | 134 |
| 7 | `src/features/profile/PublicProfileScreen.tsx` | Public user profile + stats | 345 |
| 8 | `src/features/social/LeaderboardScreen.tsx` | Friend leaderboard | 351 |
| 9 | `src/features/cashout/CashoutModal.tsx` | Cash-out confirmation modal | 199 |
| 10 | `src/features/invitations/InviteFriendModal.tsx` | Invite friend bottom sheet | 245 |
| 11 | `src/features/invitations/InvitationPopup.tsx` | Live invitation popup modal | 190 |
| 12 | `src/features/invitations/PendingInvitationCard.tsx` | (Referenced but not audited — likely small) | — |

---

## 3. Screen-by-screen audit

### 3.1 Auth screens

#### Login (`app/auth/login.tsx`)

**Components used:** `KeyboardAvoidingView`, `ScrollView`, `Text`, `TextInput`, `Pressable`, `ActivityIndicator`, `View`, `Link`
**Layout:** Vertical form, centered, dark background
**Visual tone:** Functional, dark, minimal — no brand presence

**Hardcoded values:**
- Colors: `#1a1a2e`, `#ffffff`, `#888`, `#4a1020`, `#ff6b6b`, `#cccccc`, `#16213e`, `#2a2a5a`, `#e94560`, `#666`, `#fff`
- Spacing: `padding: 24`, `marginBottom: 6`, `marginBottom: 32`, `padding: 12`, `marginBottom: 16`, `marginBottom: 18`, `marginBottom: 6`, `paddingHorizontal: 14`, `paddingVertical: 12`, `marginTop: 4`, `paddingVertical: 14`, `marginTop: 8`, `marginTop: 24`
- Font sizes: 28, 15, 14, 16, 12
- Border radius: 8

**Repeated patterns:** Form field (label + input + error), CTA button, error banner, footer link row
**Shared component candidates:** Input, Button, Text, ErrorBanner, FormField
**Complexity:** Simple reskin

#### Register (`app/auth/register.tsx`)

**Nearly identical to login** — same StyleSheet, same patterns, one additional field (full_name).
**Complexity:** Simple reskin

#### Auth layout (`app/auth/_layout.tsx`)

**Hardcoded:** `#1a1a2e`, `#ffffff`, `fontWeight: "bold"`
**Complexity:** Simple reskin

### 3.2 App shell

#### App layout (`app/(app)/_layout.tsx`)

**Components used:** `Stack`, `Pressable`, `Text`, `View`
**Layout:** Stack navigator with inline header-right components (search, notifications bell, logout)

**Hardcoded values:**
- Colors: `#1a1a2e`, `#ffffff`, `#ccc`, `#e94560`, `#fff`
- Spacing: `gap: 4`, `paddingHorizontal: 10/12/8`, `paddingVertical: 6`, `paddingHorizontal: 4`, `minWidth: 18`, `height: 18`
- Font sizes: 14, 11, 18

**Issues:**
- No bottom tab bar — uses Stack-based navigation
- Notification bell is a text label ("Notifs"), not an icon
- Search button uses emoji `🔍` instead of an icon component
- Logout is inline in the header right section

**Complexity:** Moderate restructure — must add bottom tab bar, restructure navigation

### 3.3 Dashboard / Games list

#### Games index (`app/(app)/games/index.tsx`)

**Components used:** `FlatList`, `Pressable`, `Text`, `View`, `ActivityIndicator`
**Layout:** Action row (Create + Join buttons), quick links, game card list

**Hardcoded values:**
- Colors: `#f0a500`, `#2ecc71`, `#888888`, `#e94560`, `#2a2a5a`, `#ccc`, `#888`, `#ff6b6b`, `#fff`, `#16213e`
- Spacing: `padding: 16`, `gap: 12`, `marginBottom: 8/10`, `paddingVertical: 13/6/3`, `paddingHorizontal: 8/10/14`, `marginTop: 48/12/6`
- Font sizes: 14, 13, 11, 15, 16, 12
- Border radius: 8, 6, 10

**Repeated patterns:** Game card, status badge, action button pair, error state, empty state, loading spinner
**Inline component:** `GameCard` defined inline in the file — should become shared `GameCard`
**Complexity:** Moderate restructure — adding dashboard layout, active game card, section structure

### 3.4 Game creation and joining

#### Create game (`app/(app)/games/create.tsx`)

**Components used:** `KeyboardAvoidingView`, `ScrollView`, `TextInput`, `Pressable`, `Text`, `View`, `ActivityIndicator`
**Layout:** Form (title, rate, currency) + CTA button

**Hardcoded values:** Same color palette as other screens. `padding: 20`, `paddingBottom: 48`, `marginBottom: 18`, `marginBottom: 4/6`
**Font sizes:** 14, 12, 16, 15
**Complexity:** Simple reskin

#### Join game (`app/(app)/games/join.tsx`)

**Components used:** Same as create game
**Layout:** Single input + CTA
**Complexity:** Simple reskin

### 3.5 Main game screen

#### Game screen (`app/(app)/games/[id]/index.tsx`) — **1135 lines, largest file**

**Components used:** `ScrollView`, `Pressable`, `Text`, `View`, `TextInput`, `ActivityIndicator`, `Alert`, `Modal`
**Layout:** Adaptive — shows lobby, active, or closed state based on `game.status`

**Inline sub-components (6):**
- `StatusBadge` — pill-shaped status indicator
- `SectionTitle` — uppercase section label
- `ParticipantRow` — participant with name + tags + buy-in total
- `BuyInRow` — buy-in ledger entry
- `ExpenseRow` — expense ledger entry with delete button
- `AddGuestForm` — inline form for adding a guest
- `ShortageModal` — modal for shortage strategy selection

**Hardcoded values:**
- 38 unique color values across the main and shortage modal StyleSheets
- Spacing values: 16, 48, 24, 20, 10, 8, 6, 4, 13, 14, 12, 9
- Font sizes: 11, 12, 13, 14, 15, 18
- Border radius: 6, 8, 10, 14, 3, 20, 4

**Issues:**
- No avatars next to participants
- Numeric buy-in values use default proportional font
- Delete button for expenses is an "X" text, not an icon
- Inline ShortageModal has its own complete StyleSheet

**Shared component candidates:** ParticipantRow, StatusBadge, SectionTitle, BuyInRow, ExpenseRow, ConfirmDialog (for shortage), BottomSheet
**Complexity:** Complex restructure — largest file, most sub-components, three view modes, two modals

### 3.6 Data entry screens

#### Buy-in (`app/(app)/games/[id]/buy-in.tsx`)

**Components used:** `ScrollView`, `TextInput`, `Pressable`, `Text`, `View`, `ActivityIndicator`
**Layout:** Participant selector (pill chips), type selector, cash/chips inputs with autofill

**Hardcoded values:** `#e94560`, `#2a2a5a`, `#16213e`, `#aaa`, `#ccc`, `#888`, `#555`, `#fff`, `#4a1020`, `#ff6b6b`, `#3a2a00`, `#f0a500`
**Repeated patterns:** Chip/pill selector, form field with label, error banner, warning banner
**Complexity:** Moderate restructure — needs BottomSheet presentation, NumericInput, participant selector

#### Expense (`app/(app)/games/[id]/expense.tsx`)

**Components used:** Same as buy-in + checkboxes for split selection
**Layout:** Title + amount + payer selector + split checkboxes + preview
**Inline component:** `computeEqualSplits` helper + split preview display
**Complexity:** Moderate restructure — more fields, split preview section

#### Final stacks (`app/(app)/games/[id]/final-stacks.tsx`)

**Components used:** `ScrollView`, `TextInput`, `Text`, `View`, `Pressable`, `ActivityIndicator`, `Alert`
**Layout:** List of participant name + chip input pairs
**Complexity:** Moderate restructure — needs larger NumericInput components, chip total validation display

### 3.7 Settlement screens

#### Settlement (`app/(app)/games/[id]/settlement.tsx`)

**Components used:** `ScrollView`, `Text`, `View`, `Pressable`, `ActivityIndicator`
**Layout:** Info bar + warning banners + balance cards + transfer rows + dealer edit buttons

**Inline sub-components (3):**
- `BalanceCard` — participant balance breakdown
- `Row` — label + value detail row
- `TransferRow` — "from → to: amount" display

**Hardcoded values:**
- Colors: `#2ecc71`, `#e94560`, `#888`, `#16213e`, `#aaa`, `#fff`, `#777`, `#666`, `#4a3000`, `#f0a500`, `#1a1000`, `#a07030`, `#555`, `#ff6b6b`, `#2a2a5a`, `#ccc`
- Font sizes: 12, 13, 14, 15, 16
- Spacing: 16, 48, 24, 12, 14, 10, 8, 2, 13

**Issues:**
- Transfer amounts use default font (not tabular-lining numerals)
- No visual separation between winners and losers
- Edit buttons use inline `{ color: "#ccc", fontSize: 14 }` instead of styled components
- No visual drama or hierarchy — the transfer list doesn't stand out

**Shared component candidates:** TransferRow, BalanceCard/ParticipantRow, MoneyAmount, SectionTitle
**Complexity:** Moderate restructure — needs visual hierarchy overhaul, winner/loser separation

### 3.8 Retroactive editing screens

#### Edit buy-ins (`app/(app)/games/[id]/edit-buyins.tsx`)

**Components used:** Same base set + inline `EditBuyInRow` and `AddBuyInForm` sub-components
**Layout:** List of editable buy-in rows + add form
**Inline sub-components:** `EditBuyInRow` (with edit/view toggle), `AddBuyInForm`
**Complexity:** Complex restructure — two inline sub-components with edit states, lots of styling

#### Edit final stacks (`app/(app)/games/[id]/edit-final-stacks.tsx`)

**Components used:** `ScrollView`, `TextInput`, `Pressable`, `Text`, `View`, `ActivityIndicator`, `Alert`
**Inline sub-component:** `FinalStackRow` with edit/view toggle
**Complexity:** Moderate restructure

#### Edit history (`app/(app)/games/[id]/edit-history.tsx`)

**Components used:** `FlatList`, `RefreshControl`, `Text`, `View`, `ActivityIndicator`
**Inline sub-component:** `EditEntry`
**Layout:** Chronological list of edit cards with before/after values
**Complexity:** Simple reskin — straightforward card list

### 3.9 Profile and stats

#### Profile (`app/(app)/profile.tsx`)

**Components used:** `ScrollView`, `Image`, `TextInput`, `Pressable`, `Text`, `View`, `ActivityIndicator`, `KeyboardAvoidingView`
**Layout:** Avatar + name + email + info card + stats card + edit form

**Inline sub-components (4):**
- `StatItem` — stat value + label
- `StatsSection` — stats grid + links
- `ProfileRow` — label + value row
- `EditForm` — profile edit form

**Issues:**
- Avatar is 96x96 with `#e94560` fallback — Phase 5 specifies 56px lg avatar with charcoal tones
- Stats use proportional font, not tabular-lining
- Links to friends/leaderboard/history are inline text ("Friends →"), not in a tab bar

**Complexity:** Moderate restructure — needs StatCard grid, proper avatar component, separated sections

### 3.10 History screens

#### History list (`app/(app)/history/index.tsx`)

**Components used:** `FlatList`, `Pressable`, `Text`, `View`, `ActivityIndicator`
**Inline sub-component:** `HistoryCard`
**Layout:** Flat list of game history cards with net result color coding

**Issues:** Net values use proportional font, no `MoneyAmount` formatting
**Complexity:** Simple reskin — replace HistoryCard with GameCard component

#### History game detail (`app/(app)/history/[id].tsx`)

**Components used:** `ScrollView`, `Text`, `View`, `Pressable`, `ActivityIndicator`
**Inline sub-components:** `SectionTitle`, `BalanceCard`, `TransferRow`
**Layout:** Same as settlement screen but read-only

**Issues:** Duplicates settlement screen patterns — both define their own `BalanceCard` and `TransferRow`
**Complexity:** Simple reskin — will reuse shared settlement components

### 3.11 Social screens

#### Friends (`src/features/friends/FriendsScreen.tsx`)

**Components used:** `FlatList`, `Image`, `Pressable`, `Text`, `View`, `RefreshControl`, `ActivityIndicator`
**Layout:** Tab bar (Friends/Requests) + list
**Inline sub-component:** `FriendItem`

**Issues:**
- Custom tab bar implementation (not using the Phase 5 app shell tabs)
- Uses emoji `🔍` for Find Players button
- Avatar fallback uses `#e94560` — should use design system accent

**Complexity:** Moderate restructure

#### Friend request card (`src/features/friends/FriendRequestCard.tsx`)

**Components used:** `Image`, `Pressable`, `Text`, `View`, `ActivityIndicator`
**Complexity:** Simple reskin — replace with ParticipantRow + action buttons

#### Public profile (`src/features/profile/PublicProfileScreen.tsx`)

**Components used:** `ScrollView`, `Image`, `Pressable`, `Text`, `View`, `ActivityIndicator`, `Alert`
**Inline sub-component:** `FriendshipButton`
**Layout:** Avatar + name + friendship action + stats (friend-gated)

**Issues:**
- Uses `#4caf50` for positive values — different from `#2ecc71` used elsewhere (inconsistency)
- Stats card uses 26px font — not a standard typography preset
- Lock icon is emoji `🔒`

**Complexity:** Moderate restructure

#### Leaderboard (`src/features/social/LeaderboardScreen.tsx`)

**Components used:** `FlatList`, `Image`, `Pressable`, `Text`, `View`, `ActivityIndicator`
**Layout:** Sort toggle row + ranked list
**Inline sub-components:** `LeaderboardRow`

**Issues:**
- Rank badges use gold (#f1c40f), silver (#aaa), bronze (#cd7f32) — not in the design token palette
- Avatar fallback uses `#e94560`

**Complexity:** Moderate restructure

### 3.12 Notifications

#### Notifications screen (`src/features/notifications/NotificationsScreen.tsx`)

**Components used:** `FlatList`, `Pressable`, `RefreshControl`, `Text`, `View`, `ActivityIndicator`
**Layout:** Action bar (mark all read + delete all) + notification list

**Issues:**
- Background uses `#0f0e17` — darker than `bg.primary`
- Delete All button background `#5a1a1a`

**Complexity:** Moderate restructure

#### Notification item (`src/features/notifications/NotificationItem.tsx`)

**Components used:** `Pressable`, `Text`, `View`, `ActivityIndicator`
**Inline sub-component:** `InvitationActions`
**Layout:** Unread dot + label + time + optional accept/decline buttons

**Issues:**
- Accept button uses `#2ecc71` background
- Unread indicator is `#e94560` dot — should use emerald per spec

**Complexity:** Simple reskin

### 3.13 Overlays and modals

#### Invitation popup (`src/features/invitations/InvitationPopup.tsx`)

**Components used:** `Modal`, `Pressable`, `Text`, `View`, `ActivityIndicator`
**Layout:** Centered card with title, body, accept/decline buttons

**Issues:**
- Accept uses `#4caf50` (Material green) — inconsistent
- Decline uses `#e94560`
- Card border uses `#0f3460`

**Complexity:** Simple reskin

#### Cashout modal (`src/features/cashout/CashoutModal.tsx`)

**Components used:** `Modal`, `Pressable`, `Text`, `TextInput`, `View`, `ActivityIndicator`, `Alert`
**Complexity:** Simple reskin — needs BottomSheet presentation, NumericInput

#### Invite friend modal (`src/features/invitations/InviteFriendModal.tsx`)

**Components used:** `Modal`, `FlatList`, `Pressable`, `Text`, `TextInput`, `View`, `ActivityIndicator`
**Layout:** Bottom sheet-style (flex ratio backdrop + sheet)

**Issues:**
- Uses flex-based backdrop/sheet ratio (35/65) — hacky, should use proper BottomSheet
- Close button is text `✕`

**Complexity:** Moderate restructure — needs proper BottomSheet component

### 3.14 Shared components

#### LoadingScreen (`src/components/LoadingScreen.tsx`)

**Layout:** Centered spinner on dark background
**Hardcoded:** `#1a1a2e`, `#e94560`
**Complexity:** Simple reskin — replace with Skeleton component

#### UserSearchInput (`src/components/UserSearchInput.tsx`)

**Layout:** Input + dropdown results list with avatar + name
**Hardcoded:** `#16213e`, `#0f3460`, `#ffffff`, `#e94560`, `#888`
**Complexity:** Moderate restructure — needs SearchInput component, themed results

---

## 4. Hardcoded style values inventory

### Colors (most common occurrences)

| Color | Hex | Approx. occurrences | Current usage | Phase 5 token |
|---|---|---|---|---|
| Hot pink/red | `#e94560` | 30+ files | Primary CTA, error, active accent | `semantic.negative` (not primary) |
| Dark navy | `#1a1a2e` | 15+ files | Background | `bg.primary` |
| Deep blue | `#16213e` | 15+ files | Card/input background | `bg.elevated` |
| Medium navy | `#2a2a5a` | 15+ files | Border, secondary bg | `border.default` / `bg.surface` |
| White | `#ffffff` / `#fff` | All files | Text, button text | `text.primary` |
| Gray | `#888` / `#888888` | 15+ files | Secondary text | `text.secondary` |
| Gray | `#ccc` / `#cccccc` | 10+ files | Labels | `text.primary` (lighter secondary) |
| Gray | `#666` | 10+ files | Placeholder text | `text.muted` |
| Gray | `#555` | 5+ files | Disabled text, placeholders | `text.muted` |
| Gray | `#aaa` | 10+ files | Section labels | `text.secondary` |
| Green | `#2ecc71` | 8 files | Active status, positive values | `semantic.positive` |
| Amber | `#f0a500` | 5 files | Lobby status, warnings | `semantic.warning` |
| Error red | `#ff6b6b` | 8 files | Error text | `semantic.negative` |
| Dark error bg | `#4a1020` | 5 files | Error banner background | — (derive from token) |
| Dark navy bg | `#0f0e17` | 3 files | Deep background | — (close to `bg.primary`) |
| Dark border | `#1a1a3e` | 5 files | Border between items | `border.subtle` |
| Info green bg | `#1a2a1a` | 2 files | Info banner background | — (derive from token) |
| Material green | `#4caf50` | 2 files | Accept/positive (inconsistent) | `semantic.positive` (`#2ECC71`) |
| Dark red | `#8b0000` | 1 file | Danger button | `semantic.negative` |
| Orange | `#e67e22` | 1 file | Left early status | `semantic.warning` |

### Spacing values (hardcoded)

All screens use raw pixel numbers. Most common values:

| Value | Approximate usage |
|---|---|
| `4` | 8 occurrences (margins, paddings) |
| `6` | 15 occurrences (label margins, badge padding) |
| `8` | 20 occurrences (gaps, margins, paddings) |
| `10` | 15 occurrences (paddings, gaps, margins) |
| `12` | 25 occurrences (paddings, margins, gaps) |
| `14` | 20 occurrences (paddings, card paddings) |
| `16` | 20 occurrences (screen padding, card padding) |
| `20` | 10 occurrences (paddings) |
| `24` | 10 occurrences (screen padding, section gaps) |
| `48` | 5 occurrences (paddingBottom, marginTop) |

### Font sizes (hardcoded)

| Size | Usage |
|---|---|
| `11` | Badge text, meta labels, timestamps |
| `12` | Field errors, detail labels, captions |
| `13` | Meta text, hints, labels, secondary text |
| `14` | Labels, button text, body text |
| `15` | Body text, card titles, button text |
| `16` | Input text, headings, error text |
| `18` | Modal titles, section headers |
| `20` | Stat values |
| `22` | Screen headings, display names |
| `26` | Large stat values (public profile) |
| `28` | Screen titles (login/register) |
| `36` | Avatar initials (profile) |
| `40` | Avatar initials (public profile) |

### Border radius values (hardcoded)

| Value | Usage |
|---|---|
| `3` | Tag badges |
| `4` | Role badges, small elements |
| `6` | Buttons, small cards, action buttons |
| `8` | Inputs, buttons, banners, cards |
| `10` | Cards, friend items, badges, stat cards |
| `12` | Profile card |
| `14` | Modal cards |
| `16` | Bottom sheet, invitation popup |
| `18` | Avatar (36px) |
| `20` | Pill selectors (chips) |
| `22` | Avatar (44px) |
| `48` | Avatar (96px) |

---

## 5. Repeated UI patterns (shared component candidates)

### Pattern 1: Form field (label + input + error)

**Found in:** Login, Register, Create Game, Join Game, Buy-in, Expense, Final Stacks, Profile Edit, Edit Buy-ins, Edit Final Stacks
**Frequency:** 20+ instances
**Target component:** `FormField` + `Input`

### Pattern 2: CTA button

**Found in:** Every screen
**Variants:** Primary (`#e94560` bg), Secondary (`#2a2a5a` bg), Danger (`#8b0000` bg), Ghost (text-only), Disabled (opacity 0.5-0.6)
**Frequency:** 40+ instances
**Target component:** `Button`

### Pattern 3: Error banner

**Found in:** Login, Register, Create Game, Join Game, Buy-in, Expense, Final Stacks, Profile, Edit Buy-ins
**Structure:** Dark red bg + red text
**Frequency:** 9 instances
**Target component:** Part of `ErrorState` or custom banner

### Pattern 4: Status badge / pill

**Found in:** Games list, Game screen, History cards
**Structure:** Colored pill with uppercase text
**Frequency:** 5+ instances
**Target component:** `Badge`

### Pattern 5: Participant row

**Found in:** Game screen, Final Stacks, Settlement, History Detail, Edit Buy-ins, Edit Final Stacks
**Structure:** Name + optional tags (DEALER/GUEST/LEFT EARLY) + trailing amount
**Frequency:** 6 instances (each screen defines its own)
**Target component:** `ParticipantRow`

### Pattern 6: Card container

**Found in:** Games list, History, Settlement, Profile, Edit History, Friends, Leaderboard, Public Profile
**Structure:** Dark background + border radius + padding
**Frequency:** 15+ instances
**Target component:** `Card`

### Pattern 7: Section title

**Found in:** Game screen, Settlement, History Detail, Edit Buy-ins, Profile
**Structure:** Uppercase, letter-spaced, muted color, small font
**Frequency:** 8+ instances
**Target component:** `Section` (with title prop)

### Pattern 8: Transfer row

**Found in:** Settlement, History Detail
**Structure:** "From → To: Amount"
**Frequency:** 2 files (duplicated)
**Target component:** `TransferRow`

### Pattern 9: Stat card/item

**Found in:** Profile (StatsSection), Public Profile
**Structure:** Large numeric value + small label, in a card
**Frequency:** 2 files (different implementations)
**Target component:** `StatCard`

### Pattern 10: Avatar (image or initials fallback)

**Found in:** Profile, Public Profile, Friends, Friend Request Card, Leaderboard, User Search
**Structure:** Circular image or colored circle with initials
**Frequency:** 6 files (each defines its own)
**Target component:** `Avatar`

### Pattern 11: Empty state

**Found in:** Games list, History, Notifications, Friends, Edit History
**Structure:** Centered text (usually gray)
**Frequency:** 5+ instances
**Target component:** `EmptyState`

### Pattern 12: Loading state

**Found in:** Every data-fetching screen
**Structure:** `<ActivityIndicator>` spinner
**Frequency:** 20+ instances
**Target component:** `Skeleton`

### Pattern 13: Chip/pill selector

**Found in:** Buy-in (participant + type), Expense (payer + split)
**Structure:** Row of pressable pills with selected/unselected states
**Frequency:** 4 instances
**Target component:** `SelectField` or inline in form components

### Pattern 14: Modal / overlay

**Found in:** Shortage modal, Cashout modal, Invite Friend modal, Invitation Popup
**Structure:** Dark overlay + centered or bottom-sheet card
**Frequency:** 4 instances
**Target components:** `Modal`, `BottomSheet`, `ConfirmDialog`

### Pattern 15: Money amount display

**Found in:** Settlement, History, Profile stats, Leaderboard, Game screen
**Structure:** Numeric value with +/- prefix and color coding (green positive, red negative)
**Frequency:** 10+ instances
**Target component:** `MoneyAmount`

---

## 6. Screen complexity classification

| Screen | Classification | Rationale |
|---|---|---|
| `app/index.tsx` | Simple reskin | Redirect only, no UI |
| `app/_layout.tsx` | Simple reskin | Config only, token swap |
| `app/auth/_layout.tsx` | Simple reskin | Config only |
| `app/auth/login.tsx` | Simple reskin | Standard form, well-structured |
| `app/auth/register.tsx` | Simple reskin | Nearly identical to login |
| `app/(app)/_layout.tsx` | **Complex restructure** | Must add bottom tab bar, restructure nav |
| `app/(app)/games/index.tsx` | Moderate restructure | Needs dashboard layout, active game card |
| `app/(app)/games/create.tsx` | Simple reskin | Standard form |
| `app/(app)/games/join.tsx` | Simple reskin | Single-field form |
| `app/(app)/games/[id]/index.tsx` | **Complex restructure** | 1135 lines, 7 sub-components, 3 modes |
| `app/(app)/games/[id]/buy-in.tsx` | Moderate restructure | Needs BottomSheet, NumericInput |
| `app/(app)/games/[id]/expense.tsx` | Moderate restructure | Needs BottomSheet, split UI rework |
| `app/(app)/games/[id]/final-stacks.tsx` | Moderate restructure | Needs larger NumericInput layout |
| `app/(app)/games/[id]/settlement.tsx` | Moderate restructure | Visual hierarchy overhaul |
| `app/(app)/games/[id]/edit-buyins.tsx` | **Complex restructure** | Inline edit forms, add form, 575 lines |
| `app/(app)/games/[id]/edit-final-stacks.tsx` | Moderate restructure | Inline edit toggle per row |
| `app/(app)/games/[id]/edit-history.tsx` | Simple reskin | Straightforward card list |
| `app/(app)/profile.tsx` | Moderate restructure | Stats grid, avatar, edit form |
| `app/(app)/history/index.tsx` | Simple reskin | Card list, direct mapping to GameCard |
| `app/(app)/history/[id].tsx` | Simple reskin | Reuses settlement patterns |
| `app/(app)/notifications/index.tsx` | Simple reskin | Thin route shell |
| `app/(app)/friends/index.tsx` | Simple reskin | Thin route shell |
| `app/(app)/leaderboard/index.tsx` | Simple reskin | Thin route shell |
| `app/(app)/search/index.tsx` | Simple reskin | Minimal UI |
| `app/(app)/public-profile/[userId].tsx` | Simple reskin | Thin route shell |
| `src/features/notifications/NotificationsScreen.tsx` | Moderate restructure | Action bar + themed list |
| `src/features/notifications/NotificationItem.tsx` | Simple reskin | Map to Card + Badge |
| `src/features/friends/FriendsScreen.tsx` | Moderate restructure | Tab bar + lists |
| `src/features/friends/FriendRequestCard.tsx` | Simple reskin | Map to ParticipantRow + buttons |
| `src/features/profile/PublicProfileScreen.tsx` | Moderate restructure | Stats + friendship action |
| `src/features/social/LeaderboardScreen.tsx` | Moderate restructure | Sort toggle + ranked list |
| `src/features/cashout/CashoutModal.tsx` | Simple reskin | Map to BottomSheet + NumericInput |
| `src/features/invitations/InviteFriendModal.tsx` | Moderate restructure | Needs proper BottomSheet |
| `src/features/invitations/InvitationPopup.tsx` | Simple reskin | Map to Modal component |
| `src/components/LoadingScreen.tsx` | Simple reskin | Replace with Skeleton |
| `src/components/UserSearchInput.tsx` | Moderate restructure | Needs SearchInput + themed results |

**Summary:**
- Simple reskin: **18 screens**
- Moderate restructure: **14 screens**
- Complex restructure: **3 screens** (App layout, Game screen, Edit Buy-ins)

---

## 7. Implementation risk notes

### High-risk areas

1. **App shell restructure (Stage 35):** The current app uses a Stack navigator with no bottom tab bar. Phase 5 requires adding a bottom tab bar with 3-4 tabs. This changes the navigation structure and may affect deep linking.

2. **Main game screen (Stage 37):** At 1135 lines with 7 inline sub-components, this is the riskiest screen. It handles three game states (lobby/active/closed) with different UI for dealers vs. players. Must be rebuilt carefully to preserve all conditional rendering logic.

3. **No welcome screen exists (Stage 34):** A new Welcome screen must be created from scratch. It's the first impression and requires the most atmospheric design — no existing code to build on.

4. **Numeric formatting (all stages):** Currently all money/chip values use default font. Switching to `fontVariant: ['tabular-nums']` via the `MoneyAmount` component requires touching every screen that displays money.

5. **Color palette shift:** The current primary accent is hot pink (`#e94560`). Phase 5 changes primary CTA to emerald (`#2ECC71`). The coral color becomes semantic-negative only. This is a major visual identity shift.

### Medium-risk areas

1. **BottomSheet integration (Stages 38):** Buy-in, expense, and cashout flows are currently full screens or basic modals. Converting to BottomSheet requires the new overlay component to be solid.

2. **Real-time update rendering (Stage 37):** The live game screen receives WebSocket updates. The rebuilt screen must handle incoming data changes without visual jank.

3. **Inline sub-components (multiple stages):** Several screens define their own sub-components inline (ParticipantRow, TransferRow, BalanceCard, etc.). These must be replaced with shared components while preserving the prop interfaces that screen-level data flows depend on.

### Low-risk areas

1. **Auth screens (Stage 34):** Well-structured, simple forms. Straightforward token replacement.
2. **History screens (Stage 40):** Read-only, simple card lists.
3. **Edit history (Stage 39):** Simple card list, no interactive complexity.

---

## 8. Visual tone notes per screen

| Screen | Current visual tone |
|---|---|
| Login / Register | Dark, functional, minimal. No brand presence. Hot pink CTAs feel aggressive. |
| App shell | Dark header with text-based navigation. Functional but not premium. |
| Games list (home) | Dense, utilitarian. Game cards are small and flat. Quick links feel temporary. |
| Create / Join game | Standard dark form. Adequate but generic. |
| Game screen (lobby) | Participant list is plain text rows. No avatars. Dealer controls are small. |
| Game screen (active) | Information-dense but numbers are not prominent. Buy-in values are small 13px text. |
| Game screen (closed) | Button list. No visual celebration or payoff feeling. |
| Buy-in entry | Functional form. Pill selectors are small. Autofill label is subtle. |
| Expense entry | Complex form. Split preview is useful but visually buried. |
| Final stacks | Simple input list. Chip inputs are small (110px wide). |
| Settlement | Functional but flat. Transfers don't stand out. No winner/loser drama. |
| Edit buy-ins | Dense. Edit mode toggle works but feels cramped. |
| Edit final stacks | Similar to buy-in editing. Functional. |
| Edit history | Clean card list. Most polished of the edit screens. |
| Profile | Avatar + info card + stats grid. Stats are the most visually developed section. |
| History | Game cards with net result coloring. Functional, slightly bland. |
| History detail | Mirrors settlement layout. Read-only. |
| Notifications | Dark list. Unread dot is effective. Delete All in red is appropriate. |
| Friends | Tab bar is custom. Friend items have avatars. Cleaner than game screens. |
| Public profile | Centered layout. Stats section is decent. Friendship button works. |
| Leaderboard | Ranked list with rank badges (gold/silver/bronze). Most "social" feeling screen. |
| Invite friend modal | Hacky bottom sheet (flex ratio). Functional but feels unfinished. |
| Cashout modal | Centered modal. Clear but could be a BottomSheet. |
| Invitation popup | Centered card over dark overlay. Decent but uses inconsistent green (#4caf50). |

---

## 9. Recommended execution order for Stages 32-41

### Stage 32 — Theme foundation
Create `src/theme/tokens.ts`, `typography.ts`, `shadows.ts`, `index.ts`. No screen changes.

### Stage 33 — Shared component library
Build all primitives, layout, feedback, data-display, forms, and overlay components. No screen changes yet.

**Recommended component build order within Stage 33:**
1. **Primitives first:** Text, Button, Spacer, Divider (no dependencies)
2. **Card, Badge, Avatar, Input** (depend only on tokens)
3. **Layout:** Screen, ScreenHeader, Section, Row
4. **Feedback:** Skeleton, EmptyState, ErrorState, Toast
5. **Data display:** MoneyAmount, ChipCount (depend on Text + tokens)
6. **Data display:** ParticipantRow, TransferRow, GameCard, StatCard (depend on primitives + MoneyAmount)
7. **Forms:** FormField, NumericInput, SelectField, SearchInput
8. **Overlays:** BottomSheet, Modal, ConfirmDialog (most complex — last)

### Stage 34 — Auth screens (Welcome / Login / Register)
**Order:** Welcome (new) → Login → Register
- Create the Welcome screen first (new file, no migration risk)
- Login and Register share identical structure — do Login first, copy pattern to Register
- Risk: Low. Simple form screens with well-understood data flows.

### Stage 35 — App shell + Dashboard
**Order:** App shell (tab bar) → Dashboard
- App shell is the highest-risk item in this stage — restructure from Stack to Tab navigation
- Dashboard rebuilds the games index with sections, active game card, recent games
- Risk: Medium. Tab bar change affects all screen headers.

### Stage 36 — Game Lobby + Create Game
**Order:** Create Game → Game screen (lobby state only)
- Create Game is a simple form — quick win
- Lobby view is the simplest mode of the Game screen
- Risk: Low-Medium

### Stage 37 — Live Game Dashboard
**Order:** Player view → Dealer view
- Player view is simpler (read-only) — build the base layout
- Dealer view adds action buttons and controls
- This is the highest-complexity single screen in the app
- Risk: High. Must preserve all WebSocket, mutation, and conditional rendering logic.

### Stage 38 — Data entry flows
**Order:** Buy-in → Expense → Final Stacks
- Buy-in is the most common action — get it right first
- Expense builds on buy-in patterns, adds split UI
- Final Stacks is the simplest (list of inputs)
- Risk: Medium. BottomSheet presentation is new.

### Stage 39 — Settlement + Edit History
**Order:** Settlement → Edit History
- Settlement is the payoff screen — deserves careful attention
- Edit History is a simple card list
- Risk: Medium. Visual hierarchy and drama must be added.

### Stage 40 — Profile / Stats / History / Notifications / Game Details
**Order:** Profile → History list → History detail → Notifications → Friends → Public Profile → Leaderboard
- Profile is the most complex in this group (stats grid, edit form)
- History screens reuse settlement patterns (TransferRow, BalanceCard)
- Notifications and Friends are moderate
- Leaderboard is last (most isolated)
- Risk: Low-Medium. Many screens but individually simple.

### Stage 41 — Consistency pass
- Token compliance audit (grep for hardcoded hex values)
- Component reuse audit (grep for raw RN primitives in screen files)
- Spacing/typography consistency check
- Touch target verification
- Safe area verification
- Device size testing
- Risk: Low. Cleanup only.

---

## 10. Files that will NOT change in Phase 5

These files contain only data logic (no UI) and must remain untouched:

- `src/services/*` (all API service files)
- `src/hooks/*` (all data hooks)
- `src/store/*` (all Zustand stores)
- `src/types/*` (all TypeScript types)
- `src/lib/*` (query keys, config, utils, buyInAutofill)
- `src/features/game-edits/gameEditService.ts`
- `src/features/game-edits/useGameEdits.ts`
- `src/features/invitations/PendingInvitationCard.tsx` (if it has no UI — verify)
