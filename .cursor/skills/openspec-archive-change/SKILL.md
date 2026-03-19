---
name: openspec-archive-change
description: Archive a completed change in the experimental workflow. Use when the user wants to finalize and archive a change after implementation is complete.
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: openspec
  version: "1.0"
  generatedBy: "1.2.0"
---

Archive a completed change in the experimental workflow.

**Input**: Optionally specify a change name. If omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.

**Steps**

1. **If no change name provided, prompt for selection**

   Run `openspec list --json` to get available changes. Use the **AskUserQuestion tool** to let the user select.

   Show only active changes (not already archived).
   Include the schema used for each change if available.

   **IMPORTANT**: Do NOT guess or auto-select a change. Always let the user choose.

2. **Check artifact completion status**

   Run `openspec status --change "<name>" --json` to check artifact completion.

   Parse the JSON to understand:
   - `schemaName`: The workflow being used
   - `artifacts`: List of artifacts with their status (`done` or other)

   **If any artifacts are not `done`:**
   - Display warning listing incomplete artifacts
   - Use **AskUserQuestion tool** to confirm user wants to proceed
   - Proceed if user confirms

3. **Check task completion status**

   Read the tasks file (typically `tasks.md`) to check for incomplete tasks.

   Count tasks marked with `- [ ]` (incomplete) vs `- [x]` (complete).

   **If incomplete tasks found:**
   - Display warning showing count of incomplete tasks
   - Use **AskUserQuestion tool** to confirm user wants to proceed
   - Proceed if user confirms

   **If no tasks file exists:** Proceed without task-related warning.

4. **Assess delta spec sync state**

   Check for delta specs at `openspec/changes/<name>/specs/`. If none exist, proceed without sync prompt.

   **If delta specs exist:**
   - Compare each delta spec with its corresponding main spec at `openspec/specs/<capability>/spec.md`
   - Determine what changes would be applied (adds, modifications, removals, renames)
   - Show a combined summary before prompting

   **Prompt options:**
   - If changes needed: "Sync now (recommended)", "Archive without syncing"
   - If already synced: "Archive now", "Sync anyway", "Cancel"

   If user chooses sync, use Task tool (subagent_type: "general-purpose", prompt: "Use Skill tool to invoke openspec-sync-specs for change '<name>'. Delta spec analysis: <include the analyzed delta spec summary>"). Proceed to archive regardless of choice.

5. **Perform the archive**

   Create the archive directory if it doesn't exist:
   ```bash
   mkdir -p openspec/changes/archive
   ```

   Generate target name using current date: `YYYY-MM-DD-<change-name>`

   **Check if target already exists:**
   - If yes: Fail with error, suggest renaming existing archive or using different date
   - If no: Move the change directory to archive

   ```bash
   mv openspec/changes/<name> openspec/changes/archive/YYYY-MM-DD-<name>
   ```

6. **Rebuild artifacts if needed (before archive)**

   Follow the **openspec-build-artifacts** rule (`.cursor/rules/openspec-build-artifacts.mdc`). **Order matters:** frontend build into webui first (so `src/finops_buddy/webui/` is current), then poetry build (so the package includes that webui), then Docker build (so the image gets the same `src/`).

   a. Check if the change touched frontend files (`frontend/` or `src/finops_buddy/webui/`):
      - If yes: prompt to rebuild hosted frontend with `cd frontend && npm run build:hosted` (do this first, before any poetry build or Docker build)

   b. Check if the change touched Docker-related files (`Dockerfile`, `docker-compose.yml`, `pyproject.toml`, `poetry.lock`, or `src/finops_buddy/`):
      - If yes: prompt to rebuild Docker image and restart container. Use the command from the build-artifacts rule: `docker build --build-arg GIT_SHA=$(git rev-parse --short HEAD) -t finops-buddy .` so the web UI shows version and commit in the nav bar (or omit the build-arg for version-only). Run Docker build after frontend build (and after poetry build when doing version bump).

   Use `git diff main --name-only` to detect changed files if unclear from change artifacts.

7. **Display summary**

   Show archive completion summary including:
   - Change name
   - Schema that was used
   - Archive location
   - Whether specs were synced (if applicable)
   - Note about any warnings (incomplete artifacts/tasks)
   - Build artifacts regenerated (if any)

8. **Prompt for version bump (mandatory)**

   In the **same** response as the archive summary, follow the **openspec-version-bump** rule (`.cursor/rules/openspec-version-bump.mdc`): ask the user "Should the project patch version be bumped in `pyproject.toml` and a new build generated?" If they confirm: (1) If the change touched frontend or webui, run `cd frontend && npm run build:hosted` first so the package includes the latest UI. (2) Bump the patch version in `pyproject.toml` and run `poetry build`. (3) If the user also requested a Docker rebuild, run it after poetry build so the image gets the updated `src/`. (4) If the app is run from an installed package in a local Poetry environment, remind the user to run `poetry install` in that environment after the bump/build so the runtime sees the new version. Do not end the archive flow without this prompt.

**Output On Success**

```
## Archive Complete

**Change:** <change-name>
**Schema:** <schema-name>
**Archived to:** openspec/changes/archive/YYYY-MM-DD-<name>/
**Specs:** ✓ Synced to main specs (or "No delta specs" or "Sync skipped")

All artifacts complete. All tasks complete.
```

**Guardrails**
- Always prompt for change selection if not provided
- Use artifact graph (openspec status --json) for completion checking
- Don't block archive on warnings - just inform and confirm
- Preserve .openspec.yaml when moving to archive (it moves with the directory)
- Show clear summary of what happened
- If sync is requested, use openspec-sync-specs approach (agent-driven)
- If delta specs exist, always run the sync assessment and show the combined summary before prompting
- Prompt for build artifact regeneration (frontend, Docker) before version bump if relevant files changed
- Build artifacts prompts are optional - user may decline if they've already built or don't use Docker
