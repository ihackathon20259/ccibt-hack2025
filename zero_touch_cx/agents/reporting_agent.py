from __future__ import annotations
from google.adk.agents.llm_agent import Agent
from ..tools.bigquery_tools import get_wire_status_kpis, get_usage_summary
from ..tools.rag_tools import rag_search
from ..tools.gcs_tools import upload_artifact
from ..tools.charts import bar_chart
from ..schemas import ReportCard, KPI
from ..observability import span
import json

INSTRUCTION = (
    "You are the Reporting Agent. Produce a structured report card JSON. "
    "Use rag_search for grounding, query KPIs via tools, generate/upload a chart, "
    "and output ONLY valid JSON matching ReportCard."
)

def build_wire_status_report(customer_id: str, days: int = 30) -> dict:
    with span("build_wire_status_report", customer_id=customer_id, days=days):
        k = get_wire_status_kpis(customer_id, days)
        labels = ["Pending", "Failed", "CompletionRate"]
        values = [float(k.get("pending_count",0)), float(k.get("failed_count",0)), float(k.get("completion_rate",0))]
        chart_path = bar_chart("Wire Status KPIs", labels, values, f"charts/{customer_id}_wire_status.png")
        chart_uri = upload_artifact(chart_path, f"charts/{customer_id}_wire_status.png").get("uri")

        grounding = rag_search("T-1004 Wire Status Report KPIs", top_k=2)
        rationale = "Grounded in report definitions. "
        if grounding.get("passages"):
            rationale += f"Top source: {grounding['passages'][0]['title']}"

        rc = ReportCard(
            customer_id=customer_id,
            report_id="T-1004",
            title="Wire Status Report",
            date_range=f"last {days} days",
            kpis=[
                KPI(name="pending_count", value=k.get("pending_count",0), unit="count"),
                KPI(name="failed_count", value=k.get("failed_count",0), unit="count"),
                KPI(name="completion_rate", value=k.get("completion_rate",0), unit="ratio"),
            ],
            chart_uri=chart_uri,
            data_source=k.get("source","mock"),
            rationale=rationale,
            next_best_actions=["Review failed wires.", "Schedule this report weekly."],
            confidence=0.85,
        )
        return json.loads(rc.model_dump_json())

reporting_agent = Agent(
    model="gemini-3-pro-preview",
    name="reporting_agent",
    description="Generates structured report cards with charts.",
    instruction=INSTRUCTION,
    tools=[rag_search, get_wire_status_kpis, get_usage_summary, upload_artifact, build_wire_status_report],
)
