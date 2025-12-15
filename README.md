# Zero‑Touch CX (Reporting + Plan Upgrades) — Google ADK + Vertex AI Agent Engine

This is a **working, runnable reference implementation** of the “zero‑touch customer experience” challenge:
- Natural language reporting requests (e.g., “Show me my wire status report”)
- Plan upgrade requests (e.g., “Upgrade me to Pro”)
- **Multi‑agent orchestration** using **Google ADK** (root agent + sub‑agents)
- Tools for **BigQuery**, **Cloud Storage**, and **Vertex AI Search (RAG)**
- **Guardrails** (policy grounding + optional DLP masking + Gemini safety settings)
- **Observability** (Cloud Logging + OpenTelemetry traces + basic metrics)

> Runs in **MOCK mode** by default (no GCP needed). Switch to real GCP by setting `.env`.

## Quickstart (Local / Mock)
```bash
cd zero_touch_cx_adk
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start ADK web UI (recommended)
adk web --port 8000
```

Try:
- “Show me my wire status report for last 30 days cust_001”
- “Upgrade me to Pro cust_001”
- “CONFIRM UPGRADE to Pro cust_001”

## Real GCP mode
Copy `.env.example` → `.env`, fill values, then run `adk web --port 8000`.

## Deploy to Vertex AI Agent Engine
CLI:
```bash
adk deploy agent_engine   --project=$GOOGLE_CLOUD_PROJECT   --region=$GOOGLE_CLOUD_LOCATION   --staging_bucket=gs://$STAGING_BUCKET   --display_name="zero-touch-cx"   .
```
Or:
```bash
python deploy.py
```
