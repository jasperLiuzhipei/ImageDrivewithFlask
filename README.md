# WebImageDrive (Flask)

一个可运行的智能图片素材库后端（Flask），包含认证、文件、图片、搜索、处理、分析等模块的接口占位与文档规范，面向多模块团队并行开发。

## 文档入口（强烈建议按顺序阅读）
- 项目结构（带注释）：`docs/PROJECT_STRUCTURE.md`
- 架构逻辑树与数据流：`architecture.md`
- API 规范（OpenAPI 3）：`api_spec.yaml`
- API 使用指南（示例/导入）：`docs/API_USAGE.md`
- 数据库结构与使用说明：`db_schema.md`
- 统一约定（响应/分页/错误/权限）：`api_conventions.md`
- 团队交接指南（可直接发送）：`docs/HANDOFF_TEAM_GUIDE.txt`

## 当前状态（2025-11）
- 服务可启动；部分接口返回占位数据，已统一响应结构。
- 已有的关键端点：上传、图片列表/详情（占位）、搜索（占位）、处理触发（占位）。
- 已提供 DB schema 文档与初始化脚本；迁移（Flask-Migrate）待接入。
- 依赖已补齐 CORS/YAML/迁移/结构化日志等，便于联调与后续落地。

## 快速开始（推荐 conda）

Pillow 在某些 Python 版本上构建较麻烦，推荐使用 conda 的 Python 3.11 环境。

```bash
# 使用你已有的 conda（示例）
conda create -n imagedrive python=3.11 -y
conda run -n imagedrive pip install -r requirements.txt

# 初始化数据库（开发）
conda run -n imagedrive python scripts/init_db.py

# 运行（方式一：flask run）
conda run -n imagedrive bash -lc 'export FLASK_APP=app:create_app && flask run'

# 运行（方式二：python app.py）
conda run -n imagedrive python app.py
```

### 可选：使用 venv
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=app:create_app
flask run
```

### CORS（前端本地联调）
项目已依赖 Flask-Cors；若需要全局启用，请在 `app.py` 中初始化 CORS（未来会默认打开）。

## 目录速览
（完整说明见 `docs/PROJECT_STRUCTURE.md`）

```
WebImageDrive_Flask/
├─ app.py                # 应用工厂，注册蓝图
├─ blueprints/           # REST 模块：auth/files/images/search/process/analytics
├─ models.py             # ORM 模型（User/Image/Embedding/OCRText/DownloadLog）
├─ utils/response.py     # 统一响应封装 success()/error()
├─ api_spec.yaml         # OpenAPI 3 规范（16+ 端点）
├─ api_conventions.md    # 响应/分页/错误/权限约定
├─ db_schema.md          # 数据库结构与使用说明
├─ architecture.md       # 架构逻辑树与数据流
├─ docs/                 # 团队指南与 API 使用示例
├─ scripts/init_db.py    # 初始化数据库脚本
├─ requirements.txt      # 运行与开发依赖
├─ .env.example          # 环境变量示例
└─ run.sh                # 本地运行脚本（开发）
```

## 已实现与待实现

| 模块 | 已实现 | 待实现 |
|------|--------|--------|
| 认证 | 路由占位（register/login） | JWT(access/refresh)、黑名单、受保护路由 |
| 上传 | multipart 保存到 uploads/ | checksum 去重、缩略图生成、Image 元数据入库、下载权限 |
| 图片 | 列表/详情占位返回 | 分页与过滤、详情返回 OCR/embedding 引用 |
| 搜索 | text/similar/ocr 路由占位 | 向量检索/FTS/评分字段、结果 schema 规范化 |
| 处理 | trigger 占位 | 任务状态、作业持久化、失败重试 |
| 分析 | summary 占位 | 统计计算与导出 CSV/JSON，一致响应 |
| DB   | schema 文档+init 脚本 | 迁移体系（Flask-Migrate/Alembic） |
| 日志 | 轮转日志基础 | JSON 结构化、多分类日志、脱敏 |
| 测试 | 待补充 | pytest 基础用例 + CI |

## 常用开发流程

1) 初始化数据库（开发）
```bash
conda run -n imagedrive python scripts/init_db.py
```

2) 启动服务（任选其一）
```bash
# Flask run（推荐）
export FLASK_APP=app:create_app
flask run

# 直接运行 app.py
python app.py
```

3) 示例请求（占位返回，仅用于联调结构）
```bash
# 登录（占位 token）
curl -X POST http://localhost:5000/api/auth/login -H 'Content-Type: application/json' \
	-d '{"username":"alice","password":"pass"}'

# 上传
curl -X POST http://localhost:5000/api/files/upload -F 'file=@/path/to/img.png'

# 图片列表
curl 'http://localhost:5000/api/images?page=1&page_size=20'

# 文本搜索（占位 results）
curl 'http://localhost:5000/api/search/text?q=coffee&k=10'
```

## 团队协作指引

- 按文档入口顺序先对齐规范，再开发代码。
- 改动接口或模型时，务必同步更新：`api_spec.yaml`、`api_conventions.md`、`db_schema.md` 与相关指南。
- 建议新增 `services/` 层承载业务逻辑，蓝图只做请求解析与响应包装。
- 计划新增抽象：`vector_store.py`（统一对接 FAISS/pgvector），`embedding_pipeline.py`、`ocr_pipeline.py`。

## 代码规范与工具

```bash
# 代码检查
flake8

# 格式化
black .

# 测试（将随功能补充）
pytest -q
```

## 环境变量（开发默认值可用）

参见 `config.py` 与 `.env.example`：
- `SECRET_KEY`（默认 dev-secret）
- `DATABASE_URL`（默认 SQLite data.db）
- `UPLOAD_FOLDER`、`LOG_DIR`

## 故障排查（FAQ）
- Pillow 安装问题：优先使用 Python 3.11 + conda；requirements 已固定 Pillow==10.0.1。
- 端口占用：修改 `flask run --port` 或 `run.sh` 内端口。
- SQLite “database is locked”：高并发写入请改用 PostgreSQL 并启用迁移。
- CORS 报错：启用 Flask-Cors，并在创建 app 时允许前端来源。

## 路线图（短期）
## 测试 & 环境自检

### 1. 运行单元测试（当前仅健康检查示例，会逐步扩充）
```bash
pytest -q
```
预期输出：所有测试通过（当前 1 个通过）。

### 2. 运行环境验证脚本
```bash
python scripts/verify_env.py
```
该脚本会：
- 打印核心依赖版本（Flask / Pillow / SQLAlchemy / Werkzeug）
- 尝试创建上传与日志目录
- 测试数据库连接（SQLite）
- 请求根路由并输出 JSON 响应
显示 `=== Verification PASSED ===` 表示环境就绪。

### 3. 典型失败场景
| 场景 | 可能提示 | 解决方式 |
|------|----------|----------|
| ModuleNotFoundError: app | 路径未加入 | 使用 `python scripts/verify_env.py` 而不是从其他目录执行，或手动 `cd` 至根目录 |
| AttributeError: werkzeug.__version__ | Werkzeug 3.x 与 Flask 2.2.x 不兼容 | 已在 requirements 固定 Werkzeug==2.3.7，重新安装依赖 |
| Pillow 编译失败 | 无法编译源包 | 使用 conda Python 3.11, 或 `pip install --upgrade pip` 后重试 |
| database is locked | SQLite 写锁争用 | 降低并发/切换 PostgreSQL |

### 4. 持续扩展计划（测试）
- 增加：上传 → 列表 → 详情 流程集成测试
- 增加：JWT 认证流程测试（登录/刷新/访问保护资源）
- 增加：搜索接口在索引不可用时的降级行为测试


1) 实装 JWT 与受保护路由；完善错误码
2) 上传链路：checksum/缩略图/入库/下载权限
3) 搜索：接入向量索引与 FTS，统一结果 schema（含 score）
4) 统计：summary/export 一致响应 + 指标计算
5) 迁移 + 测试 + 结构化日志文档
