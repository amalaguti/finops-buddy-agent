# chat-agent — Delta (chat-meta-commands)

## ADDED Requirements

### Requirement: Reserved meta-commands /tooling and /context

The chat loop SHALL treat the user inputs `/tooling` and `/context` as reserved commands. When the user enters `/tooling`, the CLI SHALL display internal tooling information: the list of available tools (and skills, if any), their purpose, and when they are used. When the user enters `/context`, the CLI SHALL display conversation context status: number of turns, current profile, session identity, token counts (when available from the model/runtime), and model-specific state or info (e.g. model ID, provider). Both commands SHALL be handled in the chat loop before sending input to the agent; the agent SHALL NOT receive `/tooling` or `/context` as user messages. No LLM call SHALL be made for these commands. Command matching SHALL be case-insensitive and SHALL ignore leading and trailing whitespace. The response SHALL be printed to the user and the loop SHALL prompt for the next input without appending the meta-command or its response to the conversation history.

#### Scenario: User enters /tooling and sees available tools

- **WHEN** the user enters `/tooling` (or `/Tooling` or `  /tooling  `) at the chat prompt
- **THEN** the CLI displays a human-readable summary of the agent’s available tools (names and descriptions, including when each is used), does not call the LLM, and prompts again for the next message

#### Scenario: User enters /context and sees conversation context status

- **WHEN** the user enters `/context` (or `/Context` or `  /context  `) at the chat prompt
- **THEN** the CLI displays conversation context status (e.g. number of turns, current AWS profile, session/account info, token counts and model-specific state when available), does not call the LLM, and prompts again for the next message

#### Scenario: Meta-commands are not sent to the agent

- **WHEN** the user enters `/tooling` or `/context`
- **THEN** that input is not appended to the conversation history and is not sent to the agent as a user message

#### Scenario: Chat welcome or docs mention meta-commands

- **WHEN** the user starts a chat session or consults the documented chat commands
- **THEN** `/tooling` and `/context` are documented (e.g. in the welcome message or README) as available commands alongside `/quit`
