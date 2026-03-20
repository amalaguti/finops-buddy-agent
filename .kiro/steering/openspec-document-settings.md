---
inclusion: always
---

# Document settings and environment variables

For **every OpenSpec change** that introduces or changes user-facing configuration:

- **Document in README.md** (or an appropriate doc): any new or changed **settings file** (path, format, main keys) and **environment variables** that end users need to configure the app.
- When **implementing tasks**, add or update a **Configuration** (or **Settings and environment**) section so users know:
  - Where the settings file lives (e.g. XDG path, override env var)
  - Which env vars exist, what they do, and precedence (e.g. env overrides file, `.env.local` overrides `.env`)
- When **creating tasks** for a change that adds config: include a task to update README.md (or docs) with the new settings and env vars.

This keeps the README the single place for end-user configuration documentation.
