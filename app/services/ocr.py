"""OCR service delegating to teammate's pipeline in `others/imagedrive--OCR-main/ocr_pipeline.py`.

We load the module from file location (folder name contains dashes, not importable as package)
and call `extract_text_from_image_path` directly to keep behavior consistent.
Falls back to None on any error.
"""
from __future__ import annotations

import os
from typing import Optional, List
from importlib.util import spec_from_file_location, module_from_spec

_TM_MODULE = None  # teammate's ocr_pipeline module


def _load_teammate_module():  # pragma: no cover - runtime IO
    global _TM_MODULE
    if _TM_MODULE is not None:
        return _TM_MODULE
    try:
        # project root = app/.. (two levels up from this file)
        here = os.path.dirname(__file__)
        root = os.path.dirname(os.path.dirname(here))
        path = os.path.join(root, "others", "imagedrive--OCR-main", "ocr_pipeline.py")
        if not os.path.exists(path):
            _TM_MODULE = None
            return None
        spec = spec_from_file_location("teammate_ocr_pipeline", path)
        if spec is None or spec.loader is None:
            _TM_MODULE = None
            return None
        mod = module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[attr-defined]
        _TM_MODULE = mod
        return mod
    except Exception:
        _TM_MODULE = None
        return None


def extract_text(image_path: str) -> Optional[str]:  # pragma: no cover
    mod = _load_teammate_module()
    if mod is None:
        return None
    try:
        # Prefer teammate's canonical name `process_image`, fallback to historical name
        func = getattr(mod, "process_image", None)
        if not callable(func):
            func = getattr(mod, "extract_text_from_image_path", None)
        if not callable(func):
            return None
        return func(image_path)
    except Exception:
        return None


def extract_text_batch(image_paths: List[str], batch_size: int = 32) -> List[Optional[str]]:  # pragma: no cover
    mod = _load_teammate_module()
    if mod is None:
        return [None] * len(image_paths)
    try:
        # Prefer teammate's canonical batch name
        func = getattr(mod, "process_image_batch", None)
        if callable(func):
            try:
                return func(image_paths, batch_size=batch_size)
            except TypeError:
                # If teammate didn't implement batch_size kw, try positional or no arg
                try:
                    return func(image_paths, batch_size)
                except TypeError:
                    return func(image_paths)
        # fallback to per-image
        return [extract_text(p) for p in image_paths]
    except Exception:
        return [None] * len(image_paths)
