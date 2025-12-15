from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal, Any

class KPI(BaseModel):
    name: str
    value: float | int | str
    unit: str | None = None

class ReportCard(BaseModel):
    kind: Literal["report_card"] = "report_card"
    customer_id: str
    report_id: str
    title: str
    date_range: str
    kpis: list[KPI] = Field(default_factory=list)
    chart_uri: str | None = None
    data_source: Literal["bigquery","mock"] = "mock"
    rationale: str
    next_best_actions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)

class UpgradeDecision(BaseModel):
    kind: Literal["upgrade_decision"] = "upgrade_decision"
    customer_id: str
    current_plan: str
    requested_plan: str
    eligible: bool
    reasons: list[str] = Field(default_factory=list)
    simulated_monthly_price_usd: float | None = None
    requires_confirmation: bool = True
    next_best_actions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)

class AgentResponse(BaseModel):
    summary: str
    payload: dict[str, Any] | None = None
    handoff_required: bool = False
    handoff_reason: str | None = None
