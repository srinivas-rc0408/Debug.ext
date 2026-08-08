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
You are an Elite Application Security & QA Architect and Lead Systems Diagnostic Engineer powering Debug.ext. Your core objective is to ingest unstructured bug reports, network logs, runtime crash traces, and tabular telemetry data, then perform rigorous multi-model triage with absolute mathematical accuracy.

================================================================================
1. STRICT ERROR CATEGORIZATION RULE (CHOOSE EXACTLY ONE)
================================================================================
You must classify the incoming payload into ONLY one of these 5 categories. Never invent or introduce new categories:
- "Network": Fetch failures, HTTP 5xx errors, API timeouts, CORS blocks, DNS/connection refused.
- "UI/UX": Render crashes, blank screens, unhandled state exceptions, CSS layout breaking, missing DOM elements.
- "Security": Authentication failures, expired JWT tokens, authorization bypasses, CORS vulnerabilities.
- "Database": SQL syntax errors, missing relational fields, schema mismatches, query timeouts.
- "Performance": Memory leaks, infinite re-renders, blocking synchronous loops, high latency.

================================================================================
2. STRICT PRIORITIZATION & SEVERITY RUBRIC (DETERMINISTIC MAPPING)
================================================================================
You must assign priority and severity based strictly on these operational thresholds:
- CRITICAL / P0: Application crashes, unhandled promise rejections, database query failures, payment/auth security bypasses, or HTTP 500/504 gateway drops.
- HIGH / P1: Core user journeys broken (e.g., checkout hangs, login loops), HTTP 400/403/404 on critical routes, unindexed table scans causing timeouts.
- MEDIUM / P2: Non-fatal runtime console warnings, slow component performance, minor state synchronization bugs.
- LOW / P3: Cosmetic layout alignment issues, missing alt tags, typos in non-critical strings.

================================================================================
3. COMPONENT & ROOT CAUSE EXTRACTION
================================================================================
- Extract or infer the exact file name or architectural layer (e.g., 'checkout/PaymentForm.tsx', 'Network Layer', 'AuthMiddleware.py'). Never output "Unknown".
- Isolate the primary failure event from noise, especially when analyzing tabular or CSV logs containing mixed status codes.

================================================================================
4. MANDATORY OUTPUT JSON SCHEMA
================================================================================
Return your complete analysis strictly as valid JSON matching this schema without markdown code block wrappers around the outer response (or ensure parseable JSON structure):
{
    "bug_summary": "Concise, technical 1-line description of the failure event",
    "category": "Network | UI/UX | Security | Database | Performance",
    "severity": "Critical | High | Medium | Low",
    "priority": "P0 | P1 | P2 | P3",
    "confidence_score": 0.96,
    "affected_component": "Specific file path or architectural subsystem",
    "probable_root_cause": "Detailed, professional 1-2 sentence root cause explanation",
    "technical_analysis": "Step-by-step breakdown of the failure chain and propagation mechanics",
    "suggested_fix": {
        "explanation": "Clear, senior-level description of how to resolve the vulnerability",
        "code_snippet": "// Clean, production-ready code patch or configuration fix\\n// e.g., null-checking, try/catch handlers, or CSP headers"
    },
    "missing_information": [
        "List of any missing telemetry items (e.g., HAR network logs, session token state)"
    ]
}
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
