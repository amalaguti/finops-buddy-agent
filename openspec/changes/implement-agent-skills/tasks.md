## 1. Branch and discovery

- [ ] 1.1 Create a feature branch (e.g. `feature/implement-agent-skills`); do not implement on `main`.
- [ ] 1.2 Review the design and spec in this change; ensure skills module API (discover_skills, format_skills_prompt, load_skill_instructions, create_skill_tool) and runner integration points are clear.

## 2. Configuration

- [ ] 2.1 Add optional `FINOPS_SKILLS_PATH` environment variable and, in settings loading, support `agent.skills_path` (or equivalent) for the skills directory path; implement precedence (env overrides file).
- [ ] 2.2 Add or update `config/settings.yaml` with an optional `agent.skills_path` (or top-level `skills_path`) key in template form (commented or placeholder); keep safe to commit.
- [ ] 2.3 Document Agent Skills in README.md: what they are, where to put skills (directory layout), SKILL.md format (frontmatter + body), and configuration (FINOPS_SKILLS_PATH, settings).

## 3. Skills module

- [ ] 3.1 Implement the skills module (e.g. `src/finops_agent/agent/skills.py`): SkillMeta, `discover_skills(skills_dir)`, `format_skills_prompt(skills)`, `load_skill_instructions(skills_dir, skill_name)` with path validation and size limit, and `create_skill_tool(skills_dir, skills)` returning a Strands @tool.
- [ ] 3.2 Enforce path safety: resolve paths under skills_dir only, reject invalid skill names (e.g. no `..`, no path traversal), and cap SKILL.md read size (e.g. 500 KB).

## 4. Runner integration

- [ ] 4.1 In `run_chat_loop` (and optionally in `build_agent`): resolve skills path from config; if set, call `discover_skills`, extend the system prompt with `format_skills_prompt(skills)`, and add the skill tool from `create_skill_tool` to the tools list passed to the agent.
- [ ] 4.2 When skills path is not set or discovery returns no skills, leave system prompt and tools unchanged (no skills section, no skill tool).

## 5. Example skills

- [ ] 5.1 Add at least one example FinOps skill (e.g. `skills/cost-anomaly/SKILL.md` or `skills/rightsizing-guidance/SKILL.md`) with valid YAML frontmatter (name, description) and a short markdown body so the feature is testable and documented.

## 6. Lint, format, and tests

- [ ] 6.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues.
- [ ] 6.2 Add or extend pytest tests for the skills module and configuration: discovery (empty dir, one skill, invalid frontmatter), `format_skills_prompt` output, `load_skill_instructions` (valid name, invalid/missing name, path traversal safety), and config resolution (env vs settings). One test per spec scenario where practical; place tests in `tests/` (e.g. `test_skills.py`, `test_settings.py` for new keys).
