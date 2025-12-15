from __future__ import annotations
from pathlib import Path
from google.cloud import storage
from ..config import settings
from ..observability import span

ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "artifacts"
ARTIFACT_DIR.mkdir(exist_ok=True)

def upload_artifact(local_path: str, object_name: str) -> dict:
    with span("upload_artifact", object_name=object_name, mock=settings.mock_mode):
        p = Path(local_path)
        if settings.mock_mode or not settings.gcs_bucket:
            dest = ARTIFACT_DIR / object_name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(p.read_bytes())
            return {"status":"success","uri":f"file://{dest}", "source":"mock"}
        client = storage.Client(project=settings.project)
        bucket = client.bucket(settings.gcs_bucket)
        blob = bucket.blob(object_name)
        blob.upload_from_filename(str(p))
        return {"status":"success","uri":f"gs://{settings.gcs_bucket}/{object_name}", "source":"gcs"}
