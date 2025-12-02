from __future__ import annotations
"""Runtime wrapper for CLIP online embedding.

- Lazily loads a sentence-transformers CLIP model on first use.
- Provides simple helpers to embed image/text and return python lists of floats.
- Designed to fail gracefully when deps not installed: returns None instead of raising.
"""
from typing import List, Optional
from flask import current_app

# Optional heavy deps are imported lazily
_MODEL = None  # type: ignore[var-annotated]
_EMBED_DIM: int | None = None
_BACKEND: str | None = None  # 'sentence-transformers'


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


def embed_image_path(path: str) -> Optional[List[float]]:
    """Embed a single image file and return a float list. Returns None on failure.
    The caller is responsible for normalization and persistence.
    """
    global _BACKEND

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


def embed_image_paths_batch(paths: str, batch_size: int = 32) -> Optional[List[float]]:
    """Batch embed multiple image files and return a float list. Returns None on failure.
    The caller is responsible for normalization and persistence.
    """
    global _BACKEND

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
        imgs = [Image.open(path).convert("RGB") for path in paths]
        vecs = model.encode(imgs, batch_size=batch_size, convert_to_numpy=True)
        _BACKEND = "sentence-transformers"
        return vecs
    except Exception as e:
        try:
            current_app.logger.exception("team embed_text failed: %s", e)
        except Exception:
            pass
        return None


def embed_text(text: str) -> Optional[List[float]]:
    global _BACKEND

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
    return _EMBED_DIM
