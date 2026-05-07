# PRODUCT_SPEC.md

# Product name
Poker Night Ledger

## One-line summary
A mobile app for managing real-life poker nights: players, buy-ins, chip values, shared expenses, and final settlement.

---

## Problem

During home poker nights, it is difficult to accurately track:
- who bought in and how many times
- how much money each player put in
- how many chips each player has at the end
- shared expenses like pizza or drinks
- the final settlement between winners and losers

Manual tracking becomes messy, especially with many players, multiple re-buys, and side expenses.

---

## Product goal

Provide a fast, reliable, real-time system that lets a host/dealer run the financial side of a poker night from a mobile phone, while all participants can view the live state and final outcome.

---

## In-scope for MVP

- registered user accounts
- user profile
- personal game history
- personal statistics
- create a poker game
- invite existing users
- join by invite link/token
- add guest participants
- dealer-managed live ledger
- multiple buy-ins per participant
- side expenses
- final chip counts
- settlement calculation
- optimized transfer list
- real-time updates during the game

---

## Out of scope for MVP

- online poker gameplay
- cards, blinds, hands, turns, or table rules
- payment processing or escrow
- payment-status tracking for settlement transfers
- social feed or chat
- leaderboards
- public profiles
- advanced analytics
- AI suggestions

---

## Personas

### 1) Dealer / Host
The person creating the game and managing the live ledger.

Primary goals:
- create a game quickly
- add/invite players
- track buy-ins without mistakes
- record side expenses
- close the game and see final settlement

### 2) Registered Player
A user with an account who participates in games.

Primary goals:
- join a game easily
- see live updates
- review final results
- see personal history and statistics

### 3) Guest Participant
A player who does not have an account.

Primary goals:
- be included in the game by the dealer
- appear in the ledger and settlement
- not require app signup for MVP participation

---

## Core product rules

1. Every permanent identity in the system is a `User`.
2. Dealer/player is a **per-game role**, not a global role.
3. A dealer can also be a financial participant in the same game.
4. Guests exist only inside a specific game.
5. Only the dealer can update buy-ins.
6. For MVP, dealer is the source of truth for the official live ledger.
7. Realtime is required.
8. Personal statistics are shown only for registered users.

---

## Primary user flows

## Flow A — Register and set up profile
1. User installs app
2. Registers with email/password
3. Logs in
4. Updates profile details
5. Optionally adds profile image URL

Success condition:
- user has an authenticated account and profile

## Flow B — Create a game as dealer
1. Dealer opens app
2. Creates a new game
3. Sets title/date/chip cash rate/currency
4. Becomes dealer automatically
5. Invites existing users and/or adds guests
6. Starts the game

Success condition:
- active game exists with participants

## Flow C — Join a game
1. User receives invite link or token
2. Opens the app and joins
3. Is added as a participant
4. Can view the live game state

Success condition:
- player appears in the game lobby and live table

## Flow D — Run the live ledger
1. Dealer records buy-ins for participants
2. Dealer records shared expenses
3. Live view updates for connected users
4. Dealer enters final chip counts when the game ends
5. Dealer closes the game

Success condition:
- all ledger inputs needed for settlement exist

## Flow E — See settlement
1. Dealer closes the game
2. App calculates poker result + expense result
3. App generates who-pays-whom transfers
4. Participants can view final balances

Success condition:
- settlement is understandable and auditable

## Flow F — View history and stats
1. Registered user opens profile/history
2. Sees previous games
3. Opens a past game for details
4. Sees personal statistics

Success condition:
- user can understand their long-term usage and results

---

## Game states

Recommended states:
- `lobby`
- `active`
- `closed`

### lobby
Players are being added or invited. Ledger is not yet active.

### active
Buy-ins and expenses are being tracked live.

### closed
Final stacks are locked and settlement is available.

---

## Core data concepts

### User
Permanent account in the system.

### Game
A single poker session created by a dealer.

### Participant
A person attached to a game. May represent:
- registered user
- guest

### Buy-in
A cash entry that gives chips to a participant.

### Expense
A shared side cost such as pizza or drinks.

### Expense split
The amount each selected participant owes for a given expense.

### Final stack
A participant’s ending chip count.

### Settlement
The net result and optimized transfer list for the game.

---

## Permissions model for MVP

### Dealer can:
- create game
- invite/add participants
- start game
- record/update/delete buy-ins
- record/update/delete expenses
- enter/update final stacks
- close game
- view settlement

### Participant can:
- view game details they belong to
- view live updates
- view final settlement
- view their own profile/history/stats

### Guest can:
- exist as a participant in one game
- appear in ledger and settlement
- not authenticate unless later converted to a full user

---

## Realtime requirements

Realtime is required for:
- participant joins
- game start
- buy-in updates
- expense updates
- final stack updates
- game close
- settlement refresh

Users in the same game should see the latest state without manual refresh.

---

## Key screens

- Login
- Register
- Home / Dashboard
- Create Game
- Join Game
- Game Lobby
- Live Game Dashboard
- Buy-in Entry
- Expense Entry
- Final Stacks Entry
- Settlement
- Profile
- My History
- Game Details

---

## Functional requirements

### Accounts
- register
- login
- refresh session
- view/edit profile

### Games
- create game
- list user’s games
- get game details
- invite/join flows
- add guest participants
- start/close game

### Live ledger
- create/list/update buy-ins
- create/list/update expenses
- enter/list/update final stacks

### Settlement
- calculate balances
- generate optimized transfers
- expose audit breakdown

### History and stats
- game history
- historical details
- personal stats only

---

## Non-functional requirements

- responsive mobile UX
- clear typing across client and server
- auditable calculations
- deterministic settlement results
- basic tests for critical logic
- secure auth for protected data
- explicit permission checks

---

## Success criteria for MVP

The MVP is successful if:
1. a dealer can run a full poker night from the app
2. a player can join and follow the game live
3. buy-ins, expenses, and final stacks are accurately tracked
4. settlement is correct and easy to understand
5. registered users can review personal history and stats later
