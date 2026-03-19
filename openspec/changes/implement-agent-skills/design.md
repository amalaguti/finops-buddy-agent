# Implement Agent Skills — Design

## Context

The FinOps CLI has a Strands-based chat agent in `runner.py` that builds a system prompt string and prepends it to the conversation each turn; the Agent is constructed with `tools` and `model` only. Strands does not yet support Agent Skills natively (issue [#1181](https://github.com/strands-agents/sdk-python/issues/1181)); we implement skills at the application level. Cursor skills in `.cursor/skills/` are for the IDE and remain separate; we introduce a dedicated directory for chat-agent skills (e.g. `skills/` at repo root).

Constraints: FINOPS_ prefix for new env vars; no new external dependencies; path safety and size limits for loaded content.

## Goals / Non-Goals

**Goals:**

- Discover skill directories (each with `SKILL.md`), parse YAML frontmatter (name, description), and format a short "Available skills" section for the system prompt (progressive disclosure Phase 1).
- Provide a way for the agent to load full SKILL.md content on demand (Phase 2)—e.g. a `load_skill(skill_name)` tool—with path validation and size limits.
- Make skills optional via configuration; when not configured, chat behavior is unchanged.

**Non-Goals:**

- Cursor `.cursor/skills`: no change; those are for the IDE.
- Meta-tool / sub-agent pattern (e.g. AWS sample Pattern 3); can be added later if needed.
- Publishing skills to a registry; local directory only.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|------------|
| **Implementation** | In-repo minimal (new module, no AWS sample dependency) | Full control, no new deps; same SKILL.md format allows future swap to Strands native or AWS sample. |
| **Phase 2 loading** | Tool-based `load_skill(skill_name)` returning full SKILL.md body | Simple, testable, no file_read dependency; path restricted to configured skills dir. |
| **Config** | `FINOPS_SKILLS_PATH` env and/or `agent.skills_path` in settings | Consistent with existing FINOPS_ and settings.yaml usage. |
| **Skills layout** | `skills/<skill-name>/SKILL.md` at repo root (or path from config) | Matches AgentSkills.io / Cursor format; one dir per skill. |
| **System prompt** | Extend current system_prompt string with skills metadata; optionally pass to `Agent(system_prompt=...)` if we refactor | Minimal change to runner; can later pass system_prompt into Agent constructor for clarity. |

**Alternatives considered:**

- File-based: give agent a restricted `file_read` (or strands_tools.file_read). More flexible for Phase 3 resources but adds dependency or custom file tool; can add later.
- AWS sample package: would give standard compliance and multiple patterns but adds dependency; we keep option open for later migration.

## Data Flow

1. At chat startup: resolve skills path from `FINOPS_SKILLS_PATH` or settings; if empty, skip skills.
2. If path set: `discover_skills(skills_dir)` → list of `SkillMeta` (name, description); `format_skills_prompt(skills)` → string to append to system prompt.
3. Build `system_prompt = base_finops_prompt + "\n\n" + skills_metadata_section`. Optionally add `create_skill_tool(skills_dir, skills)` to agent tools.
4. When agent calls `load_skill("cost-anomaly")`: resolve path to `skills_dir / "cost-anomaly" / "SKILL.md"`, validate path is under `skills_dir`, enforce size limit, return file body.

## Module Shape

- **New module**: `src/finops_agent/agent/skills.py` (or `src/finops_agent/skills/`)
  - `SkillMeta`: dataclass or named tuple with `name`, `description` (from frontmatter).
  - `discover_skills(skills_dir: Path) -> list[SkillMeta]`: scan for subdirs with `SKILL.md`, parse frontmatter only.
  - `format_skills_prompt(skills: list[SkillMeta]) -> str`: return "Available skills: …" block.
  - `load_skill_instructions(skills_dir: Path, skill_name: str) -> str`: return full SKILL.md body; raise or return error message if invalid/missing.
  - `create_skill_tool(skills_dir: Path, skills: list[SkillMeta])`: return a Strands `@tool` that calls `load_skill_instructions` (for use in `build_agent` when skills are enabled).

**Runner changes:** In `run_chat_loop`: resolve skills path; if set, call `discover_skills`, extend system prompt with `format_skills_prompt`, and append `create_skill_tool(...)` to the tools list passed to `build_agent`.

## Security and Safety

- **Path validation**: All reads under `skills_dir` only; resolve to real path and ensure no `..` or symlink escape; reject skill names that are not simple directory names (e.g. alphanumeric + hyphen).
- **Size limit**: Cap single SKILL.md read (e.g. 500 KB) to avoid loading huge content into context.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Invalid or malicious SKILL.md in user-provided dir | Path and name validation; size limit; document that users should only point to trusted directories. |
| Strands native skills later | Keep SKILL.md format and directory layout; migration is a thin wrapper that passes same path to Strands API. |

## Migration Plan

When Strands adds native skills (e.g. plugin or `Agent(skills=[...])`): keep `skills/` layout and SKILL.md format; replace our discovery + prompt injection + load_skill tool with Strands API; optionally keep config (FINOPS_SKILLS_PATH) and pass path to Strands.

## Open Questions

- None blocking; we can refine prompt wording and example skills during implementation.
