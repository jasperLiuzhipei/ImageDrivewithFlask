"""OCR service delegating to teammate's pipeline in `others/imagedrive--OCR-main/ocr_pipeline.py`.

We load the module from file location (folder name contains dashes, not importable as package)
and call `extract_text_from_image_path` directly to keep behavior consistent.
Falls back to None on any error.
"""
from __future__ import annotations

from typing import Optional, List
from flask import current_app

_MODEL = None


def _load_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    try:
        from rapidocr_onnxruntime import RapidOCR  # type: ignore
    except Exception as e:
        current_app.logger.error("Failed to import RapidOCR: %s", e)
        return None
    try:
        use_cuda = current_app.config.get("OCR_USE_CUDA", False)
        batch_num = current_app.config.get("OCR_REC_BATCH_NUM", 6)
        model = RapidOCR(
                det_use_cuda=use_cuda,
                cls_use_cuda=use_cuda,
                rec_use_cuda=use_cuda,
                rec_batch_num=batch_num,
                intra_op_num_threads=2,
                inter_op_num_threads=2
            )
    except Exception as e:
        current_app.logger.error("Failed to create RapidOCR instance: %s", e)
        return None
    return model


def extract_text(image_path: str) -> Optional[str]:  # pragma: no cover
    model = _load_model()
    if model is None:
        return None
    try:
        result, _ = model(image_path)
        if not result:
            return None
        text_lines = [item[1] for item in result if item and len(item) >= 2]
        return " ".join(text_lines)
    except Exception as e:
        current_app.logger.error(f"OCR Error: {e}")
        return None


def extract_text_batch(image_paths: List[str], batch_size: int = 32) -> List[Optional[str]]:  # pragma: no cover
    model = _load_model()
    if model is None:
        return [None] * len(image_paths)
    try:
        return [extract_text(p) for p in image_paths]
    except Exception:
        return [None] * len(image_paths)
