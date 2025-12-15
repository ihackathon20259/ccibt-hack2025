from __future__ import annotations
import os
import vertexai
from vertexai import agent_engines
from agent import root_agent

PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

if not PROJECT:
    raise SystemExit("Set GOOGLE_CLOUD_PROJECT before deploying.")

vertexai.init(project=PROJECT, location=LOCATION)

remote_app = agent_engines.create(
    agent_engine=root_agent,
    requirements=[
        "google-cloud-aiplatform[adk,agent_engines]",
        "google-adk",
        "google-cloud-bigquery",
        "google-cloud-storage",
        "google-cloud-logging",
        "google-cloud-dlp",
        "pydantic",
        "pandas",
        "matplotlib",
    ],
)
print("Deployment finished!")
print(f"Resource Name: {remote_app.resource_name}")
