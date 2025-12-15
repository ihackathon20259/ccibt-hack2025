# zero_touch_cx/tools/bigquery_tools.py

from typing import List, Dict, Any
from google.cloud import bigquery

# =====================================================
# BigQuery Configuration (Console-defined resources)
# =====================================================

# 🔹 MUST match your GCP Console
PROJECT_ID = "ccibt-hack25ww7-704"          # e.g. my-gcp-project
DATASET_ID = "client_report_data"          # ✅ as requested
WIRE_EVENTS_TABLE = "report_event"       # table inside dataset

# Fully-qualified table name
WIRE_EVENTS_FQN = f"{PROJECT_ID}.{DATASET_ID}.{WIRE_EVENTS_TABLE}"

# Singleton client (recommended)
_bq_client: bigquery.Client | None = None


def _get_client() -> bigquery.Client:
    global _bq_client
    if _bq_client is None:
        _bq_client = bigquery.Client(project=PROJECT_ID)
    return _bq_client


# =====================================================
# Public API used by reporting_agent
# =====================================================

def fetch_wire_status_report(
    customer_id: str,
    days: int = 30
) -> List[Dict[str, Any]]:
    """
    Fetch wire status events for a customer
    from BigQuery dataset `reporting_agent`.

    - Secure (parameterized query)
    - Read-only
    - Works with ADK Web locally
    """

    query = f"""
        SELECT
            customer_id
        FROM `{WIRE_EVENTS_FQN}`
        WHERE customer_id = @customer_id
          AND event_ts >= TIMESTAMP_SUB(
                CURRENT_TIMESTAMP(),
                INTERVAL @days DAY
          )
        ORDER BY event_ts DESC
        LIMIT 500
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "customer_id", "STRING", customer_id
            ),
            bigquery.ScalarQueryParameter(
                "days", "INT64", days
            ),
        ]
    )

    client = _get_client()
    query_job = client.query(query, job_config=job_config)
    rows = query_job.result()

    return [dict(row) for row in rows]
