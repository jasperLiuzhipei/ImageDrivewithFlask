"""Utilities for packing/unpacking normalized float32 embeddings to bytes.

- Store normalized vectors (L2=1.0) as float32 bytes (Embedding.vec)
- Avoid heavy deps; use Python stdlib array for serialization
"""
from __future__ import annotations
from typing import Iterable, List
from array import array
import math


def l2_normalize(vec: Iterable[float]) -> List[float]:
    v = list(float(x) for x in vec)
    s = math.sqrt(sum(x * x for x in v))
    if s == 0.0:
        # Return zero vector as-is to avoid NaNs; caller may choose to skip
        return v
    return [x / s for x in v]


def to_bytes(vec: Iterable[float]) -> bytes:
    """Convert sequence of floats to float32 bytes.

    Note: Uses platform-native endian for array('f'). For cross-platform
    reproducibility across DB exports, consider enforcing little-endian
    packing if needed in the future.
    """
    arr = array("f", (float(x) for x in vec))
    return arr.tobytes()


def from_bytes(b: bytes) -> List[float]:
    arr = array("f")
    arr.frombytes(b)
    return list(arr)
