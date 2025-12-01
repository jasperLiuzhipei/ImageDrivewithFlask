#!/usr/bin/env python3
"""
Quick image sanitizer: convert to RGB JPEG, optional resize, remove unreadable files.
Usage:
python3 scripts/prepare_images.py --data_dir data/imagenet_base --max_size 1024
"""
from pathlib import Path
from PIL import Image, UnidentifiedImageError
import argparse
import os

def process_image(p: Path, max_size=None, quality=90):
    try:
        with Image.open(p) as im:
            im = im.convert("RGB")
            if max_size:
                w, h = im.size
                if max(w, h) > max_size:
                    scale = max_size / float(max(w, h))
                    im = im.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
            out_path = p.with_suffix(".jpg")
            im.save(out_path, "JPEG", quality=quality)
            if out_path != p:
                try:
                    p.unlink()
                except Exception:
                    pass
            return True
    except (UnidentifiedImageError, OSError):
        try:
            p.unlink()
        except Exception:
            pass
        return False

def main(data_dir, max_size):
    base = Path(data_dir)
    total = 0
    bad = 0
    for class_dir in sorted([d for d in base.iterdir() if d.is_dir()]):
        for img_path in sorted(class_dir.iterdir()):
            total += 1
            ok = process_image(img_path, max_size=max_size)
            if not ok:
                bad += 1
        print(f"{class_dir.name}: processed images (total so far {total}, bad {bad})")
    print(f"Done. Total images processed: {total}, removed: {bad}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default="data/imagenet_base")
    parser.add_argument("--max_size", type=int, default=0)
    args = parser.parse_args()
    max_size = args.max_size if args.max_size and args.max_size > 0 else None
    main(args.data_dir, max_size)