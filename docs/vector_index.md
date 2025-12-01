# Vector Index Contract (Draft)

- Input: normalized float32 vectors (N x D)
- Build: FAISS IndexFlatL2
- Search: top‑k, returns indices + cosine similarity (derived via 1 - 0.5 * L2² under normalization)
- Mapping: positions -> image_id handled by service layer

## Persistence (per user)

- Location: `INDEX_DIR` (default `instance/faiss`), structure: `user_{id}/index.faiss` + `ids.json` (array of image_ids in index order)
- Lifecycle: lazily built and saved on first search; subsequent searches load from disk and cache in memory
- Rebuild: triggered automatically when cache/files missing; (optional) can add admin API or script if needed

## Response scoring

- Search endpoints now include `similarity` in results for FAISS-backed searches
- Fallback engine (pure Python) also returns `similarity` for consistency
