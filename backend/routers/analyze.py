"""
Debug.ext — Analysis Router
Orchestrates the multi-model pipeline with aggregator fallback logic.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from models.schemas import (
    BugAnalysisResult,
    BugMetrics,
    BugReportInput,
    SeedPayload,
    SuggestedFix,
)
from services.inkling_service import route_intent, sanitize_input
from services.minimax_service import generate_structural_analysis
from services.glm_service import deep_reasoning_analysis

logger = logging.getLogger("debug_ext.analyze")
router = APIRouter(prefix="/api", tags=["analysis"])

from services import database

# ─── In-Memory Result Store (Deprecated, kept for compatibility if needed) ───

_results_store: List[BugAnalysisResult] = []


def _get_store() -> List[BugAnalysisResult]:
    # Returning DB history to mimic old behavior just in case
    return [BugAnalysisResult(**r["full_analysis"]) for r in database.get_history()]


# ─── Aggregator Logic ─────────────────────────────────────────────────────────


def _has_error(result: Dict[str, Any]) -> bool:
    return "_error" in result


def _merge_results(
    routing: Dict[str, Any],
    minimax_result: Dict[str, Any],
    glm_result: Dict[str, Any],
    sanitized_text: str,
) -> BugAnalysisResult:
    """
    Merge outputs from Inkling routing, MiniMax structural analysis,
    and GLM deep reasoning into a single BugAnalysisResult.

    Fallback strategy:
    - If both succeed → prefer GLM for root cause/analysis, MiniMax for code fixes
    - If GLM fails → use MiniMax + Inkling routing
    - If MiniMax fails → use GLM only
    - If both fail → use Inkling routing hints as best-effort
    """
    glm_ok = not _has_error(glm_result)
    mm_ok = not _has_error(minimax_result)

    model_sources = ["inkling"]
    if glm_ok:
        model_sources.append("glm_5.2")
    if mm_ok:
        model_sources.append("minimax_m3")

    # ── Category / Severity / Priority — always from Inkling routing ───────
    category = routing.get("category", "Backend API")
    severity = routing.get("severity", "Medium")
    priority = routing.get("priority", "P2")
    summary = routing.get("summary", "Bug report analyzed")

    # ── Root Cause & Technical Analysis ────────────────────────────────────
    if glm_ok:
        root_cause = glm_result.get("probable_root_cause", "Analysis pending.")
        tech_analysis = glm_result.get("technical_analysis", "")
        missing_info = glm_result.get("missing_information", [])
    elif mm_ok:
        root_cause = minimax_result.get(
            "technical_analysis_snippet", "Structural analysis only — deep reasoning unavailable."
        )
        tech_analysis = root_cause
        missing_info = ["Deep reasoning model was unavailable — root cause may be incomplete."]
    else:
        root_cause = "All analysis models were unavailable. Manual review required."
        tech_analysis = "Unable to perform automated analysis."
        missing_info = [
            "GLM 5.2 deep reasoning failed.",
            "MiniMax M3 structural analysis failed.",
            "Manual investigation recommended.",
        ]

    # ── Suggested Fix & Component ──────────────────────────────────────────
    if mm_ok:
        fix_data = minimax_result.get("suggested_fix", {})
        component = minimax_result.get("affected_component", "Unknown")
    elif glm_ok:
        fix_data = glm_result.get("suggested_fix", {})
        component = glm_result.get("affected_component", "Unknown")
    else:
        fix_data = {"explanation": "Automated fix unavailable.", "code_snippet": ""}
        component = "Unknown"

    suggested_fix = SuggestedFix(
        explanation=fix_data.get("explanation", ""),
        code_snippet=fix_data.get("code_snippet", ""),
    )

    # ── Confidence Score — average of available models ─────────────────────
    scores = []
    if glm_ok and "confidence_score" in glm_result:
        scores.append(float(glm_result["confidence_score"]))
    if mm_ok and "confidence_score" in minimax_result:
        scores.append(float(minimax_result["confidence_score"]))
    confidence = sum(scores) / len(scores) if scores else 0.3

    # ── Metrics — prefer GLM, fallback to MiniMax ──────────────────────────
    metrics_src = {}
    if glm_ok and "metrics" in glm_result:
        metrics_src = glm_result["metrics"]
    elif mm_ok and "metrics" in minimax_result:
        metrics_src = minimax_result["metrics"]

    metrics = BugMetrics(
        estimated_fix_time_hours=float(metrics_src.get("estimated_fix_time_hours", 2.0)),
        business_impact_score=min(10.0, max(1.0, float(metrics_src.get("business_impact_score", 5.0)))),
        reproducibility_probability=min(1.0, max(0.0, float(metrics_src.get("reproducibility_probability", 0.5)))),
    )

    return BugAnalysisResult(
        bug_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        bug_summary=summary,
        category=category,
        severity=severity,
        priority=priority,
        confidence_score=round(confidence, 3),
        affected_component=component,
        probable_root_cause=root_cause,
        technical_analysis=tech_analysis,
        suggested_fix=suggested_fix,
        missing_information=missing_info,
        metrics=metrics,
        model_sources=model_sources,
        raw_input_preview=sanitized_text[:500],
    )


# ─── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/analyze", response_model=BugAnalysisResult)
async def analyze_bug(report: BugReportInput):
    """
    Main analysis endpoint.
    1. Sanitize input via Inkling
    2. Route intent
    3. Fan out to MiniMax + GLM concurrently
    4. Merge with fallback logic
    """
    logger.info("Received bug report for URL: %s", report.url)

    # Step 1: Sanitize
    sanitized = sanitize_input(report)

    # Step 2: Route intent via Inkling
    routing = await route_intent(sanitized)
    logger.info("Routing decision: %s", routing.get("routing", "both"))

    # Step 3: Determine which models to call based on routing
    route_type = routing.get("routing", "both")

    if route_type == "structural":
        # Only structural analysis needed
        mm_result = await generate_structural_analysis(sanitized, routing)
        glm_result = {"_source": "glm_5.2", "_error": "skipped_by_routing"}
    elif route_type == "deep_reasoning":
        # Only deep reasoning needed
        glm_result = await deep_reasoning_analysis(sanitized, routing)
        mm_result = {"_source": "minimax_m3", "_error": "skipped_by_routing"}
    else:
        # Both — fan out concurrently
        mm_result, glm_result = await asyncio.gather(
            generate_structural_analysis(sanitized, routing),
            deep_reasoning_analysis(sanitized, routing),
            return_exceptions=False,
        )
        # If gather returned exceptions as results, wrap them
        if isinstance(mm_result, Exception):
            mm_result = {"_source": "minimax_m3", "_error": str(mm_result)}
        if isinstance(glm_result, Exception):
            glm_result = {"_source": "glm_5.2", "_error": str(glm_result)}

    # Step 4: Merge
    result = _merge_results(routing, mm_result, glm_result, sanitized)

    # Step 5: Store
    database.insert_result(result.model_dump(), report.url, report.source)
    logger.info(
        "Analysis complete: %s [%s/%s] — models: %s",
        result.bug_id,
        result.severity,
        result.priority,
        ", ".join(result.model_sources),
    )

    return result


@router.get("/results")
async def get_results():
    """Return all stored analysis results for the dashboard."""
    return [r["full_analysis"] for r in database.get_history()]


@router.get("/history")
async def get_history():
    """Fetch all records from bug_history ordered by timestamp descending."""
    return database.get_history()


@router.post("/results/seed")
async def seed_results(payload: SeedPayload):
    """
    Seed endpoint for demo runner — bulk-insert pre-analyzed results.
    """
    count = len(payload.results)
    for res in payload.results:
        database.insert_result(res.model_dump(), "Seed", "demo_runner")
    logger.info("Seeded %d bug analysis results to SQLite", count)
    return {"status": "ok", "seeded": count, "total": database.get_history_count()}


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Debug.ext Backend",
        "results_count": database.get_history_count(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
