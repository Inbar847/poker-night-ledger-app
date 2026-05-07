# PROMPTS.md

These prompts are designed for use inside Claude Code.

---

# 1) First project prompt

Use this in the first session after opening the repository:

```text
Read the following files completely before making changes:
- CLAUDE.md
- docs/PLAN.md
- docs/PRODUCT_SPEC.md
- docs/ARCHITECTURE.md

This is a full-stack mobile app called Poker Night Ledger.

Important product rules already decided:
- support registered users and guest participants
- only the dealer can update buy-ins
- realtime updates are required
- settlement payment-status tracking is out of scope for MVP
- users can join by invite link or by being invited as existing users
- statistics are personal only

Your job is to execute exactly Stage 0 from docs/PLAN.md and stop after Stage 0 is complete.

Before coding:
1. restate Stage 0 scope
2. list likely files to be created/changed
3. mention any small assumptions

After coding:
1. summarize what you implemented
2. list all changed files
3. give exact commands to run
4. provide manual test steps
5. list tests run
6. stop and wait for approval
```

---

# 2) Generic “do the next stage” prompt

Use this whenever you want Claude to move to the next approved stage:

```text
Read CLAUDE.md, docs/PLAN.md, docs/PRODUCT_SPEC.md, and docs/ARCHITECTURE.md again before changing anything.

Execute exactly Stage X from docs/PLAN.md and stop when Stage X is complete.

Rules:
- do not implement future stages
- keep business logic out of UI
- preserve the approved product decisions
- prefer small safe changes over broad rewrites
- add/update tests where relevant

Before coding:
- restate the exact stage goal
- list likely changed files
- note any assumptions

After coding:
- summarize the implementation
- list changed files
- give commands to run
- give manual test steps
- list tests run
- mention any assumptions or deferred items
- stop and wait
```

Replace `Stage X` with the relevant stage number.

---

# 3) Strict implementation prompt

Use this if Claude starts drifting too much:

```text
You are drifting outside the approved scope.

Reset and follow only the source-of-truth files:
- CLAUDE.md
- docs/PLAN.md
- docs/PRODUCT_SPEC.md
- docs/ARCHITECTURE.md

Implement exactly Stage X only.
Do not add extra features.
Do not refactor unrelated code.
Do not continue past the stage boundary.
If something is ambiguous, choose the safest MVP interpretation and state the assumption explicitly.
```

---

# 4) Bug-fix prompt

Use this after a stage if something breaks:

```text
Read CLAUDE.md and the project docs again.

A regression was introduced while working on Stage X.
Fix only the bug(s) described below.
Do not refactor unrelated code.
Do not start the next stage.

Bug description:
<PASTE BUG HERE>

At the end:
- explain the root cause
- list changed files
- give commands to verify the fix
```

---

# 5) Review prompt before you commit

Use this before committing a stage:

```text
Read CLAUDE.md and the project docs.

Review the current implementation of Stage X only.
Do not code yet.

I want:
1. scope review against docs/PLAN.md
2. architecture review against docs/ARCHITECTURE.md
3. missing validation/permission checks
4. likely bugs or edge cases
5. a short punch-list of final fixes before commit
```
