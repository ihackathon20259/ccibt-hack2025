from __future__ import annotations
from dotenv import load_dotenv
load_dotenv()

from google.adk.agents.llm_agent import Agent

from zero_touch_cx.agents.reporting_agent import reporting_agent
from zero_touch_cx.agents.upgrade_agent import upgrade_agent
from zero_touch_cx.agents.intent_tools import classify_intent, extract_customer_id, extract_days
from zero_touch_cx.tools.dlp_tools import mask_pii
from zero_touch_cx.schemas import AgentResponse
from zero_touch_cx.observability import setup_logging, setup_tracing
from zero_touch_cx.config import settings
import json

setup_logging()
setup_tracing(settings.project)

INSTRUCTION = (
    "You are the Root Orchestration Agent for a zero-touch CX system. "
    "Use classify_intent + confidence gating; route to reporting_agent or upgrade_agent. "
    "Return ONLY AgentResponse JSON."
)

def root_handle(user_text: str) -> dict:
    masked = mask_pii(user_text).get("masked_text", user_text)

    intent = classify_intent(user_text)
    conf = float(intent.get("confidence", 0.0))
    i = intent.get("intent")

    if conf < 0.80 or i in ("ambiguous","other"):
        resp = AgentResponse(
            summary=f"I need more detail. Are you asking for a report, an upgrade, or both? (Detected={i}, confidence={conf:.2f})",
            payload={"detected_intent": i, "confidence": conf, "masked_user_text": masked},
            handoff_required=(conf < 0.50),
            handoff_reason=("Low confidence intent classification." if conf < 0.50 else None),
        )
        return json.loads(resp.model_dump_json())

    cid = extract_customer_id(user_text).get("customer_id", "cust_001")

    if i == "report_request":
        days = int(extract_days(user_text).get("days", 30))
        payload = reporting_agent.tools[-1](cid, days)
        resp = AgentResponse(
            summary=f"Generated your wire status report card for {cid} (last {days} days).",
            payload=payload,
        )
        return json.loads(resp.model_dump_json())

    if i == "plan_upgrade":
        t = user_text.lower()
        requested_plan = "Pro"
        for p in ["basic","starter","pro","max"]:
            if p in t:
                requested_plan = (p.capitalize() if p != "max" else "Max")
        payload = upgrade_agent.tools[-1](cid, requested_plan, user_text)
        resp = AgentResponse(
            summary=f"Prepared an upgrade decision for {cid} → {requested_plan}.",
            payload=payload,
        )
        return json.loads(resp.model_dump_json())

    resp = AgentResponse(summary="Unsupported request.", payload={"masked_user_text": masked})
    return json.loads(resp.model_dump_json())

root_agent = Agent(
    model="gemini-3-pro-preview",
    name="root_agent",
    description="Routes reporting and plan upgrades using sub-agents and tools.",
    instruction=INSTRUCTION,
    tools=[mask_pii, classify_intent, extract_customer_id, extract_days, root_handle],
    sub_agents=[reporting_agent, upgrade_agent],
)
