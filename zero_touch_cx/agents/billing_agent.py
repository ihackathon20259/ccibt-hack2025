from __future__ import annotations
from google.adk.agents.llm_agent import Agent
#from ..tools.bigquery_tools import get_billing_history
from ..schemas import AgentResponse
from ..observability import span
import json
from datetime import datetime

INSTRUCTION = (
    "You are the Billing Agent. You will retrieve billing information for a given customer ID "
    "from the start of the current month until today's date. "
    "Return ONLY AgentResponse in human readbale conversation format."
)

def get_billing_history(customer_id, start_of_month, end_of_month):
    return {}

def get_customer_billing_summary(customer_id: str, user_text: str) -> dict:
    with span("get_customer_billing_summary", customer_id=customer_id):
        today = datetime.now()
        start_of_month = today.replace(day=1).strftime("%Y-%m-%d")
        end_of_month = today.strftime("%Y-%m-%d")

        billing_data = get_billing_history(customer_id, start_of_month, end_of_month)

        if billing_data and billing_data.get("status") == "success":
            total_amount = sum(item.get("amount", 0) for item in billing_data.get("history", []))
            summary_message = (
                f"Here is the billing summary for customer ID {customer_id} "
                f"from {start_of_month} to {end_of_month}: "
                f"Total amount due: ${total_amount:.2f}. "
                "Details are in the payload."
            )
            payload = {
                "customer_id": customer_id,
                "start_date": start_of_month,
                "end_date": end_of_month,
                "total_amount_due": total_amount,
                "billing_history": billing_data.get("history", []),
            }
            handoff_required = False
            handoff_reason = None

        else:
            summary_message = (
                f"Could not retrieve billing information for customer ID {customer_id}. "
                "It might be that there's no billing data for the current month or an error occurred."
            )
            payload = {"customer_id": customer_id,
                "start_date": start_of_month,
                "end_date": end_of_month,
                "error": billing_data.get("error", "Unknown error"),
            }
            handoff_required = True
            handoff_reason = "Failed to retrieve billing data or no data for the current month."

        resp = AgentResponse(
            summary=summary_message,
            payload=payload,
            handoff_required=handoff_required,
            handoff_reason=handoff_reason,
        )
        return json.loads(resp.model_dump_json())

billing_agent = Agent(
    model="gemini-2.0-flash",
    name="billing_agent",
    description="Retrieves and summarizes customer billing information.",
    instruction=INSTRUCTION,
    tools=[get_billing_history, get_customer_billing_summary],
)