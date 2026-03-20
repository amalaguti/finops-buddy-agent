---
inclusion: always
---

# OpenSpec / branch policy

- When running OpenSpec workflows that make code changes (e.g. `/opsx:apply`, implementing tasks), **never do so on `main`**.
- If the current branch is `main`, require creating or switching to a feature branch (e.g. `feature/<change-name>` or `FT/<name>`) before implementing.
- Remind the user to create or switch to a branch if they are on `main` and about to apply or implement.
