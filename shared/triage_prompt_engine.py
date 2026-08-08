from __future__ import annotations

import json
import logging
import os
import time
from typing import Literal, Optional

from anthropic import Anthropic, APIError, APIStatusError
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger("debug_ext.triage_engine")

# ---------------------------------------------------------------------------
# 1. TAXONOMY & PRIORITY RUBRIC — the "deterministic" part of the matrix.
#    This is prose injected into the system prompt, not just a comment here.
# ---------------------------------------------------------------------------

TAXONOMY_RULES = """
CATEGORY TAXONOMY (choose exactly one — never invent a category outside this list):
- Network      : DNS, CDN, CSP blocks, timeouts, connection refused, offline/retry failures
                 that are NOT on a revenue-critical checkout/payment path.
- UI/UX        : rendering, state, layout, accessibility, broken interaction — no data loss,
                 no revenue impact.
- Security     : auth bypass, XSS, CSRF, exposed secrets, injection, privilege escalation.
- Database     : query failure, migration error, constraint violation, connection pool
                 exhaustion, data corruption.
- Performance  : latency regression, memory leak, N+1 queries, unoptimized render loop —
                 functionally correct but too slow.
- Payment      : ANY failure inside the checkout/payment/billing flow, regardless of the
                 underlying technical cause. Payment always wins the category assignment
                 over Network/UI/UX/Database/Performance when the failure blocks a paying
                 user from completing a transaction. State the true technical mechanism
                 (e.g. "root cause is a Network/CSP failure") inside root_cause_analysis —
                 the category field itself stays "Payment" so the triage matrix routes it
                 to the correct on-call rotation and financial-impact reporting.

PRIORITY RUBRIC (apply the highest-matching tier — do not average):
- P0 (Critical): Revenue-blocking or security-critical, affecting production users right
                 now, no viable workaround. Payment-category incidents are P0 by default
                 unless the failure rate is below 1% AND a working retry path exists.
- P1 (High)    : Major feature broken for a significant user segment; a workaround exists
                 but is painful or undocumented.
- P2 (Medium)  : Degraded experience, isolated feature failure, easy workaround, small
                 blast radius (<5% of sessions).
- P3 (Low)     : Cosmetic or edge-case only, no material user or revenue impact.

CONFIDENCE SCORE (0-100):
Your self-assessed probability that root_cause_analysis is the TRUE root cause given the
telemetry provided — not a vague "how sure do I feel" number.
- 90-100: root cause is directly observable in the provided stack trace / logs.
- 70-89 : root cause is the single most plausible explanation but relies on one inference
          not directly proven by the log (e.g. inferring a CSP change from a blocked
          request without seeing the CSP diff itself).
- Below 70: multiple plausible root causes exist and you are choosing the most likely one.
          You MUST say so explicitly in root_cause_analysis and name the runner-up cause.
"""

# ---------------------------------------------------------------------------
# 2. SYSTEM PROMPT — the "complete prompt" you asked for.
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = f"""You are the Debug.ext Autonomous Triage Engine: a fusion of a Principal
Site Reliability Engineer, a Staff Security Engineer, and a Staff Software Architect with
15+ years shipping production fixes at high-scale companies. You are embedded in a live
QA/engineering pipeline. Engineers will copy your code_patch directly into a production
codebase and your solution_summary directly into an incident postmortem. There is no human
editing pass between your output and either destination. Treat every field as a final,
customer-facing deliverable, not a draft.

You will be given raw, possibly messy input: a browser console error, a stack trace, a
server log excerpt, or an unstructured QA report. Do the following, in order, before you
answer:

1. Identify the exact failing line, function, or request from the raw input. If the input
   truncates or omits information you'd need to be certain, say so — do not silently
   assume.
2. Reconstruct the full failure chain from first triggering event to the observed
   exception/symptom. Every step in technical_execution_breakdown must be a concrete,
   falsifiable claim (a specific function call, a specific state value, a specific HTTP
   status) — never a vague gesture like "something goes wrong in the network layer."
3. Assign category and priority using the rules below. These are deterministic rules, not
   suggestions — do not override them with your own judgment about what "feels" more
   important.
4. Write a solution that fixes the ROOT cause, not just the symptom. A null-check that
   silences a TypeError without fixing why the dependency was null is an incomplete
   solution and will be rejected.

{TAXONOMY_RULES}

CODE PATCH REQUIREMENTS (this is the field most likely to break downstream — follow
exactly):
- The code must be COMPLETE and directly copy-pasteable. Never write "// ... rest unchanged"
  or "// existing code here" as a substitute for actual code. If you are patching one
  function inside a larger file, reproduce that ENTIRE function, correctly closed with
  matching braces/indentation — not a fragment.
- Match the language and framework conventions visible in the input (e.g. if the input is
  a React class component, patch it as a React class component — do not rewrite it as
  hooks unless asked).
- Every error path you introduce (null checks, try/catch) must set a concrete UI-facing
  state, not just log to console — "fail silently" is not an acceptable patch.
- Include one inline comment at the exact line that was broken, explaining what was wrong,
  and one inline comment at the fix, explaining why it resolves the root cause.

OUTPUT DISCIPLINE:
- Call the `submit_triage_report` tool exactly once, with every field populated per its
  description. Do not leave any field empty, null, or a placeholder — if genuinely
  unknown, state the specific uncertainty in prose instead of omitting the field.
- Do not include markdown code fences inside the `code` field of code_patch — that field
  is raw source code only, since it is rendered directly into both a monospace PDF block
  and a syntax-highlighted dashboard widget. Fences would corrupt both.
- qa_checklist must contain concrete, executable verification steps a QA engineer could
  actually run (e.g. "Throttle network to 'Offline' in DevTools, click Pay Now, confirm
  the error banner reads 'Payment system is temporarily unavailable' and the button
  re-enables within 1s") — not generic advice like "test thoroughly."

CALIBRATION EXAMPLE (match this depth and specificity, not this exact wording):
Input: a checkout page throws `TypeError: Cannot read properties of undefined
(reading 'id')` at PaymentForm.tsx:142, Stripe SDK request shows
ERR_CONNECTION_REFUSED in the network tab, retried 3x automatically, ~30% of
sessions affected.
Expected quality bar: category="Payment", priority="P0", confidence=92,
root_cause_analysis identifies the CSP/network block preventing SDK load AND the
missing null-guard as a compounding secondary bug, technical_execution_breakdown
lists the failure chain as 5 discrete numbered steps from CDN request to the
TypeError, code_patch is a complete handleSubmit() method with a null-guard,
optional chaining, and user-facing error state, qa_checklist includes at least
one step that reproduces the original failure and one that confirms the fix.
"""

# ---------------------------------------------------------------------------
# 3. FORCED OUTPUT SCHEMA — Claude tool-use, not "please output JSON."
#    Forcing tool_choice guarantees structurally valid, complete output.
#    This is what actually fixes "the solution part goes missing."
# ---------------------------------------------------------------------------

TRIAGE_TOOL = {
    "name": "submit_triage_report",
    "description": (
        "Submit the completed P0-P3 triage report for this incident. Every field is "
        "required and consumed verbatim by both the PDF report generator and the "
        "Streamlit dashboard — do not omit or abbreviate any field."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": ["Network", "UI/UX", "Security", "Database", "Performance", "Payment"],
                "description": "Exactly one taxonomy class. See TAXONOMY_RULES in the system prompt.",
            },
            "priority": {
                "type": "string",
                "enum": ["P0", "P1", "P2", "P3"],
                "description": "Per the priority rubric — highest matching tier, not an average.",
            },
            "confidence": {
                "type": "integer",
                "minimum": 0,
                "maximum": 100,
                "description": "Self-assessed probability the stated root cause is correct.",
            },
            "incident_summary": {
                "type": "string",
                "description": (
                    "One sentence, <25 words: what broke and where, in plain language a "
                    "non-engineer on-call manager would understand."
                ),
            },
            "root_cause_analysis": {
                "type": "string",
                "description": (
                    "2-4 sentence paragraph. The true underlying cause, not just the "
                    "symptom. If confidence < 70, explicitly name the runner-up hypothesis."
                ),
            },
            "technical_execution_breakdown": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 3,
                "maxItems": 8,
                "description": (
                    "Ordered list of concrete, falsifiable steps from trigger to observed "
                    "symptom. Each item is one step, written as a complete sentence, no "
                    "numbering prefix (the renderer numbers them)."
                ),
            },
            "solution_summary": {
                "type": "string",
                "description": "1-3 sentence paragraph describing the fix strategy, before the code.",
            },
            "code_patch": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "e.g. PaymentForm.tsx"},
                    "language": {"type": "string", "description": "e.g. typescript, python, sql"},
                    "code": {
                        "type": "string",
                        "description": "Complete, copy-pasteable code. No markdown fences. No truncation.",
                    },
                },
                "required": ["filename", "language", "code"],
            },
            "config_notes": {
                "type": ["string", "null"],
                "description": (
                    "Optional: non-code config/infra changes needed alongside the patch "
                    "(e.g. a CSP header line). Null if none."
                ),
            },
            "qa_checklist": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 3,
                "maxItems": 6,
                "description": "Concrete, executable verification steps — see OUTPUT DISCIPLINE.",
            },
        },
        "required": [
            "category",
            "priority",
            "confidence",
            "incident_summary",
            "root_cause_analysis",
            "technical_execution_breakdown",
            "solution_summary",
            "code_patch",
            "config_notes",
            "qa_checklist",
        ],
    },
}

# ---------------------------------------------------------------------------
# 4. PYDANTIC MODEL — second, independent validation layer before rendering.
#    Tool-use schemas guarantee *shape*; this guarantees your app never
#    renders a report with e.g. an empty code string.
# ---------------------------------------------------------------------------


class CodePatch(BaseModel):
    filename: str = Field(min_length=1)
    language: str = Field(min_length=1)
    code: str = Field(min_length=1)


class TriageReport(BaseModel):
    category: Literal["Network", "UI/UX", "Security", "Database", "Performance", "Payment"]
    priority: Literal["P0", "P1", "P2", "P3"]
    confidence: int = Field(ge=0, le=100)
    incident_summary: str = Field(min_length=1)
    root_cause_analysis: str = Field(min_length=1)
    technical_execution_breakdown: list[str] = Field(min_length=3)
    solution_summary: str = Field(min_length=1)
    code_patch: CodePatch
    config_notes: Optional[str] = None
    qa_checklist: list[str] = Field(min_length=3)


# ---------------------------------------------------------------------------
# 5. LLM CALL — with the retry/fallback resilience your brief already
#    promises ("httpx connection error fallbacks... guarantee uptime").
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "claude-3-5-sonnet-20241022"  # strong coding/reasoning, good cost/latency for P1-P3 volume
ESCALATION_MODEL = "claude-3-5-sonnet-20241022"  # use for P0 payment/security incidents if you want max rigor


def build_user_prompt(raw_error_log: str, source_context: Optional[str] = None) -> str:
    """Wrap the raw telemetry the extension captured into the user turn."""
    parts = [
        "Triage the following captured incident telemetry.",
        "",
        "RAW TELEMETRY:",
        "```",
        raw_error_log.strip(),
        "```",
    ]
    if source_context:
        parts += ["", f"ADDITIONAL CONTEXT: {source_context.strip()}"]
    return "\n".join(parts)


def run_triage(
    raw_error_log: str,
    source_context: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    max_retries: int = 2,
) -> TriageReport:
    """
    Single source of truth: call Claude once, get back a validated TriageReport.
    Both pdf_generator_patch.generate_triage_pdf() and
    dashboard_spotlight_patch.render_active_incident_spotlight() take this
    exact object as input — that's what keeps the two surfaces in sync.
    """
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", "your-api-key"))
    user_prompt = build_user_prompt(raw_error_log, source_context)

    last_error: Optional[Exception] = None
    for attempt in range(1, max_retries + 2):  # e.g. max_retries=2 -> 3 total attempts
        try:
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=[TRIAGE_TOOL],
                tool_choice={"type": "tool", "name": "submit_triage_report"},
                messages=[{"role": "user", "content": user_prompt}],
            )
            tool_use_block = next(
                (block for block in response.content if block.type == "tool_use"), None
            )
            if tool_use_block is None:
                raise ValueError("Model returned no tool_use block — cannot parse triage report.")

            report = TriageReport.model_validate(tool_use_block.input)
            logger.info(
                "Triage OK: category=%s priority=%s confidence=%d attempt=%d",
                report.category, report.priority, report.confidence, attempt,
            )
            return report

        except (ValidationError, ValueError) as e:
            last_error = e
            logger.warning("Triage validation failed on attempt %d: %s", attempt, e)
            user_prompt += (
                "\n\nYour previous submission was rejected by schema validation: "
                f"{e}. Resubmit with every field fully populated — no empty strings, "
                "no placeholder text."
            )
            continue

        except (APIStatusError, APIError) as e:
            last_error = e
            logger.warning("Anthropic API error on attempt %d: %s", attempt, e)
            time.sleep(min(2 ** attempt, 8))
            continue

    raise RuntimeError(
        f"Triage generation failed after {max_retries + 1} attempts: {last_error}"
    ) from last_error

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample_log = (
        "TypeError: Cannot read properties of undefined (reading 'id') "
        "at PaymentForm.handleSubmit (checkout.js:142)\n"
        "Network: GET https://js.stripe.com/v3/ net::ERR_CONNECTION_REFUSED "
        "(retried 3x, all failed)\n"
        "Affected sessions: ~30% over last 15 minutes\n"
        "UI state: button stuck on 'Processing...' after failure"
    )
    result = run_triage(sample_log)
    print(json.dumps(result.model_dump(), indent=2))
