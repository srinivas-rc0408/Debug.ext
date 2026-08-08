"""
Debug.ext — GLM 5.2 Service
Deep reasoning engine: root-cause analysis, weighted confidence scoring,
missing-information detection, and business-impact assessment.

CONFIDENCE SCORE CALCULATION RULES:
- Full stack trace + request body + URL present: confidence_score >= 0.90
- Partial console log without stack trace: confidence_score between 0.70 and 0.85
- Vague single-sentence report: confidence_score <= 0.60
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict

from openai import OpenAI

logger = logging.getLogger("debug_ext.glm")

# ─── Config ────────────────────────────────────────────────────────────────────

_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
_API_KEY = os.getenv("NVIDIA_API_KEY_GLM", "")
_MODEL = os.getenv("GLM_MODEL", "z-ai/glm-5.2")
_TIMEOUT = 60  # seconds — deep reasoning can take time


def _get_client() -> OpenAI:
    return OpenAI(base_url=_BASE_URL, api_key=_API_KEY, timeout=_TIMEOUT)


# ─── Weighted Confidence Algorithm ─────────────────────────────────────────────

def calculate_weighted_confidence(raw_report: str) -> float:
    """
    Calculate a pre-evaluation confidence score based on evidence density.
    This is sent as a hint to the LLM and used as a floor for the response.
    """
    score = 0.50  # Base confidence

    # Stack trace present (+0.20)
    if any(kw in raw_report.lower() for kw in ['stack', 'traceback', 'at ', '.js:', '.ts:', '.py:']):
        score += 0.20

    # Request body / payload captured (+0.10)
    if any(kw in raw_report.lower() for kw in ['body:', 'payload:', 'request body', '"method"', '"url"']):
        score += 0.10

    # HTTP status code present (+0.05)
    if re.search(r'(HTTP\s*)?\d{3}', raw_report):
        score += 0.05

    # URL / endpoint captured (+0.05)
    if re.search(r'https?://|/api/', raw_report):
        score += 0.05

    # Console error / DOM context (+0.05)
    if any(kw in raw_report.lower() for kw in ['console.error', 'uncaught', 'unhandled', 'dom', 'viewport']):
        score += 0.05

    # Reproduction steps / click history (+0.05)
    if any(kw in raw_report.lower() for kw in ['clicked', 'step', 'interaction', 'button']):
        score += 0.05

    return min(score, 0.99)  # Cap at 0.99


# ─── Deep Reasoning Prompt ─────────────────────────────────────────────────────

_DEEP_REASONING_SYSTEM_PROMPT = """\
You are an Elite Application Security & QA Architect. Your job is to analyze unstructured bug reports, network logs, and crash traces, converting them into strict, highly accurate JSON.

CRITICAL PARSING RULE:
If the input appears to be CSV (Comma Separated Values) or tabular log data, scan all rows for the most severe HTTP status code (e.g., 500, 403, 404) or the most critical stack trace. Isolate the primary failure event from the noise and base your triage solely on that event.

PRIORITIZATION & SEVERITY RUBRIC (STRICT ENFORCEMENT):
- CRITICAL / P0: Application crashes, unhandled exceptions, database failures, Payment/Auth bypasses, or Network HTTP 500s.
- HIGH / P1: Core feature is broken (e.g., login fails, checkout hangs) but the app hasn't completely crashed. HTTP 400s.
- MEDIUM / P2: UI bugs, slow performance (timeouts), non-fatal console errors.
- LOW / P3: Typos, minor cosmetic alignment issues, missing titles.

COMPONENT IDENTIFICATION (NO "UNKNOWN" ALLOWED):
If the exact file name (e.g., `PaymentForm.tsx`) is missing in the trace, you MUST infer the architectural layer based on the context. 
Examples: "Frontend UI Layer", "Authentication Router", "Database Schema", "Third-Party API Integration". Never output "Unknown".

CONFIDENCE SCORING ALGORITHM:
- 0.90 to 0.99: A full stack trace or exact API endpoint is provided.
- 0.70 to 0.89: Good description, but missing the exact line number or payload.
- 0.50 to 0.69: Vague manual user report (e.g., "The page is blank").

Output strictly in this JSON schema:
{
    "bug_summary": "1-line concise technical summary",
    "category": "UI/UX|Authentication|Backend API|Database|Performance|Payment|Security",
    "severity": "Critical|High|Medium|Low",
    "priority": "P0|P1|P2|P3",
    "confidence_score": 0.95,
    "affected_component": "Inferred architectural layer or specific file",
    "probable_root_cause": "Detailed root cause",
    "technical_analysis": "Step-by-step breakdown",
    "suggested_fix": {"explanation": "Fix steps", "code_snippet": "code"},
    "missing_information": ["Missing QA details"],
    "metrics": {
      "estimated_fix_time_hours": 2.0,
      "business_impact_score": 8.5,
      "reproducibility_probability": 0.90
    }
}

DO NOT RETURN MARKDOWN CODE BLOCKS. RETURN RAW JSON ONLY.
"""


async def deep_reasoning_analysis(
    sanitized_text: str,
    routing_hints: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Invoke GLM 5.2 for deep reasoning on complex error traces.
    Evaluates root cause, identifies missing parameters, and scores business impact.
    Uses weighted confidence as a floor for the LLM's confidence assessment.
    """

    # Pre-calculate evidence-based confidence floor
    confidence_floor = calculate_weighted_confidence(sanitized_text)

    user_prompt = (
        f"Classification hints: {json.dumps(routing_hints)}\n"
        f"Evidence-based confidence floor: {confidence_floor:.2f}\n\n"
        f"Bug Report:\n{sanitized_text}"
    )

    try:
        client = _get_client()
        completion = client.chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": _DEEP_REASONING_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,  # Low temperature for precise, deterministic analysis
            top_p=1,
            max_tokens=8192,
            seed=42,
            stream=False,
        )

        raw_content = completion.choices[0].message.content.strip()

        # Parse JSON — handle markdown code fences if returned despite instructions
        if raw_content.startswith("```json"):
            raw_content = raw_content[7:]
            if raw_content.endswith("```"):
                raw_content = raw_content[:-3]
            raw_content = raw_content.strip()
        elif raw_content.startswith("```"):
            raw_content = raw_content[3:]
            if raw_content.endswith("```"):
                raw_content = raw_content[:-3]
            raw_content = raw_content.strip()

        json_match = re.search(r"\{.*\}", raw_content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(raw_content)

        # Enforce confidence floor — LLM should not undervalue well-documented reports
        if result.get("confidence_score", 0) < confidence_floor:
            result["confidence_score"] = confidence_floor

        result["_source"] = "glm_5.2"
        result["_confidence_floor"] = confidence_floor
        logger.info(
            "GLM deep reasoning complete — root cause length: %d chars, "
            "confidence: %.2f (floor: %.2f), missing info items: %d",
            len(result.get("probable_root_cause", "")),
            result.get("confidence_score", 0),
            confidence_floor,
            len(result.get("missing_information", [])),
        )
        return result

    except Exception as exc:
        logger.error("GLM 5.2 deep_reasoning_analysis failed: %s", exc, exc_info=True)
        return {"_source": "glm_5.2", "_error": str(exc)}
