# Release Checklist — Poker Night Ledger MVP

Use this checklist before releasing or handing off the MVP to real users.

---

## Backend

### Security
- [ ] `SECRET_KEY` is a strong random value (32+ bytes), not the dev placeholder
- [ ] `DEBUG=false` in the production environment
- [ ] CORS `allow_origins` is restricted to known client origins (not `"*"`)
- [ ] HTTPS is enforced via a reverse proxy; the app is not exposed on plain HTTP

### Database
- [ ] `alembic upgrade head` has been run on the production database
- [ ] Automated database backups are configured and tested
- [ ] A restore procedure has been verified at least once

### Configuration
- [ ] `.env` file is **not** committed to the repo (`.gitignore` covers it)
- [ ] `backend/.env.example` is up to date with all required variables

### Tests
- [ ] `pytest` passes with no failures (`cd backend && pytest`)
- [ ] No test is marked `skip` without a documented reason

---

## Mobile

### Configuration
- [ ] `mobile/.env.local` (or equivalent) points to the correct backend URL
- [ ] `EXPO_PUBLIC_API_URL` is set to the production backend URL for production builds
- [ ] `.env.local` is **not** committed to the repo

### Build
- [ ] `npm install` completes with no unresolved peer dependency warnings
- [ ] The app builds successfully for the target platforms (iOS / Android)
- [ ] EAS Build (or equivalent) is configured if distributing outside Expo Go

---

## End-to-end QA flows

Run through each flow manually before release:

### Flow A — Register and set up profile
- [ ] Register a new user with email + password
- [ ] Log in and receive tokens
- [ ] View profile (`GET /users/me`)
- [ ] Update full name and phone
- [ ] Log out and log back in

### Flow B — Create and run a game (as dealer)
- [ ] Create a game with title, chip_cash_rate, currency
- [ ] Generate invite link
- [ ] Add a guest participant
- [ ] Start the game
- [ ] Record buy-ins for all participants (including at least one rebuy)
- [ ] Record a shared expense with splits
- [ ] Enter final chip counts for all participants
- [ ] Close the game

### Flow C — Join as a player
- [ ] A second device/user joins via invite token
- [ ] Player can view game details and participants
- [ ] Player sees live updates when dealer records buy-ins (WebSocket)

### Flow D — View settlement
- [ ] After game close, `GET /games/{id}/settlement` returns correct balances
- [ ] `GET /games/{id}/settlement/audit` shows full line-item breakdown
- [ ] Transfer list is non-empty and the amounts make sense

### Flow E — History and stats
- [ ] `GET /history/games` returns the closed game for each participating user
- [ ] `GET /history/games/{id}` returns settlement detail
- [ ] `GET /stats/me` shows correct aggregates (games played, net result)

---

## Documentation
- [ ] `README.md` setup instructions are accurate and complete
- [ ] `docs/PRODUCTION.md` has been reviewed and is current
- [ ] `docs/ARCHITECTURE.md` matches what was actually built
- [ ] `docs/PLAN.md` stages are accurately marked as done

---

## Known deferred items (intentionally out of scope for MVP)
- Settlement payment-status tracking (who has actually paid whom)
- Refresh token server-side revocation / logout
- Structured production logging
- Multi-process WebSocket scaling (Redis pub/sub)
- Social features, leaderboards, chat
- Payment processing
