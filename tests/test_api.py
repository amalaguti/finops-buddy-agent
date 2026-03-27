"""Tests for the FinOps Agent HTTP API (profiles, context, costs, chat)."""

from __future__ import annotations

import tempfile
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from finops_buddy.api.app import app
from finops_buddy.settings import (
    DEFAULT_SERVER_HOST,
    DEFAULT_SERVER_PORT,
    get_server_host,
    get_server_port,
    reset_settings_cache,
)


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


def test_get_version_returns_200_with_version_and_display(client):
    """GET /version returns 200 and JSON with version and display."""
    resp = client.get("/version")
    assert resp.status_code == 200
    data = resp.json()
    assert "version" in data
    assert "display" in data
    assert isinstance(data["version"], str)
    assert isinstance(data["display"], str)
    assert len(data["version"]) > 0
    assert data["display"] == data["version"] or "(" in data["display"]


def test_get_version_includes_commit_when_finops_git_sha_set(client, monkeypatch):
    """When FINOPS_GIT_SHA is set, GET /version includes commit and display contains it."""
    monkeypatch.setenv("FINOPS_GIT_SHA", "a1b2c3d")
    resp = client.get("/version")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("commit") == "a1b2c3d"
    assert "a1b2c3d" in data["display"]
    assert data["display"] == f"{data['version']} (a1b2c3d)"


def test_get_profiles_returns_filtered_list(client, tmp_path, monkeypatch):
    """GET /profiles returns profile names and master profile metadata."""
    config = tmp_path / "config"
    config.write_text(
        "[profile p1]\nregion = us-east-1\n"
        "[profile p2]\nregion = us-east-1\n"
        "[profile p3]\nregion = us-east-1\n"
    )
    monkeypatch.setenv("AWS_CONFIG_FILE", str(config))
    monkeypatch.setenv("FINOPS_CONFIG_FILE", str(tmp_path / "nonexistent.yaml"))
    monkeypatch.setenv("FINOPS_MASTER_PROFILE", "p2")
    resp = client.get("/profiles")
    assert resp.status_code == 200
    data = resp.json()
    assert sorted(data["profiles"]) == ["p1", "p2", "p3"]
    assert data["master_profile"] == "p2"


def test_get_profiles_with_included_only_returns_intersection(client, tmp_path, monkeypatch):
    """GET /profiles with included_only_profiles returns only those in the list."""
    reset_settings_cache()
    config = tmp_path / "config"
    config.write_text(
        "[profile a]\nregion = us-east-1\n"
        "[profile b]\nregion = us-east-1\n"
        "[profile c]\nregion = us-east-1\n"
    )
    monkeypatch.setenv("AWS_CONFIG_FILE", str(config))
    monkeypatch.setenv("FINOPS_CONFIG_FILE", tempfile.mktemp(suffix=".yaml"))
    monkeypatch.setenv("FINOPS_INCLUDED_ONLY_PROFILES", "a,c")
    monkeypatch.delenv("FINOPS_MASTER_PROFILE", raising=False)
    resp = client.get("/profiles")
    assert resp.status_code == 200
    data = resp.json()
    assert sorted(data["profiles"]) == ["a", "c"]
    assert data["master_profile"] is None


def test_get_profiles_in_demo_mode_masks_master_profile(client, tmp_path, monkeypatch):
    """GET /profiles masks both profiles and master_profile in demo mode."""
    with patch("finops_buddy.api.app.list_profiles", return_value=["payer-profile"]):
        with patch("finops_buddy.api.app.get_master_profile", return_value="payer-profile"):
            with patch(
                "finops_buddy.api.app._get_demo_mappings",
                return_value=({"payer-profile": "Master_Account"}, {}),
            ):
                resp = client.get("/profiles", headers={"X-Demo-Mode": "true"})
    assert resp.status_code == 200
    assert resp.json() == {"profiles": ["Master_Account"], "master_profile": "Master_Account"}


def test_hosted_mode_preserves_existing_api_routes(client):
    """Existing API routes stay available when hosted UI routes exist."""
    with patch("finops_buddy.api.app.list_profiles", return_value=["p1", "p2"]):
        with patch("finops_buddy.api.app.get_master_profile", return_value=None):
            resp = client.get("/profiles")
    assert resp.status_code == 200
    assert resp.json() == {"profiles": ["p1", "p2"], "master_profile": None}


def test_get_context_without_profile_returns_400_when_no_default(client, monkeypatch):
    """GET /context without profile and no default returns 400."""
    with patch("finops_buddy.api.deps.list_profiles", return_value=[]):
        monkeypatch.delenv("AWS_PROFILE", raising=False)
        resp = client.get("/context")
    assert resp.status_code == 400
    assert "profile" in resp.json()["detail"].lower()


def test_get_context_with_profile_parameter_returns_account_info(client):
    """GET /context with profile query returns account context."""
    with patch("finops_buddy.api.deps.list_profiles", return_value=["myprofile"]):
        with patch("finops_buddy.api.app.get_account_context") as m:
            m.return_value = type(
                "Ctx",
                (),
                {"account_id": "123", "arn": "arn:aws::123", "role": "master/payer"},
            )()
            resp = client.get("/context", params={"profile": "myprofile"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["account_id"] == "123"
    assert data["arn"] == "arn:aws::123"
    assert data["role"] == "master/payer"


def test_get_context_fails_when_credentials_invalid(client):
    """GET /context returns 503 when credentials/session fail."""
    with patch("finops_buddy.api.deps.list_profiles", return_value=["p"]):
        with patch("finops_buddy.api.app.get_account_context", side_effect=Exception("bad creds")):
            resp = client.get("/context", params={"profile": "p"})
    assert resp.status_code == 503
    assert "Failed to get account context" in resp.json()["detail"]


def test_get_costs_returns_data_for_profile(client):
    """GET /costs with valid profile returns list of service/cost."""
    with patch("finops_buddy.api.deps.list_profiles", return_value=["p"]):
        with patch("finops_buddy.api.app.get_session"):
            with patch(
                "finops_buddy.api.app.get_costs_by_service",
                return_value=[("Amazon S3", 10.5), ("EC2", 20.0)],
            ):
                resp = client.get("/costs", params={"profile": "p"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["service"] == "Amazon S3" and data[0]["cost"] == 10.5
    assert data[1]["service"] == "EC2" and data[1]["cost"] == 20.0


def test_get_costs_fails_on_cost_explorer_error(client):
    """GET /costs returns 403 when Cost Explorer access denied."""
    from finops_buddy.costs import CostExplorerError

    with patch("finops_buddy.api.deps.list_profiles", return_value=["p"]):
        with patch("finops_buddy.api.app.get_session"):
            with patch(
                "finops_buddy.api.app.get_costs_by_service",
                side_effect=CostExplorerError("Access denied"),
            ):
                resp = client.get("/costs", params={"profile": "p"})
    assert resp.status_code == 403
    assert "Access denied" in resp.json()["detail"]


def test_get_costs_dashboard_savings_plans_purchase_recommendations_returns_200(client):
    """GET purchase-recommendations slice returns lookback and recommendations."""
    payload = {
        "lookback_period_in_days": "THIRTY_DAYS",
        "account_scope": "PAYER",
        "matrix_term_in_years": None,
        "matrix_payment_option": None,
        "recommendations": [
            {
                "savings_plans_type": "COMPUTE_SP",
                "term_in_years": "ONE_YEAR",
                "payment_option": "NO_UPFRONT",
                "hourly_commitment_to_purchase": 0.1,
            }
        ],
    }
    with patch("finops_buddy.api.deps.list_profiles", return_value=["p"]):
        with patch("finops_buddy.api.app.get_session"):
            with patch(
                "finops_buddy.api.app.get_savings_plans_purchase_recommendations_dashboard",
                return_value=payload,
            ):
                resp = client.get(
                    "/costs/dashboard/savings-plans-purchase-recommendations",
                    params={"profile": "p"},
                )
    assert resp.status_code == 200
    data = resp.json()
    assert data["lookback_period_in_days"] == "THIRTY_DAYS"
    assert len(data["recommendations"]) == 1


def test_get_costs_dashboard_savings_plans_purchase_recommendations_403_on_error(client):
    """WHEN CE denies purchase recommendations for all cells THEN 403."""
    from finops_buddy.costs import CostExplorerError

    with patch("finops_buddy.api.deps.list_profiles", return_value=["p"]):
        with patch("finops_buddy.api.app.get_session"):
            with patch(
                "finops_buddy.api.app.get_savings_plans_purchase_recommendations_dashboard",
                side_effect=CostExplorerError("Access denied"),
            ):
                resp = client.get(
                    "/costs/dashboard/savings-plans-purchase-recommendations",
                    params={"profile": "p"},
                )
    assert resp.status_code == 403
    assert "Access denied" in resp.json()["detail"]


def test_savings_plans_purchase_400_when_only_term_query_param(client):
    """WHEN only term_in_years is passed THEN 400."""
    with patch("finops_buddy.api.deps.list_profiles", return_value=["p"]):
        with patch("finops_buddy.api.app.get_session"):
            resp = client.get(
                "/costs/dashboard/savings-plans-purchase-recommendations",
                params={"profile": "p", "term_in_years": "ONE_YEAR"},
            )
    assert resp.status_code == 400


def test_savings_plans_purchase_passes_matrix_filters_to_dashboard(client):
    """GET with term_in_years and payment_option passes them to the costs helper."""
    mock_dash = MagicMock(
        return_value={
            "lookback_period_in_days": "THIRTY_DAYS",
            "account_scope": "PAYER",
            "matrix_term_in_years": "THREE_YEARS",
            "matrix_payment_option": "ALL_UPFRONT",
            "recommendations": [],
        }
    )
    with patch("finops_buddy.api.deps.list_profiles", return_value=["p"]):
        with patch("finops_buddy.api.app.get_session"):
            with patch(
                "finops_buddy.api.app.get_savings_plans_purchase_recommendations_dashboard",
                mock_dash,
            ):
                resp = client.get(
                    "/costs/dashboard/savings-plans-purchase-recommendations",
                    params={
                        "profile": "p",
                        "term_in_years": "THREE_YEARS",
                        "payment_option": "ALL_UPFRONT",
                    },
                )
    assert resp.status_code == 200
    assert mock_dash.call_args[1]["term_in_years"] == "THREE_YEARS"
    assert mock_dash.call_args[1]["payment_option"] == "ALL_UPFRONT"
    assert mock_dash.call_args[1]["lookback_period_in_days"] == "THIRTY_DAYS"


def test_savings_plans_purchase_passes_lookback_query_to_dashboard(client):
    """GET with lookback_period_in_days passes it to the costs helper."""
    mock_dash = MagicMock(
        return_value={
            "lookback_period_in_days": "SIXTY_DAYS",
            "account_scope": "PAYER",
            "matrix_term_in_years": None,
            "matrix_payment_option": None,
            "recommendations": [],
        }
    )
    with patch("finops_buddy.api.deps.list_profiles", return_value=["p"]):
        with patch("finops_buddy.api.app.get_session"):
            with patch(
                "finops_buddy.api.app.get_savings_plans_purchase_recommendations_dashboard",
                mock_dash,
            ):
                resp = client.get(
                    "/costs/dashboard/savings-plans-purchase-recommendations",
                    params={"profile": "p", "lookback_period_in_days": "SIXTY_DAYS"},
                )
    assert resp.status_code == 200
    assert mock_dash.call_args[1]["lookback_period_in_days"] == "SIXTY_DAYS"


def test_savings_plans_purchase_400_when_invalid_lookback(client):
    """WHEN lookback_period_in_days is invalid THEN 400."""
    with patch("finops_buddy.api.deps.list_profiles", return_value=["p"]):
        with patch("finops_buddy.api.app.get_session"):
            resp = client.get(
                "/costs/dashboard/savings-plans-purchase-recommendations",
                params={"profile": "p", "lookback_period_in_days": "NINETY_DAYS"},
            )
    assert resp.status_code == 400


def test_savings_plans_purchase_uses_payer_when_profile_matches_master(client):
    """WHEN selected profile equals FINOPS_MASTER_PROFILE THEN account_scope PAYER."""
    mock_dash = MagicMock(
        return_value={
            "lookback_period_in_days": "THIRTY_DAYS",
            "account_scope": "PAYER",
            "recommendations": [],
        }
    )
    with patch("finops_buddy.api.deps.list_profiles", return_value=["master", "other"]):
        with patch("finops_buddy.api.app.get_session"):
            with patch(
                "finops_buddy.api.app.get_savings_plans_purchase_recommendations_dashboard",
                mock_dash,
            ):
                with patch("finops_buddy.api.app.get_master_profile", return_value="master"):
                    resp = client.get(
                        "/costs/dashboard/savings-plans-purchase-recommendations",
                        params={"profile": "master"},
                    )
    assert resp.status_code == 200
    mock_dash.assert_called_once()
    assert mock_dash.call_args[1]["account_scope"] == "PAYER"


def test_savings_plans_purchase_uses_linked_when_profile_not_master(client):
    """WHEN selected profile differs from FINOPS_MASTER_PROFILE THEN account_scope LINKED."""
    mock_dash = MagicMock(
        return_value={
            "lookback_period_in_days": "THIRTY_DAYS",
            "account_scope": "LINKED",
            "recommendations": [],
        }
    )
    with patch("finops_buddy.api.deps.list_profiles", return_value=["master", "other"]):
        with patch("finops_buddy.api.app.get_session"):
            with patch(
                "finops_buddy.api.app.get_savings_plans_purchase_recommendations_dashboard",
                mock_dash,
            ):
                with patch("finops_buddy.api.app.get_master_profile", return_value="master"):
                    resp = client.get(
                        "/costs/dashboard/savings-plans-purchase-recommendations",
                        params={"profile": "other"},
                    )
    assert resp.status_code == 200
    mock_dash.assert_called_once()
    assert mock_dash.call_args[1]["account_scope"] == "LINKED"


def test_savings_plans_purchase_uses_payer_when_master_profile_unset(client):
    """WHEN FINOPS_MASTER_PROFILE is unset THEN account_scope PAYER for any profile."""
    mock_dash = MagicMock(
        return_value={
            "lookback_period_in_days": "THIRTY_DAYS",
            "account_scope": "PAYER",
            "recommendations": [],
        }
    )
    with patch("finops_buddy.api.deps.list_profiles", return_value=["any"]):
        with patch("finops_buddy.api.app.get_session"):
            with patch(
                "finops_buddy.api.app.get_savings_plans_purchase_recommendations_dashboard",
                mock_dash,
            ):
                with patch("finops_buddy.api.app.get_master_profile", return_value=None):
                    resp = client.get(
                        "/costs/dashboard/savings-plans-purchase-recommendations",
                        params={"profile": "any"},
                    )
    assert resp.status_code == 200
    assert mock_dash.call_args[1]["account_scope"] == "PAYER"


def test_get_costs_dashboard_returns_all_sections_for_profile(client):
    """GET /costs/dashboard with valid profile returns all six sections."""
    with patch("finops_buddy.api.deps.list_profiles", return_value=["p"]):
        with patch("finops_buddy.api.app.get_session"):
            with patch(
                "finops_buddy.api.app.get_costs_by_service_aws_only",
                return_value=[("Amazon S3", 10.5)],
            ):
                with patch(
                    "finops_buddy.api.app.get_costs_by_linked_account",
                    return_value=[("123456789012", 100.0)],
                ):
                    with patch(
                        "finops_buddy.api.app.get_costs_marketplace",
                        return_value=[],
                    ):
                        with patch(
                            "finops_buddy.api.app.get_optimization_recommendations_top10",
                            return_value=[],
                        ):
                            with patch(
                                "finops_buddy.api.app.get_anomalies_last_3_days",
                                return_value=[],
                            ):
                                with patch(
                                    "finops_buddy.api.app.get_savings_plans_utilization_coverage",
                                    return_value={
                                        "utilization_percentage": 85.0,
                                        "coverage_percentage": 90.0,
                                        "period_months": 1,
                                    },
                                ):
                                    with patch(
                                        "finops_buddy.api.app.get_savings_plans_per_plan_details",
                                        return_value=[],
                                    ):
                                        resp = client.get(
                                            "/costs/dashboard", params={"profile": "p"}
                                        )
    assert resp.status_code == 200
    data = resp.json()
    assert "by_service_aws_only" in data
    assert "by_account" in data
    assert "by_marketplace" in data
    assert "optimization_recommendations" in data
    assert "anomalies" in data
    assert "savings_plans_1m" in data
    assert "savings_plans_2m" in data
    assert "savings_plans_3m" in data
    assert data["by_service_aws_only"][0]["service"] == "Amazon S3"
    assert data["savings_plans_1m"]["period_months"] == 1


def test_get_costs_dashboard_fails_when_no_profile(client):
    """GET /costs/dashboard without profile returns 400."""
    with patch("finops_buddy.api.deps.list_profiles", return_value=[]):
        resp = client.get("/costs/dashboard")
    assert resp.status_code == 400


def test_get_costs_dashboard_returns_savings_plans_for_all_periods(client):
    """GET /costs/dashboard fetches savings plans for 1m, 2m, 3m and returns all in one response."""
    with patch("finops_buddy.api.deps.list_profiles", return_value=["p"]):
        with patch("finops_buddy.api.app.get_session"):
            with patch(
                "finops_buddy.api.app.get_costs_by_service_aws_only",
                return_value=[],
            ):
                with patch(
                    "finops_buddy.api.app.get_costs_by_linked_account",
                    return_value=[],
                ):
                    with patch(
                        "finops_buddy.api.app.get_costs_marketplace",
                        return_value=[],
                    ):
                        with patch(
                            "finops_buddy.api.app.get_optimization_recommendations_top10",
                            return_value=[],
                        ):
                            with patch(
                                "finops_buddy.api.app.get_anomalies_last_3_days",
                                return_value=[],
                            ):
                                with patch(
                                    "finops_buddy.api.app.get_savings_plans_utilization_coverage",
                                    side_effect=lambda session, months: {
                                        "utilization_percentage": 70.0 + months * 5,
                                        "coverage_percentage": 75.0 + months * 5,
                                        "period_months": months,
                                    },
                                ) as sp_mock:
                                    with patch(
                                        "finops_buddy.api.app.get_savings_plans_per_plan_details",
                                        return_value=[],
                                    ):
                                        resp = client.get(
                                            "/costs/dashboard",
                                            params={"profile": "p"},
                                        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["savings_plans_1m"]["period_months"] == 1
    assert data["savings_plans_2m"]["period_months"] == 2
    assert data["savings_plans_3m"]["period_months"] == 3
    assert sp_mock.call_count == 3
    call_months = [c[1]["months"] for c in sp_mock.call_args_list]
    assert call_months == [1, 2, 3]


def test_post_chat_streams_response(client):
    """POST /chat returns SSE stream with message event."""
    with patch("finops_buddy.api.deps.list_profiles", return_value=["p"]):
        with patch(
            "finops_buddy.api.app.run_chat_turn",
            return_value=("Hello, here is your cost summary.", None, []),
        ):
            resp = client.post(
                "/chat",
                json={"message": "What are my costs?", "profile": "p"},
            )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")
    text = resp.text
    assert "event: message" in text
    assert "Hello, here is your cost summary" in text
    assert "event: done" in text


def test_post_chat_respects_read_only_guardrail(client):
    """POST /chat with mutating intent returns guardrail message in stream."""
    with patch("finops_buddy.api.deps.list_profiles", return_value=["p"]):
        with patch("finops_buddy.api.app.get_read_only_guardrail_input_enabled", return_value=True):
            with patch("finops_buddy.api.app.is_mutating_intent", return_value=True):
                resp = client.post(
                    "/chat",
                    json={"message": "delete my bucket", "profile": "p"},
                )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")
    # Stream should contain the read-only block message (same as CLI)
    assert "read-only" in resp.text.lower() or "can't create" in resp.text.lower()


def test_backend_uses_aws_profile_for_default(client, monkeypatch):
    """When AWS_PROFILE is set and no profile in request, backend uses it for context."""
    monkeypatch.setenv("AWS_PROFILE", "defaultprofile")
    with patch("finops_buddy.api.deps.list_profiles", return_value=["defaultprofile"]):
        with patch("finops_buddy.api.app.get_account_context") as m:
            m.return_value = type(
                "Ctx",
                (),
                {"account_id": "111", "arn": "arn:aws::111", "role": "unknown"},
            )()
            resp = client.get("/context")
    assert resp.status_code == 200
    assert resp.json()["account_id"] == "111"
    m.assert_called_once()
    call_kw = m.call_args[1]
    assert call_kw.get("profile_name") == "defaultprofile"


def test_request_can_override_profile(client):
    """Query parameter profile overrides default for context."""
    with patch("finops_buddy.api.deps.list_profiles", return_value=["p1", "p2"]):
        with patch("finops_buddy.api.app.get_account_context") as m:
            m.return_value = type(
                "Ctx",
                (),
                {"account_id": "999", "arn": "arn:aws::999", "role": "linked"},
            )()
            resp = client.get("/context", params={"profile": "p2"})
    assert resp.status_code == 200
    m.assert_called_once()
    assert m.call_args[1]["profile_name"] == "p2"


def test_get_tooling_returns_tooling_text(client):
    """GET /tooling with profile returns tooling output (same as CLI /tooling)."""
    with patch("finops_buddy.api.deps.list_profiles", return_value=["p"]):
        with patch("finops_buddy.api.app.build_agent_and_tools") as m:
            agent = object()
            tools = []
            m.return_value = (agent, tools)
            with patch(
                "finops_buddy.api.app._format_tooling_output",
                return_value="Available tools:\n  get_current_date",
            ):
                with patch("finops_buddy.api.app._cleanup_agent_tools"):
                    resp = client.get("/tooling", params={"profile": "p"})
    assert resp.status_code == 200
    data = resp.json()
    assert "tooling" in data
    assert "Available tools" in data["tooling"]


def test_get_tooling_without_profile_returns_400(client, monkeypatch):
    """GET /tooling without profile returns 400 when no default."""
    with patch("finops_buddy.api.deps.list_profiles", return_value=[]):
        monkeypatch.delenv("AWS_PROFILE", raising=False)
        resp = client.get("/tooling")
    assert resp.status_code == 400


def test_get_status_returns_agent_and_mcp_status(client):
    """GET /status with profile returns agent config and MCP status."""
    with patch("finops_buddy.api.deps.list_profiles", return_value=["p"]):
        with patch("finops_buddy.api.app.build_agent_and_tools") as m:
            agent = object()
            tools = []
            m.return_value = (agent, tools)
            with patch(
                "finops_buddy.api.app._format_mcp_status",
                return_value="MCP servers: (none)",
            ):
                with patch("finops_buddy.api.app._cleanup_agent_tools"):
                    resp = client.get("/status", params={"profile": "p"})
    assert resp.status_code == 200
    data = resp.json()
    assert "agent" in data
    assert "model_id" in data["agent"]
    assert "temperature" in data["agent"]
    assert "max_completion_tokens" in data["agent"]
    assert "mcp_status" in data
    assert "MCP" in data["mcp_status"]


def test_get_status_without_profile_returns_400(client, monkeypatch):
    """GET /status without profile returns 400 when no default."""
    with patch("finops_buddy.api.deps.list_profiles", return_value=[]):
        monkeypatch.delenv("AWS_PROFILE", raising=False)
        resp = client.get("/status")
    assert resp.status_code == 400


def test_server_listens_on_configured_port(monkeypatch):
    """get_server_port returns configured value from env."""
    reset_settings_cache()
    try:
        monkeypatch.setenv("FINOPS_SERVER_PORT", "9000")
        assert get_server_port() == 9000
    finally:
        monkeypatch.delenv("FINOPS_SERVER_PORT", raising=False)
        reset_settings_cache()


def test_server_default_bind_when_no_config(monkeypatch):
    """When no server config, get_server_host/port return safe defaults."""
    reset_settings_cache()
    for key in ("FINOPS_SERVER_HOST", "FINOPS_SERVER_PORT", "FINOPS_CONFIG_FILE"):
        monkeypatch.delenv(key, raising=False)
    # Use a nonexistent config path so file doesn't supply server section
    monkeypatch.setenv("FINOPS_CONFIG_FILE", tempfile.mktemp(suffix=".yaml"))
    try:
        assert get_server_host() == DEFAULT_SERVER_HOST
        assert get_server_port() == DEFAULT_SERVER_PORT
    finally:
        reset_settings_cache()


def test_root_serves_hosted_webui_when_assets_present(client, tmp_path):
    """GET / returns the hosted SPA entrypoint when packaged assets exist."""
    index = tmp_path / "index.html"
    index.write_text("<!DOCTYPE html><html><body>Hosted UI</body></html>", encoding="utf-8")
    with patch("finops_buddy.api.app._get_hosted_webui_index", return_value=index):
        resp = client.get("/")
    assert resp.status_code == 200
    assert "Hosted UI" in resp.text


def test_mcp_tooling_status_serves_hosted_webui_when_assets_present(client, tmp_path):
    """GET /mcp_tooling_status returns the hosted SPA entrypoint."""
    index = tmp_path / "index.html"
    index.write_text("<!DOCTYPE html><html><body>MCP page</body></html>", encoding="utf-8")
    with patch("finops_buddy.api.app._get_hosted_webui_index", return_value=index):
        resp = client.get("/mcp_tooling_status")
    assert resp.status_code == 200
    assert "MCP page" in resp.text


def test_assets_route_serves_compiled_frontend_asset(client, tmp_path):
    """GET /assets/... returns a packaged frontend asset when present."""
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    asset = assets_dir / "app.js"
    asset.write_text("console.log('finops');", encoding="utf-8")
    with patch("finops_buddy.api.app._get_hosted_webui_dir", return_value=tmp_path):
        resp = client.get("/assets/app.js")
    assert resp.status_code == 200
    assert "console.log('finops');" in resp.text


def test_root_asset_route_serves_packaged_file(client, tmp_path):
    """GET /vite.svg-style assets returns a packaged root-level frontend file."""
    asset = tmp_path / "vite.svg"
    asset.write_text("<svg></svg>", encoding="utf-8")
    with patch("finops_buddy.api.app._get_hosted_webui_dir", return_value=tmp_path):
        resp = client.get("/vite.svg")
    assert resp.status_code == 200
    assert "<svg" in resp.text


def test_docs_route_remains_available_in_hosted_mode(client):
    """Swagger docs remain available and are not masked by frontend routes."""
    resp = client.get("/docs")
    assert resp.status_code == 200
    assert "Swagger UI" in resp.text


def test_unknown_route_is_not_masked_by_spa_fallback(client, tmp_path):
    """Unknown routes return 404 instead of the SPA entrypoint."""
    index = tmp_path / "index.html"
    index.write_text("<!DOCTYPE html><html><body>Hosted UI</body></html>", encoding="utf-8")
    with patch("finops_buddy.api.app._get_hosted_webui_index", return_value=index):
        resp = client.get("/totally-unknown")
    assert resp.status_code == 404


def test_root_returns_explicit_message_when_hosted_assets_missing(client):
    """GET / returns a clear response when the hosted frontend is unavailable."""
    with patch("finops_buddy.api.app._get_hosted_webui_index", return_value=None):
        resp = client.get("/")
    assert resp.status_code == 503
    assert "Hosted web UI is not available" in resp.text
