from __future__ import annotations
from ..observability import span
from .mock_store import current_plan

PLAN_PRICING = {"Basic":0.0,"Starter":19.0,"Pro":49.0,"Max":199.0}

def simulate_pricing(customer_id: str, requested_plan: str) -> dict:
    with span("simulate_pricing", customer_id=customer_id, requested_plan=requested_plan):
        price = PLAN_PRICING.get(requested_plan)
        if price is None:
            return {"status":"error","error":"Unknown plan"}
        return {"status":"success","monthly_price_usd":price}

def check_upgrade_eligibility(customer_id: str, requested_plan: str) -> dict:
    with span("check_upgrade_eligibility", customer_id=customer_id, requested_plan=requested_plan):
        cur = current_plan(customer_id)
        eligible = True
        reasons = []
        if requested_plan in ("Pro","Max"):
            payment_on_file = (customer_id != "cust_002")  # demo
            if not payment_on_file:
                eligible = False
                reasons.append("No valid payment method on file.")
        return {"status":"success","current_plan":cur,"eligible":eligible,"reasons":reasons}

def execute_upgrade(customer_id: str, requested_plan: str) -> dict:
    with span("execute_upgrade", customer_id=customer_id, requested_plan=requested_plan):
        return {"status":"success","message":f"Upgrade to {requested_plan} submitted.", "ticket_id":f"chg_{customer_id}"}
