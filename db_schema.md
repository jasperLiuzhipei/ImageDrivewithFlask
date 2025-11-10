# 数据库结构（草案 + 使用说明）

本项目使用 SQLAlchemy 定义 ORM 模型；开发默认 SQLite，可切换至 PostgreSQL。以下为核心表及字段设计（与 `models.py` 对应）。后半部分补充：查询示例、初始化与迁移、差异与注意事项。

## 表：users
- id: INTEGER, PK
- username: VARCHAR(128), UNIQUE, NOT NULL
- password_hash: VARCHAR(256), NOT NULL
- created_at: DATETIME, DEFAULT NOW

索引：
- ix_users_username (UNIQUE)

## 表：images
- id: INTEGER, PK
- filename: VARCHAR(512), NOT NULL
- path: VARCHAR(1024), NOT NULL
- checksum: VARCHAR(64), INDEX, 可 UNIQUE（防重复）
- uploader_id: INTEGER, FK -> users.id
- size: INTEGER (bytes)
- mime: VARCHAR(64)
- category: VARCHAR(128)
- tags: VARCHAR(512)  // 逗号分隔，后续可拆表
- created_at: DATETIME, DEFAULT NOW

索引：
- ix_images_checksum
- ix_images_uploader_created (uploader_id, created_at)

## 表：embeddings
- id: INTEGER, PK
- image_id: INTEGER, FK -> images.id, INDEX
- vector_ref: VARCHAR(512)  // 指向向量存储位置（faiss/sidecar 文件路径/pgvector 引用）
- created_at: DATETIME, DEFAULT NOW

## 表：ocr_texts
- id: INTEGER, PK
- image_id: INTEGER, FK -> images.id, INDEX
- text: TEXT
- created_at: DATETIME, DEFAULT NOW

（FTS 预留）
- SQLite 可通过 FTS5 建立 `ocr_texts_fts` 虚表（后续实现），或在 PostgreSQL 中使用 `GIN` + `to_tsvector`。

## 表：download_logs
- id: INTEGER, PK
- image_id: INTEGER, FK -> images.id
- user_id: INTEGER, FK -> users.id, 可空（匿名下载）
- timestamp: DATETIME, DEFAULT NOW
- ip: VARCHAR(64)

## 关系与完整性
- users 1:N images
- images 1:1 embeddings（可扩展为 1:N 以支持多模型）
- images 1:1 ocr_texts
- images 1:N download_logs

## 约束建议
- images.checksum UNIQUE 以实现去重（冲突时返回已存在资源信息）
- 外键均使用 ON DELETE SET NULL 或 CASCADE（按业务选择；开发先用 SET NULL）

## 迁移与初始化
### 快速初始化（开发）
```bash
conda run -n imagedrive python scripts/init_db.py
```
或：
```python
from app import create_app, db
app = create_app()
with app.app_context():
	db.create_all()
```

### Alembic / Flask-Migrate（规划）
安装已在 requirements：`Flask-Migrate`, `Alembic`
预计添加到 `app.py`：
```python
from flask_migrate import Migrate
migrate = Migrate(app, db)
```
初始化迁移：
```bash
flask db init
flask db migrate -m "init"
flask db upgrade
```

### 字段变更流程
1. 修改 `models.py`
2. 运行 `flask db migrate -m "describe change"`
3. 审核自动生成文件，必要时手动调整
4. `flask db upgrade` 应用到本地 / 测试环境

## 常用查询示例
```python
from models import User, Image, Embedding, OCRText
from app import create_app, db

app = create_app()
with app.app_context():
	# 所有用户
	users = User.query.all()

	# 最近上传的 10 张图片
	latest = Image.query.order_by(Image.created_at.desc()).limit(10).all()

	# 根据 checksum 查重
	existing = Image.query.filter_by(checksum="abcd1234").first()

	# 某图片的 OCR 文本
	ocr = OCRText.query.filter_by(image_id=123).first()

	# 某图片向量引用
	emb = Embedding.query.filter_by(image_id=123).first()
```

## SQLite 与 PostgreSQL 差异注意事项
| 主题 | SQLite | PostgreSQL |
|------|--------|------------|
| 并发写入 | 锁粒度粗，适合低并发开发 | 行级锁，适合生产高并发 |
| FTS 支持 | 需 FTS5 虚表 | 原生 `to_tsvector` + GIN/GIST 索引 |
| 数据类型 | 动态类型弱 | 强类型，多样索引策略 |
| JSON 支持 | 需手动序列化 TEXT | 原生 JSON/JSONB 字段 |

## 后续扩展字段建议
- Image: width, height, format, exif_json
- Embedding: model_name, dim, version
- OCRText: language, confidence_avg
- DownloadLog: user_agent

## 数据一致性与清理策略（规划）
- 当删除 Image 时：对应 Embedding/OCRText/DownloadLog 记录同步删除（CASCADE）
- 定期清理：孤立的 Embedding/OCRText（无对应 image）
- 去重落库策略：插入前先比对 checksum；若存在则复用旧记录并返回其 id。

## 安全与审计（规划）
- DownloadLog 可扩展记录：user_id, success_flag, latency_ms
- 敏感字段（密码哈希）不出现在日志与导出。

## 测试数据注入建议
在 `scripts/` 添加 `seed_demo.py`：批量插入 5~10 条 Image 与对应 OCRText/Embedding 占位，方便前端联调与搜索开发。

---
更新本文件的原则：**任何模型字段或索引改动需同步此文档**，并在 PR 中标注 “DB schema 变更”。
