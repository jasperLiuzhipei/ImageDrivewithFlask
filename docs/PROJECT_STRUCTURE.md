# 项目结构与目录说明 (当前阶段)

```
WebImageDrive_Flask/
├─ app.py                  # 应用工厂 create_app()，注册所有蓝图
├─ config.py               # 全局配置 (SECRET_KEY, DB URI, 路径)
├─ models.py               # SQLAlchemy 模型初版 (User, Image, Embedding, OCRText, DownloadLog)
├─ logging_config.py       # 日志轮转与基础 logger 配置
├─ api_spec.yaml           # OpenAPI 3.0.3 规范 (16+ 端点)
├─ api_conventions.md      # 统一响应/分页/错误码/鉴权约定
├─ db_schema.md            # 数据库结构与字段/索引说明
├─ architecture.md         # 架构逻辑树与数据流说明
├─ requirements.txt        # 运行时 + 开发依赖（含 CORS/Migrate/FTS 预备）
├─ run.sh                  # 快速启动脚本 (开发模式)
├─ .env.example            # 环境变量示例 (SECRET_KEY 等)
├─ uploads/                # 上传文件存储目录 (开发模式本地持久)
├─ logs/                   # 日志输出目录 (轮转文件在此)
├─ blueprints/             # Flask 蓝图模块集合
│   ├─ auth.py             # 认证占位 (register/login 等)
│   ├─ files.py            # 上传接口 (后续扩展: checksum/缩略图/下载)
│   ├─ images.py           # 列表与详情占位
│   ├─ search.py           # 文本/相似/OCR 搜索占位
│   ├─ processing.py       # 触发 embedding/OCR 任务占位
│   ├─ analytics.py        # 数据统计占位
│   └─ __init__.py         # 包声明
├─ utils/
│   └─ response.py         # success()/error() 统一响应封装
├─ scripts/
│   └─ init_db.py          # 初始化数据库 & 种子数据（示例 user）
├─ docs/                   # 文档目录 (当前文件 + API_USAGE 计划)
│   └─ PROJECT_STRUCTURE.md# 本文件
└─ data.db                 # 默认 SQLite 数据库文件 (开发态)
```

## 目录策略
| 目录 / 文件 | 说明 | 后续扩展 |
|-------------|------|----------|
| blueprints/ | REST 接口边界，每个功能域一个文件 | 可拆分 service 层（services/）做业务逻辑解耦 |
| models.py   | 统一模型定义 | 迁移后可拆分 models/ 目录按领域拆文件 |
| scripts/    | 维护数据库/批处理脚本 | 增加迁移、数据回填、批量任务脚本 |
| utils/      | 小工具与通用辅助 | 增加校验、缓存、token 相关工具 |
| docs/       | 二级文档集合 | 添加 API_USAGE、SECURITY、LOGGING、MIGRATION 指南 |
| uploads/    | 本地文件存储 | 生产替换对象存储 (S3/OSS) 并用环境变量开关 |
| logs/       | 日志文件输出 | 细分多文件：app.log, access.log, error.log 等 |

## 代码组织原则
1. 蓝图只做请求解析与响应包装，业务逻辑迁出到 service 层（下一阶段）。
2. 响应结构保持一致：`utils/response.py` 中 success()/error()。
3. 所有外部集成（OCR、Embedding、向量索引）通过明确的抽象接口（例如 `vector_store.py`、`embedding_pipeline.py`）。
4. 模型演进通过 Alembic 迁移管理，避免手动修改生产表。
5. 文档与规范（OpenAPI、架构、DB）版本需在合并前更新，保证团队共享共识。

## 后续将新增的关键文件 (规划)
```
services/
  auth_service.py
  file_service.py
  search_service.py
  analytics_service.py
vector_store.py
embedding_pipeline.py
ocr_pipeline.py
security.md
logging.md
migration/ (Alembic 自动生成)
tests/
```

## 快速检查脚本建议 (占位说明)
后续可在 `scripts/` 添加：
- `check_spec.py`：加载 `api_spec.yaml` 验证 schema/路径数量。
- `smoke_test.py`：发起 3~5 个关键接口请求验证 200。

## 提交前核对 Checklist
- [ ] 新增或修改的接口已更新 `api_spec.yaml`
- [ ] 响应仍保持标准 envelope
- [ ] db_schema.md 若涉及模型变更已同步字段说明
- [ ] README 或 docs 中的链接未失效
- [ ] migrations 已生成并测试升级/降级
