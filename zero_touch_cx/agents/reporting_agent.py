# zero_touch_cx/agents/reporting_agent.py

from google.adk.agents import Agent
from zero_touch_cx.schemas import ReportCard
from zero_touch_cx.observability import trace
from zero_touch_cx.tools.bigquery_tools import fetch_wire_status_report

reporting_agent = Agent(
    name="reporting_agent",
    instruction="""
    You generate structured report cards for customers.
    Use authoritative BigQuery data sources and return JSON only.
    """
)

async def run_reporting_agent(customer_id: str, days: int = 30):
    rows = fetch_wire_status_report(
        customer_id=customer_id,
        days=days
    )

    status_counts = {}
    for r in rows:
        status = r["status"]
        status_counts[status] = status_counts.get(status, 0) + 1

    report = ReportCard(
        title="Wire Status Report",
        customer_id=customer_id,
        summary=status_counts,
        records=rows[:50],
        next_best_actions=[
            "Investigate wires delayed over 2 days",
            "Enable proactive notifications"
        ],
        rationale="Generated from BigQuery wire_events table"
    )

    return report.dict()