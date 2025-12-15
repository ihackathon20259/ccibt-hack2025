from __future__ import annotations
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    mock_mode: bool = os.getenv("MOCK_MODE", "true").lower() == "true"
    project: str | None = os.getenv("GOOGLE_CLOUD_PROJECT")
    location: str = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    google_api_key: str | None = os.getenv("GOOGLE_API_KEY")

    bq_dataset: str = os.getenv("BQ_DATASET", "cx_demo")
    bq_usage_table: str = os.getenv("BQ_TABLE_USAGE", "usage_events")
    bq_billing_table: str = os.getenv("BQ_TABLE_BILLING", "billing_history")
    bq_report_events_table: str = os.getenv("BQ_TABLE_REPORT_EVENTS", "report_events")

    gcs_bucket: str | None = os.getenv("GCS_BUCKET")

    vertex_search_location: str = os.getenv("VERTEX_SEARCH_LOCATION", "global")
    vertex_search_datastore_id: str | None = os.getenv("VERTEX_SEARCH_DATASTORE_ID")

    enable_dlp: bool = os.getenv("ENABLE_DLP", "false").lower() == "true"

settings = Settings()
