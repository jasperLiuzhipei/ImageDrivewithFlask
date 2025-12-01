from __future__ import annotations
"""Runtime wrapper for CLIP online embedding.

- Lazily loads a sentence-transformers CLIP model on first use.
- Provides simple helpers to embed image/text and return python lists of floats.
- Designed to fail gracefully when deps not installed: returns None instead of raising.
"""
from typing import List, Optional
from flask import current_app
import os
from importlib.util import spec_from_file_location, module_from_spec
import sys

# Optional heavy deps are imported lazily
_MODEL = None  # type: ignore[var-annotated]
_EMBED_DIM: int | None = None
_TEAM_PROC = None  # teammate EmbeddingProcessor instance
_TEAM_DIM: int | None = None
_BACKEND: str | None = None  # 'sentence-transformers' | 'team-processor'


def _load_model():
    global _MODEL, _EMBED_DIM
    if _MODEL is not None:
        return _MODEL
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except Exception:
        return None
    name = current_app.config.get("CLIP_MODEL_NAME", "clip-ViT-B-32")
    try:
        _MODEL = SentenceTransformer(name)
        # Try to get embedding dim if available
        try:
            _EMBED_DIM = int(_MODEL.get_sentence_embedding_dimension())
        except Exception:
            _EMBED_DIM = None
        return _MODEL
    except Exception:
        # model load failed
        return None


def _load_team_processor():  # pragma: no cover - runtime IO
    """Load teammate's EmbeddingProcessor by file path and instantiate it.
    Returns the processor instance or None on failure.
    """
    global _TEAM_PROC, _TEAM_DIM
    if _TEAM_PROC is not None:
        return _TEAM_PROC
    try:
        # Resolve processor.py path
        override = current_app.config.get("TEAM_CLIP_PROCESSOR_PATH") or ""
        # Determine processor path and package root
        if override:
            processor_path = override
            pkg_dir = os.path.dirname(processor_path)
            pkg_root = os.path.dirname(pkg_dir)
            pkg_name = os.path.basename(pkg_dir) or "clip_pipeline"
        else:
            here = os.path.dirname(__file__)
            root = os.path.dirname(os.path.dirname(here))
            pkg_root = os.path.join(root, "others", "7008A_Clip-main")
            pkg_dir = os.path.join(pkg_root, "clip_pipeline")
            processor_path = os.path.join(pkg_dir, "processor.py")
            pkg_name = "clip_pipeline"
        if not os.path.exists(processor_path):
            return None
        # Prefer importing as a package so that relative imports (from .model) work
        try:
            if pkg_root not in sys.path:
                sys.path.insert(0, pkg_root)
            import importlib

            mod = importlib.import_module(f"{pkg_name}.processor")
            EmbeddingProcessor = getattr(mod, "EmbeddingProcessor", None)
        except Exception:
            # Fallback: direct module load (may break relative imports)
            spec = spec_from_file_location("teammate_clip_processor", processor_path)
            if spec is None or spec.loader is None:
                return None
            mod = module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[attr-defined]
            EmbeddingProcessor = getattr(mod, "EmbeddingProcessor", None)
        if EmbeddingProcessor is None:
            return None
        model_name = current_app.config.get("CLIP_MODEL_NAME", "clip-ViT-B-32")
        _TEAM_PROC = EmbeddingProcessor(model_name=model_name)
        try:
            _TEAM_DIM = int(getattr(_TEAM_PROC, "embedding_dim", None) or 0) or None
        except Exception:
            _TEAM_DIM = None
        return _TEAM_PROC
    except Exception:
        _TEAM_PROC = None
        _TEAM_DIM = None
        return None


def _use_team_backend() -> bool:
    return bool(current_app.config.get("USE_TEAM_CLIP", False))


def embed_image_path(path: str) -> Optional[List[float]]:
    """Embed a single image file and return a float list. Returns None on failure.
    The caller is responsible for normalization and persistence.
    """
    global _BACKEND
    if _use_team_backend():
        proc = _load_team_processor()
        if proc is None:
            return None
        try:
            vec = proc.embed_image(path)
            if vec is None:
                return None
            _BACKEND = "team-processor"
            global _TEAM_DIM
            if _TEAM_DIM is None:
                try:
                    _TEAM_DIM = int(len(vec))
                except Exception:
                    pass
            return [float(x) for x in vec.tolist()]
        except Exception as e:
            try:
                current_app.logger.exception("team embed_image failed: %s", e)
            except Exception:
                pass
            return None
    else:
        model = _load_model()
        if model is None:
            return None
        try:
            from PIL import Image  # type: ignore
        except Exception as e:
            try:
                current_app.logger.exception("st embed_image failed: %s", e)
            except Exception:
                pass
            return None
        try:
            img = Image.open(path).convert("RGB")
            vec = model.encode(img, convert_to_numpy=True)
            _BACKEND = "sentence-transformers"
            return [float(x) for x in vec.tolist()]
        except Exception as e:
            try:
                current_app.logger.exception("team embed_text failed: %s", e)
            except Exception:
                pass
            return None


def embed_text(text: str) -> Optional[List[float]]:
    global _BACKEND
    if _use_team_backend():
        proc = _load_team_processor()
        if proc is None:
            return None
        try:
            vec = proc.embed_text(text)
            if vec is None:
                return None
            _BACKEND = "team-processor"
            global _TEAM_DIM
            if _TEAM_DIM is None:
                try:
                    _TEAM_DIM = int(len(vec))
                except Exception:
                    pass
            return [float(x) for x in vec.tolist()]
        except Exception as e:
            try:
                current_app.logger.exception("st embed_text failed: %s", e)
            except Exception:
                pass
            return None
    else:
        model = _load_model()
        if model is None:
            return None
        try:
            vec = model.encode(text, convert_to_numpy=True)
            _BACKEND = "sentence-transformers"
            return [float(x) for x in vec.tolist()]
        except Exception:
            return None


def embedding_backend() -> Optional[str]:
    """Return current embedding backend identifier if known."""
    return _BACKEND


def embedding_dim() -> Optional[int]:
    """Return the embedding dimension if known (from loaded backend)."""
    if _use_team_backend():
        return _TEAM_DIM
    return _EMBED_DIM
