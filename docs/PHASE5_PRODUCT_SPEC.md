# PHASE5_PRODUCT_SPEC.md

# Phase 5 — Frontend redesign and design system

This document extends `PRODUCT_SPEC.md`, `PHASE2_PRODUCT_SPEC.md`, `PHASE3_PRODUCT_SPEC.md`, and `PHASE4_PRODUCT_SPEC.md` for the frontend redesign phase.  
**Do not modify earlier product spec documents.** All MVP, Phase 2, Phase 3, and Phase 4 behavior is preserved. Phase 5 changes **only** the visual presentation, interaction feel, and component architecture of the mobile app. No backend logic, API contracts, or data models are changed.

---

## Phase 5 goal

Replace the current functional-but-generic mobile UI with a **premium, cohesive design system** that feels native to iPhone, specific to poker, and confident in its visual identity — without changing any app behavior.

Phase 5 is a **pure frontend phase**. Every screen is rebuilt visually using a shared component library and design token system, while all data flows, API calls, permissions, and realtime behavior remain untouched.

---

## What is preserved from all prior phases

Every feature, endpoint, permission rule, realtime event, and data model from Phases 1–4 is preserved **exactly as-is**:

- Guest participant support
- Dealer-only buy-in control
- WebSocket realtime for live games (per-game + personal channels)
- Personal statistics for registered users
- Settlement engine with audit trail and re-settlement
- Game states: lobby → active → closed
- Invite link / token join flow
- Friends system, user search, public profiles
- Friend leaderboard
- Buy-in smart autofill
- Pending game invitation model (lobby + active games)
- Early cash-out and participant lifecycle statuses
- Settlement transfer notifications
- Close-game validation requiring final stacks
- Live invitation popup via personal WebSocket
- Retroactive game editing with audit trail
- Player-added side expenses
- Notification delete-all
- All API request/response contracts

**No backend code is modified in Phase 5.**

---

## Design philosophy

### The identity

Poker Night Ledger is a **premium social utility** — not a casino app, not a gaming product, not a fintech dashboard. It is the app you open when you host poker night with friends. It should feel like an extension of a well-run evening: confident, organized, slightly dramatic when it matters, and effortless the rest of the time.

### Core design principles

1. **Premium, not flashy.** Soft surfaces, generous spacing, confident typography. The app should feel expensive without trying hard.

2. **Dark charcoal, not black.** The primary background is a warm dark charcoal (`#1A1A2E` range), not pure black and not OLED-dark. This creates depth and warmth that pure black cannot.

3. **iPhone-native in feel.** Respect iOS interaction patterns, safe areas, gesture navigation, and system conventions. The app should feel like it belongs on the home screen next to Apple's own apps.

4. **Poker-specific but subtle.** The identity references poker through color, texture, and rhythm — not through card icons, chip clipart, or casino imagery. Emerald green is the accent color (felt-table energy), used sparingly for primary actions and positive outcomes.

5. **Social but not childish.** This is an app for adults managing real money among friends. Avatars, names, and social elements are warm and personal — not gamified, not cartoonish, not decorated with badges or achievements.

6. **No neon. No loud casino energy. No cheap gaming UI.** This rule is absolute. If a design choice could appear in a slot machine app, it does not belong here.

7. **Numeric readability is paramount.** Money amounts, chip counts, buy-in totals, and settlement figures must be the most readable elements on any screen. Large, high-contrast, monospace or tabular-lining numerals.

8. **Fast dealer workflows.** The dealer touches the app more than anyone. Dealer-facing screens must minimize taps, maximize clarity, and never make the dealer hunt for the next action.

9. **Simpler player views.** Non-dealer participants need less — a clean read-only view of the game state, their own position, and the settlement. Do not clutter the player view with controls they cannot use.

10. **Premium settlement with light drama.** The settlement screen is the payoff moment. It deserves a moment of visual drama: clear winners/losers, confident transfer amounts, a sense of resolution. Not animated confetti — more like the final score of a well-played match.

11. **More cinematic auth/entry than in-app functional screens.** The welcome, login, and register screens are the first impression. They should feel more spacious, more atmospheric, more brand-forward than the utilitarian in-app screens. Once inside the app, function wins over atmosphere.

---

## Design direction by screen category

### Auth and entry screens (Welcome / Login / Register)

- Full-bleed dark charcoal backgrounds with subtle gradient or texture
- Centered, generous layouts with large brand presence
- Emerald accent on primary CTA buttons
- Minimal field count — email and password only for login, plus display name for register
- Cinematic feel: atmospheric, spacious, unhurried
- Soft transitions between auth screens
- No poker imagery — just confidence, typography, and color

### App shell and navigation

- Bottom tab bar with 3–4 tabs maximum (Home, Games, Profile — possibly Notifications)
- Tab bar uses muted icons with emerald highlight for active tab
- No top tab bars or complex nested navigation visible at the shell level
- Status bar: light content on dark background
- Safe area handling: proper insets on all edges, no content behind the home indicator

### Home / Dashboard

- Clean card-based layout
- Active game card is prominent with live status indicator
- Recent games section with soft cards
- Quick-create game action is immediately accessible
- Notification badge is visible but not aggressive
- Greeting is personal (name-based) but not performative

### Game Lobby

- Participant list as large, clear rows
- Dealer controls (invite, start, add guest) are prominent buttons — not hidden in menus
- Player view is a clean read-only list
- Invite link sharing is a single prominent action
- Status indicators for pending invitations

### Live Game Dashboard

- The most information-dense screen — must be extremely well-organized
- Dealer sees: participant list with running buy-in totals, add buy-in / add expense actions, end game
- Player sees: participant list with buy-in totals (read-only), their own position highlighted
- Numeric values are the visual priority — large, high-contrast, tabular
- Actions are large touch targets suited for a table environment (the dealer may be distracted)
- Real-time updates should feel seamless — no jarring reloads

### Buy-in / Expense / Final Stacks entry flows

- Modal or half-sheet presentation for data entry
- Large numeric inputs with clear labels
- Pre-filled values where smart autofill applies
- Minimal fields per form — one concept per screen
- Confirmation before destructive actions (delete buy-in, delete expense)
- Instant feedback on save

### Settlement screen

- The emotional payoff of the game
- Clear separation between winners and losers
- Transfer list is the hero element: "A pays B $X" in large, readable rows
- Net result per player is prominent
- Expense breakdown is available but secondary
- Audit trail access (edit history) is a subtle link, not a primary element
- Light visual drama: perhaps a subtle divider between positive and negative results, or a gentle color shift for winners vs. losers
- No animated celebrations, confetti, or gamification

### Profile / Stats / History

- Profile: avatar, display name, member since — clean and personal
- Stats: lifetime totals in large numeric displays (games played, net result, biggest win, etc.)
- History: chronological game list with key outcomes per game
- Game detail: full breakdown of a past game — participants, buy-ins, expenses, settlement
- Notifications: clean list, read/unread states, delete-all action

---

## Typography rules

- **Primary font:** System font (San Francisco on iOS) for all body text, labels, and navigation
- **Numeric font:** Tabular-lining figures for all money/chip values — no proportional spacing on numbers
- **Hierarchy:** 3–4 type sizes maximum per screen. Heading, subheading, body, caption.
- **Weight:** Bold for headings and key values. Medium for labels. Regular for body.
- **Color:** Primary text is off-white (`#F0F0F5` range). Secondary text is muted (`#8888A0` range). Accent text (positive money) uses emerald. Negative money uses a soft rose/coral.

---

## Color system

| Role | Token name | Approximate value | Usage |
|---|---|---|---|
| Background primary | `bg.primary` | `#1A1A2E` | Main screen background |
| Background elevated | `bg.elevated` | `#232340` | Cards, sheets, modals |
| Background surface | `bg.surface` | `#2A2A4A` | Inputs, interactive surfaces |
| Accent primary | `accent.primary` | `#2ECC71` | Primary CTA buttons, positive values, active tab |
| Accent muted | `accent.muted` | `#1A8F4A` | Secondary accent, hover states |
| Text primary | `text.primary` | `#F0F0F5` | Primary text |
| Text secondary | `text.secondary` | `#8888A0` | Labels, captions, inactive text |
| Text muted | `text.muted` | `#55556A` | Disabled text, placeholders |
| Positive | `semantic.positive` | `#2ECC71` | Winnings, positive balances |
| Negative | `semantic.negative` | `#E74C6F` | Losses, negative balances, destructive actions |
| Warning | `semantic.warning` | `#F39C12` | Alerts, pending states |
| Border | `border.default` | `#333355` | Card borders, dividers |
| Border subtle | `border.subtle` | `#2A2A45` | Faint separators |

**Hard rules:**
- No neon green, electric blue, hot pink, or saturated yellow anywhere in the app
- No gradients on interactive elements (buttons are solid color)
- Subtle gradients permitted only on non-interactive decorative backgrounds (auth screens)
- No glow effects, no drop shadows heavier than 4px blur
- Card backgrounds are solid color with optional 1px border — not frosted glass

---

## Spacing and layout system

- **Base unit:** 4px
- **Standard spacing scale:** 4, 8, 12, 16, 20, 24, 32, 40, 48, 64
- **Card padding:** 16px (compact) or 20px (comfortable)
- **Screen horizontal padding:** 16px minimum, 20px preferred
- **Card border radius:** 12px for standard cards, 16px for prominent cards
- **Button border radius:** 12px
- **Input border radius:** 10px
- **Minimum touch target:** 44x44px (iOS guideline)
- **List item height:** 56–64px for standard rows, 72–80px for rich rows

---

## Interaction patterns

- **Sheet modals** for data entry (buy-in, expense, final stack) — slide up from bottom, max 80% screen height
- **Full-screen modals** for complex flows (create game, invite friends)
- **Swipe-to-dismiss** on all modals where safe (no unsaved data)
- **Haptic feedback** on primary actions (create, save, delete) — light impact
- **Pull-to-refresh** on list screens
- **Skeleton screens** for loading states — not spinners
- **Fade transitions** between screens — no slide-from-right overuse
- **Optimistic updates** for mutations where possible (already implemented in data layer)

---

## Component categories

Phase 5 introduces a shared component library with these categories:

1. **Primitives** — Text, Button, Card, Input, Badge, Avatar, Divider, Spacer
2. **Layout** — Screen, ScreenHeader, Section, Row, Grid
3. **Feedback** — Skeleton, EmptyState, ErrorState, Toast
4. **Data display** — MoneyAmount, ChipCount, StatCard, ParticipantRow, TransferRow
5. **Forms** — FormField, NumericInput, SelectField, SearchInput
6. **Overlays** — BottomSheet, Modal, ConfirmDialog, InvitationPopup

All existing screens will be rebuilt using these shared primitives. No screen should define its own one-off styled components for elements that exist in the shared library.

---

## Accessibility requirements

- Minimum contrast ratio 4.5:1 for body text, 3:1 for large text (WCAG AA)
- All interactive elements have accessible labels
- Touch targets minimum 44x44px
- Color is never the only indicator of state (positive/negative values also use +/- prefix or arrow icons)
- Screen reader support for key flows (auth, view game, view settlement)
- Reduced-motion: skip any decorative animations when system reduce-motion is enabled

---

## What Phase 5 does NOT change

- No backend code modifications
- No API contract changes (request/response shapes are identical)
- No new API endpoints
- No database schema changes
- No new data models
- No permission model changes
- No realtime event changes
- No business logic changes
- No new features (no new functionality that didn't exist in Phase 4)
- No changes to the Expo Router route structure (paths stay the same)

---

## Out of scope for Phase 5

- Dark/light mode toggle (Phase 5 is dark-only; light mode is a future consideration)
- Animated transitions beyond simple fades and slides
- Custom fonts (system font only)
- Illustration or custom iconography (use system icons or a standard icon set)
- Onboarding tutorial or walkthrough
- Push notifications (APNs / FCM)
- Tablet or web layout adaptations
- Internationalization or localization
- Backend performance optimizations

---

## Success criteria for Phase 5

1. Every screen in the app uses the shared design token system — no hardcoded colors, spacing, or type sizes
2. Every screen uses shared primitive components — no one-off styled elements for common patterns
3. The app feels premium and iPhone-native: dark charcoal palette, generous spacing, confident typography
4. Numeric values (money, chips, buy-ins, settlements) are the most readable elements on every screen
5. Dealer workflows require fewer taps and less visual scanning than before
6. Player views are clean and uncluttered — read-only data is presented simply
7. The settlement screen has clear visual hierarchy and light drama
8. Auth screens feel more cinematic and brand-forward than in-app screens
9. No poker cliches: no card icons, chip clipart, neon, casino imagery, or gamified decorations
10. All existing app behavior is preserved — every feature from Phases 1–4 works identically
11. The component library is documented, consistent, and reusable across all screens
