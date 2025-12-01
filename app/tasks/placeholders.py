"""Task placeholders; real Celery wiring can attach these later."""
from __future__ import annotations


def init_celery(celery):  # pragma: no cover - placeholder
    """Attach tasks to a Celery app (no-op placeholder)."""

    @celery.task(name="compute_embedding")  # type: ignore[attr-defined]
    def compute_embedding(image_id: int):
        return {"status": "skipped", "image_id": image_id}

    @celery.task(name="run_ocr")  # type: ignore[attr-defined]
    def run_ocr(image_id: int):
        return {"status": "skipped", "image_id": image_id}

    @celery.task(name="generate_thumbs")  # type: ignore[attr-defined]
    def generate_thumbs(image_id: int):
        return {"status": "skipped", "image_id": image_id}

    return celery
