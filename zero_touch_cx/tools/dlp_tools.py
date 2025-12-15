from __future__ import annotations
import re
from ..observability import span
from ..config import settings

def mask_pii(text: str) -> dict:
    with span("mask_pii", enable_dlp=settings.enable_dlp):
        masked = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[EMAIL]", text)
        masked = re.sub(r"\b\+?\d[\d\- ]{8,}\d\b", "[PHONE]", masked)
        return {"status":"success","masked_text":masked,"source":"regex"}
