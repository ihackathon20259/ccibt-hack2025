from __future__ import annotations
from ..observability import span
from .rag_tools import rag_search

def policy_check(action: str, context: str) -> dict:
    with span("policy_check", action=action):
        res = rag_search(f"policy {action} {context}", top_k=3)
        passages = res.get("passages", [])
        text = " ".join(p["text"] for p in passages).lower()
        if "no financial action without confirmation" in text and action.startswith("upgrade"):
            if "confirm upgrade" not in context.lower():
                return {"status":"deny","reason":"Upgrade requires explicit confirmation phrase: CONFIRM UPGRADE.", "grounding":passages}
        return {"status":"allow","reason":"Allowed under policy.", "grounding":passages}
