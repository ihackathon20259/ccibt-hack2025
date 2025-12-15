from __future__ import annotations
from typing import Literal
from ..observability import span
import re

Intent = Literal["report_request","plan_upgrade","ambiguous","other"]

def classify_intent(user_text: str) -> dict:
    with span("classify_intent"):
        t = user_text.lower()
        report = bool(re.search(r"\breport\b|status report|wire status", t))
        upgrade = bool(re.search(r"\bupgrade\b|\bpro\b|plan\b", t))
        if report and upgrade:
            return {"intent":"ambiguous","confidence":0.55}
        if report:
            return {"intent":"report_request","confidence":0.85}
        if upgrade:
            return {"intent":"plan_upgrade","confidence":0.85}
        return {"intent":"other","confidence":0.6}

def extract_customer_id(user_text: str) -> dict:
    with span("extract_customer_id"):
        m = re.search(r"(cust_\d{3})", user_text.lower())
        return {"status":"success","customer_id": (m.group(1) if m else "cust_001")}

def extract_days(user_text: str) -> dict:
    with span("extract_days"):
        m = re.search(r"last\s+(\d+)\s+days", user_text.lower())
        return {"status":"success","days": (int(m.group(1)) if m else 30)}
