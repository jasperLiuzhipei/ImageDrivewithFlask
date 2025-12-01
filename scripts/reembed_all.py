#!/usr/bin/env python3
"""Rebuild (re-embed) all image embeddings using online CLIP.

Usage:
  python scripts/reembed_all.py                # re-embed all READY images (overwrite embeddings)
  python scripts/reembed_all.py --only-missing # only embed images that currently lack an embedding
  python scripts/reembed_all.py --limit 100    # process first 100 images
  python scripts/reembed_all.py --dry-run      # show plan without writing

Behavior:
- Loads Flask app context.
- Optionally wipes existing embeddings (default unless --only-missing).
- For each selected image (status=READY, storage_uri starting with local://):
  * Loads file, runs embed_image_path -> float list.
  * L2 normalizes vector (epsilon guarded) and stores bytes.
- Skips images with failed embedding silently; prints summary at end.

Return codes:
- 0 on success (even with some failures)
- 1 on fatal initialization error
"""
from __future__ import annotations
import os
import sys
import argparse
import math
from typing import List

# Ensure project root importable when invoked from scripts/
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import create_app  # type: ignore
from app.extensions import db  # type: ignore
from app.models import Image, Embedding  # type: ignore
from app.services.clip_runtime import embed_image_path  # type: ignore
from app.services.embedding_io import to_bytes  # type: ignore


def l2_normalize(v: List[float]) -> List[float]:
    s = math.sqrt(sum(x * x for x in v))
    if s == 0.0:
        return v
    return [x / s for x in v]


def parse_args():
    ap = argparse.ArgumentParser(description="Re-embed all images using CLIP")
    ap.add_argument("--only-missing", action="store_true", help="Only embed images without an existing embedding")
    ap.add_argument("--limit", type=int, default=None, help="Process at most N images")
    ap.add_argument("--dry-run", action="store_true", help="Show plan without modifying database")
    return ap.parse_args()


def main():
    args = parse_args()
    app = create_app()
    with app.app_context():
        q = Image.query.filter(Image.status == "READY")
        if args.only_missing:
            # Left outer join style selection: image without embedding
            q = q.filter(~Image.id.in_(db.session.query(Embedding.image_id)))
        q = q.order_by(Image.id.asc())
        images = q.all()
        if args.limit is not None:
            images = images[: args.limit]

        print(f"Selected images: {len(images)} (only_missing={args.only_missing})")
        if args.dry_run:
            for img in images[:10]:  # preview first few
                print(f"DRY-RUN image_id={img.id} storage_uri={img.storage_uri}")
            print("Dry run complete.")
            return 0

        # If not only-missing: wipe existing embeddings first for a clean rebuild
        if not args.only_missing:
            deleted = Embedding.query.delete()
            db.session.commit()
            print(f"Removed {deleted} existing embeddings.")

        upload_dir = app.config.get("UPLOAD_DIR")
        ok_count = 0
        fail_count = 0
        for img in images:
            if not img.storage_uri.startswith("local://"):
                fail_count += 1
                continue
            fname = img.storage_uri[len("local://"):]
            path = os.path.join(upload_dir, fname)
            if not os.path.isfile(path):
                print(f"[WARN] file missing: image_id={img.id} path={path}")
                fail_count += 1
                continue
            vec = embed_image_path(path)
            if not vec:
                print(f"[WARN] embed failed: image_id={img.id}")
                fail_count += 1
                continue
            norm = l2_normalize(vec)
            payload = to_bytes(norm)
            emb = Embedding(image_id=img.id, vec=payload, dim=len(norm), model_version=app.config.get("CLIP_MODEL_NAME", "clip-ViT-B-32"))
            db.session.add(emb)
            ok_count += 1
            if ok_count % 50 == 0:
                db.session.flush()
        db.session.commit()
        print(f"Embedding rebuild finished: success={ok_count} failed={fail_count}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
