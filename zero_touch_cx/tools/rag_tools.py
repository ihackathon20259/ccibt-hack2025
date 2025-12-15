from __future__ import annotations
from ..config import settings
from ..observability import span

def rag_search(query: str, top_k: int = 3) -> dict:
    with span("rag_search", top_k=top_k, mock=settings.mock_mode):
        if settings.mock_mode or not settings.vertex_search_datastore_id:
            import glob, pathlib
            passages=[]
            for fp in glob.glob(str(pathlib.Path(__file__).resolve().parents[2] / "docs" / "*.md")):
                txt = pathlib.Path(fp).read_text(encoding="utf-8")
                score = sum(1 for w in query.lower().split() if w in txt.lower())
                if score:
                    passages.append({"title":pathlib.Path(fp).name,"text":txt[:800],"score":score})
            passages = sorted(passages, key=lambda x: x["score"], reverse=True)[:top_k]
            return {"status":"success","passages":passages,"source":"mock"}
        return {"status":"error","error":"Real Vertex AI Search call not implemented in this sample.", "source":"vertex_search"}
