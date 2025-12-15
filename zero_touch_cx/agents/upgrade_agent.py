from __future__ import annotations
from google.adk.agents.llm_agent import Agent
from ..tools.billing_tools import check_upgrade_eligibility, simulate_pricing, execute_upgrade
from ..tools.policy_tools import policy_check
from ..tools.rag_tools import rag_search
from ..schemas import UpgradeDecision
import json

INSTRUCTION = (
    "You are the Upgrade Agent. Provide UpgradeDecision JSON. "
    "Always run policy_check before execute_upgrade. "
    "Never execute without explicit 'CONFIRM UPGRADE'."
)

def handle_upgrade(customer_id: str, requested_plan: str, user_text: str) -> dict:
    elig = check_upgrade_eligibility(customer_id, requested_plan)
    sim = simulate_pricing(customer_id, requested_plan)

    decision = UpgradeDecision(
        customer_id=customer_id,
        current_plan=elig.get("current_plan","Unknown"),
        requested_plan=requested_plan,
        eligible=bool(elig.get("eligible", False)),
        reasons=list(elig.get("reasons", [])),
        simulated_monthly_price_usd=(sim.get("monthly_price_usd") if sim.get("status")=="success" else None),
        requires_confirmation=True,
        next_best_actions=[f"Reply: CONFIRM UPGRADE to {requested_plan} to proceed."],
        confidence=0.85 if elig.get("eligible") else 0.7,
    )

    if "confirm upgrade" in user_text.lower() and decision.eligible:
        pol = policy_check("upgrade_plan", user_text)
        if pol.get("status") == "allow":
            execute_upgrade(customer_id, requested_plan)
            decision.requires_confirmation = False
            decision.next_best_actions = ["Upgrade executed. Monitor usage in 24 hours."]
        else:
            decision.reasons.append(pol.get("reason","Denied by policy."))

    return json.loads(decision.model_dump_json())

upgrade_agent = Agent(
    model="gemini-3-pro-preview",
    name="upgrade_agent",
    description="Handles plan upgrades with guardrails and billing simulation.",
    instruction=INSTRUCTION,
    tools=[rag_search, policy_check, check_upgrade_eligibility, simulate_pricing, execute_upgrade, handle_upgrade],
)
