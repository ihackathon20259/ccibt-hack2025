"""Compliance guardrails for the Zero-touch CX system.

This is a *gateway* layer you can place in front of the root orchestrator.
It validates user inputs, applies basic policy checks, and sanitizes/filters
PII before downstream agents/tools see the request.

Why this file exists:
- ADK/Agent Engine deployments often start with a single root agent.
- To add a "pre-orchestrator" guardrail, we make a new root agent that
  runs compliance checks and then forwards the sanitized request to the
  original orchestrator.

You can extend this module later to:
- call Cloud DLP for enterprise PII inspection
- enforce tenant/customer authorization checks (e.g., customer_id ownership)
- implement allow/deny lists for actions, tools, and data sources
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from zero_touch_cx.tools.dlp_tools import mask_pii


# -----------------------------
# Policy configuration
# -----------------------------

# Keep this small & strict. You can expand as your product grows.
ALLOWED_INTENTS = {
    "report_request",
    "plan_upgrade",
    "billing_inquiry",
    "current_balance"
    "other"
}

# High-level disallowed content. This is not a safety system; it's a baseline
# business guardrail to keep demo flows deterministic.
DISALLOWED_KEYWORDS = [
    "password",
    "credit card",
    "cvv",
    "otp",
    "social security",
    "ssn",
    "aadhar",
]

# Extra regex-based checks for common secrets; adjust to your context.
SECRET_PATTERNS: List[Tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "SSN-like identifier"),
    (re.compile(r"\b\d{16}\b"), "Card-like 16-digit number"),
    (re.compile(r"\b\d{12}\b"), "Aadhaar-like 12-digit number"),
]


@dataclass
class ComplianceDecision:
    allow: bool
    reason: str
    sanitized_text: str
    risk_score: float
    violations: List[str]
    required_clarification: Optional[str] = None


def _keyword_violations(text: str) -> List[str]:
    t = text.lower()
    hits = []
    for kw in DISALLOWED_KEYWORDS:
        if kw in t:
            hits.append(f"Contains disallowed keyword: {kw}")
    return hits


def _pattern_violations(text: str) -> List[str]:
    hits = []
    for pat, label in SECRET_PATTERNS:
        if pat.search(text):
            hits.append(f"Contains sensitive pattern: {label}")
    return hits


def _infer_intent_cheap(text: str) -> str:
    """A deterministic, non-LLM intent hint.

    We still rely on the real intent classifier in intent_tools, but this helps
    catch obviously off-topic requests before we invoke more expensive steps.
    """
    t = text.lower()
    if any(k in t for k in ["upgrade", "downgrade", "plan", "pro", "max", "starter", "basic"]):
        return "plan_upgrade"
    if any(k in t for k in ["report", "status", "usage", "wire", "events", "history"]):
        return "report_request"
    if any(k in t for k in ["bill", "billing", "bills"]):
        return "billing_inquiry"
    return "other"


def validate_and_sanitize(user_text: str) -> Dict[str, Any]:
    """Tool-friendly compliance entrypoint.

    Returns a dict so it can be used directly as an ADK tool.
    """
    user_text = user_text or ""

    # 1) Mask PII using existing DLP helper (works locally; can be swapped for Cloud DLP)
    masked_out = mask_pii(user_text)
    sanitized = masked_out.get("masked_text", user_text)

    violations = []
    violations.extend(_keyword_violations(user_text))
    violations.extend(_pattern_violations(user_text))

    # 2) Cheap intent allow-list gate
    intent_hint = _infer_intent_cheap(sanitized)
    if intent_hint not in ALLOWED_INTENTS:
        # Not necessarily malicious — just not supported.
        decision = ComplianceDecision(
            allow=False,
            reason=f"Unsupported request type (hint={intent_hint}).",
            sanitized_text=sanitized,
            risk_score=0.70,
            violations=violations,
            required_clarification="Please ask for a report (e.g., wire status) or a plan upgrade (e.g., Upgrade me to Pro).",
        )
        return {
            "allow": decision.allow,
            "reason": decision.reason,
            "sanitized_text": decision.sanitized_text,
            "risk_score": decision.risk_score,
            "violations": decision.violations,
            "required_clarification": decision.required_clarification,
            "pii_masked": bool(masked_out.get("masked", False)),
        }

    # 3) If we detect sensitive patterns/keywords, block until user removes them.
    if violations:
        decision = ComplianceDecision(
            allow=False,
            reason="Sensitive data detected; please remove secrets/PII.",
            sanitized_text=sanitized,
            risk_score=0.90,
            violations=violations,
            required_clarification="Please resend your request without passwords, OTPs, card numbers, or other sensitive identifiers.",
        )
        return {
            "allow": decision.allow,
            "reason": decision.reason,
            "sanitized_text": decision.sanitized_text,
            "risk_score": decision.risk_score,
            "violations": decision.violations,
            "required_clarification": decision.required_clarification,
            "pii_masked": bool(masked_out.get("masked", False)),
        }

    # 4) Allow
    decision = ComplianceDecision(
        allow=True,
        reason="Input allowed by policy.",
        sanitized_text=sanitized,
        risk_score=0.10,
        violations=[],
        required_clarification=None,
    )
    return {
        "allow": decision.allow,
        "reason": decision.reason,
        "sanitized_text": decision.sanitized_text,
        "risk_score": decision.risk_score,
        "violations": decision.violations,
        "required_clarification": decision.required_clarification,
        "pii_masked": bool(masked_out.get("masked", False)),
    }