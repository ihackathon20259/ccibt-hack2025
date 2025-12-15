from __future__ import annotations
from typing import Any
import pandas as pd
from google.cloud import bigquery
from .mock_store import load_csv
from ..config import settings
from ..observability import span

def bq_query(sql: str, params: dict[str, Any] | None = None) -> dict:
    with span("bq_query", mock=settings.mock_mode):
        if settings.mock_mode:
            return {"status": "error", "error": "Mock mode does not support arbitrary SQL.", "source": "mock"}
        client = bigquery.Client(project=settings.project)
        job = client.query(sql)
        rows = [dict(r) for r in job.result()]
        return {"status": "success", "rows": rows, "row_count": len(rows), "source": "bigquery"}

def get_usage_summary(customer_id: str, days: int = 30) -> dict:
    with span("get_usage_summary", customer_id=customer_id, days=days):
        if settings.mock_mode:
            df = load_csv("usage_events.csv")
            df = df[df["customer_id"] == customer_id].copy()
            df["event_ts"] = pd.to_datetime(df["event_ts"])
            cutoff = df["event_ts"].max() - pd.Timedelta(days=days)
            df = df[df["event_ts"] >= cutoff]
            if df.empty:
                return {"status":"success","days":days,"top_feature":None,"total_events":0,"source":"mock"}
            top = df.groupby("feature")["value"].sum().sort_values(ascending=False).head(1)
            return {"status":"success","days":days,"top_feature":top.index[0],"total_events":int(df["value"].sum()),"source":"mock"}
        return {"status":"success","days":days,"top_feature":None,"total_events":0,"source":"bigquery"}

def get_wire_status_kpis(customer_id: str, days: int = 30) -> dict:
    with span("get_wire_status_kpis", customer_id=customer_id, days=days):
        if settings.mock_mode:
            df = load_csv("report_events.csv")
            df = df[(df["customer_id"]==customer_id) & (df["report_id"]=="T-1004")].copy()
            df["run_ts"] = pd.to_datetime(df["run_ts"])
            if df.empty:
                return {"status":"success","days":days,"pending_count":0,"completion_rate":0.0,"failed_count":0,"source":"mock"}
            cutoff = df["run_ts"].max() - pd.Timedelta(days=days)
            df = df[df["run_ts"] >= cutoff]
            total = len(df)
            success = int((df["status"]=="SUCCESS").sum())
            fail = int((df["status"]=="FAILED").sum())
            completion_rate = (success/total) if total else 0.0
            pending = max(0, int(total*0.15 - fail))
            return {"status":"success","days":days,"pending_count":pending,"completion_rate":round(completion_rate,3),"failed_count":fail,"source":"mock"}
        return {"status":"success","days":days,"pending_count":0,"completion_rate":0.0,"failed_count":0,"source":"bigquery"}
