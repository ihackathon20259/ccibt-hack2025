from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

from google.adk.agents.llm_agent import Agent

from zero_touch_cx.agents.reporting_agent import reporting_agent
from zero_touch_cx.agents.billing_agent import billing_agent
from zero_touch_cx.agents.upgrade_agent import upgrade_agent
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
# Agent Instruction
# ---------------------------------------------------------------------

ORCHESTRATOR_INSTRUCTION = (
    "You are the Root Orchestration Agent for a zero-touch CX system. "
    "Classify intent, apply confidence gating, and route to the correct "
    "domain agent (reporting, billing, upgrade). "
    "Return ONLY human readable response."
)

# ---------------------------------------------------------------------
# Root Orchestrator Logic
# ---------------------------------------------------------------------

def root_handle(user_text: str) -> dict:
    masked_text = mask_pii(user_text).get("masked_text", user_text)

    intent_info = classify_intent(user_text)
    intent = intent_info.get("intent")
    confidence = float(intent_info.get("confidence", 0.0))

    # ---------------- Confidence Gating ----------------
    if confidence < 0.80 or intent in ("ambiguous", "other"):
        return AgentResponse(
            summary="I need more detail to help you.",
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
            summary=f"Billing details retrieved for customer {customer_id}.",
            payload=payload,
            handoff_required=False,
        ).model_dump()

    # ---------------- Reporting ----------------
    if intent == "report_request":
        days = int(extract_days(user_text).get("days", 30))
        payload = reporting_agent.tools[-1](customer_id, days)
        return AgentResponse(
            summary=f"Wire status report generated for last {days} days.",
            payload=payload,
        ).model_dump()

    # ---------------- Plan Upgrade ----------------
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
            summary=f"Upgrade prepared → {requested_plan}.",
            payload=payload,
        ).model_dump()

    # ---------------- Fallback ----------------
    return AgentResponse(
        summary="Unsupported request.",
        payload={"masked_user_text": masked_text},
    ).model_dump()

# ---------------------------------------------------------------------
# ADK Agent Definition
# ---------------------------------------------------------------------

root_orchestrator_agent = Agent(
    model="gemini-2.0-flash",
    name="root_orchestrator",
    description="Routes customer intents to domain agents.",
    instruction=ORCHESTRATOR_INSTRUCTION,
    tools=[root_handle],
    sub_agents=[
        reporting_agent,
        billing_agent,
        upgrade_agent,
    ],
)