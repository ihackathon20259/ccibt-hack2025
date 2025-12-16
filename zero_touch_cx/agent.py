from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

from google.adk.agents.llm_agent import Agent

from zero_touch_cx.agents.reporting_agent import reporting_agent
from zero_touch_cx.agents.compliance_agent import validate_and_sanitize
from zero_touch_cx.agents.billing_agent import billing_agent
from zero_touch_cx.agents.upgrade_agent import upgrade_agent
from zero_touch_cx.agents.root_orchestration_agent import root_orchestrator_agent
from zero_touch_cx.agents.intent_tools import (
    classify_intent,
    extract_customer_id,
    extract_days,
)
from zero_touch_cx.tools.dlp_tools import mask_pii
from zero_touch_cx.schemas import AgentResponse
from zero_touch_cx.observability import setup_logging, setup_tracing
from zero_touch_cx.config import settings

# ---------------------------------------------------------------------
# Observability
# ---------------------------------------------------------------------

setup_logging()
setup_tracing(settings.project)

# ---------------------------------------------------------------------
# Agent Instructions
# ---------------------------------------------------------------------

ORCHESTRATOR_INSTRUCTION = (
    "You are the Root Orchestration Agent for a zero-touch CX system. "
    "Classify intent and route to reporting, billing, or upgrade flows. "
    "Return ONLY AgentResponse JSON."
)

COMPLIANCE_INSTRUCTION = (
    "You are the Compliance Gateway Agent. "
    "Validate and sanitize user input (PII masking, policy checks). "
    "If blocked, return ONLY AgentResponse JSON."
)

# ---------------------------------------------------------------------
# Root Orchestrator Logic (Business Routing)
# ---------------------------------------------------------------------

def root_handle(user_text: str) -> dict:
    masked_text = mask_pii(user_text).get("masked_text", user_text)

    intent_info = classify_intent(user_text)
    intent = intent_info.get("intent")
    confidence = float(intent_info.get("confidence", 0.0))

    if confidence < 0.80 or intent in ("ambiguous", "other"):
        return AgentResponse(
            summary="I need a bit more detail to help you.",
            payload={
                "detected_intent": intent,
                "confidence": confidence,
                "masked_user_text": masked_text,
            },
            handoff_required=confidence < 0.50,
            handoff_reason="Low confidence intent classification"
            if confidence < 0.50
            else None,
        ).model_dump()

    customer_id = extract_customer_id(user_text).get("customer_id", "cust_001")

    # ---------------- Billing ----------------
    if intent == "billing_inquiry":
        payload = billing_agent.tools[-1](customer_id, user_text)
        return AgentResponse(
            summary=f"Here’s the billing information for customer {customer_id}.",
            payload=payload,
        ).model_dump()

    # ---------------- Reporting ----------------
    if intent == "report_request":
        days = int(extract_days(user_text).get("days", 30))
        payload = reporting_agent.tools[-1](customer_id, days)
        return AgentResponse(
            summary=f"Your wire transfer report for the last {days} days is ready.",
            payload=payload,
        ).model_dump()

    # ---------------- Upgrade ----------------
    if intent == "plan_upgrade":
        requested_plan = next(
            (
                p.capitalize()
                for p in ["basic", "starter", "pro", "max"]
                if p in user_text.lower()
            ),
            "Pro",
        )
        payload = upgrade_agent.tools[-1](
            customer_id, requested_plan, user_text
        )
        return AgentResponse(
            summary=f"I’ve prepared your upgrade to the {requested_plan} plan.",
            payload=payload,
        ).model_dump()

    return AgentResponse(
        summary="I’m not able to support this request yet.",
        payload={"masked_user_text": masked_text},
    ).model_dump()

# ---------------------------------------------------------------------
# Compliance Gate (Runs ONCE)
# ---------------------------------------------------------------------

def compliance_gate(user_text: str) -> dict:
    decision = validate_and_sanitize(user_text)

    # ❌ Blocked
    if not decision.get("allow", False):
        return AgentResponse(
            summary="I can’t process this request yet.",
            payload={
                "type": "compliance_block",
                "reason": decision.get("reason"),
                "risk_score": decision.get("risk_score"),
                "pii_masked": decision.get("pii_masked"),
            },
            handoff_required=decision.get("risk_score", 0) >= 0.85,
            handoff_reason="Sensitive data detected"
            if decision.get("risk_score", 0) >= 0.85
            else None,
        ).model_dump()

    # ✅ Allowed → call orchestrator directly
    sanitized_text = decision.get("sanitized_text", user_text)
    response = root_handle(sanitized_text)

    # Attach compliance metadata
    response.setdefault("payload", {})
    response["payload"]["compliance"] = {
        "allow": True,
        "risk_score": decision.get("risk_score"),
        "pii_masked": decision.get("pii_masked"),
    }

    return response

# ---------------------------------------------------------------------
# Human-Friendly Renderer (Presentation Layer)
# ---------------------------------------------------------------------

def render_human_response(agent_response: dict) -> str:
    summary = agent_response.get("summary", "")
    payload = agent_response.get("payload", {})

    # Compliance block
    if payload.get("type") == "compliance_block":
        return (
            "⚠️ **Request blocked for security reasons**\n\n"
            f"Reason: {payload.get('reason', 'Policy restriction')}.\n"
            "Please revise your request and try again."
        )

    # Reporting
    if "report" in payload:
        return (
            "📄 **Wire Transfer Report Ready**\n\n"
            f"{summary}"
        )

    # Billing
    if "billing" in payload:
        return (
            "💳 **Billing Information**\n\n"
            f"{summary}"
        )

    # Upgrade
    if "upgrade" in payload:
        return (
            "🚀 **Plan Upgrade**\n\n"
            f"{summary}"
        )

    return summary


# ✅ Only root agent ADK should load
root_agent = Agent(
    model="gemini-2.0-flash",
    name="compliance_gateway",
    description="Runs one-time compliance before orchestration.",
    instruction=COMPLIANCE_INSTRUCTION,
    tools=[compliance_gate],
    sub_agents=[root_orchestrator_agent],
)

# ---------------------------------------------------------------------
# Optional Entry Point for UI / API
# ---------------------------------------------------------------------

def handle_user_input(user_text: str) -> dict:
    """
    Entry point for UI or API.
    Returns both human-friendly message and raw JSON.
    """
    raw_response = compliance_gate(user_text)
    return {
        "message": render_human_response(raw_response),
        "data": raw_response,  # structured, auditable output
    }