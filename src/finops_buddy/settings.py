"""App settings: YAML config and environment resolution."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

_EXCLUDED_PROFILES_CACHE: list[str] | None = None
_INCLUDED_ONLY_PROFILES_CACHE: list[str] | None = None
_AGENT_MODEL_ID_CACHE: str | None = None
_AGENT_TEMPERATURE_CACHE: float | None = None
_AGENT_MAX_COMPLETION_TOKENS_CACHE: int | None = None
_KNOWLEDGE_MCP_ENABLED_CACHE: bool | None = None
_KNOWLEDGE_MCP_URL_CACHE: str | None = None
_BILLING_MCP_ENABLED_CACHE: bool | None = None
_BILLING_MCP_COMMAND_CACHE: tuple[str, list[str]] | None = None
_DOCUMENTATION_MCP_ENABLED_CACHE: bool | None = None
_DOCUMENTATION_MCP_COMMAND_CACHE: tuple[str, list[str]] | None = None
_COST_EXPLORER_MCP_ENABLED_CACHE: bool | None = None
_COST_EXPLORER_MCP_COMMAND_CACHE: tuple[str, list[str]] | None = None
_PRICING_MCP_ENABLED_CACHE: bool | None = None
_PRICING_MCP_COMMAND_CACHE: tuple[str, list[str]] | None = None
_CORE_MCP_ENABLED_CACHE: bool | None = None
_CORE_MCP_COMMAND_CACHE: tuple[str, list[str]] | None = None
_CORE_MCP_ROLES_CACHE: list[str] | None = None
_PDF_MCP_ENABLED_CACHE: bool | None = None
_PDF_MCP_COMMAND_CACHE: tuple[str, list[str]] | None = None
_EXCEL_MCP_ENABLED_CACHE: bool | None = None
_EXCEL_MCP_COMMAND_CACHE: tuple[str, list[str]] | None = None
_READ_ONLY_GUARDRAIL_INPUT_ENABLED_CACHE: bool | None = None
_VERBOSE_TOOL_DEBUG_CACHE: bool | None = None
_AGENT_WARM_ON_STARTUP_CACHE: bool | None = None
_READ_ONLY_ALLOWED_TOOLS_CACHE: frozenset[str] | None = None
_SERVER_HOST_CACHE: str | None = None
_SERVER_PORT_CACHE: int | None = None
_CORS_ORIGINS_CACHE: list[str] | None = None
_DEMO_ACCOUNT_MAPPING_CACHE: dict[str, str] | None = None
_DEMO_ACCOUNT_ID_MAPPING_CACHE: dict[str, str] | None = None

DEFAULT_SERVER_HOST = "127.0.0.1"
DEFAULT_SERVER_PORT = 8000

DEFAULT_KNOWLEDGE_MCP_URL = "https://knowledge-mcp.global.api.aws"

# Default uvx package for Billing/Cost MCP server (see README for Docker alternative)
DEFAULT_BILLING_MCP_PACKAGE = "awslabs.billing-cost-management-mcp-server@latest"

# Default uvx package for AWS Documentation MCP server (stdio)
DEFAULT_DOCUMENTATION_MCP_PACKAGE = "awslabs.aws-documentation-mcp-server@latest"

# Default uvx package for AWS Cost Explorer MCP server (stdio); disabled by default
DEFAULT_COST_EXPLORER_MCP_PACKAGE = "awslabs.cost-explorer-mcp-server@latest"

# Default uvx package for AWS Pricing MCP server (stdio); disabled by default
DEFAULT_PRICING_MCP_PACKAGE = "awslabs.aws-pricing-mcp-server@latest"

# Default uvx package for AWS Core MCP Server (stdio); disabled by default
DEFAULT_CORE_MCP_PACKAGE = "awslabs.core-mcp-server@latest"

# Default roles for Core MCP when unset (finops, aws-foundation, solutions-architect)
DEFAULT_CORE_MCP_ROLES = ["aws-foundation", "finops", "solutions-architect"]

# Default package for PDF MCP (conversation /print; md-to-pdf-mcp: Markdown → PDF via WeasyPrint)
DEFAULT_PDF_MCP_PACKAGE = "md-to-pdf-mcp"

# Default package for Excel MCP (conversation /print; excel-mcp-server for xlsx export)
DEFAULT_EXCEL_MCP_PACKAGE = "excel-mcp-server"


def _default_config_path() -> Path:
    """Return default settings path: XDG_CONFIG_HOME/finops-agent/settings.yaml or ~/.config/..."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "finops-agent" / "settings.yaml"
    return Path.home() / ".config" / "finops-agent" / "settings.yaml"


def _get_config_path() -> Path:
    """Return config path: FINOPS_CONFIG_FILE if set, else default XDG path."""
    path = os.environ.get("FINOPS_CONFIG_FILE")
    if path:
        return Path(path)
    return _default_config_path()


def _load_yaml_server(path: Path) -> dict | None:
    """Load server section from YAML. Returns None if missing/invalid."""
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            return None
        server = data.get("server")
        return server if isinstance(server, dict) else None
    except (yaml.YAMLError, OSError) as e:
        logger.warning("Settings YAML load failed for %s: %s", path, e)
        return None


def _env_server_host() -> str | None:
    """Return FINOPS_SERVER_HOST if set, else None."""
    val = os.environ.get("FINOPS_SERVER_HOST")
    return val.strip() if val and isinstance(val, str) else None


def _env_server_port() -> int | None:
    """Return FINOPS_SERVER_PORT as int if set and valid, else None."""
    val = os.environ.get("FINOPS_SERVER_PORT")
    if val is None or (isinstance(val, str) and not val.strip()):
        return None
    try:
        n = int(val.strip())
        return n if 1 <= n <= 65535 else None
    except ValueError:
        return None


def _env_cors_origins() -> list[str] | None:
    """Return FINOPS_CORS_ORIGINS as list (comma-separated) if set, else None."""
    val = os.environ.get("FINOPS_CORS_ORIGINS")
    if val is None or (isinstance(val, str) and not val.strip()):
        return None
    return [o.strip() for o in val.split(",") if o.strip()]


def get_server_host() -> str:
    """
    Return the host the API server should bind to.
    FINOPS_SERVER_HOST overrides file; else server.host from YAML; else 127.0.0.1.
    """
    global _SERVER_HOST_CACHE
    if _SERVER_HOST_CACHE is not None:
        return _SERVER_HOST_CACHE
    env_val = _env_server_host()
    if env_val:
        _SERVER_HOST_CACHE = env_val
        return env_val
    path = _get_config_path()
    server = _load_yaml_server(path)
    if server is not None:
        h = server.get("host")
        if h and isinstance(h, str) and h.strip():
            _SERVER_HOST_CACHE = h.strip()
            return _SERVER_HOST_CACHE
    _SERVER_HOST_CACHE = DEFAULT_SERVER_HOST
    return DEFAULT_SERVER_HOST


def get_server_port() -> int:
    """
    Return the port the API server should bind to.
    FINOPS_SERVER_PORT overrides file; else server.port from YAML; else 8000.
    """
    global _SERVER_PORT_CACHE
    if _SERVER_PORT_CACHE is not None:
        return _SERVER_PORT_CACHE
    env_val = _env_server_port()
    if env_val is not None:
        _SERVER_PORT_CACHE = env_val
        return env_val
    path = _get_config_path()
    server = _load_yaml_server(path)
    if server is not None:
        p = server.get("port")
        if p is not None:
            try:
                n = int(p)
                if 1 <= n <= 65535:
                    _SERVER_PORT_CACHE = n
                    return n
            except (TypeError, ValueError):
                pass
    _SERVER_PORT_CACHE = DEFAULT_SERVER_PORT
    return DEFAULT_SERVER_PORT


def get_cors_origins() -> list[str]:
    """
    Return CORS allowed origins for the API server.
    FINOPS_CORS_ORIGINS (comma-separated) overrides file; else server.cors_origins from YAML;
    when unset or empty, returns [] (no CORS middleware applied; same-origin only).
    """
    global _CORS_ORIGINS_CACHE
    if _CORS_ORIGINS_CACHE is not None:
        return _CORS_ORIGINS_CACHE
    env_val = _env_cors_origins()
    if env_val is not None:
        _CORS_ORIGINS_CACHE = env_val
        return env_val
    path = _get_config_path()
    server = _load_yaml_server(path)
    if server is not None:
        raw = server.get("cors_origins")
        if isinstance(raw, list):
            _CORS_ORIGINS_CACHE = [str(x).strip() for x in raw if str(x).strip()]
            return _CORS_ORIGINS_CACHE
    _CORS_ORIGINS_CACHE = []
    return []


def _get_demo_config_path() -> Path:
    """Return the path to config/demo.yaml relative to the project root."""
    return Path(__file__).resolve().parents[2] / "config" / "demo.yaml"


def _load_demo_config() -> dict | None:
    """Load demo config from config/demo.yaml. Returns None if missing/invalid."""
    try:
        path = _get_demo_config_path()
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def get_demo_account_mapping() -> dict[str, str]:
    """
    Return demo mode account name mapping from config/demo.yaml.
    Keys are real account/profile names, values are masked names.
    Example: {"payer-profile": "aws-tokyo-prd"}
    """
    global _DEMO_ACCOUNT_MAPPING_CACHE
    if _DEMO_ACCOUNT_MAPPING_CACHE is not None:
        return _DEMO_ACCOUNT_MAPPING_CACHE
    demo = _load_demo_config()
    if demo is not None:
        raw = demo.get("account_mapping")
        if isinstance(raw, dict):
            _DEMO_ACCOUNT_MAPPING_CACHE = {str(k): str(v) for k, v in raw.items()}
            return _DEMO_ACCOUNT_MAPPING_CACHE
    _DEMO_ACCOUNT_MAPPING_CACHE = {}
    return {}


def get_demo_account_id_mapping() -> dict[str, str]:
    """
    Return demo mode account ID mapping from config/demo.yaml.
    Keys are real 12-digit account IDs, values are masked IDs.
    Example: {"123456789012": "847291038572"}
    """
    global _DEMO_ACCOUNT_ID_MAPPING_CACHE
    if _DEMO_ACCOUNT_ID_MAPPING_CACHE is not None:
        return _DEMO_ACCOUNT_ID_MAPPING_CACHE
    demo = _load_demo_config()
    if demo is not None:
        raw = demo.get("account_id_mapping")
        if isinstance(raw, dict):
            _DEMO_ACCOUNT_ID_MAPPING_CACHE = {str(k): str(v) for k, v in raw.items()}
            return _DEMO_ACCOUNT_ID_MAPPING_CACHE
    _DEMO_ACCOUNT_ID_MAPPING_CACHE = {}
    return {}


def _load_yaml_excluded_profiles(path: Path) -> list[str]:
    """Load excluded_profiles from YAML file. Returns [] if missing/invalid."""
    if not path.exists():
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            return []
        raw = data.get("excluded_profiles")
        if raw is None:
            return []
        if isinstance(raw, list):
            return [str(x).strip() for x in raw if str(x).strip()]
        return []
    except (yaml.YAMLError, OSError) as e:
        logger.warning("Settings YAML load failed for %s: %s", path, e)
        return []


def _load_yaml_agent(path: Path) -> dict | None:
    """Load agent section from YAML. Returns None if missing/invalid."""
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            return None
        agent = data.get("agent")
        return agent if isinstance(agent, dict) else None
    except (yaml.YAMLError, OSError) as e:
        logger.warning("Settings YAML load failed for %s: %s", path, e)
        return None


def _load_yaml_agent_model_id(path: Path) -> str | None:
    """Load agent.model_id from YAML. Returns None if missing/invalid."""
    agent = _load_yaml_agent(path)
    if not agent:
        return None
    model_id = agent.get("model_id")
    return str(model_id).strip() if model_id else None


def _load_yaml_agent_temperature(path: Path) -> float | None:
    """Load agent.temperature from YAML. Returns None if missing/invalid."""
    agent = _load_yaml_agent(path)
    if not agent:
        return None
    val = agent.get("temperature")
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _env_agent_temperature() -> float | None:
    """Return FINOPS_AGENT_TEMPERATURE as float if set and valid, else None."""
    val = os.environ.get("FINOPS_AGENT_TEMPERATURE")
    if val is None or (isinstance(val, str) and not val.strip()):
        return None
    try:
        return float(val.strip())
    except ValueError:
        return None


def _load_yaml_included_only_profiles(path: Path) -> list[str]:
    """Load included_only_profiles from YAML file. Returns [] if missing/invalid."""
    if not path.exists():
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            return []
        raw = data.get("included_only_profiles")
        if raw is None:
            return []
        if isinstance(raw, list):
            return [str(x).strip() for x in raw if str(x).strip()]
        return []
    except (yaml.YAMLError, OSError) as e:
        logger.warning("Settings YAML load failed for %s: %s", path, e)
        return []


def _env_included_only_profiles() -> list[str] | None:
    """Return FINOPS_INCLUDED_ONLY_PROFILES as list if set, else None (use YAML)."""
    val = os.environ.get("FINOPS_INCLUDED_ONLY_PROFILES")
    if val is None or (isinstance(val, str) and not val.strip()):
        return None
    return [p.strip() for p in val.split(",") if p.strip()]


def get_openai_api_key() -> str | None:
    """Return FINOPS_OPENAI_API_KEY if set (for chat agent OpenAI provider)."""
    val = os.environ.get("FINOPS_OPENAI_API_KEY")
    return val.strip() if val and isinstance(val, str) else None


def _env_agent_model_id() -> str | None:
    """Return FINOPS_AGENT_MODEL_ID if set, else None."""
    val = os.environ.get("FINOPS_AGENT_MODEL_ID")
    return val.strip() if val and isinstance(val, str) else None


def _env_excluded_profiles() -> list[str] | None:
    """Return FINOPS_EXCLUDED_PROFILES as list if set, else None (use YAML)."""
    val = os.environ.get("FINOPS_EXCLUDED_PROFILES")
    if val is None or (isinstance(val, str) and not val.strip()):
        return None
    return [p.strip() for p in val.split(",") if p.strip()]


def get_excluded_profiles() -> list[str]:
    """
    Return resolved excluded profiles list (lazy, cached).

    YAML from config path (excluded_profiles key); FINOPS_EXCLUDED_PROFILES
    (comma-separated) overrides entire list when set. Missing/invalid file
    yields empty list.
    """
    global _EXCLUDED_PROFILES_CACHE
    if _EXCLUDED_PROFILES_CACHE is not None:
        return _EXCLUDED_PROFILES_CACHE
    env_list = _env_excluded_profiles()
    if env_list is not None:
        _EXCLUDED_PROFILES_CACHE = env_list
        return _EXCLUDED_PROFILES_CACHE
    path = _get_config_path()
    _EXCLUDED_PROFILES_CACHE = _load_yaml_excluded_profiles(path)
    return _EXCLUDED_PROFILES_CACHE


def get_included_only_profiles() -> list[str]:
    """
    Return resolved included-only profiles list (lazy, cached).

    YAML from config path (included_only_profiles key); FINOPS_INCLUDED_ONLY_PROFILES
    (comma-separated) overrides entire list when set. Missing/invalid file
    yields empty list.
    """
    global _INCLUDED_ONLY_PROFILES_CACHE
    if _INCLUDED_ONLY_PROFILES_CACHE is not None:
        return _INCLUDED_ONLY_PROFILES_CACHE
    env_list = _env_included_only_profiles()
    if env_list is not None:
        _INCLUDED_ONLY_PROFILES_CACHE = env_list
        return _INCLUDED_ONLY_PROFILES_CACHE
    path = _get_config_path()
    _INCLUDED_ONLY_PROFILES_CACHE = _load_yaml_included_only_profiles(path)
    return _INCLUDED_ONLY_PROFILES_CACHE


def get_agent_model_id() -> str | None:
    """
    Return the agent model ID for Strands (e.g. Bedrock model id).
    FINOPS_AGENT_MODEL_ID overrides file; else agent.model_id from YAML; else None.
    """
    global _AGENT_MODEL_ID_CACHE
    if _AGENT_MODEL_ID_CACHE is not None:
        return _AGENT_MODEL_ID_CACHE if _AGENT_MODEL_ID_CACHE else None
    env_val = _env_agent_model_id()
    if env_val:
        _AGENT_MODEL_ID_CACHE = env_val
        return env_val
    path = _get_config_path()
    yaml_val = _load_yaml_agent_model_id(path)
    _AGENT_MODEL_ID_CACHE = yaml_val or ""
    return yaml_val


DEFAULT_AGENT_TEMPERATURE = 0.2


def get_agent_temperature() -> float:
    """
    Return the agent temperature for OpenAI (0..2). Some models (e.g. gpt-5-nano) only support 1.
    FINOPS_AGENT_TEMPERATURE overrides file; else agent.temperature from YAML; else 0.2.
    """
    global _AGENT_TEMPERATURE_CACHE
    if _AGENT_TEMPERATURE_CACHE is not None:
        return _AGENT_TEMPERATURE_CACHE
    env_val = _env_agent_temperature()
    if env_val is not None:
        _AGENT_TEMPERATURE_CACHE = env_val
        return env_val
    path = _get_config_path()
    yaml_val = _load_yaml_agent_temperature(path)
    out = yaml_val if yaml_val is not None else DEFAULT_AGENT_TEMPERATURE
    _AGENT_TEMPERATURE_CACHE = out
    return out


DEFAULT_AGENT_MAX_COMPLETION_TOKENS = 8192


def _load_yaml_agent_max_completion_tokens(path: Path) -> int | None:
    """Load agent.max_completion_tokens from YAML. Returns None if missing/invalid."""
    agent = _load_yaml_agent(path)
    if not agent:
        return None
    val = agent.get("max_completion_tokens")
    if val is None:
        return None
    try:
        n = int(val)
        return n if n > 0 else None
    except (TypeError, ValueError):
        return None


def _env_agent_max_completion_tokens() -> int | None:
    """Return FINOPS_AGENT_MAX_COMPLETION_TOKENS as int if set and valid, else None."""
    val = os.environ.get("FINOPS_AGENT_MAX_COMPLETION_TOKENS")
    if val is None or (isinstance(val, str) and not val.strip()):
        return None
    try:
        n = int(val.strip())
        return n if n > 0 else None
    except ValueError:
        return None


def get_agent_max_completion_tokens() -> int:
    """
    Return max completion tokens for the agent (OpenAI/Bedrock). Avoids truncation mid-tool-call.
    Env FINOPS_AGENT_MAX_COMPLETION_TOKENS overrides file; else YAML; else 8192.
    """
    global _AGENT_MAX_COMPLETION_TOKENS_CACHE
    if _AGENT_MAX_COMPLETION_TOKENS_CACHE is not None:
        return _AGENT_MAX_COMPLETION_TOKENS_CACHE
    env_val = _env_agent_max_completion_tokens()
    if env_val is not None:
        _AGENT_MAX_COMPLETION_TOKENS_CACHE = env_val
        return env_val
    path = _get_config_path()
    yaml_val = _load_yaml_agent_max_completion_tokens(path)
    out = yaml_val if yaml_val is not None else DEFAULT_AGENT_MAX_COMPLETION_TOKENS
    _AGENT_MAX_COMPLETION_TOKENS_CACHE = out
    return out


def _env_knowledge_mcp_enabled() -> bool | None:
    """Return FINOPS_KNOWLEDGE_MCP_ENABLED as bool if set, else None."""
    val = os.environ.get("FINOPS_KNOWLEDGE_MCP_ENABLED")
    if val is None or (isinstance(val, str) and not val.strip()):
        return None
    return str(val).strip().lower() in ("1", "true", "yes")


def _env_knowledge_mcp_url() -> str | None:
    """Return FINOPS_KNOWLEDGE_MCP_URL if set, else None."""
    val = os.environ.get("FINOPS_KNOWLEDGE_MCP_URL")
    return val.strip() if val and isinstance(val, str) else None


def get_knowledge_mcp_enabled() -> bool:
    """
    Return whether the AWS Knowledge MCP Server is enabled.
    FINOPS_KNOWLEDGE_MCP_ENABLED overrides file; else agent.knowledge_mcp_enabled
    from YAML; else True.
    """
    global _KNOWLEDGE_MCP_ENABLED_CACHE
    if _KNOWLEDGE_MCP_ENABLED_CACHE is not None:
        return _KNOWLEDGE_MCP_ENABLED_CACHE
    env_val = _env_knowledge_mcp_enabled()
    if env_val is not None:
        _KNOWLEDGE_MCP_ENABLED_CACHE = env_val
        return env_val
    path = _get_config_path()
    agent = _load_yaml_agent(path)
    if agent is not None:
        v = agent.get("knowledge_mcp_enabled")
        if v is not None:
            _KNOWLEDGE_MCP_ENABLED_CACHE = (
                bool(v) if isinstance(v, bool) else str(v).strip().lower() in ("1", "true", "yes")
            )
            return _KNOWLEDGE_MCP_ENABLED_CACHE
    _KNOWLEDGE_MCP_ENABLED_CACHE = True
    return True


def get_knowledge_mcp_url() -> str:
    """
    Return the AWS Knowledge MCP Server URL.
    FINOPS_KNOWLEDGE_MCP_URL overrides file; else agent.knowledge_mcp_url from YAML; else default.
    """
    global _KNOWLEDGE_MCP_URL_CACHE
    if _KNOWLEDGE_MCP_URL_CACHE is not None:
        return _KNOWLEDGE_MCP_URL_CACHE
    env_val = _env_knowledge_mcp_url()
    if env_val:
        _KNOWLEDGE_MCP_URL_CACHE = env_val
        return env_val
    path = _get_config_path()
    agent = _load_yaml_agent(path)
    if agent is not None:
        v = agent.get("knowledge_mcp_url")
        if v and isinstance(v, str) and v.strip():
            _KNOWLEDGE_MCP_URL_CACHE = v.strip()
            return _KNOWLEDGE_MCP_URL_CACHE
    _KNOWLEDGE_MCP_URL_CACHE = DEFAULT_KNOWLEDGE_MCP_URL
    return DEFAULT_KNOWLEDGE_MCP_URL


def _env_billing_mcp_enabled() -> bool | None:
    """Return FINOPS_MCP_BILLING_ENABLED as bool if set, else None."""
    val = os.environ.get("FINOPS_MCP_BILLING_ENABLED")
    if val is None or (isinstance(val, str) and not val.strip()):
        return None
    return str(val).strip().lower() in ("1", "true", "yes")


def _env_billing_mcp_command() -> str | None:
    """Return FINOPS_MCP_BILLING_COMMAND if set, else None (use default uvx command)."""
    val = os.environ.get("FINOPS_MCP_BILLING_COMMAND")
    return val.strip() if val and isinstance(val, str) else None


def _parse_billing_mcp_command(cmd_str: str) -> tuple[str, list[str]]:
    """Parse command string into (command, args). Uses shlex.split for robustness."""
    import shlex

    parts = shlex.split(cmd_str.strip())
    if not parts:
        return ("uvx", [DEFAULT_BILLING_MCP_PACKAGE])
    return (parts[0], parts[1:])


def get_billing_mcp_enabled() -> bool:
    """
    Return whether the AWS Billing and Cost Management MCP server is enabled.
    FINOPS_MCP_BILLING_ENABLED overrides file; else agent.billing_mcp_enabled from YAML; else False.
    """
    global _BILLING_MCP_ENABLED_CACHE
    if _BILLING_MCP_ENABLED_CACHE is not None:
        return _BILLING_MCP_ENABLED_CACHE
    env_val = _env_billing_mcp_enabled()
    if env_val is not None:
        _BILLING_MCP_ENABLED_CACHE = env_val
        return env_val
    path = _get_config_path()
    agent = _load_yaml_agent(path)
    if agent is not None:
        v = agent.get("billing_mcp_enabled")
        if v is not None:
            _BILLING_MCP_ENABLED_CACHE = (
                bool(v) if isinstance(v, bool) else str(v).strip().lower() in ("1", "true", "yes")
            )
            return _BILLING_MCP_ENABLED_CACHE
    _BILLING_MCP_ENABLED_CACHE = False
    return False


def get_billing_mcp_command() -> tuple[str, list[str]]:
    """
    Return (command, args) to run the Billing/Cost MCP server (e.g. uvx).
    FINOPS_MCP_BILLING_COMMAND overrides (parsed with shlex); else agent.billing_mcp_command
    from YAML; else default uvx command with platform-specific args.
    """
    global _BILLING_MCP_COMMAND_CACHE
    if _BILLING_MCP_COMMAND_CACHE is not None:
        return _BILLING_MCP_COMMAND_CACHE
    env_val = _env_billing_mcp_command()
    if env_val:
        _BILLING_MCP_COMMAND_CACHE = _parse_billing_mcp_command(env_val)
        return _BILLING_MCP_COMMAND_CACHE
    path = _get_config_path()
    agent = _load_yaml_agent(path)
    if agent is not None:
        v = agent.get("billing_mcp_command")
        if v and isinstance(v, str) and v.strip():
            _BILLING_MCP_COMMAND_CACHE = _parse_billing_mcp_command(v)
            return _BILLING_MCP_COMMAND_CACHE
    # Default: uvx with platform-specific args (Windows uses --from and .exe)
    if sys.platform == "win32":
        _BILLING_MCP_COMMAND_CACHE = (
            "uvx",
            [
                "--from",
                DEFAULT_BILLING_MCP_PACKAGE,
                "awslabs.billing-cost-management-mcp-server.exe",
            ],
        )
    else:
        _BILLING_MCP_COMMAND_CACHE = ("uvx", [DEFAULT_BILLING_MCP_PACKAGE])
    return _BILLING_MCP_COMMAND_CACHE


def _env_documentation_mcp_enabled() -> bool | None:
    """Return parsed FINOPS_MCP_DOCUMENTATION_ENABLED if set, else None."""
    val = os.environ.get("FINOPS_MCP_DOCUMENTATION_ENABLED")
    if val is None or (isinstance(val, str) and not val.strip()):
        return None
    return str(val).strip().lower() in ("1", "true", "yes")


def _env_documentation_mcp_command() -> str | None:
    """Return FINOPS_MCP_DOCUMENTATION_COMMAND if set, else None (use default uvx command)."""
    val = os.environ.get("FINOPS_MCP_DOCUMENTATION_COMMAND")
    return val.strip() if val and isinstance(val, str) else None


def _parse_documentation_mcp_command(cmd_str: str) -> tuple[str, list[str]]:
    """Parse command string into (command, args). Uses shlex.split for robustness."""
    import shlex

    parts = shlex.split(cmd_str.strip())
    if not parts:
        return ("uvx", [DEFAULT_DOCUMENTATION_MCP_PACKAGE])
    return (parts[0], parts[1:])


def get_documentation_mcp_enabled() -> bool:
    """
    Return whether the AWS Documentation MCP server is enabled.
    FINOPS_MCP_DOCUMENTATION_ENABLED overrides file; else agent.documentation_mcp_enabled
    from YAML; else False.
    """
    global _DOCUMENTATION_MCP_ENABLED_CACHE
    if _DOCUMENTATION_MCP_ENABLED_CACHE is not None:
        return _DOCUMENTATION_MCP_ENABLED_CACHE
    env_val = _env_documentation_mcp_enabled()
    if env_val is not None:
        _DOCUMENTATION_MCP_ENABLED_CACHE = env_val
        return env_val
    path = _get_config_path()
    agent = _load_yaml_agent(path)
    if agent is not None:
        v = agent.get("documentation_mcp_enabled")
        if v is not None:
            _DOCUMENTATION_MCP_ENABLED_CACHE = (
                bool(v) if isinstance(v, bool) else str(v).strip().lower() in ("1", "true", "yes")
            )
            return _DOCUMENTATION_MCP_ENABLED_CACHE
    _DOCUMENTATION_MCP_ENABLED_CACHE = False
    return False


def get_documentation_mcp_command() -> tuple[str, list[str]]:
    """
    Return (command, args) to run the Documentation MCP server (e.g. uvx).
    FINOPS_MCP_DOCUMENTATION_COMMAND overrides (parsed with shlex); else
    agent.documentation_mcp_command from YAML; else default uvx with platform-specific args.
    """
    global _DOCUMENTATION_MCP_COMMAND_CACHE
    if _DOCUMENTATION_MCP_COMMAND_CACHE is not None:
        return _DOCUMENTATION_MCP_COMMAND_CACHE
    env_val = _env_documentation_mcp_command()
    if env_val:
        _DOCUMENTATION_MCP_COMMAND_CACHE = _parse_documentation_mcp_command(env_val)
        return _DOCUMENTATION_MCP_COMMAND_CACHE
    path = _get_config_path()
    agent = _load_yaml_agent(path)
    if agent is not None:
        v = agent.get("documentation_mcp_command")
        if v and isinstance(v, str) and v.strip():
            _DOCUMENTATION_MCP_COMMAND_CACHE = _parse_documentation_mcp_command(v)
            return _DOCUMENTATION_MCP_COMMAND_CACHE
    # Default: uvx with platform-specific args (Windows uses --from and .exe)
    if sys.platform == "win32":
        _DOCUMENTATION_MCP_COMMAND_CACHE = (
            "uvx",
            [
                "--from",
                DEFAULT_DOCUMENTATION_MCP_PACKAGE,
                "awslabs.aws-documentation-mcp-server.exe",
            ],
        )
    else:
        _DOCUMENTATION_MCP_COMMAND_CACHE = ("uvx", [DEFAULT_DOCUMENTATION_MCP_PACKAGE])
    return _DOCUMENTATION_MCP_COMMAND_CACHE


def _env_cost_explorer_mcp_enabled() -> bool | None:
    """Return FINOPS_MCP_COST_EXPLORER_ENABLED as bool if set, else None."""
    val = os.environ.get("FINOPS_MCP_COST_EXPLORER_ENABLED")
    if val is None or (isinstance(val, str) and not val.strip()):
        return None
    return str(val).strip().lower() in ("1", "true", "yes")


def _env_cost_explorer_mcp_command() -> str | None:
    """Return FINOPS_MCP_COST_EXPLORER_COMMAND if set, else None (use default uvx command)."""
    val = os.environ.get("FINOPS_MCP_COST_EXPLORER_COMMAND")
    return val.strip() if val and isinstance(val, str) else None


def _parse_cost_explorer_mcp_command(cmd_str: str) -> tuple[str, list[str]]:
    """Parse command string into (command, args). Uses shlex.split for robustness."""
    import shlex

    parts = shlex.split(cmd_str.strip())
    if not parts:
        return ("uvx", [DEFAULT_COST_EXPLORER_MCP_PACKAGE])
    return (parts[0], parts[1:])


def get_cost_explorer_mcp_enabled() -> bool:
    """
    Return whether the AWS Cost Explorer MCP server is enabled.
    FINOPS_MCP_COST_EXPLORER_ENABLED overrides file; else agent.cost_explorer_mcp_enabled
    from YAML; else False (disabled by default; BCM MCP covers Cost Explorer).
    """
    global _COST_EXPLORER_MCP_ENABLED_CACHE
    if _COST_EXPLORER_MCP_ENABLED_CACHE is not None:
        return _COST_EXPLORER_MCP_ENABLED_CACHE
    env_val = _env_cost_explorer_mcp_enabled()
    if env_val is not None:
        _COST_EXPLORER_MCP_ENABLED_CACHE = env_val
        return env_val
    path = _get_config_path()
    agent = _load_yaml_agent(path)
    if agent is not None:
        v = agent.get("cost_explorer_mcp_enabled")
        if v is not None:
            _COST_EXPLORER_MCP_ENABLED_CACHE = (
                bool(v) if isinstance(v, bool) else str(v).strip().lower() in ("1", "true", "yes")
            )
            return _COST_EXPLORER_MCP_ENABLED_CACHE
    _COST_EXPLORER_MCP_ENABLED_CACHE = False
    return False


def get_cost_explorer_mcp_command() -> tuple[str, list[str]]:
    """
    Return (command, args) to run the Cost Explorer MCP server (e.g. uvx).
    FINOPS_MCP_COST_EXPLORER_COMMAND overrides (parsed with shlex); else
    agent.cost_explorer_mcp_command from YAML; else default uvx with platform-specific args.
    """
    global _COST_EXPLORER_MCP_COMMAND_CACHE
    if _COST_EXPLORER_MCP_COMMAND_CACHE is not None:
        return _COST_EXPLORER_MCP_COMMAND_CACHE
    env_val = _env_cost_explorer_mcp_command()
    if env_val:
        _COST_EXPLORER_MCP_COMMAND_CACHE = _parse_cost_explorer_mcp_command(env_val)
        return _COST_EXPLORER_MCP_COMMAND_CACHE
    path = _get_config_path()
    agent = _load_yaml_agent(path)
    if agent is not None:
        v = agent.get("cost_explorer_mcp_command")
        if v and isinstance(v, str) and v.strip():
            _COST_EXPLORER_MCP_COMMAND_CACHE = _parse_cost_explorer_mcp_command(v)
            return _COST_EXPLORER_MCP_COMMAND_CACHE
    # Default: uvx with platform-specific args (Windows uses --from and .exe)
    if sys.platform == "win32":
        _COST_EXPLORER_MCP_COMMAND_CACHE = (
            "uvx",
            [
                "--from",
                DEFAULT_COST_EXPLORER_MCP_PACKAGE,
                "awslabs.cost-explorer-mcp-server.exe",
            ],
        )
    else:
        _COST_EXPLORER_MCP_COMMAND_CACHE = ("uvx", [DEFAULT_COST_EXPLORER_MCP_PACKAGE])
    return _COST_EXPLORER_MCP_COMMAND_CACHE


def _env_pricing_mcp_enabled() -> bool | None:
    """Return FINOPS_MCP_PRICING_ENABLED as bool if set, else None."""
    val = os.environ.get("FINOPS_MCP_PRICING_ENABLED")
    if val is None or (isinstance(val, str) and not val.strip()):
        return None
    return str(val).strip().lower() in ("1", "true", "yes")


def _env_pricing_mcp_command() -> str | None:
    """Return FINOPS_MCP_PRICING_COMMAND if set, else None (use default uvx command)."""
    val = os.environ.get("FINOPS_MCP_PRICING_COMMAND")
    return val.strip() if val and isinstance(val, str) else None


def _parse_pricing_mcp_command(cmd_str: str) -> tuple[str, list[str]]:
    """Parse command string into (command, args). Uses shlex.split for robustness."""
    import shlex

    parts = shlex.split(cmd_str.strip())
    if not parts:
        return ("uvx", [DEFAULT_PRICING_MCP_PACKAGE])
    return (parts[0], parts[1:])


def get_pricing_mcp_enabled() -> bool:
    """
    Return whether the AWS Pricing MCP server is enabled.
    FINOPS_MCP_PRICING_ENABLED overrides file; else agent.pricing_mcp_enabled
    from YAML; else False (disabled by default).
    """
    global _PRICING_MCP_ENABLED_CACHE
    if _PRICING_MCP_ENABLED_CACHE is not None:
        return _PRICING_MCP_ENABLED_CACHE
    env_val = _env_pricing_mcp_enabled()
    if env_val is not None:
        _PRICING_MCP_ENABLED_CACHE = env_val
        return env_val
    path = _get_config_path()
    agent = _load_yaml_agent(path)
    if agent is not None:
        v = agent.get("pricing_mcp_enabled")
        if v is not None:
            _PRICING_MCP_ENABLED_CACHE = (
                bool(v) if isinstance(v, bool) else str(v).strip().lower() in ("1", "true", "yes")
            )
            return _PRICING_MCP_ENABLED_CACHE
    _PRICING_MCP_ENABLED_CACHE = False
    return False


def get_pricing_mcp_command() -> tuple[str, list[str]]:
    """
    Return (command, args) to run the Pricing MCP server (e.g. uvx).
    FINOPS_MCP_PRICING_COMMAND overrides (parsed with shlex); else
    agent.pricing_mcp_command from YAML; else default uvx with platform-specific args.
    """
    global _PRICING_MCP_COMMAND_CACHE
    if _PRICING_MCP_COMMAND_CACHE is not None:
        return _PRICING_MCP_COMMAND_CACHE
    env_val = _env_pricing_mcp_command()
    if env_val:
        _PRICING_MCP_COMMAND_CACHE = _parse_pricing_mcp_command(env_val)
        return _PRICING_MCP_COMMAND_CACHE
    path = _get_config_path()
    agent = _load_yaml_agent(path)
    if agent is not None:
        v = agent.get("pricing_mcp_command")
        if v and isinstance(v, str) and v.strip():
            _PRICING_MCP_COMMAND_CACHE = _parse_pricing_mcp_command(v)
            return _PRICING_MCP_COMMAND_CACHE
    # Default: uvx with platform-specific args (Windows uses --from and .exe)
    if sys.platform == "win32":
        _PRICING_MCP_COMMAND_CACHE = (
            "uvx",
            [
                "--from",
                DEFAULT_PRICING_MCP_PACKAGE,
                "awslabs.aws-pricing-mcp-server.exe",
            ],
        )
    else:
        _PRICING_MCP_COMMAND_CACHE = ("uvx", [DEFAULT_PRICING_MCP_PACKAGE])
    return _PRICING_MCP_COMMAND_CACHE


def _env_core_mcp_enabled() -> bool | None:
    """Return FINOPS_MCP_CORE_ENABLED as bool if set, else None."""
    val = os.environ.get("FINOPS_MCP_CORE_ENABLED")
    if val is None or (isinstance(val, str) and not val.strip()):
        return None
    return str(val).strip().lower() in ("1", "true", "yes")


def _env_core_mcp_command() -> str | None:
    """Return FINOPS_MCP_CORE_COMMAND if set, else None (use default uvx command)."""
    val = os.environ.get("FINOPS_MCP_CORE_COMMAND")
    return val.strip() if val and isinstance(val, str) else None


def _env_core_mcp_roles() -> list[str] | None:
    """Return FINOPS_MCP_CORE_ROLES as list of role strings if set, else None."""
    val = os.environ.get("FINOPS_MCP_CORE_ROLES")
    if val is None or (isinstance(val, str) and not val.strip()):
        return None
    return [r.strip() for r in val.split(",") if r.strip()]


def _parse_core_mcp_command(cmd_str: str) -> tuple[str, list[str]]:
    """Parse command string into (command, args). Uses shlex.split for robustness."""
    import shlex

    parts = shlex.split(cmd_str.strip())
    if not parts:
        return ("uvx", [DEFAULT_CORE_MCP_PACKAGE])
    return (parts[0], parts[1:])


def get_core_mcp_enabled() -> bool:
    """
    Return whether the AWS Core MCP Server is enabled.
    FINOPS_MCP_CORE_ENABLED overrides file; else agent.core_mcp_enabled
    from YAML; else False (disabled by default).
    """
    global _CORE_MCP_ENABLED_CACHE
    if _CORE_MCP_ENABLED_CACHE is not None:
        return _CORE_MCP_ENABLED_CACHE
    env_val = _env_core_mcp_enabled()
    if env_val is not None:
        _CORE_MCP_ENABLED_CACHE = env_val
        return env_val
    path = _get_config_path()
    agent = _load_yaml_agent(path)
    if agent is not None:
        v = agent.get("core_mcp_enabled")
        if v is not None:
            _CORE_MCP_ENABLED_CACHE = (
                bool(v) if isinstance(v, bool) else str(v).strip().lower() in ("1", "true", "yes")
            )
            return _CORE_MCP_ENABLED_CACHE
    _CORE_MCP_ENABLED_CACHE = False
    return False


def get_core_mcp_command() -> tuple[str, list[str]]:
    """
    Return (command, args) to run the Core MCP server (e.g. uvx).
    FINOPS_MCP_CORE_COMMAND overrides (parsed with shlex); else
    agent.core_mcp_command from YAML; else default uvx with platform-specific args.
    """
    global _CORE_MCP_COMMAND_CACHE
    if _CORE_MCP_COMMAND_CACHE is not None:
        return _CORE_MCP_COMMAND_CACHE
    env_val = _env_core_mcp_command()
    if env_val:
        _CORE_MCP_COMMAND_CACHE = _parse_core_mcp_command(env_val)
        return _CORE_MCP_COMMAND_CACHE
    path = _get_config_path()
    agent = _load_yaml_agent(path)
    if agent is not None:
        v = agent.get("core_mcp_command")
        if v and isinstance(v, str) and v.strip():
            _CORE_MCP_COMMAND_CACHE = _parse_core_mcp_command(v)
            return _CORE_MCP_COMMAND_CACHE
    if sys.platform == "win32":
        _CORE_MCP_COMMAND_CACHE = (
            "uv",
            [
                "tool",
                "run",
                "--from",
                DEFAULT_CORE_MCP_PACKAGE,
                "awslabs.core-mcp-server.exe",
            ],
        )
    else:
        _CORE_MCP_COMMAND_CACHE = ("uvx", [DEFAULT_CORE_MCP_PACKAGE])
    return _CORE_MCP_COMMAND_CACHE


def get_core_mcp_roles() -> list[str]:
    """
    Return the list of role names to pass to the Core MCP server (e.g. finops, aws-foundation).
    FINOPS_MCP_CORE_ROLES overrides (comma-separated); else agent.core_mcp_roles from YAML;
    else DEFAULT_CORE_MCP_ROLES.
    """
    global _CORE_MCP_ROLES_CACHE
    if _CORE_MCP_ROLES_CACHE is not None:
        return _CORE_MCP_ROLES_CACHE
    env_val = _env_core_mcp_roles()
    if env_val is not None:
        _CORE_MCP_ROLES_CACHE = env_val
        return env_val
    path = _get_config_path()
    agent = _load_yaml_agent(path)
    if agent is not None:
        raw = agent.get("core_mcp_roles")
        if isinstance(raw, list) and len(raw) > 0:
            _CORE_MCP_ROLES_CACHE = [str(x).strip() for x in raw if str(x).strip()]
            return _CORE_MCP_ROLES_CACHE
    _CORE_MCP_ROLES_CACHE = list(DEFAULT_CORE_MCP_ROLES)
    return _CORE_MCP_ROLES_CACHE


def _env_pdf_mcp_enabled() -> bool | None:
    """Return FINOPS_MCP_PDF_ENABLED as bool if set, else None."""
    val = os.environ.get("FINOPS_MCP_PDF_ENABLED")
    if val is None or (isinstance(val, str) and not val.strip()):
        return None
    return str(val).strip().lower() in ("1", "true", "yes")


def _env_pdf_mcp_command() -> str | None:
    """Return FINOPS_MCP_PDF_COMMAND if set, else None (use default uvx command)."""
    val = os.environ.get("FINOPS_MCP_PDF_COMMAND")
    return val.strip() if val and isinstance(val, str) else None


def _parse_pdf_mcp_command(cmd_str: str) -> tuple[str, list[str]]:
    """Parse command string into (command, args). Uses shlex.split for robustness."""
    import shlex

    parts = shlex.split(cmd_str.strip())
    if not parts:
        return ("uvx", [DEFAULT_PDF_MCP_PACKAGE])
    return (parts[0], parts[1:])


def get_pdf_mcp_enabled() -> bool:
    """
    Return whether the PDF MCP server (e.g. md-to-pdf-mcp) is enabled for /print.
    FINOPS_MCP_PDF_ENABLED overrides file; else agent.pdf_mcp_enabled from YAML; else True.
    """
    global _PDF_MCP_ENABLED_CACHE
    if _PDF_MCP_ENABLED_CACHE is not None:
        return _PDF_MCP_ENABLED_CACHE
    env_val = _env_pdf_mcp_enabled()
    if env_val is not None:
        _PDF_MCP_ENABLED_CACHE = env_val
        return env_val
    path = _get_config_path()
    agent = _load_yaml_agent(path)
    if agent is not None:
        v = agent.get("pdf_mcp_enabled")
        if v is not None:
            _PDF_MCP_ENABLED_CACHE = (
                bool(v) if isinstance(v, bool) else str(v).strip().lower() in ("1", "true", "yes")
            )
            return _PDF_MCP_ENABLED_CACHE
    _PDF_MCP_ENABLED_CACHE = True
    return True


def get_pdf_mcp_command() -> tuple[str, list[str]]:
    """
    Return (command, args) to run the PDF MCP server (e.g. uvx md-to-pdf-mcp).
    FINOPS_MCP_PDF_COMMAND overrides (parsed with shlex); else agent.pdf_mcp_command
    from YAML; else default uvx command.
    """
    global _PDF_MCP_COMMAND_CACHE
    if _PDF_MCP_COMMAND_CACHE is not None:
        return _PDF_MCP_COMMAND_CACHE
    env_val = _env_pdf_mcp_command()
    if env_val:
        _PDF_MCP_COMMAND_CACHE = _parse_pdf_mcp_command(env_val)
        return _PDF_MCP_COMMAND_CACHE
    path = _get_config_path()
    agent = _load_yaml_agent(path)
    if agent is not None:
        v = agent.get("pdf_mcp_command")
        if v and isinstance(v, str) and v.strip():
            _PDF_MCP_COMMAND_CACHE = _parse_pdf_mcp_command(v)
            return _PDF_MCP_COMMAND_CACHE
    _PDF_MCP_COMMAND_CACHE = ("uvx", [DEFAULT_PDF_MCP_PACKAGE])
    return _PDF_MCP_COMMAND_CACHE


def _env_excel_mcp_enabled() -> bool | None:
    """Return FINOPS_MCP_EXCEL_ENABLED as bool if set, else None."""
    val = os.environ.get("FINOPS_MCP_EXCEL_ENABLED")
    if val is None or (isinstance(val, str) and not val.strip()):
        return None
    return str(val).strip().lower() in ("1", "true", "yes")


def _env_excel_mcp_command() -> str | None:
    """Return FINOPS_MCP_EXCEL_COMMAND if set, else None (use default uvx command)."""
    val = os.environ.get("FINOPS_MCP_EXCEL_COMMAND")
    return val.strip() if val and isinstance(val, str) else None


def _parse_excel_mcp_command(cmd_str: str) -> tuple[str, list[str]]:
    """Parse command string into (command, args). Uses shlex.split for robustness."""
    import shlex

    parts = shlex.split(cmd_str.strip())
    if not parts:
        return ("uvx", [DEFAULT_EXCEL_MCP_PACKAGE, "stdio"])
    return (parts[0], parts[1:])


def get_excel_mcp_enabled() -> bool:
    """
    Return whether the Excel MCP server (e.g. excel-mcp-server) is enabled for /print.
    FINOPS_MCP_EXCEL_ENABLED overrides file; else agent.excel_mcp_enabled from YAML; else True.
    """
    global _EXCEL_MCP_ENABLED_CACHE
    if _EXCEL_MCP_ENABLED_CACHE is not None:
        return _EXCEL_MCP_ENABLED_CACHE
    env_val = _env_excel_mcp_enabled()
    if env_val is not None:
        _EXCEL_MCP_ENABLED_CACHE = env_val
        return env_val
    path = _get_config_path()
    agent = _load_yaml_agent(path)
    if agent is not None:
        v = agent.get("excel_mcp_enabled")
        if v is not None:
            _EXCEL_MCP_ENABLED_CACHE = (
                bool(v) if isinstance(v, bool) else str(v).strip().lower() in ("1", "true", "yes")
            )
            return _EXCEL_MCP_ENABLED_CACHE
    _EXCEL_MCP_ENABLED_CACHE = True
    return True


def get_excel_mcp_command() -> tuple[str, list[str]]:
    """
    Return (command, args) to run the Excel MCP server (e.g. uvx excel-mcp-server stdio).
    FINOPS_MCP_EXCEL_COMMAND overrides (parsed with shlex); else agent.excel_mcp_command
    from YAML; else default uvx with stdio.
    """
    global _EXCEL_MCP_COMMAND_CACHE
    if _EXCEL_MCP_COMMAND_CACHE is not None:
        return _EXCEL_MCP_COMMAND_CACHE
    env_val = _env_excel_mcp_command()
    if env_val:
        _EXCEL_MCP_COMMAND_CACHE = _parse_excel_mcp_command(env_val)
        return _EXCEL_MCP_COMMAND_CACHE
    path = _get_config_path()
    agent = _load_yaml_agent(path)
    if agent is not None:
        v = agent.get("excel_mcp_command")
        if v and isinstance(v, str) and v.strip():
            _EXCEL_MCP_COMMAND_CACHE = _parse_excel_mcp_command(v)
            return _EXCEL_MCP_COMMAND_CACHE
    _EXCEL_MCP_COMMAND_CACHE = ("uvx", [DEFAULT_EXCEL_MCP_PACKAGE, "stdio"])
    return _EXCEL_MCP_COMMAND_CACHE


def _env_read_only_guardrail_input_enabled() -> bool | None:
    """Return FINOPS_READ_ONLY_GUARDRAIL_INPUT_ENABLED as bool if set, else None."""
    val = os.environ.get("FINOPS_READ_ONLY_GUARDRAIL_INPUT_ENABLED")
    if val is None or (isinstance(val, str) and not val.strip()):
        return None
    return str(val).strip().lower() in ("1", "true", "yes")


def get_read_only_guardrail_input_enabled() -> bool:
    """
    Return whether the input guardrail (read-only intent check) is enabled.
    FINOPS_READ_ONLY_GUARDRAIL_INPUT_ENABLED overrides file; else
    agent.read_only_guardrail_input_enabled from YAML; else True (enabled by default).
    """
    global _READ_ONLY_GUARDRAIL_INPUT_ENABLED_CACHE
    if _READ_ONLY_GUARDRAIL_INPUT_ENABLED_CACHE is not None:
        return _READ_ONLY_GUARDRAIL_INPUT_ENABLED_CACHE
    env_val = _env_read_only_guardrail_input_enabled()
    if env_val is not None:
        _READ_ONLY_GUARDRAIL_INPUT_ENABLED_CACHE = env_val
        return env_val
    path = _get_config_path()
    agent = _load_yaml_agent(path)
    if agent is not None:
        v = agent.get("read_only_guardrail_input_enabled")
        if v is not None:
            _READ_ONLY_GUARDRAIL_INPUT_ENABLED_CACHE = (
                bool(v) if isinstance(v, bool) else str(v).strip().lower() in ("1", "true", "yes")
            )
            return _READ_ONLY_GUARDRAIL_INPUT_ENABLED_CACHE
    _READ_ONLY_GUARDRAIL_INPUT_ENABLED_CACHE = True
    return True


def _env_verbose_tool_debug() -> bool | None:
    """Return FINOPS_VERBOSE_TOOL_DEBUG as bool if set, else None."""
    val = os.environ.get("FINOPS_VERBOSE_TOOL_DEBUG")
    if val is None or (isinstance(val, str) and not val.strip()):
        return None
    return str(val).strip().lower() in ("1", "true", "yes")


def get_verbose_tool_debug() -> bool:
    """
    Return whether to show verbose tool/MCP debug output (inputs and responses).
    FINOPS_VERBOSE_TOOL_DEBUG overrides file; else agent.verbose_tool_debug from YAML;
    else True (enabled by default) to help debug permission and tool errors.
    """
    global _VERBOSE_TOOL_DEBUG_CACHE
    if _VERBOSE_TOOL_DEBUG_CACHE is not None:
        return _VERBOSE_TOOL_DEBUG_CACHE
    env_val = _env_verbose_tool_debug()
    if env_val is not None:
        _VERBOSE_TOOL_DEBUG_CACHE = env_val
        return env_val
    path = _get_config_path()
    agent = _load_yaml_agent(path)
    if agent is not None:
        v = agent.get("verbose_tool_debug")
        if v is not None:
            _VERBOSE_TOOL_DEBUG_CACHE = (
                bool(v) if isinstance(v, bool) else str(v).strip().lower() in ("1", "true", "yes")
            )
            return _VERBOSE_TOOL_DEBUG_CACHE
    _VERBOSE_TOOL_DEBUG_CACHE = True
    return True


def _env_agent_warm_on_startup() -> bool | None:
    """Return FINOPS_AGENT_WARM_ON_STARTUP as bool if set and non-empty, else None.
    Truthy: 1, true, yes; Falsy: 0, false, no. Empty string means unset (use YAML)."""
    val = os.environ.get("FINOPS_AGENT_WARM_ON_STARTUP")
    if val is None or (isinstance(val, str) and not val.strip()):
        return None
    lower = str(val).strip().lower()
    if lower in ("1", "true", "yes"):
        return True
    if lower in ("0", "false", "no"):
        return False
    return None


def get_agent_warm_on_startup() -> bool:
    """
    Return whether to warm up the chat agent at API startup.
    FINOPS_AGENT_WARM_ON_STARTUP overrides file; else agent.warm_on_startup from YAML;
    else True (enabled by default for faster first request).
    """
    global _AGENT_WARM_ON_STARTUP_CACHE
    if _AGENT_WARM_ON_STARTUP_CACHE is not None:
        return _AGENT_WARM_ON_STARTUP_CACHE
    env_val = _env_agent_warm_on_startup()
    if env_val is not None:
        _AGENT_WARM_ON_STARTUP_CACHE = env_val
        return env_val
    path = _get_config_path()
    agent = _load_yaml_agent(path)
    if agent is not None:
        v = agent.get("warm_on_startup")
        if v is not None:
            _AGENT_WARM_ON_STARTUP_CACHE = (
                bool(v) if isinstance(v, bool) else str(v).strip().lower() in ("1", "true", "yes")
            )
            return _AGENT_WARM_ON_STARTUP_CACHE
    _AGENT_WARM_ON_STARTUP_CACHE = True
    return True


def get_read_only_allowed_tools() -> frozenset[str]:
    """
    Return the read-only tool allow-list for the guardrail.
    When agent.read_only_allowed_tools is set to a non-empty list in YAML, that list is used;
    otherwise the application default (built-in + known MCP read-only tools) is used.
    """
    from finops_buddy.agent.guardrails import get_default_allowed_tools

    global _READ_ONLY_ALLOWED_TOOLS_CACHE
    if _READ_ONLY_ALLOWED_TOOLS_CACHE is not None:
        return _READ_ONLY_ALLOWED_TOOLS_CACHE
    path = _get_config_path()
    agent = _load_yaml_agent(path)
    if agent is not None:
        raw = agent.get("read_only_allowed_tools")
        if isinstance(raw, list) and len(raw) > 0:
            _READ_ONLY_ALLOWED_TOOLS_CACHE = frozenset(
                str(x).strip() for x in raw if str(x).strip()
            )
            return _READ_ONLY_ALLOWED_TOOLS_CACHE
    _READ_ONLY_ALLOWED_TOOLS_CACHE = get_default_allowed_tools()
    return _READ_ONLY_ALLOWED_TOOLS_CACHE


def reset_settings_cache() -> None:
    """Clear cached settings (for tests)."""
    global _EXCLUDED_PROFILES_CACHE, _INCLUDED_ONLY_PROFILES_CACHE, _AGENT_MODEL_ID_CACHE
    global _AGENT_TEMPERATURE_CACHE, _AGENT_MAX_COMPLETION_TOKENS_CACHE
    global _KNOWLEDGE_MCP_ENABLED_CACHE, _KNOWLEDGE_MCP_URL_CACHE
    global _BILLING_MCP_ENABLED_CACHE, _BILLING_MCP_COMMAND_CACHE
    global _DOCUMENTATION_MCP_ENABLED_CACHE, _DOCUMENTATION_MCP_COMMAND_CACHE
    global _COST_EXPLORER_MCP_ENABLED_CACHE, _COST_EXPLORER_MCP_COMMAND_CACHE
    global _PRICING_MCP_ENABLED_CACHE, _PRICING_MCP_COMMAND_CACHE
    global _CORE_MCP_ENABLED_CACHE, _CORE_MCP_COMMAND_CACHE, _CORE_MCP_ROLES_CACHE
    global _PDF_MCP_ENABLED_CACHE, _PDF_MCP_COMMAND_CACHE
    global _EXCEL_MCP_ENABLED_CACHE, _EXCEL_MCP_COMMAND_CACHE
    global _READ_ONLY_GUARDRAIL_INPUT_ENABLED_CACHE, _VERBOSE_TOOL_DEBUG_CACHE
    global _READ_ONLY_ALLOWED_TOOLS_CACHE, _AGENT_WARM_ON_STARTUP_CACHE
    global _SERVER_HOST_CACHE, _SERVER_PORT_CACHE, _CORS_ORIGINS_CACHE
    global _DEMO_ACCOUNT_MAPPING_CACHE, _DEMO_ACCOUNT_ID_MAPPING_CACHE
    _EXCLUDED_PROFILES_CACHE = None
    _INCLUDED_ONLY_PROFILES_CACHE = None
    _AGENT_MODEL_ID_CACHE = None
    _AGENT_TEMPERATURE_CACHE = None
    _AGENT_MAX_COMPLETION_TOKENS_CACHE = None
    _KNOWLEDGE_MCP_ENABLED_CACHE = None
    _KNOWLEDGE_MCP_URL_CACHE = None
    _BILLING_MCP_ENABLED_CACHE = None
    _BILLING_MCP_COMMAND_CACHE = None
    _DOCUMENTATION_MCP_ENABLED_CACHE = None
    _DOCUMENTATION_MCP_COMMAND_CACHE = None
    _COST_EXPLORER_MCP_ENABLED_CACHE = None
    _COST_EXPLORER_MCP_COMMAND_CACHE = None
    _PRICING_MCP_ENABLED_CACHE = None
    _PRICING_MCP_COMMAND_CACHE = None
    _CORE_MCP_ENABLED_CACHE = None
    _CORE_MCP_COMMAND_CACHE = None
    _CORE_MCP_ROLES_CACHE = None
    _PDF_MCP_ENABLED_CACHE = None
    _PDF_MCP_COMMAND_CACHE = None
    _EXCEL_MCP_ENABLED_CACHE = None
    _EXCEL_MCP_COMMAND_CACHE = None
    _READ_ONLY_GUARDRAIL_INPUT_ENABLED_CACHE = None
    _VERBOSE_TOOL_DEBUG_CACHE = None
    _READ_ONLY_ALLOWED_TOOLS_CACHE = None
    _AGENT_WARM_ON_STARTUP_CACHE = None
    _SERVER_HOST_CACHE = None
    _SERVER_PORT_CACHE = None
    _CORS_ORIGINS_CACHE = None
    _DEMO_ACCOUNT_MAPPING_CACHE = None
    _DEMO_ACCOUNT_ID_MAPPING_CACHE = None
