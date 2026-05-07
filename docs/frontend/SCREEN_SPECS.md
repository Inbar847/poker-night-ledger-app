# SCREEN_SPECS.md

# Poker Night Ledger — Screen-by-Screen Specifications

This document specifies the visual structure, component usage, and interaction behavior of every screen in the app. Each screen spec is the blueprint for its rebuild in Phase 5.

**Important:** These specs define the visual layer only. All data hooks, API calls, store usage, permissions, and navigation remain exactly as built in Phases 1–4.

---

## Global screen tone rules

Every screen in the app must follow these visual priorities:

1. The app must feel like a **premium private poker utility**, not a casino app, not a generic fintech dashboard, and not a mobile starter template.
2. Poker atmosphere must be present but subtle:
   - dark charcoal surfaces
   - restrained felt-inspired green
   - deep wine / burgundy accents
   - soft material depth
   - no neon
   - no loud casino styling
3. The UI must remain calm and minimal even when the data is dense.
4. Numbers are first-class content:
   - totals
   - buy-ins
   - balances
   - settlement transfers
   must always be easy to scan.
5. Dealer screens must feel operational and fast.
6. Player screens must feel simpler, calmer, and more read-only.
7. Auth / entry screens may be more cinematic and atmospheric than the in-app functional screens.
8. Avoid generic gaming metaphors such as gamepad-like iconography or playful arcade styling.
9. Avoid bright emerald/coral color usage; prefer more muted, premium semantic tones.
10. When in doubt, remove one decorative layer rather than add one.

---

## Auth screens (Stage 34)

### Welcome screen

**Purpose:** First impression. Establish a premium, atmospheric, private-poker identity before the user enters the functional app.

**Visual tone:**
- cinematic
- elegant
- calm
- premium
- low-noise
- subtly poker-specific

**Layout:**
```
┌──────────────────────────────┐
│  [Living visual background]  │
│  dark, atmospheric, premium  │
│                              │
│  [Soft dark overlay]         │
│  to ensure text legibility   │
│                              │
│        [Spacer 6xl]          │
│                              │
│     "Poker Night Ledger"     │
│      (h1, text.primary,      │
│         centered)            │
│                              │
│     "Run the table with      │
│      calm precision"         │
│     (body, text.secondary,   │
│         centered)            │
│                              │
│        [Spacer 4xl]          │
│                              │
│   [ Get Started — primary ]  │
│        (lg, full-width)      │
│                              │
│     "Already have an         │
│      account? Log in"        │
│     (ghost button, centered) │
│                              │
│        [Spacer 3xl]          │
│                              │
└──────────────────────────────┘
```

**Background:**
Use a living, atmospheric visual background rather than a plain gradient.
Preferred direction:
- dark cinematic poker-table mood
- subtle felt-inspired texture
- low-motion or still premium background image
- no literal casino imagery
- no loud chips/cards decoration
- no bright highlights

The background must remain decorative only and must never harm readability.

**Interactions:**
- "Get Started" → navigates to Register
- "Log in" → navigates to Login

**Components used:** Screen, Text, Button (primary lg), Button (ghost), Spacer, BackgroundVisualLayer

---

### Login screen

**Purpose:** Returning user authentication.

**Visual tone:**
- refined
- cinematic but quieter than the welcome screen
- minimal
- premium
- high-trust

**Background:** Use the same dark atmospheric background family as the Welcome screen, but quieter and more subdued. It should feel like the user has already entered the product world, not like a generic auth form.

**Layout:**
```
┌──────────────────────────────┐
│                              │
│   [Gradient background]      │
│                              │
│        [Spacer 5xl]          │
│                              │
│        "Welcome back"        │
│      (h1, text.primary,      │
│         centered)            │
│                              │
│        [Spacer 3xl]          │
│                              │
│   [Email input]              │
│        [Spacer base]         │
│   [Password input]           │
│                              │
│        [Spacer xl]           │
│                              │
│   [ Log In — primary lg ]    │
│                              │
│     "Don't have an account?  │
│      Sign up"                │
│     (ghost button, centered) │
│                              │
│   [Error message if any]     │
│   (caption, semantic.negative)│
│                              │
└──────────────────────────────┘
```

**Interactions:**
- Submit → existing auth mutation → navigate to app on success
- Error → display below form in `semantic.negative`
- "Sign up" → navigate to Register

**Components used:** Screen, Text, Input (email), Input (password), Button (primary lg), Button (ghost), Spacer

---

### Register screen

**Purpose:** New user account creation.

**Visual tone:**
- refined
- calm
- premium
- inviting
- minimal

**Layout:** Same structure as Login with three fields:
1. Display name
2. Email
3. Password

CTA: "Create Account" (primary lg)
Secondary: "Already have an account? Log in" (ghost)

**Background:** Same visual family as Welcome/Login, with a subdued cinematic layer and strong foreground clarity.

**Components used:** Screen, Text, Input (x3), Button (primary lg), Button (ghost), Spacer

---

## App shell (Stage 35)

### Tab bar

**Structure:** Bottom tab bar with 3–4 tabs.

| Tab | Icon | Label |
|---|---|---|
| Home | `home-outline` / `home` | Home |
| Games | `layers-outline` / `layers` | Games |
| Profile | `person-outline` / `person` | Profile |

**Optional 4th tab:**

| Notifications | `notifications-outline` / `notifications` | Alerts |

**Styling:**
- Background: `bg.elevated`
- Border top: 1px `border.subtle`
- Inactive icons: `text.muted`
- Active icon: `accent.primary`
- Active label: `accent.primary`
- Inactive label: `text.muted`
- Label typography: `captionBold`

**Status bar:** Light content (`light-content` style) on all screens.

---

### Home / Dashboard screen

**Purpose:** Entry point after login. Shows current game state and recent activity.

**Visual tone:**
- calm
- premium
- social-entry
- lightly atmospheric
- not dashboard-heavy

**Layout:**
```
┌──────────────────────────────┐
│ ScreenHeader: "Hey, {name}"  │
│  right: notification bell    │
│  (badge if unread count > 0) │
├──────────────────────────────┤
│                              │
│ [Active Game Section]        │
│ Section title: "Live Game"   │
│ ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐ │
│ │ Card (prominent)         │ │
│ │  Game title     [LIVE]   │ │
│ │  Player count   Pot total│ │
│ │  "Tap to continue"       │ │
│ └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘ │
│                              │
│ [Quick Actions]              │
│ ┌──────────┐ ┌──────────┐   │
│ │ Create   │ │ Join     │   │
│ │ Game     │ │ Game     │   │
│ └──────────┘ └──────────┘   │
│                              │
│ [Recent Games Section]       │
│ Section title: "Recent"      │
│ ┌──────────────────────────┐ │
│ │ GameCard                 │ │
│ │  Title  Date  Net result │ │
│ └──────────────────────────┘ │
│ ┌──────────────────────────┐ │
│ │ GameCard                 │ │
│ └──────────────────────────┘ │
│                              │
│ [EmptyState if no games]     │
│                              │
└──────────────────────────────┘
```

**Active game card:**
- Only shown when user has an active/lobby game
- `prominent` card variant
- Live status badge: small muted felt-green pill with "LIVE" text
- Tap navigates to the game

**Quick actions:**
- Two buttons side by side
- "Create Game" (primary), "Join Game" (secondary)
- Or single "Create Game" primary button if join flow is invite-only

**Recent games:**
- List of GameCard components, most recent first
- Each shows: title, date, net result (MoneyAmount with sign)
- Empty state if no past games

**Components used:** Screen, ScreenHeader, Section, Card (prominent), Badge, GameCard, MoneyAmount, Button, EmptyState, Skeleton

**Rules:**
- The screen should feel like an elegant re-entry into the user's poker world.
- Avoid making the home screen feel like a dense admin dashboard.
- The active game card is the emotional anchor of the screen.
- Quick actions should be obvious, but the screen should still feel spacious and composed.

---

## Game Lobby (Stage 36)

### Game Lobby — Dealer view

**Purpose:** Manage participants before starting the game.

**Visual tone:**
- participant-centered
- anticipatory
- composed
- premium
- operational but not heavy

**Layout:**
```
┌──────────────────────────────┐
│ ScreenHeader: "{Game Title}" │
│  left: back                  │
│  right: settings/options     │
├──────────────────────────────┤
│                              │
│ Section: "Players ({count})" │
│ ┌──────────────────────────┐ │
│ │ ParticipantRow           │ │
│ │ [Avatar] Name [Dealer]   │ │
│ │ ParticipantRow           │ │
│ │ [Avatar] Name            │ │
│ │ ParticipantRow           │ │
│ │ [Avatar] Name [Guest]    │ │
│ │ ...                      │ │
│ └──────────────────────────┘ │
│                              │
│ [Pending invitations]        │
│ "2 pending invitations"      │
│ (caption, semantic.warning)  │
│                              │
│ ┌──────────────────────────┐ │
│ │ [ Invite Friend ]        │ │
│ │ [ Add Guest     ]        │ │
│ │ [ Share Link    ]        │ │
│ └──────────────────────────┘ │
│                              │
│ [ Start Game — primary lg ]  │
│ (bottom, full-width)         │
│                              │
└──────────────────────────────┘
```

**Dealer controls:**
- "Invite Friend" (secondary button) → opens InviteFriendModal
- "Add Guest" (secondary button) → opens guest name entry
- "Share Link" (ghost button) → shares invite link
- "Start Game" (primary lg) — fixed at bottom or prominent in view

**Components used:** Screen, ScreenHeader, Section, ParticipantRow, Badge, Button (secondary x2, ghost x1, primary lg x1), BottomSheet (for invite friend modal)

**Rules:**
- The participant list is the visual hero of the screen.
- Dealer controls should be grouped clearly and feel intentional, not scattered.
- The lobby should feel like the table is being prepared, not like a generic settings page.

### Game Lobby — Player view

**Visual tone:**
- quieter
- read-only
- socially aware
- lower-pressure

Same structure but without dealer controls. Shows:
- Participant list (read-only)
- Game info (title, date, chip rate)
- "Waiting for dealer to start" status message in `text.secondary`

---

### Create Game screen

**Purpose:** Create a new poker game.

**Layout:** Form with themed inputs:
1. Game title (Input)
2. Date (DatePicker or Input)
3. Chip cash rate (NumericInput with currency prefix)
4. Currency selector (SelectField)

CTA: "Create Game" (primary lg)

**Components used:** Screen, ScreenHeader, FormField, Input, NumericInput, SelectField, Button (primary lg)

---

## Live Game Dashboard (Stage 37)

### Live Game — Dealer view

**Purpose:** The primary working screen during a game. Maximum information density with maximum clarity.

**Visual tone:**
- premium control center
- high-trust
- fast
- calm under pressure
- numerically focused

**Layout:**
```
┌──────────────────────────────┐
│ ScreenHeader: "{Game Title}" │
│  left: back  right: [•••]   │
│  Badge: "LIVE" (muted felt-green) │
├──────────────────────────────┤
│                              │
│ [Game totals bar]            │
│  Total pot: $X,XXX           │
│  (numericLarge, text.primary)│
│  Players: N                  │
│                              │
│ Divider                      │
│                              │
│ Section: "Players"           │
│ ┌──────────────────────────┐ │
│ │ ParticipantRow           │ │
│ │ [Av] Name     $XXX [+]  │ │
│ │ ParticipantRow           │ │
│ │ [Av] Name     $XXX [+]  │ │
│ │ ParticipantRow           │ │
│ │ [Av] Name     $XXX [+]  │ │
│ └──────────────────────────┘ │
│                              │
│ ┌────────────┐┌────────────┐ │
│ │ Add        ││ Add        │ │
│ │ Expense    ││ Buy-In     │ │
│ └────────────┘└────────────┘ │
│                              │
│ [ End Game — secondary ]     │
│                              │
└──────────────────────────────┘
```

**Game totals bar:**
- Total pot in `numericLarge` — the largest text on the screen
- Player count in `caption`

**Player list:**
- ParticipantRow for each participant
- Trailing: total buy-in amount (MoneyAmount, numeric)
- [+] quick-add buy-in button (dealer only) — small felt-green icon button with restrained emphasis

**Dealer actions:**
- "Add Expense" + "Add Buy-In" side by side (secondary buttons)
- "End Game" (secondary or ghost, positioned deliberately — not accidental)
- "Invite Friend" accessible from overflow menu or header action

**Components used:** Screen, ScreenHeader, Section, ParticipantRow, MoneyAmount, Badge, Button (secondary x2), Divider

**Rules:**
- This is the operational heart of the app.
- The screen must prioritize scan speed over decorative complexity.
- The participant ledger is the hero, not the buttons.
- Total pot and participant buy-in values must feel visually authoritative.
- The screen should feel premium and decisive, never cluttered or improvised.

### Live Game — Player view

**Visual tone:**
- simpler
- lower-noise
- status-first
- emotionally aligned with the live table, but not operational

Same layout minus dealer controls:
- Participant list with buy-in totals (read-only)
- Own row highlighted (slightly different background or left accent)
- "Add Expense" button (player-added expenses — Phase 4 feature)
- No "Add Buy-In" for others, no "End Game"
- Early cash-out action if applicable

**Rules:**
- The player's own row should feel clearly discoverable.
- The player screen must not visually compete with dealer tools.
- Keep the structure familiar to the dealer view, but noticeably lighter.

---

## Data entry flows (Stage 38)

### Buy-in entry

**Presentation:** BottomSheet (60% height)

**Layout:**
```
┌──────────────────────────────┐
│  [Drag handle]               │
│  "Add Buy-In" (h3)           │
│  ──────────────────          │
│                              │
│  [Participant selector]      │
│  (dealer sees list/picker)   │
│                              │
│  Cash amount                 │
│  ┌──────────────────────────┐│
│  │ $  [  NumericInput     ] ││
│  └──────────────────────────┘│
│                              │
│  Chips amount                │
│  ┌──────────────────────────┐│
│  │    [  NumericInput     ] ││
│  └──────────────────────────┘│
│                              │
│  [Buy-in type: initial /     │
│   rebuy / addon — pills]     │
│                              │
│  [ Save — primary ]          │
│                              │
└──────────────────────────────┘
```

**Smart autofill:** Preserve the existing buy-in autofill behavior already implemented in the product. The visual layer must support it clearly without changing the underlying business logic.

**Components used:** BottomSheet, Text, FormField, NumericInput, SelectField (participant picker), Button (primary)

---

### Expense entry

**Presentation:** BottomSheet (80% height — more fields)

**Layout:**
```
┌──────────────────────────────┐
│  [Drag handle]               │
│  "Add Expense" (h3)          │
│  ──────────────────          │
│                              │
│  Description                 │
│  ┌──────────────────────────┐│
│  │ [  Input: "Pizza" etc  ] ││
│  └──────────────────────────┘│
│                              │
│  Total amount                │
│  ┌──────────────────────────┐│
│  │ $  [  NumericInput     ] ││
│  └──────────────────────────┘│
│                              │
│  Paid by                     │
│  [Participant picker]        │
│  (dealer: any participant)   │
│  (player: auto-set to self,  │
│   selector hidden or locked) │
│                              │
│  Split between               │
│  [Participant checkboxes]    │
│                              │
│  [ Save — primary ]          │
│                              │
└──────────────────────────────┘
```

**Components used:** BottomSheet, Text, FormField, Input, NumericInput, SelectField, Button (primary)

---

### Final stacks entry

**Presentation:** Full screen (too many inputs for a sheet)

**Layout:**
```
┌──────────────────────────────┐
│ ScreenHeader: "Final Stacks" │
│  left: back                  │
├──────────────────────────────┤
│                              │
│ [Instructions]               │
│ "Enter each player's final   │
│  chip count" (body,          │
│  text.secondary)             │
│                              │
│ ┌──────────────────────────┐ │
│ │ [Avatar] Player name     │ │
│ │ Chips: [ NumericInput  ] │ │
│ ├──────────────────────────┤ │
│ │ [Avatar] Player name     │ │
│ │ Chips: [ NumericInput  ] │ │
│ ├──────────────────────────┤ │
│ │ [Avatar] Player name     │ │
│ │ Chips: [ NumericInput  ] │ │
│ └──────────────────────────┘ │
│                              │
│ [Chip total vs expected]     │
│ "Total: 1,500 / 1,500"      │
│ (numeric, positive if match) │
│                              │
│ [ Close Game — primary lg ]  │
│                              │
└──────────────────────────────┘
```

**Validation feedback:** Total chips entered vs. expected total — green if matching, warning if mismatched.

**Components used:** Screen, ScreenHeader, Text, ParticipantRow (simplified), NumericInput, MoneyAmount/ChipCount, Button (primary lg)

---

## Settlement (Stage 39)

### Settlement screen

**Purpose:** The emotional payoff. Who pays whom.

**Visual tone:**
- premium payoff
- financial clarity
- emotional resolution
- calm drama
- high trust

**Layout:**
```
┌──────────────────────────────┐
│ ScreenHeader: "Settlement"   │
│  left: back                  │
│  right: "Edit History"       │
│  (ghost, text link)          │
├──────────────────────────────┤
│                              │
│ [Game summary bar]           │
│  "{Game Title}" (h3)         │
│  "{Date}" (caption)          │
│  Total pot: $X,XXX (numeric) │
│                              │
│ Divider                      │
│                              │
│ Section: "Transfers"         │
│ (the hero section)           │
│ ┌──────────────────────────┐ │
│ │ TransferRow              │ │
│ │ Alice → Bob     $120     │ │
│ ├──────────────────────────┤ │
│ │ TransferRow              │ │
│ │ Carol → Dave     $85     │ │
│ ├──────────────────────────┤ │
│ │ TransferRow              │ │
│ │ Eve → Frank      $35     │ │
│ └──────────────────────────┘ │
│                              │
│ Divider                      │
│                              │
│ Section: "Results"           │
│ ┌──────────────────────────┐ │
│ │ ParticipantRow           │ │
│ │ [Av] Bob      +$150 ▲   │ │
│ │ ParticipantRow           │ │
│ │ [Av] Dave      +$85 ▲   │ │
│ │ (positive, muted felt-green) │ │
│ │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │ │
│ │ ParticipantRow           │ │
│ │ [Av] Alice    −$120 ▼   │ │
│ │ ParticipantRow           │ │
│ │ [Av] Carol     −$85 ▼   │ │
│ │ (negative, deep muted red) │ │
│ └──────────────────────────┘ │
│                              │
│ [Expense summary —           │
│  collapsible section]        │
│                              │
│ [Dealer: Edit Buy-Ins /      │
│  Edit Final Stacks buttons]  │
│                              │
└──────────────────────────────┘
```

**Transfer list (hero):**
- Largest section, most prominent
- Each transfer in a TransferRow component
- Amounts in `numeric` or `numericLarge`

**Results list:**
- Winners first (positive, muted felt-green), then losers (negative, deep muted red)
- Subtle visual divider between winners and losers
- MoneyAmount with `showSign: true`

**Expense summary:** Collapsible — shows expenses split breakdown when expanded. Secondary information.

**Dealer actions (closed game):**
- "Edit Buy-Ins" and "Edit Final Stacks" — secondary buttons, only visible to dealer
- "View Edit History" — ghost text link in header or section

**Components used:** Screen, ScreenHeader, Section, TransferRow, ParticipantRow, MoneyAmount, Divider, Button (secondary), Card

**Rules:**
- This screen should feel like the final reveal of the night.
- The transfer list is the emotional and functional hero.
- The design must create payoff without becoming theatrical.
- Maintain trust and numeric clarity above all.

---

### Edit History screen

**Purpose:** Audit trail for retroactive edits on a closed game.

**Layout:** Simple chronological list:
```
┌──────────────────────────────┐
│ ScreenHeader: "Edit History" │
│  left: back                  │
├──────────────────────────────┤
│                              │
│ ┌──────────────────────────┐ │
│ │ Card                     │ │
│ │ "{Editor name}" (bodyBold│ │
│ │ "{Action}" (body)        │ │
│ │ Before: $XX → After: $YY│ │
│ │ "{Timestamp}" (caption)  │ │
│ └──────────────────────────┘ │
│ ┌──────────────────────────┐ │
│ │ Card                     │ │
│ │ ...                      │ │
│ └──────────────────────────┘ │
│                              │
│ [EmptyState if no edits]     │
│                              │
└──────────────────────────────┘
```

**Components used:** Screen, ScreenHeader, Card, Text, MoneyAmount, EmptyState

---

## Profile / Stats / History / Notifications (Stage 40)

### Profile screen

**Purpose:** Personal identity and stats overview.

**Visual tone:**
- personal
- premium
- composed
- lightly fintech-inspired
- not overly social

**Layout:**
```
┌──────────────────────────────┐
│ ScreenHeader: "Profile"      │
│  right: "Edit" (ghost)       │
├──────────────────────────────┤
│                              │
│       [Avatar — lg (56px)]   │
│       "{Display Name}" (h2)  │
│       "Member since {date}"  │
│       (caption, text.secondary)│
│                              │
│ Divider                      │
│                              │
│ Section: "Stats"             │
│ ┌────────────┐┌────────────┐ │
│ │ StatCard   ││ StatCard   │ │
│ │ 42         ││ +$1,250    │ │
│ │ Games      ││ Net Result │ │
│ └────────────┘└────────────┘ │
│ ┌────────────┐┌────────────┐ │
│ │ StatCard   ││ StatCard   │ │
│ │ +$450      ││ −$200      │ │
│ │ Best Win   ││ Worst Loss │ │
│ └────────────┘└────────────┘ │
│                              │
│ Divider                      │
│                              │
│ Section: "Account"           │
│ [ Log Out — destructive ]    │
│                              │
└──────────────────────────────┘
```

**StatCard:** 2x2 grid layout. Each card shows:
- Large numeric value (numericLarge or numeric)
- Small label below (caption)
- Card variant: default

**Components used:** Screen, ScreenHeader, Avatar (lg), Text, Divider, Section, StatCard, Button (destructive)

---

### Stats screen (if separate from profile)

Expanded stats view with more detailed lifetime statistics. Uses StatCard components in a grid, plus a recent performance section with GameCard list showing last 5 games.

---

### Game History screen

**Layout:**
```
┌──────────────────────────────┐
│ ScreenHeader: "Game History" │
│  left: back                  │
├──────────────────────────────┤
│                              │
│ [FlatList of GameCards]      │
│ ┌──────────────────────────┐ │
│ │ GameCard                 │ │
│ │ "Friday Night Poker"     │ │
│ │ Mar 15, 2026 • 6 players │ │
│ │ Net: +$150 (muted felt-green) │ │
│ └──────────────────────────┘ │
│ ┌──────────────────────────┐ │
│ │ GameCard                 │ │
│ │ "Weekend Game"           │ │
│ │ Mar 8, 2026 • 4 players  │ │
│ │ Net: −$75 (deep muted red) │ │
│ └──────────────────────────┘ │
│ ...                          │
│                              │
│ [EmptyState if no games]     │
│                              │
└──────────────────────────────┘
```

**GameCard:** Shows game title, date, player count, and net result (MoneyAmount with sign).

**Components used:** Screen, ScreenHeader, GameCard, MoneyAmount, EmptyState, Skeleton

---

### Game Detail screen (past game)

Full breakdown of a completed game. Shows:
- Game info header (title, date, chip rate, status)
- Participant list with final results
- Buy-in history per participant (collapsible)
- Expense list (collapsible)
- Settlement summary with transfers
- Link to edit history (if edits exist)

Uses the same settlement layout patterns as the Settlement screen, but in a read-only context.

---

### Notifications screen

**Visual tone:**
- quiet
- clean
- low-drama
- readable
- lightly elevated

**Layout:**
```
┌──────────────────────────────┐
│ ScreenHeader: "Notifications"│
│  right: "Delete All" (ghost  │
│  destructive text)           │
├──────────────────────────────┤
│                              │
│ [FlatList of notifications]  │
│ ┌──────────────────────────┐ │
│ │ Card (unread — slightly  │ │
│ │ different bg or left      │ │
│ │ accent bar)              │ │
│ │ "Alice invited you to    │ │
│ │  Friday Poker"           │ │
│ │ "2 minutes ago" (caption)│ │
│ │ [Accept] [Decline]       │ │
│ └──────────────────────────┘ │
│ ┌──────────────────────────┐ │
│ │ Card (read — standard    │ │
│ │ bg.elevated)             │ │
│ │ "Game settled: Weekend   │ │
│ │  Poker"                  │ │
│ │ "1 hour ago"             │ │
│ └──────────────────────────┘ │
│ ...                          │
│                              │
│ [EmptyState: "No            │
│  notifications"]             │
│                              │
└──────────────────────────────┘
```

**Unread distinction:** Unread notifications have a subtle left accent bar (2px felt-green) or a slightly lighter surface tone.

**Actionable notifications:** Game invitations show Accept/Decline buttons inline.

**Delete All:** Ghost button with `semantic.negative` color. Shows ConfirmDialog before deleting.

**Components used:** Screen, ScreenHeader, Card, Text, Button (secondary for accept, ghost for decline, ghost-destructive for delete all), Badge, EmptyState, ConfirmDialog

---

## Invitation popup (overlay — always present)

**Trigger:** Personal WebSocket receives `user.game_invitation` event.

**Visual tone:**
- premium modal
- immediate but not alarming
- socially relevant
- calm and focused

**Layout:**
```
┌──────────────────────────────┐
│ [Full-screen backdrop,       │
│  40% black opacity]          │
│                              │
│  ┌────────────────────────┐  │
│  │ Modal (centered)       │  │
│  │                        │  │
│  │  "Game Invitation"     │  │
│  │  (h3, centered)        │  │
│  │                        │  │
│  │  "{Inviter} invited    │  │
│  │   you to {Game Title}" │  │
│  │  (body, centered)      │  │
│  │                        │  │
│  │ [Accept — primary]     │  │
│  │ [Decline — secondary]  │  │
│  │                        │  │
│  └────────────────────────┘  │
│                              │
│  [Tap backdrop to dismiss    │
│   without acting]            │
│                              │
└──────────────────────────────┘
```

**Components used:** Modal, Text, Button (primary, secondary)

---

## Loading, empty, and error states (all screens)

**Tone rule for states:**
Loading, empty, and error states must feel intentional and premium.
They should never feel like unfinished placeholders or generic framework defaults.

### Loading state pattern

Every screen that fetches data shows a **skeleton** matching the shape of its content:
- Dashboard: skeleton cards in place of active game card and recent games
- Game list: skeleton rows
- Participant list: skeleton ParticipantRows
- Stats: skeleton StatCards
- Settlement: skeleton TransferRows and ParticipantRows

No spinners. No blank screens. No "Loading..." text.

### Empty state pattern

Every list/collection screen shows an EmptyState when no data exists:

| Screen | Empty state title | Empty state description | Action |
|---|---|---|---|
| Dashboard (no games) | "No games yet" | "Create your first poker night" | "Create Game" |
| Game history (no history) | "No games played" | "Your completed games will appear here" | — |
| Notifications (none) | "All caught up" | "You'll see game invitations and updates here" | — |
| Participant list (empty) | "No players yet" | "Invite friends or add guests" | "Invite" |

### Error state pattern

Every screen that fetches data shows an ErrorState on failure:
- Brief error message ("Failed to load games")
- "Try Again" button that calls refetch
- No technical error details (no stack traces, no HTTP codes)
