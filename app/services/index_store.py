from __future__ import annotations
"""Per-user FAISS index persistence and in-memory cache.

Stores FAISS index file and image_id mapping under `INDEX_DIR`/user_{id}/.

Usage:
- search_topk(user_id, query_vec, k): ensure index exists (load or build), then return top‑K with similarities.
"""
import json
import os
from typing import List, Tuple, Optional

from flask import current_app
from app.extensions import db
from app.models import Image, Embedding
from app.services.embedding_io import from_bytes
from app.services.vector_index import FaissVectorIndex


CacheEntry = tuple[FaissVectorIndex, List[int]]
_CACHE: dict[int, CacheEntry] = {}


def _user_dir(user_id: int) -> str:
    base = current_app.config.get("INDEX_DIR")
    path = os.path.join(base, f"user_{user_id}")
    os.makedirs(path, exist_ok=True)
    return path


def _paths(user_id: int) -> tuple[str, str]:
    root = _user_dir(user_id)
    return os.path.join(root, "index.faiss"), os.path.join(root, "ids.json")


def _load_files(user_id: int) -> Optional[CacheEntry]:
    idx_path, ids_path = _paths(user_id)
    if not (os.path.exists(idx_path) and os.path.exists(ids_path)):
        return None
    try:
        with open(ids_path, "r", encoding="utf-8") as f:
            ids = json.load(f)
            if not isinstance(ids, list):
                return None
            ids = [int(x) for x in ids]
        idx = FaissVectorIndex.load_from_file(idx_path, norm=True)
        if idx.index is None:
            return None
        return (idx, ids)
    except Exception:
        return None


def _save_files(user_id: int, index: FaissVectorIndex, image_ids: List[int]) -> None:
    idx_path, ids_path = _paths(user_id)
    index.save(idx_path)
    with open(ids_path, "w", encoding="utf-8") as f:
        json.dump([int(i) for i in image_ids], f)


def _build_from_db(user_id: int) -> Optional[CacheEntry]:
    # Fetch user's READY images with embeddings ordered by image id (stable mapping)
    rows = (
        db.session.query(Image.id, Embedding.vec, Embedding.dim)
        .join(Embedding, Embedding.image_id == Image.id)
        .filter(Image.owner_id == user_id, Image.status == "READY")
        .order_by(Image.id.asc())
        .all()
    )
    if not rows:
        return None

    image_ids: List[int] = []
    vectors: List[List[float]] = []
    for iid, vec_bytes, dim in rows:
        v = from_bytes(vec_bytes)
        if len(v) != int(dim):
            # skip malformed
            continue
        image_ids.append(int(iid))
        vectors.append(v)

    if not vectors:
        return None

    idx = FaissVectorIndex(norm=True)
    idx.build(vectors)
    return (idx, image_ids)


def ensure_index(user_id: int) -> Optional[CacheEntry]:
    # Try cache
    entry = _CACHE.get(user_id)
    if entry is not None:
        return entry
    # Try files
    entry = _load_files(user_id)
    if entry is not None:
        _CACHE[user_id] = entry
        return entry
    # Build and persist
    entry = _build_from_db(user_id)
    if entry is None:
        return None
    _save_files(user_id, entry[0], entry[1])
    _CACHE[user_id] = entry
    return entry


def rebuild_index(user_id: int) -> bool:
    entry = _build_from_db(user_id)
    if entry is None:
        return False
    _save_files(user_id, entry[0], entry[1])
    _CACHE[user_id] = entry
    return True


def search_topk(user_id: int, query_vec: List[float], k: int = 10) -> List[Tuple[int, float]]:
    entry = ensure_index(user_id)
    if entry is None:
        return []
    idx, image_ids = entry
    inds, sims = idx.search_topk_scores(query_vec, k=min(k, len(image_ids)))
    results: List[Tuple[int, float]] = []
    for i, s in zip(list(inds), list(sims)):
        # Safety for out-of-range indices
        if 0 <= int(i) < len(image_ids):
            results.append((int(image_ids[int(i)]), float(s)))
    return results
