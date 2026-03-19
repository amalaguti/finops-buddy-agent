"""Tests for app settings (YAML + env resolution) and dotenv precedence."""

import os

import pytest
from dotenv import load_dotenv

from finops_buddy.settings import (
    DEFAULT_BILLING_MCP_PACKAGE,
    DEFAULT_CORE_MCP_PACKAGE,
    DEFAULT_CORE_MCP_ROLES,
    DEFAULT_COST_EXPLORER_MCP_PACKAGE,
    DEFAULT_DOCUMENTATION_MCP_PACKAGE,
    DEFAULT_KNOWLEDGE_MCP_URL,
    DEFAULT_PRICING_MCP_PACKAGE,
    _default_config_path,
    _get_config_path,
    get_agent_model_id,
    get_agent_warm_on_startup,
    get_billing_mcp_command,
    get_billing_mcp_enabled,
    get_core_mcp_command,
    get_core_mcp_enabled,
    get_core_mcp_roles,
    get_cost_explorer_mcp_command,
    get_cost_explorer_mcp_enabled,
    get_documentation_mcp_command,
    get_documentation_mcp_enabled,
    get_excluded_profiles,
    get_included_only_profiles,
    get_knowledge_mcp_enabled,
    get_knowledge_mcp_url,
    get_pricing_mcp_command,
    get_pricing_mcp_enabled,
    get_read_only_allowed_tools,
    get_read_only_guardrail_input_enabled,
    get_verbose_tool_debug,
    reset_settings_cache,
)


@pytest.fixture(autouse=True)
def _reset_cache():
    """Reset settings cache and env so tests don't leak state."""
    reset_settings_cache()
    yield
    reset_settings_cache()
    for key in (
        "FINOPS_CONFIG_FILE",
        "FINOPS_EXCLUDED_PROFILES",
        "FINOPS_INCLUDED_ONLY_PROFILES",
        "FINOPS_AGENT_MODEL_ID",
        "FINOPS_OPENAI_API_KEY",
        "FINOPS_KNOWLEDGE_MCP_ENABLED",
        "FINOPS_KNOWLEDGE_MCP_URL",
        "FINOPS_MCP_BILLING_ENABLED",
        "FINOPS_MCP_BILLING_COMMAND",
        "FINOPS_MCP_DOCUMENTATION_ENABLED",
        "FINOPS_MCP_DOCUMENTATION_COMMAND",
        "FINOPS_MCP_COST_EXPLORER_ENABLED",
        "FINOPS_MCP_COST_EXPLORER_COMMAND",
        "FINOPS_MCP_PRICING_ENABLED",
        "FINOPS_MCP_PRICING_COMMAND",
        "FINOPS_MCP_CORE_ENABLED",
        "FINOPS_MCP_CORE_COMMAND",
        "FINOPS_MCP_CORE_ROLES",
        "XDG_CONFIG_HOME",
    ):
        os.environ.pop(key, None)


def test_default_config_path_uses_xdg_when_set(monkeypatch):
    """Default path is XDG_CONFIG_HOME/finops-agent/settings.yaml when set."""
    monkeypatch.setenv("XDG_CONFIG_HOME", "/xdg")
    path = _default_config_path()
    assert "finops-agent" in str(path)
    assert path.name == "settings.yaml"
    assert path.parent.name == "finops-agent"


def test_default_config_path_uses_home_config_when_xdg_unset(monkeypatch):
    """Default path is ~/.config/finops-agent/settings.yaml when XDG_CONFIG_HOME unset."""
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    path = _default_config_path()
    assert ".config" in str(path)
    assert "finops-agent" in str(path)
    assert path.name == "settings.yaml"


def test_get_config_path_uses_finops_config_file_when_set(monkeypatch):
    """When FINOPS_CONFIG_FILE is set, that path is used."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", "/custom/settings.yaml")
    assert _get_config_path().as_posix() == "/custom/settings.yaml"


def test_get_config_path_uses_default_when_finops_config_file_unset(monkeypatch):
    """When FINOPS_CONFIG_FILE is unset, default XDG path is used."""
    monkeypatch.delenv("FINOPS_CONFIG_FILE", raising=False)
    path = _get_config_path()
    assert "finops-agent" in str(path)
    assert path.name == "settings.yaml"


def test_get_excluded_profiles_reads_from_default_xdg_path(tmp_path, monkeypatch):
    """When FINOPS_CONFIG_FILE is unset, settings are read from XDG default path."""
    monkeypatch.delenv("FINOPS_CONFIG_FILE", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv("FINOPS_EXCLUDED_PROFILES", raising=False)
    config_dir = tmp_path / "finops-agent"
    config_dir.mkdir()
    (config_dir / "settings.yaml").write_text("excluded_profiles:\n  - default-path")
    assert get_excluded_profiles() == ["default-path"]


def test_get_excluded_profiles_missing_yaml_returns_empty(tmp_path, monkeypatch):
    """When settings file is missing, excluded list is empty."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "nonexistent.yaml"))
    monkeypatch.delenv("FINOPS_EXCLUDED_PROFILES", raising=False)
    assert get_excluded_profiles() == []


def test_get_excluded_profiles_invalid_yaml_returns_empty(tmp_path, monkeypatch):
    """When YAML is invalid, excluded list is empty (no crash)."""
    bad = tmp_path / "settings.yaml"
    bad.write_text("not: valid: yaml: [")
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(bad))
    monkeypatch.delenv("FINOPS_EXCLUDED_PROFILES", raising=False)
    assert get_excluded_profiles() == []


def test_get_excluded_profiles_yaml_only_when_env_unset(tmp_path, monkeypatch):
    """When YAML has excluded_profiles and env is unset, YAML list is used."""
    cfg = tmp_path / "settings.yaml"
    cfg.write_text("excluded_profiles:\n  - personal\n  - test")
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(cfg))
    monkeypatch.delenv("FINOPS_EXCLUDED_PROFILES", raising=False)
    assert get_excluded_profiles() == ["personal", "test"]


def test_get_excluded_profiles_env_overrides_yaml(tmp_path, monkeypatch):
    """When FINOPS_EXCLUDED_PROFILES is set, env list replaces YAML."""
    cfg = tmp_path / "settings.yaml"
    cfg.write_text("excluded_profiles:\n  - from_yaml")
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(cfg))
    monkeypatch.setenv("FINOPS_EXCLUDED_PROFILES", "env1,env2")
    assert get_excluded_profiles() == ["env1", "env2"]


def test_get_excluded_profiles_no_exclusions_when_neither_set(tmp_path, monkeypatch):
    """When no file and no env, excluded list is empty."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "missing.yaml"))
    monkeypatch.delenv("FINOPS_EXCLUDED_PROFILES", raising=False)
    assert get_excluded_profiles() == []


def test_get_excluded_profiles_cached():
    """Repeated calls return same cached list (no re-read)."""
    os.environ["FINOPS_EXCLUDED_PROFILES"] = "a,b"
    first = get_excluded_profiles()
    second = get_excluded_profiles()
    assert first == second == ["a", "b"]


def test_dotenv_env_local_overrides_env(tmp_path, monkeypatch):
    """When both .env and .env.local define same variable, .env.local wins."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("FINOPS_EXCLUDED_PROFILES=from_env")
    (tmp_path / ".env.local").write_text("FINOPS_EXCLUDED_PROFILES=from_env_local")
    monkeypatch.delenv("FINOPS_EXCLUDED_PROFILES", raising=False)
    load_dotenv()
    load_dotenv(".env.local", override=True)
    assert os.environ.get("FINOPS_EXCLUDED_PROFILES") == "from_env_local"


def test_get_included_only_profiles_yaml_only_when_env_unset(tmp_path, monkeypatch):
    """When YAML has included_only_profiles and env is unset, YAML list is used."""
    cfg = tmp_path / "settings.yaml"
    cfg.write_text("included_only_profiles:\n  - prod\n  - staging")
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(cfg))
    monkeypatch.delenv("FINOPS_INCLUDED_ONLY_PROFILES", raising=False)
    assert get_included_only_profiles() == ["prod", "staging"]


def test_get_included_only_profiles_env_overrides_yaml(tmp_path, monkeypatch):
    """When FINOPS_INCLUDED_ONLY_PROFILES is set, env list replaces YAML."""
    cfg = tmp_path / "settings.yaml"
    cfg.write_text("included_only_profiles:\n  - from_yaml")
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(cfg))
    monkeypatch.setenv("FINOPS_INCLUDED_ONLY_PROFILES", "env1,env2")
    assert get_included_only_profiles() == ["env1", "env2"]


def test_get_included_only_profiles_empty_when_unset(tmp_path, monkeypatch):
    """When no file and no env, included_only list is empty."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "missing.yaml"))
    monkeypatch.delenv("FINOPS_INCLUDED_ONLY_PROFILES", raising=False)
    assert get_included_only_profiles() == []


def test_get_included_only_profiles_cached():
    """Repeated calls return same cached list (no re-read)."""
    os.environ["FINOPS_INCLUDED_ONLY_PROFILES"] = "x,y"
    first = get_included_only_profiles()
    second = get_included_only_profiles()
    assert first == second == ["x", "y"]


def test_get_read_only_allowed_tools_default_when_key_absent(tmp_path, monkeypatch):
    """When settings file has no agent.read_only_allowed_tools, resolved list is app default."""
    from finops_buddy.agent.guardrails import get_default_allowed_tools

    cfg = tmp_path / "settings.yaml"
    cfg.write_text("excluded_profiles: []\n")
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(cfg))
    result = get_read_only_allowed_tools()
    assert result == get_default_allowed_tools()


def test_get_read_only_allowed_tools_default_when_empty_list(tmp_path, monkeypatch):
    """When agent.read_only_allowed_tools is [], resolved list is app default."""
    from finops_buddy.agent.guardrails import get_default_allowed_tools

    cfg = tmp_path / "settings.yaml"
    cfg.write_text("agent:\n  read_only_allowed_tools: []\n")
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(cfg))
    result = get_read_only_allowed_tools()
    assert result == get_default_allowed_tools()


def test_get_read_only_allowed_tools_custom_when_non_empty_list(tmp_path, monkeypatch):
    """When agent.read_only_allowed_tools is non-empty list, that set is used."""
    cfg = tmp_path / "settings.yaml"
    cfg.write_text(
        "agent:\n  read_only_allowed_tools:\n    - get_current_date\n"
        "    - current_period_costs\n    - session-sql\n"
    )
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(cfg))
    result = get_read_only_allowed_tools()
    assert result == frozenset({"get_current_date", "current_period_costs", "session-sql"})


def test_reset_settings_cache_clears_included_cache(monkeypatch):
    """reset_settings_cache() clears included_only cache so next call re-reads."""
    monkeypatch.setenv("FINOPS_INCLUDED_ONLY_PROFILES", "first")
    get_included_only_profiles()
    reset_settings_cache()
    monkeypatch.setenv("FINOPS_INCLUDED_ONLY_PROFILES", "second")
    assert get_included_only_profiles() == ["second"]


def test_dotenv_missing_files_do_not_error(tmp_path, monkeypatch):
    """Loading when .env and .env.local are missing does not raise."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("FINOPS_EXCLUDED_PROFILES", raising=False)
    load_dotenv()
    load_dotenv(".env.local", override=True)
    # No exception; env may or may not have the var


def test_agent_runs_with_default_model_when_no_config_set(monkeypatch):
    """When no agent model is configured, get_agent_model_id returns None (Strands default)."""
    monkeypatch.delenv("FINOPS_AGENT_MODEL_ID", raising=False)
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(__file__) + ".nonexistent.yaml")
    assert get_agent_model_id() is None


def test_agent_respects_model_override_from_environment(monkeypatch):
    """When FINOPS_AGENT_MODEL_ID is set, get_agent_model_id returns that value."""
    monkeypatch.setenv("FINOPS_AGENT_MODEL_ID", "anthropic.claude-sonnet-4-20250514-v1:0")
    assert get_agent_model_id() == "anthropic.claude-sonnet-4-20250514-v1:0"


def test_get_knowledge_mcp_enabled_default_true(tmp_path, monkeypatch):
    """When no config and no env, get_knowledge_mcp_enabled returns True."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "missing.yaml"))
    monkeypatch.delenv("FINOPS_KNOWLEDGE_MCP_ENABLED", raising=False)
    assert get_knowledge_mcp_enabled() is True


def test_get_knowledge_mcp_enabled_false_when_env_set(monkeypatch):
    """When FINOPS_KNOWLEDGE_MCP_ENABLED is false, get_knowledge_mcp_enabled returns False."""
    monkeypatch.setenv("FINOPS_KNOWLEDGE_MCP_ENABLED", "false")
    assert get_knowledge_mcp_enabled() is False


def test_get_knowledge_mcp_url_default(tmp_path, monkeypatch):
    """When no config and no env, get_knowledge_mcp_url returns default URL."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "missing.yaml"))
    monkeypatch.delenv("FINOPS_KNOWLEDGE_MCP_URL", raising=False)
    assert get_knowledge_mcp_url() == DEFAULT_KNOWLEDGE_MCP_URL


def test_get_knowledge_mcp_url_override_from_env(monkeypatch):
    """When FINOPS_KNOWLEDGE_MCP_URL is set, get_knowledge_mcp_url returns it."""
    monkeypatch.setenv("FINOPS_KNOWLEDGE_MCP_URL", "https://custom-mcp.example.com")
    assert get_knowledge_mcp_url() == "https://custom-mcp.example.com"


def test_reset_settings_cache_clears_knowledge_mcp_cache(monkeypatch):
    """reset_settings_cache() clears knowledge MCP caches so next call re-reads."""
    monkeypatch.setenv("FINOPS_KNOWLEDGE_MCP_ENABLED", "true")
    get_knowledge_mcp_enabled()
    reset_settings_cache()
    monkeypatch.setenv("FINOPS_KNOWLEDGE_MCP_ENABLED", "false")
    assert get_knowledge_mcp_enabled() is False


def test_get_billing_mcp_enabled_default_false(tmp_path, monkeypatch):
    """When no config and no env, get_billing_mcp_enabled returns False."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "missing.yaml"))
    monkeypatch.delenv("FINOPS_MCP_BILLING_ENABLED", raising=False)
    assert get_billing_mcp_enabled() is False


def test_get_billing_mcp_enabled_true_when_env_set(monkeypatch):
    """When FINOPS_MCP_BILLING_ENABLED is true, get_billing_mcp_enabled returns True."""
    monkeypatch.setenv("FINOPS_MCP_BILLING_ENABLED", "true")
    assert get_billing_mcp_enabled() is True


def test_get_billing_mcp_enabled_from_yaml(tmp_path, monkeypatch):
    """When agent.billing_mcp_enabled is true in YAML, get_billing_mcp_enabled returns True."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "settings.yaml"))
    monkeypatch.delenv("FINOPS_MCP_BILLING_ENABLED", raising=False)
    (tmp_path / "settings.yaml").write_text("agent:\n  billing_mcp_enabled: true\n")
    assert get_billing_mcp_enabled() is True


def test_get_billing_mcp_command_default_returns_uvx_and_args(tmp_path, monkeypatch):
    """When no override, get_billing_mcp_command returns (uvx, [package]) or Windows variant."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "missing.yaml"))
    monkeypatch.delenv("FINOPS_MCP_BILLING_COMMAND", raising=False)
    cmd, args = get_billing_mcp_command()
    assert cmd == "uvx"
    assert DEFAULT_BILLING_MCP_PACKAGE in args


def test_get_billing_mcp_command_override_from_env(monkeypatch):
    """When FINOPS_MCP_BILLING_COMMAND is set, get_billing_mcp_command returns parsed command."""
    monkeypatch.setenv(
        "FINOPS_MCP_BILLING_COMMAND",
        "uvx awslabs.billing-cost-management-mcp-server@latest",
    )
    cmd, args = get_billing_mcp_command()
    assert cmd == "uvx"
    assert "awslabs.billing-cost-management-mcp-server@latest" in args


def test_reset_settings_cache_clears_billing_mcp_cache(monkeypatch):
    """reset_settings_cache() clears billing MCP caches so next call re-reads."""
    monkeypatch.setenv("FINOPS_MCP_BILLING_ENABLED", "true")
    get_billing_mcp_enabled()
    reset_settings_cache()
    monkeypatch.setenv("FINOPS_MCP_BILLING_ENABLED", "false")
    assert get_billing_mcp_enabled() is False


def test_get_documentation_mcp_enabled_default_false(tmp_path, monkeypatch):
    """When no config and no env, get_documentation_mcp_enabled returns False."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "missing.yaml"))
    monkeypatch.delenv("FINOPS_MCP_DOCUMENTATION_ENABLED", raising=False)
    assert get_documentation_mcp_enabled() is False


def test_get_documentation_mcp_enabled_true_when_env_set(monkeypatch):
    """When FINOPS_MCP_DOCUMENTATION_ENABLED is true, get_documentation_mcp_enabled returns True."""
    monkeypatch.setenv("FINOPS_MCP_DOCUMENTATION_ENABLED", "true")
    assert get_documentation_mcp_enabled() is True


def test_get_documentation_mcp_enabled_from_yaml(tmp_path, monkeypatch):
    """When agent.documentation_mcp_enabled is true in YAML, getter returns True."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "settings.yaml"))
    monkeypatch.delenv("FINOPS_MCP_DOCUMENTATION_ENABLED", raising=False)
    (tmp_path / "settings.yaml").write_text("agent:\n  documentation_mcp_enabled: true\n")
    assert get_documentation_mcp_enabled() is True


def test_get_documentation_mcp_command_default_returns_uvx_and_args(tmp_path, monkeypatch):
    """When no override, get_documentation_mcp_command returns (uvx, [package]) or Windows."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "missing.yaml"))
    monkeypatch.delenv("FINOPS_MCP_DOCUMENTATION_COMMAND", raising=False)
    cmd, args = get_documentation_mcp_command()
    assert cmd == "uvx"
    assert DEFAULT_DOCUMENTATION_MCP_PACKAGE in args


def test_get_documentation_mcp_command_override_from_env(monkeypatch):
    """When FINOPS_MCP_DOCUMENTATION_COMMAND is set, getter returns parsed command."""
    monkeypatch.setenv(
        "FINOPS_MCP_DOCUMENTATION_COMMAND",
        "uvx awslabs.aws-documentation-mcp-server@latest",
    )
    cmd, args = get_documentation_mcp_command()
    assert cmd == "uvx"
    assert "awslabs.aws-documentation-mcp-server@latest" in args


def test_reset_settings_cache_clears_documentation_mcp_cache(monkeypatch):
    """reset_settings_cache() clears documentation MCP caches so next call re-reads."""
    monkeypatch.setenv("FINOPS_MCP_DOCUMENTATION_ENABLED", "true")
    get_documentation_mcp_enabled()
    reset_settings_cache()
    monkeypatch.setenv("FINOPS_MCP_DOCUMENTATION_ENABLED", "false")
    assert get_documentation_mcp_enabled() is False


# --- Cost Explorer MCP (disabled by default) ---


def test_get_cost_explorer_mcp_enabled_default_false(tmp_path, monkeypatch):
    """When no config and no env, get_cost_explorer_mcp_enabled returns False."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "missing.yaml"))
    monkeypatch.delenv("FINOPS_MCP_COST_EXPLORER_ENABLED", raising=False)
    assert get_cost_explorer_mcp_enabled() is False


def test_get_cost_explorer_mcp_enabled_true_when_env_set(monkeypatch):
    """When FINOPS_MCP_COST_EXPLORER_ENABLED is true, getter returns True."""
    monkeypatch.setenv("FINOPS_MCP_COST_EXPLORER_ENABLED", "true")
    assert get_cost_explorer_mcp_enabled() is True


def test_get_cost_explorer_mcp_enabled_from_yaml(tmp_path, monkeypatch):
    """When agent.cost_explorer_mcp_enabled is true in YAML, getter returns True."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "settings.yaml"))
    monkeypatch.delenv("FINOPS_MCP_COST_EXPLORER_ENABLED", raising=False)
    (tmp_path / "settings.yaml").write_text("agent:\n  cost_explorer_mcp_enabled: true\n")
    assert get_cost_explorer_mcp_enabled() is True


def test_get_cost_explorer_mcp_enabled_env_overrides_yaml(tmp_path, monkeypatch):
    """When YAML has cost_explorer_mcp_enabled true and env false, getter returns False."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "settings.yaml"))
    (tmp_path / "settings.yaml").write_text("agent:\n  cost_explorer_mcp_enabled: true\n")
    monkeypatch.setenv("FINOPS_MCP_COST_EXPLORER_ENABLED", "false")
    assert get_cost_explorer_mcp_enabled() is False


def test_get_cost_explorer_mcp_command_default_returns_uvx_and_args(tmp_path, monkeypatch):
    """When no override, get_cost_explorer_mcp_command returns (uvx, [package]) or Windows."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "missing.yaml"))
    monkeypatch.delenv("FINOPS_MCP_COST_EXPLORER_COMMAND", raising=False)
    cmd, args = get_cost_explorer_mcp_command()
    assert cmd == "uvx"
    assert DEFAULT_COST_EXPLORER_MCP_PACKAGE in args


def test_get_cost_explorer_mcp_command_override_from_env(monkeypatch):
    """When FINOPS_MCP_COST_EXPLORER_COMMAND is set, getter returns parsed command."""
    monkeypatch.setenv(
        "FINOPS_MCP_COST_EXPLORER_COMMAND",
        "uvx awslabs.cost-explorer-mcp-server@latest",
    )
    cmd, args = get_cost_explorer_mcp_command()
    assert cmd == "uvx"
    assert "awslabs.cost-explorer-mcp-server@latest" in args


def test_reset_settings_cache_clears_cost_explorer_mcp_cache(monkeypatch):
    """reset_settings_cache() clears Cost Explorer MCP caches so next call re-reads."""
    monkeypatch.setenv("FINOPS_MCP_COST_EXPLORER_ENABLED", "true")
    get_cost_explorer_mcp_enabled()
    reset_settings_cache()
    monkeypatch.setenv("FINOPS_MCP_COST_EXPLORER_ENABLED", "false")
    assert get_cost_explorer_mcp_enabled() is False


# --- Pricing MCP (disabled by default) ---


def test_get_pricing_mcp_enabled_default_false(tmp_path, monkeypatch):
    """When no config and no env, get_pricing_mcp_enabled returns False."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "missing.yaml"))
    monkeypatch.delenv("FINOPS_MCP_PRICING_ENABLED", raising=False)
    assert get_pricing_mcp_enabled() is False


def test_get_pricing_mcp_enabled_true_when_env_set(monkeypatch):
    """When FINOPS_MCP_PRICING_ENABLED is true, getter returns True."""
    monkeypatch.setenv("FINOPS_MCP_PRICING_ENABLED", "true")
    assert get_pricing_mcp_enabled() is True


def test_get_pricing_mcp_enabled_from_yaml(tmp_path, monkeypatch):
    """When agent.pricing_mcp_enabled is true in YAML, getter returns True."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "settings.yaml"))
    monkeypatch.delenv("FINOPS_MCP_PRICING_ENABLED", raising=False)
    (tmp_path / "settings.yaml").write_text("agent:\n  pricing_mcp_enabled: true\n")
    assert get_pricing_mcp_enabled() is True


def test_get_pricing_mcp_enabled_env_overrides_yaml(tmp_path, monkeypatch):
    """When YAML has pricing_mcp_enabled true and env false, getter returns False."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "settings.yaml"))
    (tmp_path / "settings.yaml").write_text("agent:\n  pricing_mcp_enabled: true\n")
    monkeypatch.setenv("FINOPS_MCP_PRICING_ENABLED", "false")
    assert get_pricing_mcp_enabled() is False


def test_get_pricing_mcp_command_default_returns_uvx_and_args(tmp_path, monkeypatch):
    """When no override, get_pricing_mcp_command returns (uvx, [package]) or Windows."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "missing.yaml"))
    monkeypatch.delenv("FINOPS_MCP_PRICING_COMMAND", raising=False)
    cmd, args = get_pricing_mcp_command()
    assert cmd == "uvx"
    assert DEFAULT_PRICING_MCP_PACKAGE in args


def test_get_pricing_mcp_command_override_from_env(monkeypatch):
    """When FINOPS_MCP_PRICING_COMMAND is set, getter returns parsed command."""
    monkeypatch.setenv(
        "FINOPS_MCP_PRICING_COMMAND",
        "uvx awslabs.aws-pricing-mcp-server@latest",
    )
    cmd, args = get_pricing_mcp_command()
    assert cmd == "uvx"
    assert "awslabs.aws-pricing-mcp-server@latest" in args


def test_reset_settings_cache_clears_pricing_mcp_cache(monkeypatch):
    """reset_settings_cache() clears Pricing MCP caches so next call re-reads."""
    monkeypatch.setenv("FINOPS_MCP_PRICING_ENABLED", "true")
    get_pricing_mcp_enabled()
    reset_settings_cache()
    monkeypatch.setenv("FINOPS_MCP_PRICING_ENABLED", "false")
    assert get_pricing_mcp_enabled() is False


# --- Core MCP (disabled by default) ---


def test_get_core_mcp_enabled_default_false(tmp_path, monkeypatch):
    """When no config and no env, get_core_mcp_enabled returns False."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "missing.yaml"))
    monkeypatch.delenv("FINOPS_MCP_CORE_ENABLED", raising=False)
    assert get_core_mcp_enabled() is False


def test_get_core_mcp_enabled_true_when_env_set(monkeypatch):
    """When FINOPS_MCP_CORE_ENABLED is true, getter returns True."""
    monkeypatch.setenv("FINOPS_MCP_CORE_ENABLED", "true")
    assert get_core_mcp_enabled() is True


def test_get_core_mcp_enabled_from_yaml(tmp_path, monkeypatch):
    """When agent.core_mcp_enabled is true in YAML, getter returns True."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "settings.yaml"))
    monkeypatch.delenv("FINOPS_MCP_CORE_ENABLED", raising=False)
    (tmp_path / "settings.yaml").write_text("agent:\n  core_mcp_enabled: true\n")
    assert get_core_mcp_enabled() is True


def test_get_core_mcp_enabled_env_overrides_yaml(tmp_path, monkeypatch):
    """When YAML has core_mcp_enabled true and env false, getter returns False."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "settings.yaml"))
    (tmp_path / "settings.yaml").write_text("agent:\n  core_mcp_enabled: true\n")
    monkeypatch.setenv("FINOPS_MCP_CORE_ENABLED", "false")
    assert get_core_mcp_enabled() is False


def test_get_core_mcp_roles_default_when_unset(tmp_path, monkeypatch):
    """When no override, get_core_mcp_roles returns default role list."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "missing.yaml"))
    monkeypatch.delenv("FINOPS_MCP_CORE_ROLES", raising=False)
    assert get_core_mcp_roles() == DEFAULT_CORE_MCP_ROLES


def test_get_core_mcp_roles_from_yaml(tmp_path, monkeypatch):
    """When agent.core_mcp_roles is set in YAML, getter returns that list."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "settings.yaml"))
    monkeypatch.delenv("FINOPS_MCP_CORE_ROLES", raising=False)
    (tmp_path / "settings.yaml").write_text(
        "agent:\n  core_mcp_roles:\n    - finops\n    - aws-foundation\n"
    )
    assert get_core_mcp_roles() == ["finops", "aws-foundation"]


def test_get_core_mcp_roles_override_from_env(monkeypatch):
    """When FINOPS_MCP_CORE_ROLES is set, getter returns parsed list."""
    monkeypatch.setenv("FINOPS_MCP_CORE_ROLES", "finops, solutions-architect")
    assert get_core_mcp_roles() == ["finops", "solutions-architect"]


def test_get_core_mcp_command_default_returns_uvx_or_uv_and_args(tmp_path, monkeypatch):
    """When no override, get_core_mcp_command returns (uvx/uv, [package]) or Windows variant."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "missing.yaml"))
    monkeypatch.delenv("FINOPS_MCP_CORE_COMMAND", raising=False)
    cmd, args = get_core_mcp_command()
    assert DEFAULT_CORE_MCP_PACKAGE in args or "core-mcp-server" in " ".join(args)


def test_get_core_mcp_command_override_from_env(monkeypatch):
    """When FINOPS_MCP_CORE_COMMAND is set, getter returns parsed command."""
    monkeypatch.setenv(
        "FINOPS_MCP_CORE_COMMAND",
        "uvx awslabs.core-mcp-server@latest",
    )
    cmd, args = get_core_mcp_command()
    assert cmd == "uvx"
    assert "awslabs.core-mcp-server@latest" in args


def test_reset_settings_cache_clears_core_mcp_cache(monkeypatch):
    """reset_settings_cache() clears Core MCP caches so next call re-reads."""
    monkeypatch.setenv("FINOPS_MCP_CORE_ENABLED", "true")
    get_core_mcp_enabled()
    reset_settings_cache()
    monkeypatch.setenv("FINOPS_MCP_CORE_ENABLED", "false")
    assert get_core_mcp_enabled() is False


def test_get_read_only_guardrail_input_enabled_default_true_when_no_config(tmp_path, monkeypatch):
    """When no config, input guardrail enabled flag is True."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "missing.yaml"))
    monkeypatch.delenv("FINOPS_READ_ONLY_GUARDRAIL_INPUT_ENABLED", raising=False)
    assert get_read_only_guardrail_input_enabled() is True


def test_get_read_only_guardrail_input_enabled_disabled_via_yaml(tmp_path, monkeypatch):
    """When agent.read_only_guardrail_input_enabled is false in YAML, getter returns False."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "settings.yaml"))
    monkeypatch.delenv("FINOPS_READ_ONLY_GUARDRAIL_INPUT_ENABLED", raising=False)
    (tmp_path / "settings.yaml").write_text("agent:\n  read_only_guardrail_input_enabled: false\n")
    assert get_read_only_guardrail_input_enabled() is False


def test_get_read_only_guardrail_input_enabled_env_overrides_yaml(tmp_path, monkeypatch):
    """When YAML has false and env true, getter returns True (env overrides file)."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "settings.yaml"))
    (tmp_path / "settings.yaml").write_text("agent:\n  read_only_guardrail_input_enabled: false\n")
    monkeypatch.setenv("FINOPS_READ_ONLY_GUARDRAIL_INPUT_ENABLED", "true")
    assert get_read_only_guardrail_input_enabled() is True


def test_get_verbose_tool_debug_default_true_when_no_config(tmp_path, monkeypatch):
    """When no config, verbose_tool_debug is True (default on for debugging)."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "missing.yaml"))
    monkeypatch.delenv("FINOPS_VERBOSE_TOOL_DEBUG", raising=False)
    assert get_verbose_tool_debug() is True


def test_get_verbose_tool_debug_disabled_via_yaml(tmp_path, monkeypatch):
    """When agent.verbose_tool_debug is false in YAML, getter returns False."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "settings.yaml"))
    monkeypatch.delenv("FINOPS_VERBOSE_TOOL_DEBUG", raising=False)
    (tmp_path / "settings.yaml").write_text("agent:\n  verbose_tool_debug: false\n")
    assert get_verbose_tool_debug() is False


def test_get_verbose_tool_debug_env_overrides_yaml(tmp_path, monkeypatch):
    """When YAML has false and env true, getter returns True (env overrides file)."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "settings.yaml"))
    (tmp_path / "settings.yaml").write_text("agent:\n  verbose_tool_debug: false\n")
    monkeypatch.setenv("FINOPS_VERBOSE_TOOL_DEBUG", "true")
    assert get_verbose_tool_debug() is True


def test_get_agent_warm_on_startup_default_true_when_no_config(tmp_path, monkeypatch):
    """When no config (neither file nor env set), warm_on_startup defaults to True."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "missing.yaml"))
    monkeypatch.delenv("FINOPS_AGENT_WARM_ON_STARTUP", raising=False)
    assert get_agent_warm_on_startup() is True


def test_get_agent_warm_on_startup_true_via_yaml(tmp_path, monkeypatch):
    """When agent.warm_on_startup is true in YAML, getter returns True."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "settings.yaml"))
    monkeypatch.delenv("FINOPS_AGENT_WARM_ON_STARTUP", raising=False)
    (tmp_path / "settings.yaml").write_text("agent:\n  warm_on_startup: true\n")
    assert get_agent_warm_on_startup() is True


def test_get_agent_warm_on_startup_false_via_yaml(tmp_path, monkeypatch):
    """When agent.warm_on_startup is false in YAML, getter returns False."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "settings.yaml"))
    monkeypatch.delenv("FINOPS_AGENT_WARM_ON_STARTUP", raising=False)
    (tmp_path / "settings.yaml").write_text("agent:\n  warm_on_startup: false\n")
    assert get_agent_warm_on_startup() is False


def test_get_agent_warm_on_startup_env_override_enable(tmp_path, monkeypatch):
    """When YAML has false and env true, getter returns True (env overrides file)."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "settings.yaml"))
    (tmp_path / "settings.yaml").write_text("agent:\n  warm_on_startup: false\n")
    monkeypatch.setenv("FINOPS_AGENT_WARM_ON_STARTUP", "true")
    assert get_agent_warm_on_startup() is True


def test_get_agent_warm_on_startup_env_override_disable(tmp_path, monkeypatch):
    """When YAML has true and env false, getter returns False (env overrides file)."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "settings.yaml"))
    (tmp_path / "settings.yaml").write_text("agent:\n  warm_on_startup: true\n")
    monkeypatch.setenv("FINOPS_AGENT_WARM_ON_STARTUP", "false")
    assert get_agent_warm_on_startup() is False


def test_get_agent_warm_on_startup_empty_env_uses_yaml(tmp_path, monkeypatch):
    """When env is empty string, it is treated as unset and YAML value is used."""
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "settings.yaml"))
    (tmp_path / "settings.yaml").write_text("agent:\n  warm_on_startup: false\n")
    monkeypatch.setenv("FINOPS_AGENT_WARM_ON_STARTUP", "")
    assert get_agent_warm_on_startup() is False


def test_reset_settings_cache_clears_warm_on_startup_cache(monkeypatch):
    """reset_settings_cache() clears warm_on_startup cache so next call re-reads."""
    monkeypatch.setenv("FINOPS_AGENT_WARM_ON_STARTUP", "true")
    get_agent_warm_on_startup()
    reset_settings_cache()
    monkeypatch.setenv("FINOPS_AGENT_WARM_ON_STARTUP", "false")
    assert get_agent_warm_on_startup() is False
