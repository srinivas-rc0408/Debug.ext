"""
Debug.ext — MiniMax M3 Service
Rapid structural analysis: code snippets, component mapping, and quick-fix generation.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict

import requests

logger = logging.getLogger("debug_ext.minimax")

# ─── Config ────────────────────────────────────────────────────────────────────

_INVOKE_URL = os.getenv(
    "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"
) + "/chat/completions"

_API_KEY = os.getenv("NVIDIA_API_KEY_MINIMAX", "")
_MODEL = os.getenv("MINIMAX_MODEL", "minimaxai/minimax-m3")
_TIMEOUT = 30  # seconds


# ─── Analysis Prompt ───────────────────────────────────────────────────────────

_STRUCTURAL_SYSTEM_PROMPT = """\
You are a senior frontend/backend engineer specializing in rapid bug patching.
Given a sanitized bug report with classification hints, produce a structural analysis.

Respond ONLY with valid JSON matching this schema:
{
  "affected_component": "<string — e.g. 'checkout/PaymentForm.tsx'>",
  "suggested_fix": {
    "explanation": "<string — clear explanation of the fix>",
    "code_snippet": "<string — corrected code>"
  },
  "confidence_score": <float 0-1>,
  "technical_analysis_snippet": "<string — brief technical analysis of the structural issue>",
  "metrics": {
    "estimated_fix_time_hours": <float>,
    "business_impact_score": <float 1-10>,
    "reproducibility_probability": <float 0-1>
  }
}
"""


async def generate_structural_analysis(
    sanitized_text: str,
    routing_hints: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Call MiniMax M3 for fast structural analysis, code snippet generation,
    and affected-component mapping.
    """
    user_prompt = (
        f"Classification hints: {json.dumps(routing_hints)}\n\n"
        f"Bug Report:\n{sanitized_text}"
    )

    headers = {
        "Authorization": f"Bearer {_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    payload = {
        "model": _MODEL,
        "messages": [
            {"role": "system", "content": _STRUCTURAL_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.4,
        "top_p": 0.95,
        "max_tokens": 4096,
        "stream": False,
    }

    try:
        response = requests.post(
            _INVOKE_URL,
            headers=headers,
            json=payload,
            timeout=_TIMEOUT,
        )
        response.raise_for_status()

        data = response.json()
        raw_content = data["choices"][0]["message"]["content"].strip()

        # Parse JSON from response
        json_match = re.search(r"\{.*\}", raw_content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(raw_content)

        result["_source"] = "minimax_m3"
        logger.info(
            "MiniMax structural analysis complete — component: %s, confidence: %.2f",
            result.get("affected_component", "?"),
            result.get("confidence_score", 0),
        )
        return result

    except requests.exceptions.Timeout:
        logger.warning("MiniMax M3 request timed out after %ds", _TIMEOUT)
        return {"_source": "minimax_m3", "_error": "timeout"}

    except Exception as exc:
        logger.error("MiniMax M3 failed: %s", exc, exc_info=True)
        return {"_source": "minimax_m3", "_error": str(exc)}
