from __future__ import annotations
import logging, os, time
from contextlib import contextmanager
from google.cloud import logging as cloud_logging

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

try:
    from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
    HAS_GCP_TRACE = True
except Exception:
    HAS_GCP_TRACE = False

logger = logging.getLogger("zero_touch_cx")

def setup_logging() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    try:
        client = cloud_logging.Client()
        client.setup_logging()
        logger.info("Cloud Logging is configured.")
    except Exception:
        logger.info("Cloud Logging not configured (local run or missing credentials).")

def setup_tracing(project_id: str | None) -> None:
    provider = TracerProvider()
    if project_id and HAS_GCP_TRACE:
        exporter = CloudTraceSpanExporter(project_id=project_id)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

@contextmanager
def span(name: str, **attrs):
    tracer = trace.get_tracer("zero_touch_cx")
    with tracer.start_as_current_span(name) as sp:
        for k, v in attrs.items():
            sp.set_attribute(k, str(v))
        start = time.time()
        try:
            yield sp
        finally:
            sp.set_attribute("duration_ms", int((time.time()-start)*1000))
