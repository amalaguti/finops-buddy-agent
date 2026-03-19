# agent-skills Specification

## Purpose

Define how the FinOps chat agent discovers and uses optional Agent Skills: skill metadata in the system prompt (progressive disclosure) and on-demand loading of full skill instructions via a safe, configurable skills directory.

## ADDED Requirements

### Requirement: Skills discovery and metadata

The system SHALL support discovering skill directories from a configurable path. Each skill SHALL be a directory containing a `SKILL.md` file with YAML frontmatter including `name` and `description`. The system SHALL parse only the frontmatter for discovery and SHALL produce a list of skill metadata (name, description) without loading full file contents.

#### Scenario: Discover skills from directory

- **WHEN** a configured skills path points to a directory containing subdirectories with valid `SKILL.md` files (with `name` and `description` in frontmatter)
- **THEN** discovery returns a list of skill metadata entries, one per valid skill directory

#### Scenario: Empty or missing skills directory

- **WHEN** the configured skills path is empty, missing, or points to a directory with no subdirectories containing `SKILL.md`
- **THEN** discovery returns an empty list and the agent runs without any skills section in the system prompt

#### Scenario: Invalid or missing frontmatter

- **WHEN** a subdirectory contains `SKILL.md` but the file has no valid YAML frontmatter or is missing required `name` or `description`
- **THEN** that subdirectory is either skipped or reported in a defined way (e.g. omitted from the list); discovery still returns metadata for other valid skills

### Requirement: System prompt includes skills metadata when configured

When a skills path is configured and discovery returns at least one skill, the system SHALL append an "Available skills" (or equivalent) section to the chat agent's system prompt, containing at least the name and description of each discovered skill so the agent can decide when to use a skill.

#### Scenario: System prompt contains skill metadata when skills are configured

- **WHEN** skills path is set and discovery returns one or more skills
- **THEN** the string used as the agent's system prompt (or prepended to the conversation) includes a section listing available skills with name and description

#### Scenario: No skills section when skills are disabled

- **WHEN** no skills path is configured or discovery returns no skills
- **THEN** the system prompt does not include an "Available skills" section (or includes an empty one); chat behavior is unchanged from current non-skills behavior

### Requirement: On-demand loading of full skill instructions

The system SHALL provide a way for the agent to load the full content of a skill's `SKILL.md` (body and frontmatter or body only) by skill name when skills are enabled. Loading SHALL be restricted to files under the configured skills directory and SHALL enforce path validation and a maximum file size.

#### Scenario: Load full instructions for valid skill name

- **WHEN** the agent requests full instructions for a skill name that matches a discovered skill directory
- **THEN** the system returns the contents of that skill's `SKILL.md` (or the body after frontmatter), subject to the configured size limit

#### Scenario: Reject invalid or unknown skill name

- **WHEN** the agent requests full instructions for a skill name that is not in the discovered list or contains invalid characters (e.g. path traversal)
- **THEN** the system does not read any file outside the skills directory and returns an error or safe message instead of file contents

#### Scenario: Path and size safety

- **WHEN** loading skill instructions, the system resolves the path to the skill's `SKILL.md`
- **THEN** the resolved path SHALL be strictly under the configured skills directory (no `..` or symlink escape), and the file size SHALL not exceed the configured maximum (e.g. 500 KB)

### Requirement: Skills configuration

The system SHALL support optional configuration for the skills feature. Configuration SHALL include a way to set the skills directory path (e.g. `FINOPS_SKILLS_PATH` environment variable and/or `agent.skills_path` in settings YAML). When the path is not set, the skills feature SHALL be disabled. All new environment variables SHALL use the `FINOPS_` prefix. Configuration SHALL be documented in README and, if applicable, in config/settings.yaml.

#### Scenario: Skills path from environment

- **WHEN** `FINOPS_SKILLS_PATH` is set to a valid directory path
- **THEN** the agent uses that path for skill discovery and for loading skill instructions (when the feature is enabled)

#### Scenario: Skills path from settings file

- **WHEN** the settings file (e.g. config/settings.yaml or path from FINOPS_CONFIG_FILE) contains `agent.skills_path` (or equivalent) set to a valid directory path, and no env override is set
- **THEN** the agent uses that path for skill discovery and loading

#### Scenario: Environment overrides settings

- **WHEN** both `FINOPS_SKILLS_PATH` and a settings file value for skills path are present
- **THEN** the environment variable takes precedence (consistent with existing FINOPS_ precedence rules)

### Requirement: Example skills and documentation

The change SHALL include at least one example FinOps skill (e.g. cost-anomaly or rightsizing-guidance) in the standard SKILL.md format so the feature is testable and documented. The README SHALL describe the Agent Skills feature, where to put skills, the SKILL.md format, and how configuration works.

#### Scenario: Example skill is valid and discoverable

- **WHEN** the repository includes an example skill directory under the default or documented skills location
- **THEN** discovery finds it and its metadata appears in the system prompt when the skills path is configured to include it

#### Scenario: README documents Agent Skills

- **WHEN** a user reads the README section for Agent Skills
- **THEN** they find the skills directory location, configuration options (FINOPS_SKILLS_PATH and/or settings), and SKILL.md format (frontmatter + body)
