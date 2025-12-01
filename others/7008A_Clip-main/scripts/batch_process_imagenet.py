"""
#!/usr/bin/env python3
"""

"""
Robust batch processing for ImageNet-style directories.

Features:
- Reads images from data/imagenet_base/<synset>/* (supports .jpg/.jpeg/.png/.JPEG etc.)
- Builds metadata: index, path, synset, class_name (if mapping provided)
- Processes images in small batches to avoid OOM and save time
- Saves embeddings and metadata in chunks (embeddings_part_{i}.npy, metadata_part_{i}.json)
- Optionally merges parts into embeddings.npy and image_metadata.json at the end
- Supports resume by skipping already processed chunks

Usage example:
python3 scripts/batch_process_imagenet.py \
    --base_dir data/imagenet_base \
    --output_dir data/output \
    --model clip-ViT-B-32 \
    --batch_size 64 \
    --chunk_size 2000 \
    --merge
"""
import argparse
import json
import os
from pathlib import Path
from PIL import Image, UnidentifiedImageError
import numpy as np
from tqdm import tqdm
import math
import sys

# make sure project root is importable
sys.path.append(str(Path(__file__).resolve().parents[1]))

from clip_pipeline.processor import EmbeddingProcessor

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".JPEG"}

def find_image_files(base_dir):
    base = Path(base_dir)
    image_paths = []
    for class_dir in sorted([p for p in base.iterdir() if p.is_dir()]):
        for p in sorted(class_dir.iterdir()):
            if p.suffix.lower() in SUPPORTED_EXTS:
                image_paths.append(p)
    return image_paths

def load_synset_mapping(mapping_path):
    """
mapping file format (simple): each line "n01440764 tench, Tinca tinca"
Or JSON mapping: {"n01440764": "tench", ...}
"""  
    if not mapping_path:
        return {}
    mp = Path(mapping_path)
    if not mp.exists():
        print(f"Warning: mapping file {mapping_path} not found. Using synset as class_name.")
        return {}
    # try JSON
    try:
        with open(mp, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    # fallback parse plain text
    mapping = {}
    with open(mp, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(" ", 1)
            if len(parts) == 2:
                mapping[parts[0]] = parts[1].strip()
    return mapping

def pil_open_safe(path, max_size=None):
    try:
        with Image.open(path) as im:
            im = im.convert("RGB")
            if max_size:
                w, h = im.size
                if max(w,h) > max_size:
                    scale = max_size / float(max(w,h))
                    im = im.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
            return im.copy()
    except (UnidentifiedImageError, OSError) as e:
        return None

def save_metadata_part(metadata_part, out_dir, part_idx):
    out_json = Path(out_dir) / f"image_metadata_part_{part_idx}.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(metadata_part, f, indent=2, ensure_ascii=False)
    return out_json

def save_embeddings_part(embeddings_part, out_dir, part_idx):
    out_npy = Path(out_dir) / f"embeddings_part_{part_idx}.npy"
    np.save(out_npy, embeddings_part)
    return out_npy

def merge_parts(out_dir, merged_embeddings_file, merged_metadata_file):
    out_dir = Path(out_dir)
    parts_emb = sorted(out_dir.glob("embeddings_part_*.npy"))
    parts_meta = sorted(out_dir.glob("image_metadata_part_*.json"))
    if not parts_emb or not parts_meta:
        print("No parts found to merge.")
        return False
    # merge embeddings
    embeddings_list = []
    for p in parts_emb:
        embeddings_list.append(np.load(p))
    merged = np.vstack(embeddings_list).astype(np.float32)
    np.save(Path(out_dir) / merged_embeddings_file, merged)
    # merge metadata
    merged_meta = []
    for p in parts_meta:
        with open(p, "r", encoding="utf-8") as f:
            merged_meta.extend(json.load(f))
    with open(Path(out_dir) / merged_metadata_file, "w", encoding="utf-8") as f:
        json.dump(merged_meta, f, indent=2, ensure_ascii=False)
    print(f"Merged {len(parts_emb)} embedding parts into {merged_embeddings_file} (N={{merged.shape[0]}})")
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_dir", type=str, default="data/imagenet_base")
    parser.add_argument("--output_dir", type=str, default="data/output")
    parser.add_argument("--model", type=str, default="clip-ViT-B-32")
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--chunk_size", type=int, default=2000, help="How many images per saved chunk")
    parser.add_argument("--max_size", type=int, default=0, help="Max image long edge to resize (0 = no resize)")
    parser.add_argument("--mapping", type=str, default="", help="Optional synset->name mapping file (json or txt)")
    parser.add_argument("--merge", action="store_true", help="Merge parts at end")
    parser.add_argument("--resume", action="store_true", help="Skip parts already saved")
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    mapping = load_synset_mapping(args.mapping) if args.mapping else {}

    # find images
    image_paths = find_image_files(base_dir)
    if not image_paths:
        print(f"No images found in {base_dir}. Please ensure ImageNet data is placed there as <synset> directories.")
        return
    print(f"Found {len(image_paths)} images under {base_dir}.")

    # split into chunks
    total = len(image_paths)
    chunk_size = max(1, args.chunk_size)
    num_parts = math.ceil(total / chunk_size)

    # init model once
    processor = EmbeddingProcessor(model_name=args.model)
    print(f"Model embedding dim: {{processor.embedding_dim}}")

    processed_parts = set()
    if args.resume:
        # detect already saved parts
        for p in out_dir.glob("embeddings_part_*.npy"):
            name = p.stem  # embeddings_part_X
            try:
                idx = int(name.split("_")[-1])
                processed_parts.add(idx)
            except:
                pass

    idx_global = 0
    for part_idx in range(num_parts):
        if args.resume and part_idx in processed_parts:
            print(f"Skipping already processed part {{part_idx}}")
            idx_global += min(chunk_size, total - idx_global)
            continue

        start = part_idx * chunk_size
        end = min(start + chunk_size, total)
        part_paths = image_paths[start:end]
        metadata_part = []
        embeddings_part = []

        # process in smaller batches to avoid sending too large lists to model.encode
        bs = max(1, args.batch_size)
        for bstart in range(0, len(part_paths), bs):
            batch_paths = part_paths[bstart:bstart+bs]
            pil_images = []
            valid_indexes = []
            for p in batch_paths:
                img = pil_open_safe(p, max_size=(args.max_size or None))
                if img is None:
                    print(f"Warning: skipping corrupted/unreadable image {{p}}")
                    continue
                pil_images.append(img)
                valid_indexes.append(p)
            if not pil_images:
                continue
            # encode batch
            try:
                emb_batch = processor.model.encode(pil_images, batch_size=bs, convert_to_numpy=True, show_progress_bar=False)
                # ensure emb_batch is np.ndarray and shape matches
                if emb_batch is None:
                    print("Warning: encoder returned None for a batch; skipping.")
                    continue
            except Exception as e:
                print(f"Error encoding batch starting at {{bstart}} in part {{part_idx}}: {{e}}")
                continue

            # append embeddings and metadata entries
            for ppath, emb in zip(valid_indexes, emb_batch):
                synset = ppath.parent.name
                class_name = mapping.get(synset, synset)
                metadata_part.append({
                    "index": idx_global,
                    "path": str(ppath),
                    "synset": synset,
                    "class_name": class_name,
                    "image_id": f"{{synset}}_{{ppath.name}}"
                })
                embeddings_part.append(emb.astype(np.float32))
                idx_global += 1

        if embeddings_part:
            embeddings_part = np.vstack(embeddings_part)
        else:
            embeddings_part = np.zeros((0, processor.embedding_dim), dtype=np.float32)

        # save this part
        save_embeddings_part(embeddings_part, out_dir, part_idx)
        save_metadata_part(metadata_part, out_dir, part_idx)
        print(f"Saved part {{part_idx}}: images {{start}}..{{end-1}}, embeddings shape {{embeddings_part.shape}}")

    # merge parts if requested
    if args.merge:
        merged_embeddings_file = "embeddings.npy"
        merged_metadata_file = "image_metadata.json"
        merged_ok = merge_parts(out_dir, merged_embeddings_file, merged_metadata_file)
        if merged_ok:
            print(f"Merge complete. Files: {{out_dir/merged_embeddings_file}}, {{out_dir/merged_metadata_file}}")

    print("Done.")

if __name__ == "__main__":
    main()
