"""FastAPI application for the FinOps Agent HTTP API."""

from __future__ import annotations

import json
import logging
import os
import queue
import threading
import time
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, Response, StreamingResponse
from pydantic import BaseModel

from finops_buddy import __version__ as _pkg_version
from finops_buddy.agent.format import _format_tooling_output
from finops_buddy.agent.guardrails import MESSAGE_INPUT_BLOCKED, is_mutating_intent
from finops_buddy.agent.mcp import _format_mcp_status
from finops_buddy.config import get_master_profile
from finops_buddy.context import get_account_context
from finops_buddy.costs import (
    CostExplorerError,
    get_costs_by_account_and_service,
    get_costs_by_linked_account,
    get_costs_by_service,
    get_costs_by_service_and_account,
    get_costs_by_service_aws_only,
    get_costs_marketplace,
    get_savings_plans_per_plan_details,
    get_savings_plans_utilization_coverage,
)
from finops_buddy.identity import (
    get_profile_account_ids_from_local_files,
    get_session,
    list_profiles,
)
from finops_buddy.optimization import (
    get_anomalies_last_3_days,
    get_optimization_recommendations_top10,
)
from finops_buddy.settings import (
    get_agent_max_completion_tokens,
    get_agent_model_id,
    get_agent_temperature,
    get_agent_warm_on_startup,
    get_cors_origins,
    get_demo_account_id_mapping,
    get_demo_account_mapping,
    get_excel_mcp_enabled,
    get_pdf_mcp_enabled,
    get_read_only_guardrail_input_enabled,
)

from .chat import (  # noqa: F401
    _cleanup_agent_tools,
    build_agent_and_tools,
    resolve_agent_profile,
    run_chat_turn,
    start_profile_account_mapping_refresh,
    warm_chat_agent_on_startup,
)
from .demo import mask_response_data
from .deps import resolve_profile

logger = logging.getLogger(__name__)
# Ensure app logger emits to console (uvicorn log_level does not add handlers to app loggers)
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(levelname)s [%(name)s] %(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)


def _load_dotenv_for_api() -> None:
    """Load .env and .env.local so API (and uvicorn workers) see FINOPS_* vars."""
    root = Path(__file__).resolve()
    for _ in range(6):
        root = root.parent
        if (root / "pyproject.toml").exists() or (root / ".env.local").exists():
            load_dotenv(root / ".env")
            load_dotenv(root / ".env.local", override=True)
            break


_load_dotenv_for_api()


@asynccontextmanager
async def _app_lifespan(app: FastAPI):
    """
    Run warm-up only when the ASGI app starts.

    This avoids doing work when the module is imported in tests.
    """
    # Start profile→account_id mapping in background so it is often ready by first chat
    start_profile_account_mapping_refresh()
    logger.info("Profile→account mapping refresh started in background.")
    if get_agent_warm_on_startup():
        logger.info(
            "Agent warm-up: loading MCP servers now (may take 1–2 min); watch logs for progress. "
            "To see MCP progress in the UI on first chat instead, set "
            "FINOPS_AGENT_WARM_ON_STARTUP=false."
        )
        try:
            warm_chat_agent_on_startup()
        except Exception:
            pass
    yield
    # shutdown: optional cleanup could go here


app = FastAPI(
    title="FinOps Agent API",
    description="HTTP API for AWS cost visibility: profiles, context, costs, and chat.",
    version="0.1.0",
    lifespan=_app_lifespan,
)

_HOSTED_WEBUI_DIR = Path(__file__).resolve().parents[1] / "webui"


def _get_hosted_webui_dir() -> Path | None:
    """Return the packaged hosted UI directory when present."""
    if _HOSTED_WEBUI_DIR.exists() and _HOSTED_WEBUI_DIR.is_dir():
        return _HOSTED_WEBUI_DIR
    return None


def _get_hosted_webui_index() -> Path | None:
    """Return the hosted UI entrypoint when present."""
    webui_dir = _get_hosted_webui_dir()
    if webui_dir is None:
        return None
    index_path = webui_dir / "index.html"
    if index_path.exists() and index_path.is_file():
        return index_path
    return None


def _missing_hosted_webui_response() -> HTMLResponse:
    """Return a clear message when hosted UI assets are unavailable."""
    return HTMLResponse(
        content=(
            "<!DOCTYPE html><html><head><title>FinOps Buddy UI unavailable</title></head>"
            "<body><h1>Hosted web UI is not available</h1>"
            "<p>The FastAPI server is running, but the compiled frontend bundle was not found.</p>"
            "<p>For development, run the Vite frontend separately. "
            "For hosted mode, build the frontend bundle first.</p></body></html>"
        ),
        status_code=503,
    )


# Request logging: log method + path when request arrives (helps debug hanging endpoints)
@app.middleware("http")
async def _log_request(request: Request, call_next):
    logger.info("Request: %s %s", request.method, request.url.path)
    return await call_next(request)


# CORS: when cors_origins is set, allow those origins; otherwise no CORS middleware (same-origin)
_cors_origins = get_cors_origins()
if _cors_origins:
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/", include_in_schema=False, response_model=None)
def get_hosted_webui_root() -> Response:
    """Serve the hosted SPA entrypoint when the compiled frontend is available."""
    index_path = _get_hosted_webui_index()
    if index_path is None:
        return _missing_hosted_webui_response()
    return FileResponse(index_path)


@app.get("/mcp_tooling_status", include_in_schema=False, response_model=None)
def get_hosted_webui_mcp_status() -> Response:
    """Serve the hosted SPA entrypoint for the MCP status page."""
    index_path = _get_hosted_webui_index()
    if index_path is None:
        return _missing_hosted_webui_response()
    return FileResponse(index_path)


@app.get("/demo", include_in_schema=False, response_model=None)
def get_hosted_webui_demo() -> Response:
    """Serve the hosted SPA entrypoint in demo mode."""
    index_path = _get_hosted_webui_index()
    if index_path is None:
        return _missing_hosted_webui_response()
    return FileResponse(index_path)


@app.get("/demo/{path:path}", include_in_schema=False, response_model=None)
def get_hosted_webui_demo_path(path: str) -> Response:
    """Serve the hosted SPA entrypoint for demo mode sub-routes."""
    index_path = _get_hosted_webui_index()
    if index_path is None:
        return _missing_hosted_webui_response()
    return FileResponse(index_path)


@app.get("/assets/{asset_path:path}", include_in_schema=False, response_model=None)
def get_hosted_webui_asset(asset_path: str) -> Response:
    """Serve compiled frontend assets from the packaged hosted UI bundle."""
    webui_dir = _get_hosted_webui_dir()
    if webui_dir is None:
        raise HTTPException(status_code=404, detail="Hosted frontend assets not found.")
    target = (webui_dir / "assets" / asset_path).resolve()
    assets_dir = (webui_dir / "assets").resolve()
    if assets_dir not in target.parents or not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Frontend asset not found.")
    return FileResponse(target)


def _is_demo_mode(request: Request) -> bool:
    """Check if request has X-Demo-Mode: true header."""
    return request.headers.get("X-Demo-Mode", "").lower() == "true"


def _get_demo_mappings() -> tuple[dict[str, str], dict[str, str]]:
    """Get demo mode mappings (creates copies to allow auto-generation)."""
    return dict(get_demo_account_mapping()), dict(get_demo_account_id_mapping())


def _reverse_demo_profile(masked_profile: str | None) -> str | None:
    """Reverse-map a masked profile name back to the real profile name."""
    if masked_profile is None:
        return None
    name_mapping = get_demo_account_mapping()
    reverse_map = {v: k for k, v in name_mapping.items()}
    return reverse_map.get(masked_profile, masked_profile)


@lru_cache(maxsize=1)
def _get_account_id_to_profile_map(cache_key: str = "default") -> dict[str, str]:
    """
    Build a mapping from AWS account ID to profile name.

    Uses local AWS config/credentials only (no AWS API calls) so dashboard requests
    do not trigger STS calls for every configured profile.
    """
    profiles = list_profiles()
    logger.info(
        "Building account_id_to_profile map from local files for %d profile(s)", len(profiles)
    )
    profile_to_account = get_profile_account_ids_from_local_files(profiles)
    # Invert mapping: account_id -> profile_name
    mapping: dict[str, str] = {
        account_id: profile_name for profile_name, account_id in profile_to_account.items()
    }
    logger.info(
        "Built account_id_to_profile map from local files: %d entries "
        "(profiles with resolvable account IDs)",
        len(mapping),
    )
    return mapping


class ProfilesResponse(BaseModel):
    """Response body for GET /profiles."""

    profiles: list[str]
    master_profile: str | None = None


@app.get("/version")
def get_version() -> dict:
    """
    Return running package version and optional git commit SHA.

    Used by the web UI to display version in the nav bar. Commit comes from
    FINOPS_GIT_SHA (set at build time, e.g. Docker build-arg).
    """
    commit = os.environ.get("FINOPS_GIT_SHA") or None
    version_str = _pkg_version
    display = f"{version_str} ({commit})" if commit else version_str
    return {"version": version_str, "commit": commit, "display": display}


@app.get("/profiles")
def get_profiles(request: Request) -> ProfilesResponse:
    """
    List configured AWS profile names.

    Honors excluded_profiles and included_only_profiles (same as CLI).
    When X-Demo-Mode: true header is present, returns masked profile names.
    """
    payload: dict[str, list[str] | str | None] = {
        "profiles": list_profiles(),
        "master_profile": get_master_profile(),
    }
    if _is_demo_mode(request):
        name_mapping, id_mapping = _get_demo_mappings()
        payload = mask_response_data(payload, name_mapping, id_mapping)
    return ProfilesResponse(**payload)


@app.get("/context")
def get_context(request: Request, profile: str | None = Depends(resolve_profile)) -> dict:
    """
    Return account context (account_id, arn, role, master/payer) for the given or default profile.
    When X-Demo-Mode: true header is present, masks account_id and profile in response.
    """
    logger.info("GET /context start profile=%s", profile)
    if profile is None:
        logger.warning("GET /context: no profile")
        raise HTTPException(
            status_code=400,
            detail=(
                "No AWS profile available. Set AWS_PROFILE, pass ?profile=... or "
                "X-AWS-Profile header, or configure profiles in settings."
            ),
        )
    try:
        real_profile = _reverse_demo_profile(profile) if _is_demo_mode(request) else profile
        logger.info("GET /context resolving real_profile=%s", real_profile)
        ctx = get_account_context(profile_name=real_profile)
        result = {
            "account_id": ctx.account_id,
            "arn": ctx.arn,
            "role": ctx.role,
        }
        if _is_demo_mode(request):
            name_mapping, id_mapping = _get_demo_mappings()
            result = mask_response_data(result, name_mapping, id_mapping)
        logger.info("GET /context done account_id=%s", result.get("account_id"))
        return result
    except Exception as e:
        logger.exception("GET /context error: %s", e)
        raise HTTPException(
            status_code=503,
            detail=f"Failed to get account context: {e!s}",
        ) from e


@app.get("/costs")
def get_costs(request: Request, profile: str | None = Depends(resolve_profile)) -> list[dict]:
    """
    Return current-month costs by service for the given or default profile.
    When X-Demo-Mode: true header is present, masks any account identifiers in response.
    """
    if profile is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "No AWS profile available. Set AWS_PROFILE, pass ?profile=... or "
                "X-AWS-Profile header, or configure profiles in settings."
            ),
        )
    try:
        real_profile = _reverse_demo_profile(profile) if _is_demo_mode(request) else profile
        session = get_session(profile_name=real_profile)
        rows = get_costs_by_service(session)
        result = [{"service": svc, "cost": float(amt)} for svc, amt in rows]
        if _is_demo_mode(request):
            name_mapping, id_mapping = _get_demo_mappings()
            result = mask_response_data(result, name_mapping, id_mapping)
        return result
    except CostExplorerError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to get costs: {e!s}",
        ) from e


@app.get("/costs/dashboard")
def get_costs_dashboard(
    request: Request,
    profile: str | None = Depends(resolve_profile),
) -> dict:
    """
    Return the full costs dashboard for the given or default profile: current-month
    costs by AWS service only, by linked account, by marketplace; top 10 cost
    optimization recommendations; anomalies in the last 3 days; Savings Plans
    utilization and coverage for 1, 2, and 3 months (all returned so the client
    can cache once and switch period without refetching).
    When X-Demo-Mode: true, account identifiers are masked.
    """
    t0 = time.monotonic()
    logger.info("GET /costs/dashboard start profile=%s", profile)
    if profile is None:
        logger.warning("GET /costs/dashboard: no profile")
        raise HTTPException(
            status_code=400,
            detail=(
                "No AWS profile available. Set AWS_PROFILE, pass ?profile=... or "
                "X-AWS-Profile header, or configure profiles in settings."
            ),
        )
    try:
        real_profile = _reverse_demo_profile(profile) if _is_demo_mode(request) else profile
        logger.info("GET /costs/dashboard resolving session real_profile=%s", real_profile)
        session = get_session(profile_name=real_profile)
        logger.info("GET /costs/dashboard session resolved in %.2fs", time.monotonic() - t0)
    except Exception as e:
        logger.exception("GET /costs/dashboard session error: %s", e)
        raise HTTPException(status_code=503, detail=f"Failed to resolve session: {e!s}") from e

    try:
        logger.info("GET /costs/dashboard fetching by_service_aws_only")
        by_service = get_costs_by_service_aws_only(session)
        logger.info("GET /costs/dashboard by_service_aws_only done (%d rows)", len(by_service))
        logger.info("GET /costs/dashboard fetching by_linked_account")
        by_account = get_costs_by_linked_account(session)
        logger.info("GET /costs/dashboard by_linked_account done (%d rows)", len(by_account))
        logger.info("GET /costs/dashboard fetching by_marketplace")
        by_marketplace = get_costs_marketplace(session)
        logger.info("GET /costs/dashboard by_marketplace done (%d rows)", len(by_marketplace))
    except CostExplorerError as e:
        logger.exception("GET /costs/dashboard Cost Explorer error: %s", e)
        raise HTTPException(status_code=403, detail=str(e)) from e

    logger.info("GET /costs/dashboard building account_id_to_profile map")
    account_id_to_profile = _get_account_id_to_profile_map()
    logger.info(
        "GET /costs/dashboard account_id_to_profile done (%d entries)", len(account_id_to_profile)
    )

    logger.info("GET /costs/dashboard fetching optimization_recommendations")
    optimization_recommendations = get_optimization_recommendations_top10(session)
    logger.info(
        "GET /costs/dashboard optimization_recommendations done (%d items)",
        len(optimization_recommendations),
    )

    logger.info("GET /costs/dashboard fetching anomalies")
    anomalies = get_anomalies_last_3_days(session)
    logger.info("GET /costs/dashboard anomalies done (%d items)", len(anomalies))

    logger.info("GET /costs/dashboard fetching savings_plans (1m, 2m, 3m)")
    savings_plans_1m = get_savings_plans_utilization_coverage(session, months=1)
    savings_plans_2m = get_savings_plans_utilization_coverage(session, months=2)
    savings_plans_3m = get_savings_plans_utilization_coverage(session, months=3)
    savings_plans_details_1m = get_savings_plans_per_plan_details(session, months=1)
    savings_plans_details_2m = get_savings_plans_per_plan_details(session, months=2)
    savings_plans_details_3m = get_savings_plans_per_plan_details(session, months=3)
    logger.info(
        "GET /costs/dashboard savings_plans done (details: %d, %d, %d)",
        len(savings_plans_details_1m),
        len(savings_plans_details_2m),
        len(savings_plans_details_3m),
    )

    payload = {
        "by_service_aws_only": [{"service": svc, "cost": float(amt)} for svc, amt in by_service],
        "by_account": [
            {
                "account_id": aid,
                "account_name": account_id_to_profile.get(aid, aid),
                "cost": float(amt),
            }
            for aid, amt in by_account
        ],
        "by_marketplace": [{"product": p, "cost": float(amt)} for p, amt in by_marketplace],
        "optimization_recommendations": optimization_recommendations,
        "anomalies": anomalies,
        "savings_plans_1m": savings_plans_1m,
        "savings_plans_2m": savings_plans_2m,
        "savings_plans_3m": savings_plans_3m,
        "savings_plans_details_1m": savings_plans_details_1m,
        "savings_plans_details_2m": savings_plans_details_2m,
        "savings_plans_details_3m": savings_plans_details_3m,
    }
    if _is_demo_mode(request):
        name_mapping, id_mapping = _get_demo_mappings()
        payload = mask_response_data(payload, name_mapping, id_mapping)
    elapsed = time.monotonic() - t0
    logger.info("GET /costs/dashboard done in %.2fs", elapsed)
    return payload


def _resolve_dashboard_session(request: Request, profile: str | None):
    """Resolve profile and session for dashboard slice endpoints."""
    if profile is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "No AWS profile available. Set AWS_PROFILE, pass ?profile=... or "
                "X-AWS-Profile header, or configure profiles in settings."
            ),
        )
    real_profile = _reverse_demo_profile(profile) if _is_demo_mode(request) else profile
    try:
        return get_session(profile_name=real_profile), real_profile
    except Exception as e:
        logger.exception("Dashboard slice session error: %s", e)
        raise HTTPException(status_code=503, detail=f"Failed to resolve session: {e!s}") from e


@app.get("/costs/dashboard/by-service")
def get_costs_dashboard_by_service(
    request: Request,
    profile: str | None = Depends(resolve_profile),
) -> list[dict]:
    """
    Return current-month costs by AWS service only (dashboard slice).
    When X-Demo-Mode: true, account identifiers are masked.
    """
    session, _ = _resolve_dashboard_session(request, profile)
    try:
        by_service = get_costs_by_service_aws_only(session)
    except CostExplorerError as e:
        logger.exception("GET /costs/dashboard/by-service Cost Explorer error: %s", e)
        raise HTTPException(status_code=403, detail=str(e)) from e
    payload = [{"service": svc, "cost": float(amt)} for svc, amt in by_service]
    if _is_demo_mode(request):
        name_mapping, id_mapping = _get_demo_mappings()
        payload = mask_response_data(payload, name_mapping, id_mapping)
    return payload


@app.get("/costs/dashboard/by-account")
def get_costs_dashboard_by_account(
    request: Request,
    profile: str | None = Depends(resolve_profile),
) -> list[dict]:
    """
    Return current-month costs by linked account with account names (dashboard slice).
    When X-Demo-Mode: true, account identifiers are masked.
    """
    session, _ = _resolve_dashboard_session(request, profile)
    try:
        by_account = get_costs_by_linked_account(session)
    except CostExplorerError as e:
        logger.exception("GET /costs/dashboard/by-account Cost Explorer error: %s", e)
        raise HTTPException(status_code=403, detail=str(e)) from e
    account_id_to_profile = _get_account_id_to_profile_map()
    payload = [
        {
            "account_id": aid,
            "account_name": account_id_to_profile.get(aid, aid),
            "cost": float(amt),
        }
        for aid, amt in by_account
    ]
    if _is_demo_mode(request):
        name_mapping, id_mapping = _get_demo_mappings()
        payload = mask_response_data(payload, name_mapping, id_mapping)
    return payload


@app.get("/costs/dashboard/by-marketplace")
def get_costs_dashboard_by_marketplace(
    request: Request,
    profile: str | None = Depends(resolve_profile),
) -> list[dict]:
    """
    Return current-month costs by marketplace product (dashboard slice).
    When X-Demo-Mode: true, account identifiers are masked.
    """
    session, _ = _resolve_dashboard_session(request, profile)
    try:
        by_marketplace = get_costs_marketplace(session)
    except CostExplorerError as e:
        logger.exception("GET /costs/dashboard/by-marketplace Cost Explorer error: %s", e)
        raise HTTPException(status_code=403, detail=str(e)) from e
    payload = [{"product": p, "cost": float(amt)} for p, amt in by_marketplace]
    if _is_demo_mode(request):
        name_mapping, id_mapping = _get_demo_mappings()
        payload = mask_response_data(payload, name_mapping, id_mapping)
    return payload


@app.get("/costs/dashboard/recommendations")
def get_costs_dashboard_recommendations(
    request: Request,
    profile: str | None = Depends(resolve_profile),
) -> list:
    """
    Return top 10 cost optimization recommendations (dashboard slice).
    When X-Demo-Mode: true, account identifiers are masked.
    """
    session, _ = _resolve_dashboard_session(request, profile)
    optimization_recommendations = get_optimization_recommendations_top10(session)
    if _is_demo_mode(request):
        name_mapping, id_mapping = _get_demo_mappings()
        optimization_recommendations = mask_response_data(
            optimization_recommendations, name_mapping, id_mapping
        )
    return optimization_recommendations


@app.get("/costs/dashboard/anomalies")
def get_costs_dashboard_anomalies(
    request: Request,
    profile: str | None = Depends(resolve_profile),
) -> list:
    """
    Return anomalies in the last 3 days (dashboard slice).
    When X-Demo-Mode: true, account identifiers are masked.
    """
    session, _ = _resolve_dashboard_session(request, profile)
    anomalies = get_anomalies_last_3_days(session)
    if _is_demo_mode(request):
        name_mapping, id_mapping = _get_demo_mappings()
        anomalies = mask_response_data(anomalies, name_mapping, id_mapping)
    return anomalies


@app.get("/costs/dashboard/savings-plans")
def get_costs_dashboard_savings_plans(
    request: Request,
    profile: str | None = Depends(resolve_profile),
) -> dict:
    """
    Return Savings Plans utilization/coverage and per-plan details for 1m, 2m, 3m (dashboard slice).
    When X-Demo-Mode: true, account identifiers are masked.
    """
    session, _ = _resolve_dashboard_session(request, profile)
    savings_plans_1m = get_savings_plans_utilization_coverage(session, months=1)
    savings_plans_2m = get_savings_plans_utilization_coverage(session, months=2)
    savings_plans_3m = get_savings_plans_utilization_coverage(session, months=3)
    savings_plans_details_1m = get_savings_plans_per_plan_details(session, months=1)
    savings_plans_details_2m = get_savings_plans_per_plan_details(session, months=2)
    savings_plans_details_3m = get_savings_plans_per_plan_details(session, months=3)
    payload = {
        "savings_plans_1m": savings_plans_1m,
        "savings_plans_2m": savings_plans_2m,
        "savings_plans_3m": savings_plans_3m,
        "savings_plans_details_1m": savings_plans_details_1m,
        "savings_plans_details_2m": savings_plans_details_2m,
        "savings_plans_details_3m": savings_plans_details_3m,
    }
    if _is_demo_mode(request):
        name_mapping, id_mapping = _get_demo_mappings()
        payload = mask_response_data(payload, name_mapping, id_mapping)
    return payload


@app.get("/costs/by-service-accounts")
def get_costs_by_service_accounts(
    request: Request,
    service: str,
    profile: str | None = Depends(resolve_profile),
) -> list[dict]:
    """
    Return current-month costs for a single AWS service, grouped by linked account.

    Used by the dashboard details pane when clicking a service in the
    "By AWS service (current month)" table.
    """
    if profile is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "No AWS profile available. Set AWS_PROFILE, pass ?profile=... or "
                "X-AWS-Profile header, or configure profiles in settings."
            ),
        )
    if not service:
        raise HTTPException(status_code=400, detail="Missing required query parameter: service")
    try:
        real_profile = _reverse_demo_profile(profile) if _is_demo_mode(request) else profile
        session = get_session(profile_name=real_profile)
        rows = get_costs_by_service_and_account(session, service_name=service)
        account_id_to_profile = _get_account_id_to_profile_map()
        result = [
            {
                "account_id": account_id,
                "account_name": account_id_to_profile.get(account_id, account_id),
                "cost": float(amt),
            }
            for account_id, amt in rows
        ]
        if _is_demo_mode(request):
            name_mapping, id_mapping = _get_demo_mappings()
            result = mask_response_data(result, name_mapping, id_mapping)
        return result
    except CostExplorerError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to get service/account costs: {e!s}",
        ) from e


@app.get("/costs/by-account-services")
def get_costs_by_account_services(
    request: Request,
    account_id: str,
    profile: str | None = Depends(resolve_profile),
) -> list[dict]:
    """
    Return current-month costs for a single linked account, grouped by AWS service.

    Used by the dashboard details pane when clicking an account in the
    "By linked account (current month)" table.
    """
    if profile is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "No AWS profile available. Set AWS_PROFILE, pass ?profile=... or "
                "X-AWS-Profile header, or configure profiles in settings."
            ),
        )
    if not account_id:
        raise HTTPException(status_code=400, detail="Missing required query parameter: account_id")
    try:
        real_profile = _reverse_demo_profile(profile) if _is_demo_mode(request) else profile
        session = get_session(profile_name=real_profile)
        rows = get_costs_by_account_and_service(session, account_id=account_id)
        result = [
            {
                "service": service_name,
                "cost": float(amt),
            }
            for service_name, amt in rows
        ]
        if _is_demo_mode(request):
            name_mapping, id_mapping = _get_demo_mappings()
            result = mask_response_data(result, name_mapping, id_mapping)
        return result
    except CostExplorerError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to get account/service costs: {e!s}",
        ) from e


@app.get("/tooling")
def get_tooling(request: Request, profile: str | None = Depends(resolve_profile)) -> dict:
    """
    Return available tools (built-in and MCP) for the given or default profile.

    Same information as the CLI /tooling command in chat.
    """
    if profile is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "No AWS profile available. Set AWS_PROFILE, pass ?profile=... or "
                "X-AWS-Profile header, or configure profiles in settings."
            ),
        )
    try:
        real_profile = _reverse_demo_profile(profile) if _is_demo_mode(request) else profile
        agent_profile = resolve_agent_profile(real_profile)
        agent, tools = build_agent_and_tools(agent_profile)
        text = _format_tooling_output(
            agent,
            tools_override=tools,
            pdf_mcp_enabled=get_pdf_mcp_enabled(),
            excel_mcp_enabled=get_excel_mcp_enabled(),
        )
        return {"tooling": text}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to build tooling: {e!s}",
        ) from e


@app.get("/status")
def get_status(request: Request, profile: str | None = Depends(resolve_profile)) -> dict:
    """
    Return agent config and MCP server readiness for the given or default profile.

    Same information as the CLI /status command in chat.
    """
    if profile is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "No AWS profile available. Set AWS_PROFILE, pass ?profile=... or "
                "X-AWS-Profile header, or configure profiles in settings."
            ),
        )
    try:
        real_profile = _reverse_demo_profile(profile) if _is_demo_mode(request) else profile
        agent_profile = resolve_agent_profile(real_profile)
        agent, tools = build_agent_and_tools(agent_profile)
        model_id = get_agent_model_id() or "default"
        temperature = get_agent_temperature()
        max_tokens = get_agent_max_completion_tokens()
        mcp_status_text = _format_mcp_status(tools)
        return {
            "agent": {
                "model_id": model_id,
                "temperature": temperature,
                "max_completion_tokens": max_tokens,
            },
            "mcp_status": mcp_status_text,
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to build status: {e!s}",
        ) from e


def _sse_event(event: str, data: str | dict) -> str:
    """Format one SSE event. data is sent as JSON if dict, else raw string."""
    payload = json.dumps(data) if isinstance(data, dict) else data
    return f"event: {event}\ndata: {payload}\n\n"


def _stream_chat(
    profile: str | None,
    message: str,
    messages: list[dict] | None,
    demo_mode: bool = False,
):
    """Generator yielding SSE events for chat response (progress, message, done, error)."""
    if get_read_only_guardrail_input_enabled() and is_mutating_intent(message):
        yield _sse_event("message", {"content": MESSAGE_INPUT_BLOCKED})
        yield _sse_event("done", {})
        return
    if profile is None:
        yield _sse_event(
            "error",
            {"detail": "No AWS profile available. Set AWS_PROFILE or pass profile in body."},
        )
        yield _sse_event("done", {})
        return

    real_profile = _reverse_demo_profile(profile) if demo_mode else profile

    progress_queue = queue.Queue()
    result_holder = [None, None, None, None]  # reply, usage, artifacts, error
    heartbeat_seconds = 2.5

    def run_agent():
        try:
            reply, usage, artifacts = run_chat_turn(
                real_profile,
                message,
                messages,
                progress_callback=lambda event, tool_name: progress_queue.put((event, tool_name)),
                demo_mode=demo_mode,
            )
            result_holder[0], result_holder[1], result_holder[2] = reply, usage, artifacts
        except Exception as err:
            result_holder[3] = err

    yield _sse_event(
        "progress",
        {"message": "Working on your request…", "phase": "thinking"},
    )
    stream_start = time.monotonic()
    thread = threading.Thread(target=run_agent)
    thread.start()
    last_heartbeat = time.monotonic()
    while thread.is_alive() or not progress_queue.empty():
        try:
            event, tool_name = progress_queue.get(timeout=0.2)
            if event == "phase":
                yield _sse_event(
                    "progress",
                    {"phase": "phase", "message": str(tool_name or "Working...")},
                )
            elif event == "mcp_loading":
                yield _sse_event(
                    "progress",
                    {"phase": "mcp_loading", "message": str(tool_name or "")},
                )
            else:
                yield _sse_event(
                    "progress",
                    {"phase": event, "tool": tool_name},
                )
            last_heartbeat = time.monotonic()
        except queue.Empty:
            if thread.is_alive() and (time.monotonic() - last_heartbeat) >= heartbeat_seconds:
                elapsed = int(time.monotonic() - stream_start)
                yield _sse_event(
                    "progress",
                    {
                        "phase": "heartbeat",
                        "message": f"Still working... {elapsed}s elapsed",
                    },
                )
                last_heartbeat = time.monotonic()
            continue
    thread.join()

    if result_holder[3] is not None:
        yield _sse_event("error", {"detail": str(result_holder[3])})
        yield _sse_event("done", {})
        return
    artifacts = result_holder[2] or []
    for art in artifacts:
        yield _sse_event("artifact", art)
    yield _sse_event("message", {"content": result_holder[0]})
    yield _sse_event("done", {"usage": result_holder[1]} if result_holder[1] else {})


class ChatBody(BaseModel):
    """Request body for POST /chat."""

    message: str
    messages: list[dict] | None = None
    profile: str | None = None


@app.post(
    "/chat",
    responses={
        200: {
            "description": (
                "SSE stream: event `progress` (data: {message?, phase, tool?}), "
                "`message` (data: {content}), `done` (data: {usage?}), `error` (data: {detail})."
            ),
            "content": {"text/event-stream": {}},
        },
    },
)
def post_chat(
    request: Request,
    body: ChatBody,
    profile_from_request: str | None = Depends(resolve_profile),
) -> StreamingResponse:
    """
    Send a message and stream the agent reply as Server-Sent Events.

    **Body:** `message` (required), `messages` (optional list of {role, content} for
    conversation history), `profile` (optional; overrides query/header default).

    **SSE events:**
    - `progress`: data is JSON with message?, phase (thinking|tool_start|tool_end), tool?.
    - `message`: data is JSON `{ "content": "<chunk or full reply>" }`.
    - `done`: data is JSON `{ "usage": { "input_tokens", "output_tokens" } }` when available.
    - `error`: data is JSON `{ "detail": "<error message>" }` on failure.

    Read-only guardrail: if the message is detected as mutating intent, the stream
    returns the same friendly read-only message as the CLI and no tool calls run.

    When X-Demo-Mode: true header is present, the agent uses masked account names.
    """
    profile = (
        body.profile.strip() if body.profile and body.profile.strip() else None
    ) or profile_from_request
    demo_mode = _is_demo_mode(request)
    return StreamingResponse(
        _stream_chat(profile, body.message, body.messages or None, demo_mode=demo_mode),
        media_type="text/event-stream",
    )


@app.get("/{asset_name}", include_in_schema=False, response_model=None)
def get_hosted_webui_root_asset(asset_name: str) -> Response:
    """Serve single-file frontend assets emitted at the web UI root."""
    if "." not in asset_name:
        raise HTTPException(status_code=404, detail="Not found")
    webui_dir = _get_hosted_webui_dir()
    if webui_dir is None:
        raise HTTPException(status_code=404, detail="Hosted frontend assets not found.")
    target = (webui_dir / asset_name).resolve()
    if target.parent != webui_dir.resolve() or not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Frontend asset not found.")
    return FileResponse(target)
