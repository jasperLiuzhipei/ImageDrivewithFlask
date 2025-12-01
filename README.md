# WebImageDrive Flask Backend (Minimal Skeleton)

This is a minimal Flask backend scaffold with an application factory, configuration, core extensions, empty blueprints, placeholder services/tasks, and an OpenAPI draft.

## What's included

- App factory: `app/create_app`
- Config classes: `app/config.py` (dev/prod/test)
- Extensions: SQLAlchemy, Migrate, JWT
- Blueprints:
  - `core` (/api/v1, /api/v1/health)
  - `auth`, `files`, `ingest`, `search`, `search_ocr`, `analytics` (placeholders)
- Services (placeholders): embedding, ocr, storage, vector_index
- Tasks (placeholders): optional Celery wiring stub
- API spec draft: `api_spec.yaml`
- Runner: `app.py`

## Project structure

```
app/
  __init__.py
  config.py
  extensions.py
  models/
    __init__.py
    base.py
  blueprints/
    core/           # health & root
    auth/           # authentication (todo)
    files/          # upload & file ops (todo)
    ingest/         # write embeddings/OCR (todo)
    search/         # vector search (todo)
    search_ocr/     # OCR text search (todo)
    analytics/      # simple metrics (todo)
  services/
    embedding.py
    embedding_io.py
    ocr.py
    storage.py
    vector_index.py
  tasks/
    __init__.py
    placeholders.py
  utils/
    __init__.py
    responses.py    # unified JSON response helpers
docs/
  config.md
  integration_guide.md
  runtime.md
  vector_index.md
scripts/
  seed.py
samples/
  (manual testing images)
api_spec.yaml
requirements.txt
environment.yml
README.md
```

## Quick start (macOS / zsh)

```zsh
# 创建或重建环境（如以前已创建过 3.13 的同名环境请先删除）
conda env remove -n webimagedrive  # 可选
conda env create -f environment.yml
conda activate webimagedrive

# 安装剩余 pip 依赖（若未自动安装）
python3 -m pip install -r requirements.txt

# 运行应用
APP_VERSION=dev python3 app.py

# 健康检查
curl -s http://127.0.0.1:5000/api/v1/health | jq
```

如果 `conda activate webimagedrive` 失败，可尝试：
```zsh
conda init zsh
exec $SHELL -l
conda activate webimagedrive
```

快速验证关键依赖：
```zsh
python3 -c "import torch, faiss, sentence_transformers; print('torch', torch.__version__)"
```

### Seed demo data

Prefer running as a module (resolves imports reliably):
```zsh
python3 -m scripts.seed
```

Or run directly:
```zsh
python3 scripts/seed.py
```

Note: If you see `ModuleNotFoundError: No module named 'app'`, ensure you run the command from the project root directory and use the module form above.

## Database migrations (Flask-Migrate)

Initialize (first time):
```zsh
export FLASK_APP="app:create_app"
flask db init
```

Generate migration from current models:
```zsh
flask db migrate -m "initial schema"
```

Apply migrations:
```zsh
flask db upgrade
```

The default SQLite file will live at `./instance/app.db`.

Expected response:

```json
{"status":"healthy"}
```

## Configuration

Configuration precedence: defaults < .env < environment variables.

- Copy `.env.example` to `.env` and adjust values for local dev.
- Select config via `FLASK_CONFIG=dev|prod|test` (default `dev`).
- Default DB is SQLite file at `./instance/app.db`.
- In production, you must set a strong `SECRET_KEY` (app will refuse to start if using default).

## PostgreSQL 16（Docker）

- 启动数据库：
  - 在项目根目录运行 `docker compose up -d`
- 配置环境：
  - 将 `.env.example` 复制为 `.env` 并设置 `DATABASE_URL=postgresql://webimg:webimg@localhost:5432/webimagedrive`
  - 本项目会在启动时自动加载 `.env`（通过 `python-dotenv`）
- 执行迁移：
  - `export FLASK_APP="app:create_app"`
  - `flask db migrate -m "init pg schema"`
  - `flask db upgrade`
- 启动后端与验证：
  - `flask run --port 5000`
  - `curl -s http://127.0.0.1:5000/api/v1/health | jq`
- 团队一致性：
  - 所有人使用仓库内同一份 `docker-compose.yml` 启动 PostgreSQL 16。
  - 数据持久化路径挂载到 `./.docker/pgdata`，便于本地开发。
  - IDE 的 Run/Debug 配置请确保加载 `.env` 或显式设置 `DATABASE_URL`。

## Next steps

- Add database models and Alembic migrations
- Implement auth endpoints (register/login/refresh)
- Wire object storage (local/MinIO/S3) in `services/storage.py`
- Implement vector index integration (FAISS) following `DESIGN V5.md`
- Add Celery and call `app.tasks.init_celery(celery_app)` when you are ready
- Flesh out API in `api_spec.yaml` and keep server responses consistent

## OCR APIs (brief)

- `POST /api/v1/ingest/ocr`
  - body: `{ "image_id": number, "include_text"?: bool, "snippet_len"?: number }`
  - notes: 返回 `has_text`；当 `include_text=true` 时附加 `text_preview`（长度受 `snippet_len` 限制，默认 120）。
  - example:
    ```zsh
    curl -s -X POST http://127.0.0.1:5000/api/v1/ingest/ocr \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"image_id":13, "include_text": true, "snippet_len": 50}' | jq
    ```
    响应示例: `{ "status":"ok", "data": { "image_id":13, "has_text":true, "created":false, "text_preview":"..." } }`

- `POST /api/v1/ingest/ocr/batch`
  - body: `{ "image_ids": number[], "batch_size"?: number, "include_text"?: bool, "snippet_len"?: number }`
    - 也支持 `{ "items": [{"image_id": number}, ...] }` 形式。
  - notes: 仅处理当前用户且本地存储（`local://`）图片；优先调用组员的 `process_image_batch`，否则逐张降级；结果写入 `OCRText`。
  - example:
    ```zsh
    curl -s -X POST http://127.0.0.1:5000/api/v1/ingest/ocr/batch \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"items":[{"image_id":13},{"image_id":14}], "include_text": true, "snippet_len": 50}' | jq
    ```
    响应示例(节选): `{ "status":"ok", "data": { "results": [ {"image_id":13, "ok":true, "has_text":true, "text_preview":"..."} ] } }`

- `POST /api/v1/search/ocr`
  - body: `{ "query": string, "top_k"?: number }`
  - notes: 按 OCR 文本模糊搜索当前用户的图片，返回 `items: [{ image_id, snippet }]`。
  - response: `{ "status":"ok", "data": { "query":"...", "count": N, "items": [ {"image_id":X, "snippet":"..."} ] } }`

## Notes

- 重依赖用 conda（torch、faiss）；其余使用 pip。
- Services 和 tasks 仍保持轻量导入策略。

### Sample images

为避免仓库根目录杂乱，示例图片已移动到 `samples/` 目录，用于手动上传和调试：
```zsh
ls samples/
# a.png b.png valid.png valid2.png

# 手动测试上传示例
curl -s -X POST http://127.0.0.1:5000/api/v1/files/upload \
  -H "Authorization: Bearer <your_token>" \
  -F file=@samples/valid.png | jq
```
