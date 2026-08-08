"""
Debug.ext — Inkling Service
Handles input sanitization and intent routing via the Inkling model.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict

from openai import OpenAI

from models.schemas import BugReportInput

logger = logging.getLogger("debug_ext.inkling")

# ─── Client Setup ──────────────────────────────────────────────────────────────

_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
_API_KEY = os.getenv("NVIDIA_API_KEY_INKLING", "")
_MODEL = os.getenv("INKLING_MODEL", "thinkingmachines/inkling")


def _get_client() -> OpenAI:
    return OpenAI(base_url=_BASE_URL, api_key=_API_KEY)


# ─── PII / Size Sanitization ──────────────────────────────────────────────────

_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_JWT_RE = re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")
_PHONE_RE = re.compile(r"\+?\d[\d\s\-()]{7,}\d")
_IP_RE = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")

MAX_DOM_CHARS = 4000
MAX_CONSOLE_ENTRIES = 10


def sanitize_input(raw: BugReportInput) -> str:
    """
    Strip PII, truncate large DOM fragments, and format the payload
    into a single text block suitable for LLM consumption.
    """
    def _scrub(text: str) -> str:
        text = _EMAIL_RE.sub("[EMAIL_REDACTED]", text)
        text = _JWT_RE.sub("[JWT_REDACTED]", text)
        text = _PHONE_RE.sub("[PHONE_REDACTED]", text)
        text = _IP_RE.sub("[IP_REDACTED]", text)
        return text

    url = _scrub(raw.url)
    title = _scrub(raw.dom_title)
    ua = raw.user_agent
    logs = [_scrub(l) for l in raw.console_logs[-MAX_CONSOLE_ENTRIES:]]
    highlighted = _scrub(raw.highlighted_text)[:MAX_DOM_CHARS]
    active_el = _scrub(raw.active_element_html)[:MAX_DOM_CHARS]
    error = _scrub(raw.raw_error or raw.raw_report)
    context = _scrub(raw.additional_context)

    parts = [
        f"URL: {url}",
        f"Page Title: {title}",
        f"User-Agent: {ua}",
        f"Error: {error}",
    ]
    if logs:
        parts.append("Console Logs (recent):\n" + "\n".join(f"  • {l}" for l in logs))
    if highlighted:
        parts.append(f"Highlighted Text: {highlighted}")
    if active_el:
        parts.append(f"Active Element HTML:\n{active_el}")
    if context:
        parts.append(f"Additional Context: {context}")

    return "\n\n".join(parts)


# ─── Intent Routing via Inkling ────────────────────────────────────────────────

_ROUTING_SYSTEM_PROMPT = """\
You are an expert bug triage assistant. Given a sanitized bug report, perform the following:
1. Classify the bug into EXACTLY ONE category from: UI/UX, Authentication, Backend API, Database, Performance, Payment, Security, State Management.
2. Estimate severity (Critical, High, Medium, Low).
3. Estimate priority (P0, P1, P2, P3).
4. Provide a brief 1-sentence summary of the bug.
5. Identify which downstream analysis approach is best:
   - "structural" for issues solvable with quick code patches (UI glitches, typos, missing null checks).
   - "deep_reasoning" for complex issues requiring root-cause investigation (race conditions, auth flows, performance).
   - "both" when unsure.

Respond ONLY with valid JSON matching this schema:
{
  "category": "<string>",
  "severity": "<string>",
  "priority": "<string>",
  "summary": "<string>",
  "routing": "<structural|deep_reasoning|both>"
}
"""


async def route_intent(sanitized_text: str) -> Dict[str, Any]:
    """
    Call Inkling to classify the bug and decide which downstream models to invoke.
    Returns a dict with category, severity, priority, summary, and routing hint.
    """
    try:
        client = _get_client()
        completion = client.chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": _ROUTING_SYSTEM_PROMPT},
                {"role": "user", "content": sanitized_text},
            ],
            temperature=0.3,
            top_p=0.95,
            max_tokens=1024,
            stream=False,
        )

        raw_content = completion.choices[0].message.content.strip()

        # Try to extract JSON from the response (handle markdown code blocks)
        json_match = re.search(r"\{.*\}", raw_content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(raw_content)

        # Validate expected keys
        expected_keys = {"category", "severity", "priority", "summary", "routing"}
        for key in expected_keys:
            if key not in result:
                result[key] = _DEFAULTS.get(key, "unknown")

        logger.info("Inkling routing: %s → %s", result.get("category"), result.get("routing"))
        return result

    except Exception as exc:
        logger.error("Inkling route_intent failed: %s", exc, exc_info=True)
        return {
            "category": "Backend API",
            "severity": "Medium",
            "priority": "P2",
            "summary": "Bug report received — Inkling classification unavailable.",
            "routing": "both",
            "error": str(exc),
        }


_DEFAULTS = {
    "category": "Backend API",
    "severity": "Medium",
    "priority": "P2",
    "summary": "Unclassified bug report",
    "routing": "both",
}
