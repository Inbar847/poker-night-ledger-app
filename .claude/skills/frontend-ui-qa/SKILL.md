---
name: frontend-ui-qa
description: Run a UI quality assurance check on one or more screens against the Phase 5 design system. Verifies token compliance, component usage, accessibility, and visual consistency.
---

# frontend-ui-qa

Use this skill when the user asks to QA, audit, or verify the UI of one or more screens against the Phase 5 design system.

## Required behavior

1. Read these files first:
   - `docs/PHASE5_PRODUCT_SPEC.md`
   - `docs/frontend/DESIGN_LANGUAGE.md`
   - `docs/frontend/COMPONENT_RULES.md`
   - `docs/frontend/SCREEN_SPECS.md`

2. Read the screen file(s) to be audited.

3. Run the following checks:

### Token compliance
- [ ] No hardcoded color values (search for `#`, `rgb(`, `'red'`, `'white'`, etc.)
- [ ] No hardcoded spacing values (search for raw numbers in padding/margin/gap)
- [ ] No hardcoded font sizes (search for `fontSize:` not referencing typography presets)
- [ ] No hardcoded border radii (search for `borderRadius:` not referencing tokens)
- [ ] All colors come from `tokens.color.*`
- [ ] All spacing comes from `tokens.spacing.*`
- [ ] All radii come from `tokens.radius.*`

### Component usage
- [ ] No raw `<Text>` from React Native — all text uses themed `<Text>` component
- [ ] No raw `<TextInput>` — uses `<Input>` or `<NumericInput>`
- [ ] No raw `<TouchableOpacity>` — uses `<Button>` or `<Card onPress>`
- [ ] No `<ActivityIndicator>` — uses `<Skeleton>`
- [ ] No one-off styled components for patterns covered by the library
- [ ] Money values use `<MoneyAmount>`
- [ ] Chip counts use `<ChipCount>`
- [ ] Screen wrapped in `<Screen>` component

### State handling
- [ ] Loading state shows Skeleton (not spinner, not blank)
- [ ] Empty state shows EmptyState component (not blank screen)
- [ ] Error state shows ErrorState with retry (not unhandled crash)

### Data layer preservation
- [ ] All original hook calls are preserved (useQuery, useMutation, etc.)
- [ ] All service imports are preserved
- [ ] All store usage is preserved
- [ ] All navigation calls are preserved
- [ ] All permission checks are preserved
- [ ] No business logic changes

### Design language compliance
- [ ] Background uses `bg.primary` (not white, not black)
- [ ] Cards use `bg.elevated` (not custom colors)
- [ ] No neon, casino imagery, or gamified elements
- [ ] Maximum 3–4 type sizes on the screen
- [ ] Maximum one primary button per visible section
- [ ] Positive amounts in emerald, negative in coral, zero in secondary
- [ ] Numeric values use tabular-lining font variant
- [ ] Touch targets are minimum 44x44px

### Accessibility
- [ ] Contrast ratio meets WCAG AA (4.5:1 body, 3:1 large text)
- [ ] Interactive elements have accessible labels
- [ ] Color is not the only indicator of state (+/− prefix on amounts)

4. Report findings:
   - **Pass:** checks that pass
   - **Fail:** violations found with file, line number, and specific issue
   - **Fix suggestions:** concrete code changes for each violation

5. If the user asks, fix the violations directly.

## When to use this skill

- After completing a Phase 5 screen rebuild stage
- During Stage 41 (consistency pass)
- When the user asks "does this screen match the design system?"
- When reviewing a PR that touches mobile UI
- When the user asks to audit the frontend

## Output format

```
## UI QA Report: {Screen name}

### Token compliance: {PASS/FAIL}
- [details if fail]

### Component usage: {PASS/FAIL}
- [details if fail]

### State handling: {PASS/FAIL}
- [details if fail]

### Data layer preservation: {PASS/FAIL}
- [details if fail]

### Design language: {PASS/FAIL}
- [details if fail]

### Accessibility: {PASS/FAIL}
- [details if fail]

### Overall: {PASS/FAIL} ({N} issues found)
```
