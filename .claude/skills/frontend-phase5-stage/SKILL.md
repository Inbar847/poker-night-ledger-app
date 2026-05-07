---
name: frontend-phase5-stage
description: Execute exactly one Phase 5 frontend redesign stage. Read all Phase 5 docs and frontend specs first, rebuild screens using the shared component library and design tokens, preserve all existing app behavior.
---

# frontend-phase5-stage

Use this skill when the user asks to implement a specific Phase 5 stage (Stages 30–41).

## Required behavior

1. Read these files first:
   - `CLAUDE.md`
   - `docs/PHASE5_PRODUCT_SPEC.md`
   - `docs/PHASE5_ARCHITECTURE.md`
   - `docs/PHASE5_PLAN.md`
   - `docs/frontend/DESIGN_LANGUAGE.md`
   - `docs/frontend/COMPONENT_RULES.md`
   - `docs/frontend/SCREEN_SPECS.md`

2. If the stage rebuilds screens (Stages 34–41), also read:
   - `docs/frontend/AUDIT_REPORT.md` (created in Stage 31)

3. Identify the exact stage requested by the user.

4. Before coding, provide:
   - a concise restatement of the stage goal
   - screens or components being created/rebuilt
   - files to be created/changed
   - any small assumptions

5. Implement **only** the requested stage.
   - Do not continue into future stages.
   - Do not change backend code, API contracts, or data models.
   - Do not change data hooks, services, stores, or types.
   - Do not change Expo Router route paths.
   - Use only shared components from `src/components/`.
   - Use only design tokens from `src/theme/`.
   - No hardcoded colors, spacing, font sizes, or border radii.

6. For screen rebuilds:
   - Read the existing screen file first.
   - Identify all data hooks, mutations, queries, navigation calls, and permission checks.
   - Preserve them exactly.
   - Replace only the JSX/View layer and StyleSheet with themed components.
   - Add Skeleton loading states (replace any ActivityIndicator).
   - Add EmptyState for empty lists.
   - Add ErrorState for failed data fetches.

7. Visual verification:
   - Start the Expo dev server if not running.
   - Check the rebuilt screens on device/simulator.
   - Verify all interactions work (press, submit, navigate, refresh).
   - Verify real-time updates still display correctly.

8. At the end, provide:
   - what was implemented
   - changed files
   - commands to run
   - manual test steps (visual verification + interaction testing)
   - design token compliance check (any hardcoded values remaining?)
   - assumptions/deferred items
   - next recommended stage

9. Stop and wait for the next instruction.

## Phase 5 constraints

- **Pure frontend phase.** No backend changes.
- Screens are rebuilt in place (same file, same route path).
- All data flows, permissions, and real-time behavior are preserved.
- Every component must consume design tokens — no hardcoded values.
- Every screen must use shared primitives — no one-off styled elements.
- Loading states use Skeleton, not ActivityIndicator.
- Empty states use EmptyState component.
- Error states use ErrorState component with retry.
- Touch targets are minimum 44x44px.
- Numeric values use MoneyAmount or ChipCount with tabular-lining numerals.
- No neon, no casino imagery, no gamified decorations.
- No white backgrounds, no pure black backgrounds.
- Maximum one primary button per screen section.

## Design identity reminders

- Premium, dark charcoal, iPhone-native
- Emerald accent used sparingly (primary CTA, positive values, active tab)
- Auth screens: cinematic, atmospheric, generous spacing
- In-app screens: functional, clear, fast
- Dealer screens: optimized for speed and large touch targets
- Player screens: clean, read-only, uncluttered
- Settlement: clear hierarchy, light drama, no gamification
- Numerics: tabular-lining, high-contrast, largest element on the screen
