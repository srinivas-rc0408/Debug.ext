"""
Debug.ext — Pydantic Schema Definitions
Structured models for bug analysis pipeline I/O.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ─── Input Models ──────────────────────────────────────────────────────────────

class BugReportInput(BaseModel):
    """Raw payload received from the Chrome extension."""
    url: str = Field(..., description="Page URL where the error occurred")
    dom_title: str = Field("", description="Document title of the page")
    user_agent: str = Field("", description="Browser User-Agent string")
    console_logs: List[str] = Field(
        default_factory=list,
        description="Last N console log entries captured by content script",
    )
    highlighted_text: str = Field(
        "",
        description="Text the user had selected on the page, if any",
    )
    active_element_html: str = Field(
        "",
        description="outerHTML of the currently focused DOM element",
    )
    raw_error: str = Field(
        "",
        description="The primary error message or stack trace",
    )
    additional_context: str = Field(
        "",
        description="Any extra context supplied by the user",
    )
    source: str = Field(
        "extension",
        description="Source of the bug report",
    )
    raw_report: str = Field(
        "",
        description="Raw report text from manual upload",
    )


# ─── Output Sub-models ────────────────────────────────────────────────────────

class SuggestedFix(BaseModel):
    explanation: str = Field(..., description="Human-readable explanation of the fix")
    code_snippet: str = Field("", description="Suggested code patch")


class BugMetrics(BaseModel):
    estimated_fix_time_hours: float = Field(
        1.0, ge=0, description="Estimated developer-hours to resolve"
    )
    business_impact_score: float = Field(
        5.0, ge=1, le=10, description="1 (negligible) – 10 (catastrophic)"
    )
    reproducibility_probability: float = Field(
        0.5, ge=0, le=1, description="Likelihood the bug can be reproduced"
    )


# ─── Primary Result Model ─────────────────────────────────────────────────────

BUG_CATEGORIES = Literal[
    "UI/UX",
    "Authentication",
    "Backend API",
    "Database",
    "Performance",
    "Payment",
    "Security",
    "State Management",
]

SEVERITY_LEVELS = Literal["Critical", "High", "Medium", "Low"]

PRIORITY_LEVELS = Literal["P0", "P1", "P2", "P3"]


class BugAnalysisResult(BaseModel):
    """
    Canonical structured output produced by the multi-model analysis pipeline.
    Every API response and dashboard record conforms to this schema.
    """
    bug_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier (UUID v4)",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 timestamp of analysis",
    )
    bug_summary: str = Field(..., description="One-line human-readable summary")
    category: BUG_CATEGORIES = Field(..., description="Bug classification bucket")
    severity: SEVERITY_LEVELS = Field(..., description="Impact severity level")
    priority: PRIORITY_LEVELS = Field(..., description="Triage priority")
    confidence_score: float = Field(
        0.5, ge=0.0, le=1.0, description="Model confidence in analysis accuracy"
    )
    affected_component: str = Field(
        ..., description="Module / service / component affected"
    )
    probable_root_cause: str = Field(
        ..., description="Most likely root cause explanation"
    )
    technical_analysis: str = Field(
        ..., description="Detailed technical breakdown"
    )
    suggested_fix: SuggestedFix = Field(
        ..., description="Recommended fix with optional code"
    )
    missing_information: List[str] = Field(
        default_factory=list,
        description="Info the reporter should supply for a complete diagnosis",
    )
    metrics: BugMetrics = Field(
        default_factory=BugMetrics,
        description="Quantitative triage metrics",
    )

    # ── Provenance ─────────────────────────────────────────────────────────
    model_sources: List[str] = Field(
        default_factory=list,
        description="Which AI models contributed to this analysis",
    )
    raw_input_preview: Optional[str] = Field(
        None,
        description="Truncated copy of the raw input for dashboard side-by-side view",
    )


# ─── Seeding / Bulk Import ─────────────────────────────────────────────────────

class SeedPayload(BaseModel):
    """Used by the demo runner to pre-populate the result store."""
    results: List[BugAnalysisResult]
