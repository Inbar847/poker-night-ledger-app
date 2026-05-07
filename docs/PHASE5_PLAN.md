# PHASE5_PLAN.md

This file is the execution roadmap for **Phase 5** of Poker Night Ledger.  
Claude must implement **one stage at a time** and stop after the requested stage.

Read `PHASE5_PRODUCT_SPEC.md`, `PHASE5_ARCHITECTURE.md`, and the `docs/frontend/` documents before implementing any stage.  
The MVP stages (0–9), Phase 2 stages (10–17), Phase 3 stages (18–23), and Phase 4 stages (24–29) are complete and must not be regressed.

**Phase 5 is a pure frontend phase.** No backend code, API contracts, database schemas, or business logic are modified.

---

# Stage 30 — Phase 5 docs + skills bootstrap

## Goal
Create the Phase 5 documentation set and skills that define the design system, component rules, screen specs, and execution workflow for the frontend redesign.

## Scope
- Documentation only — no code changes

## Deliverables
- `docs/PHASE5_PRODUCT_SPEC.md` — design philosophy, principles, and product rules for the redesign
- `docs/PHASE5_ARCHITECTURE.md` — component architecture, token system, and mobile structure changes
- `docs/PHASE5_PLAN.md` — this file: stage-by-stage execution roadmap
- `docs/frontend/DESIGN_LANGUAGE.md` — detailed design language specification
- `docs/frontend/COMPONENT_RULES.md` — rules for building and using shared components
- `docs/frontend/SCREEN_SPECS.md` — per-screen visual and interaction specifications
- `.claude/skills/frontend-phase5-stage/SKILL.md` — skill for executing Phase 5 stages
- `.claude/skills/frontend-ui-qa/SKILL.md` — skill for UI quality assurance
- Updated `CLAUDE.md` with Phase 5 section
- Updated `execute-stage` skill to reference Phase 5 docs

## Acceptance criteria
- All documentation files exist and are internally consistent
- Design tokens, component specs, and screen specs are detailed enough to implement without ambiguity
- Skills are functional and reference the correct docs
- No code changes were made

## Stop boundary
Do not begin the mobile UI audit. Do not write any code.

---

# Stage 31 — Current mobile UI audit

## Goal
Audit every existing mobile screen and document the current state: what components exist, what styling patterns are used, what hardcoded values need replacement, and what screens need the most work.

## Scope
- Read-only audit of existing mobile code
- Output: audit report document

## Deliverables
- `docs/frontend/AUDIT_REPORT.md` — comprehensive audit of the current mobile UI
  - List of every screen file with its current component structure
  - Inventory of hardcoded colors, spacing, font sizes, and one-off styled components
  - Identification of shared patterns that can be extracted into primitives
  - Screen-by-screen difficulty assessment (simple reskin vs. significant restructure)
  - Recommended execution order within each stage (tackle similar patterns together)
  - Screenshots or descriptions of current visual state for comparison

## Acceptance criteria
- Every route and screen file in the mobile app is accounted for
- Hardcoded values and one-off components are inventoried
- The audit provides clear guidance for Stages 32–41

## Stop boundary
Do not create theme files. Do not modify any code. Audit only.

---

# Stage 32 — Theme foundation and design tokens

## Goal
Create the design token system and theme foundation that all shared components and screens will use.

## Scope
- New files in `mobile/src/theme/`
- No screen changes yet

## Deliverables
- `mobile/src/theme/tokens.ts` — color, spacing, radius, and size tokens as specified in `PHASE5_ARCHITECTURE.md`
- `mobile/src/theme/typography.ts` — text style presets with tabular-lining numerals for numeric values
- `mobile/src/theme/shadows.ts` — shadow/elevation presets
- `mobile/src/theme/index.ts` — re-exports all theme modules
- Verify: tokens compile, are importable, and TypeScript types are correct

## Acceptance criteria
- All token values match `PHASE5_PRODUCT_SPEC.md` color system and spacing system
- Typography presets include `fontVariant: ['tabular-nums']` for all numeric styles
- TypeScript provides autocomplete for all token paths
- No screen changes — tokens are created but not yet consumed

## Stop boundary
Do not create shared components. Do not modify screens.

---

# Stage 33 — Shared primitive component system

## Goal
Build the full shared component library that all screens will use.

## Scope
- New files in `mobile/src/components/` subdirectories
- No screen changes yet

## Deliverables

### Primitives (`src/components/primitives/`)
- `Text.tsx` — themed text with `variant` and `color` props
- `Button.tsx` — primary, secondary, ghost, destructive variants with loading and disabled states
- `Card.tsx` — default and prominent variants with optional press handler
- `Input.tsx` — themed text input with label, placeholder, and error state
- `Badge.tsx` — count/status badge with accent, warning, neutral variants
- `Avatar.tsx` — circular avatar with image URI or fallback initials
- `Divider.tsx` — themed horizontal rule
- `Spacer.tsx` — vertical/horizontal spacing using token values

### Layout (`src/components/layout/`)
- `Screen.tsx` — safe area wrapper with background color, optional scroll, optional padding
- `ScreenHeader.tsx` — consistent header with title, left/right actions
- `Section.tsx` — titled content group with optional action
- `Row.tsx` — horizontal flex layout with standard gap

### Feedback (`src/components/feedback/`)
- `Skeleton.tsx` — animated placeholder blocks
- `EmptyState.tsx` — centered empty state with title, description, optional CTA
- `ErrorState.tsx` — error display with retry button
- `Toast.tsx` — transient feedback message

### Data display (`src/components/data-display/`)
- `MoneyAmount.tsx` — formatted currency with positive/negative coloring and tabular numerals
- `ChipCount.tsx` — formatted chip count display
- `StatCard.tsx` — stat value + label card for profile/stats screens
- `ParticipantRow.tsx` — participant with avatar, name, role badge, trailing content
- `TransferRow.tsx` — settlement transfer row ("A → B: $X")
- `GameCard.tsx` — game summary card for dashboard/history lists

### Forms (`src/components/forms/`)
- `FormField.tsx` — label + children + error wrapper
- `NumericInput.tsx` — large numeric entry with prefix/suffix
- `SelectField.tsx` — selection input
- `SearchInput.tsx` — search/filter input with icon

### Overlays (`src/components/overlays/`)
- `BottomSheet.tsx` — slide-up modal with configurable height
- `Modal.tsx` — centered modal
- `ConfirmDialog.tsx` — destructive action confirmation

### Index files
- `src/components/index.ts` — master re-export of all component groups

## Acceptance criteria
- Every component specified in `PHASE5_ARCHITECTURE.md` exists and compiles
- All components consume design tokens from `src/theme/` — no hardcoded values
- Components are typed with clear prop interfaces
- Components render correctly in isolation (visual check)
- No screen files are modified — components are built but not yet integrated

## Stop boundary
Do not begin screen redesigns. Components only.

---

# Stage 34 — Welcome / Login / Register redesign

## Goal
Redesign the auth screens to be cinematic and brand-forward: the first impression of the app.

## Scope
- Rebuild Welcome, Login, and Register screens using shared components
- Auth-specific atmospheric styling (gradients, generous spacing)
- No changes to auth logic, API calls, token storage, or navigation

## Deliverables
- Welcome screen: full-bleed dark charcoal with subtle gradient, large brand text, "Get Started" CTA
- Login screen: generous layout, themed inputs, emerald CTA, error handling preserved
- Register screen: display name + email + password fields, themed consistently with login
- All auth data hooks, validation, error handling, and navigation remain unchanged
- Skeleton/loading states for async operations

## Key design rules for auth screens
- More atmospheric than in-app screens — this is the brand moment
- Subtle gradient background (not on buttons — only decorative background)
- Large heading typography with generous vertical spacing
- Emerald primary CTA buttons (large variant, full width)
- Minimal content — no clutter, no explanatory paragraphs
- Soft transitions between screens

## Files likely to change
- `mobile/app/(auth)/welcome.tsx` or equivalent
- `mobile/app/(auth)/login.tsx` or equivalent
- `mobile/app/(auth)/register.tsx` or equivalent
- Any shared auth layout file

## Acceptance criteria
- Auth screens feel premium and cinematic — spacious, confident, dark
- All existing auth flows work: register, login, error display, navigation
- Design tokens are used throughout — no hardcoded values
- Shared components (Button, Input, Text) are used — no one-off elements

## Stop boundary
Do not redesign the app shell or in-app screens.

---

# Stage 35 — App shell + Home / Dashboard redesign

## Goal
Redesign the app shell (tab bar, navigation structure) and the home/dashboard screen.

## Scope
- Tab bar styling (dark charcoal, muted icons, emerald active indicator)
- Dashboard screen rebuild with themed cards and sections
- No changes to navigation structure, route paths, or data fetching

## Deliverables
- App shell: themed bottom tab bar with 3–4 tabs, proper safe area handling, dark status bar
- Dashboard: personal greeting, active game card (prominent with live indicator), recent games section, quick-create action
- Notification badge on tab bar (if notifications tab exists)
- All data hooks, queries, and navigation remain unchanged
- Skeleton loading state for dashboard data

## Files likely to change
- `mobile/app/(app)/_layout.tsx`
- `mobile/app/(app)/index.tsx` or home screen equivalent
- Tab bar configuration files

## Acceptance criteria
- Tab bar is dark charcoal with emerald active indicator
- Dashboard shows active game prominently and recent games in card layout
- Quick-create game action is immediately accessible
- All existing navigation works unchanged
- Status bar shows light content on dark background

## Stop boundary
Do not redesign game lobby or live game screens.

---

# Stage 36 — Game Lobby redesign

## Goal
Redesign the game lobby screen for both dealer and player views, and the create game flow.

## Scope
- Game lobby screen (dealer view + player view)
- Create game screen/flow
- No changes to game creation logic, invitation flow, or participant management APIs

## Deliverables
- Game lobby — dealer view: participant list with clear rows, prominent invite/start/add-guest buttons, invite link sharing
- Game lobby — player view: clean read-only participant list, game info
- Create game flow: themed form inputs, minimal fields, emerald CTA
- Pending invitation status indicators
- All data hooks, mutations, and navigation remain unchanged
- Skeleton and empty states

## Key design rules
- Dealer controls are large, prominent buttons — not hidden in menus or overflow actions
- Player view is deliberately simpler — remove controls they cannot use
- Participant rows use ParticipantRow component with avatar, name, role badge
- Invite link sharing is a single prominent action (not buried)

## Files likely to change
- `mobile/app/(app)/games/[id]/lobby.tsx` or equivalent
- `mobile/app/(app)/games/create.tsx` or equivalent
- `mobile/src/features/invitations/InviteFriendModal.tsx`

## Acceptance criteria
- Dealer controls are prominent and fast to reach
- Player sees a clean, read-only lobby view
- Create game form is clean and minimal
- All invitation, participant management, and game creation flows work unchanged

## Stop boundary
Do not redesign the live game dashboard or data entry flows.

---

# Stage 37 — Live Game Dashboard redesign

## Goal
Redesign the live game dashboard — the most information-dense and interaction-heavy screen in the app.

## Scope
- Live game screen (dealer view + player view)
- No changes to WebSocket connections, data hooks, or mutation logic

## Deliverables
- Dealer view: participant list with running buy-in totals, large add-buy-in / add-expense / end-game actions, clear numeric totals
- Player view: participant list with buy-in totals (read-only), own position highlighted, live status
- Real-time update display is seamless — no jarring reloads or flashes
- Numeric values are the visual priority: large, high-contrast, tabular-lining
- Dealer action buttons are large touch targets (44px+ minimum) — designed for use at a busy table
- Early cash-out action visible for players with appropriate status

## Key design rules
- This is the most-used screen during a game — optimize for speed and clarity over aesthetics
- Numeric values (buy-in totals, chip counts) must be the most prominent elements
- Dealer actions must be reachable without scrolling on a standard iPhone screen
- Player view should feel calm and simple — a read-only scoreboard
- Real-time participant joins and buy-in updates should animate smoothly into the list

## Files likely to change
- `mobile/app/(app)/games/[id]/index.tsx` or active game screen
- Related feature components in `src/features/`

## Acceptance criteria
- Dealer can add buy-ins, add expenses, and manage the game with minimal taps
- Player sees a clear, real-time-updating read-only view
- All numeric values use `MoneyAmount` or `ChipCount` components with tabular numerals
- WebSocket updates reflect instantly without visual jank
- All existing dealer and player interactions work unchanged

## Stop boundary
Do not redesign the data entry modals (buy-in, expense, final stacks).

---

# Stage 38 — Buy-in / Expense / Final Stacks flows redesign

## Goal
Redesign the data entry flows for buy-ins, expenses, and final stacks.

## Scope
- Buy-in entry modal/screen
- Expense entry modal/screen (including player-added expenses)
- Final stacks entry screen
- No changes to validation logic, API calls, or form data handling

## Deliverables
- Buy-in entry: bottom sheet with large NumericInput, participant selector (dealer only), pre-filled values from smart autofill
- Expense entry: bottom sheet with amount, description, payer selector (dealer), split configuration. Non-dealer: auto-set payer, simplified view
- Final stacks entry: list of participants with large numeric inputs for chip counts
- All forms use FormField, NumericInput, and Button components
- Confirmation dialogs for delete actions use ConfirmDialog
- Instant feedback on save (loading state on button)

## Key design rules
- One concept per modal — do not combine buy-in and expense entry
- Large numeric inputs with clear labels — the dealer may be entering data quickly while managing a table
- Pre-fill and smart defaults wherever the data layer supports them
- Destructive actions (delete buy-in, delete expense) require confirmation

## Files likely to change
- `mobile/app/(app)/games/[id]/buyin.tsx` or equivalent
- `mobile/app/(app)/games/[id]/expense.tsx` or equivalent
- `mobile/app/(app)/games/[id]/final-stacks.tsx` or equivalent
- Related modals and forms in `src/features/`

## Acceptance criteria
- Buy-in entry is fast and clear with large numeric input
- Expense entry works for both dealers (any payer) and players (self-payer)
- Final stacks entry shows all participants with large chip count inputs
- Smart autofill pre-fills correctly
- All validation and error handling works unchanged
- Confirmation dialogs appear for destructive actions

## Stop boundary
Do not redesign the settlement screen.

---

# Stage 39 — Settlement redesign

## Goal
Redesign the settlement screen — the emotional payoff of the game — with clear visual hierarchy and light drama.

## Scope
- Settlement screen
- Transfer list display
- Audit trail / edit history screen
- Retroactive editing UI for dealers
- No changes to settlement calculation logic or API calls

## Deliverables
- Settlement screen: clear winner/loser separation, prominent transfer list, net result per player
- Transfer list: large TransferRow components with "A → B: $X" format
- Visual distinction between positive and negative results (emerald for winners, coral for losers)
- Expense breakdown as a collapsible or secondary section
- Audit trail: clean chronological list of edits with before/after values
- Dealer edit actions on closed games (edit buy-ins, edit final stacks) — UI only, reusing existing mutations
- `game_resettled` notification rendering

## Key design rules
- The transfer list is the hero element — largest and most prominent
- Subtle visual drama: clear separation between winners and losers, perhaps a divider or background tint shift
- Net result per player uses MoneyAmount with positive/negative coloring
- No confetti, no animations, no gamification — just confident, clear resolution
- Audit trail access is a subtle link, not a primary element

## Files likely to change
- Settlement screen file
- `mobile/src/features/game-edits/EditHistoryScreen.tsx`
- `mobile/src/features/notifications/NotificationItem.tsx` (game_resettled rendering)

## Acceptance criteria
- Settlement clearly shows who pays whom with large, readable amounts
- Winners and losers are visually distinct (color, not just numbers)
- Transfer list is the most prominent element on the screen
- Audit trail is accessible and readable
- Dealer can trigger retroactive edits from the settlement screen
- All existing settlement and editing flows work unchanged

## Stop boundary
Do not redesign profile, stats, or history screens.

---

# Stage 40 — Profile / Stats / History / Notifications / Game Details redesign

## Goal
Redesign the remaining screens: profile, personal statistics, game history, notification list, and game detail views.

## Scope
- Profile screen
- Stats screen
- Game history list
- Game detail screen (past games)
- Notifications screen
- No changes to data fetching, queries, or navigation

## Deliverables
- Profile: themed avatar, display name, member-since, clean personal info
- Stats: large StatCard components for lifetime totals (games played, net result, biggest win, etc.)
- History: chronological game list using GameCard components with key outcomes
- Game detail: full past game breakdown using shared components
- Notifications: clean list with read/unread states, delete-all action, themed notification items
- All screens use skeleton loading, empty states, and error states

## Files likely to change
- Profile screen
- Stats screen
- History/game list screen
- Game detail screen
- Notifications screen and notification item components

## Acceptance criteria
- Stats display uses large, readable numeric formats with StatCard
- Game history uses GameCard with clear game outcomes
- Notifications are visually clean with proper read/unread distinction
- All existing navigation, data fetching, and actions work unchanged
- Empty states appear for empty lists (no games, no notifications, etc.)

## Stop boundary
Do not begin the consistency pass.

---

# Stage 41 — Consistency pass + QA polish

## Goal
Final pass across every screen to ensure visual consistency, fix spacing/alignment issues, verify token compliance, and catch edge cases.

## Scope
- Every screen in the app
- No new features or components

## Deliverables
- **Token audit:** verify no hardcoded colors, spacing, or font sizes remain in any screen file
- **Component audit:** verify no one-off styled components exist for elements covered by the shared library
- **Spacing consistency:** verify all screens use the same spacing scale and horizontal padding
- **Typography consistency:** verify all text uses the Text component with correct variants
- **Numeric formatting:** verify all money/chip values use MoneyAmount or ChipCount
- **Loading states:** verify every screen has a skeleton state (no spinners)
- **Empty states:** verify every list has an appropriate empty state
- **Error states:** verify API failures show ErrorState with retry
- **Touch targets:** verify all interactive elements are at least 44x44px
- **Safe area:** verify no content overlaps with status bar, home indicator, or notch
- **Device testing:** verify layout on iPhone SE (small), standard, and Pro Max (large)
- **Dark background:** verify the app looks cohesive — no screens with white backgrounds or mismatched tones
- **Reduced motion:** verify decorative animations respect system reduced-motion setting
- Fix any issues found during the audit

## Acceptance criteria
- Zero hardcoded colors, spacing, or font sizes in screen files
- Zero one-off styled components for shared patterns
- Consistent visual appearance across all screens
- All touch targets meet minimum size
- All states (loading, empty, error, data) are handled on every screen
- App works correctly on small, standard, and large iPhone screens
- Every feature from Phases 1–4 still works identically

## Stop boundary
This is the final Phase 5 stage. Do not begin Phase 6 work.

---

# Phase 5 stage execution rules

For every Phase 5 stage Claude must:

1. Read `PHASE5_PRODUCT_SPEC.md`, `PHASE5_ARCHITECTURE.md`, and the relevant `docs/frontend/` documents before starting.
2. Restate the stage goal in 3–6 bullets.
3. List files to be created/changed.
4. Implement only that stage.
5. Run or describe the exact commands needed.
6. Visually verify changes where possible (start dev server, check screens).
7. End with:
   - summary
   - changed files
   - commands
   - manual test steps (visual verification + interaction testing)
   - assumptions
   - next recommended stage

Do not silently continue into the next stage.  
Do not regress any behavior from Phases 1–4.  
Do not change backend code, API contracts, or data models.
