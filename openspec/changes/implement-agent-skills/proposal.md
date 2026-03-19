# Implement Agent Skills — Proposal

## Why

The Strands chat agent today has a fixed system prompt and cost tools; it has no way to load task-specific knowledge (e.g. cost anomaly investigation, rightsizing guidance) on demand. The [Agent Skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills) pattern (Anthropic / [AgentSkills.io](https://agentskills.io)) uses progressive disclosure: lightweight skill metadata in the system prompt, full instructions loaded only when the agent decides a skill is relevant. The Strands SDK does not yet support skills natively ([strands-agents/sdk-python#1181](https://github.com/strands-agents/sdk-python/issues/1181)); implementing skills at the application level in finops-agent will let the chat agent specialize by task now and migrate to native support later.

## What Changes

- Add a **skills module** that discovers skill directories (each with a `SKILL.md`), parses YAML frontmatter (name, description), and builds a short "Available skills" block for the system prompt.
- **Config**: Optional `FINOPS_SKILLS_PATH` and/or `agent.skills_path` in settings; when set, the chat agent gets skill metadata in its system prompt and a way to load full skill instructions on demand (e.g. a `load_skill` tool).
- **Runner**: Extend the system prompt with skills metadata; optionally pass `system_prompt` to the Strands Agent and add a skill-loading tool so the agent can pull full SKILL.md content when relevant.
- **Layout**: A dedicated skills directory (e.g. `skills/` at repo root), each skill a subdirectory with `SKILL.md` (YAML frontmatter + markdown body). Add 1–2 example FinOps skills (e.g. cost-anomaly, rightsizing-guidance) for testing and documentation.
- **Security**: Path validation (no traversal outside skills dir), safe skill names, and a size limit for SKILL.md.

## Capabilities

### New Capabilities

- **agent-skills**: The system SHALL support optional Agent Skills for the Strands chat agent. When a skills path is configured, the system SHALL discover skill directories containing `SKILL.md`, parse name and description from frontmatter, and inject an "Available skills" section into the agent's system prompt. The system SHALL provide a way for the agent to load full skill instructions on demand (e.g. a `load_skill(skill_name)` tool) with path and size safeguards. Configuration SHALL use FINOPS_ prefixed env or app settings and SHALL be documented in README and config/settings.yaml.

### Modified Capabilities

- **Chat agent**: When skills are configured, the agent's system prompt includes skill metadata and (if implemented) has access to a skill-loading tool; when not configured, behavior is unchanged.

## Impact

- **Dependencies**: None new; in-repo implementation only.
- **Code**: New module (e.g. `finops_agent/agent/skills.py` or `finops_agent/skills/`), changes in `runner.py` to resolve skills path, build extended system prompt, and optionally register the skill tool.
- **Configuration**: New optional `FINOPS_SKILLS_PATH` and/or `agent.skills_path` in config/settings.yaml; README update.
- **Testing**: Unit tests for discovery, prompt formatting, load_skill (valid/invalid name, path safety); optional integration test with a small skills dir.
