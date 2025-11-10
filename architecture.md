# WebImageDrive 架构逻辑树 (当前版本快照)

> 目的：为前端、算法、后端、运维快速理解目前的模块边界、数据流与演进路线。此文档对应代码版本（功能占位阶段，尚未实现真实鉴权/搜索/分析）。

## 1. 分层概览

```
Client (Browser / Tools / Postman)
    |
    | HTTP/JSON (统一响应包)
    v
Flask App (app.py)
    ├─ Config / Env (config.py, .env.example)
    ├─ Logging (logging_config.py)
    ├─ Blueprints (REST API)
    │    ├─ auth         (/api/auth/*)
    │    ├─ files        (/api/files/*)
    │    ├─ images       (/api/images/*)
    │    ├─ search       (/api/search/*)
    │    ├─ processing   (/api/process/*)
    │    └─ analytics    (/api/analytics/*)
    ├─ Models / ORM (models.py, SQLAlchemy)
    ├─ Response Utils (utils/response.py)
    ├─ Scripts (scripts/init_db.py)
    └─ Spec Docs (api_spec.yaml, api_conventions.md, db_schema.md)
        └─ Architecture (architecture.md)
```

后续将新增：`services/` 业务服务层、`vector_store.py` 向量索引抽象、`tasks/` 异步任务或队列适配。

## 2. 模块逻辑树

### 2.1 蓝图与端点

```
auth
  ├─ POST /auth/register    注册（占位，无 DB 写入）
  ├─ POST /auth/login       登录（占位，返回 stub tokens）
  ├─ POST /auth/refresh     刷新令牌（规范中定义，待实现）
  └─ POST /auth/logout      登出/黑名单（待实现）

files
  ├─ POST /files/upload     上传文件，保存磁盘，返回路径（未做 checksum 去重/缩略图）
  └─ GET  /files/{id}/download  规范中定义，占位未实现

images
  ├─ GET /images            分页/过滤（占位返回空列表）
  └─ GET /images/{id}       元数据详情（占位）

search
  ├─ GET /search/text       文本语义占位（返回 query 空结果）
  ├─ GET /search/similar    相似检索占位
  └─ GET /search/ocr        OCR 文本检索占位

processing
  ├─ POST /process/trigger  触发 embedding / ocr 任务（记录请求，返回 queued_tasks）
  └─ GET /process/status    任务状态查询（待实现）

analytics
  ├─ GET /analytics/summary 基础统计占位
  └─ GET /analytics/export  导出（待实现）
```

### 2.2 数据模型树 (models.py)

```
User
  ├─ id, username(unique), password_hash, created_at

Image
  ├─ id, filename, path, checksum(index), uploader_id(FK User)
  ├─ size, mime, category, tags, created_at

Embedding
  ├─ id, image_id(FK Image, index), vector_ref, created_at

OCRText
  ├─ id, image_id(FK Image, index), text, created_at

DownloadLog
  ├─ id, image_id(FK Image), user_id(FK User nullable), timestamp, ip
```

即将补充：关系（backref）、checksum 唯一索引、OCR FTS、软删除标记、图片宽高/格式、向量维度元数据。

### 2.3 响应与错误

统一响应包：

```
{
  "success": true/false,
  "data": <任意业务对象或 null>,
  "error": { "code": int, "message": str, "details": any|null }
}
```

当前错误码示例（占位）：
```
1001 参数缺失 / 验证失败
1002 文件名为空
...  后续将扩展：2xxx 认证、3xxx 文件处理、4xxx 搜索、5xxx 系统错误
```

### 2.4 数据流（典型场景）

#### 上传 + 后续处理（目标态 vs 当前态）

```
[当前]
Client -> POST /files/upload → 保存文件 → 返回 {filename,path}

[目标演进]
Client -> POST /files/upload
    -> 保存原图 & 计算 checksum
    -> 若重复：返回已有资源引用
    -> 异步：生成缩略图 / 提交 embedding & OCR 任务
    -> 持久化 Image 记录
    -> 返回 Image 完整元数据 + 后续任务状态入口 (/process/status)
```

#### 检索（目标态）

```
Client -> GET /search/text?q=... → 基于 OCRText / Embedding 混合策略 → 返回匹配 Image 列表
Client -> GET /search/similar?image_id=... → 读取 Embedding → 调用 vector_store.search → 返回最近邻
Client -> GET /search/ocr?q=... → SQLite FTS / LIKE 条件 → 分页返回
```

#### 统计分析（目标态）

```
Client -> GET /analytics/summary?window=week → 聚合: 上传数/类别分布/大小分布
Client -> GET /analytics/export?format=csv → 生成临时 CSV 流 → 下载
```

### 2.5 依赖与扩展点

| 组件 | 现状 | 后续扩展 |
|------|------|----------|
| 鉴权 | 占位（stub tokens） | JWT(access/refresh)、黑名单、角色/权限 |
| 文件存储 | 本地 uploads/ | S3/OSS、分块上传、CDN、缩略图管线 |
| 向量检索 | 未实现 | `vector_store.py` 抽象 + FAISS/pgvector provider |
| OCR/Embedding | 占位触发 | 任务队列（Celery / RQ）与状态跟踪 |
| 日志 | 基础轮转 | JSON 结构化、多分类日志文件、敏感信息脱敏 |
| 测试 | 未添加 | pytest 单元 & 集成，CI pipeline |

## 3. 前后端对接清单

| 功能 | 前端当前可调用 | 期望返回 | 备注 |
|------|----------------|----------|------|
| 注册/登录 | POST /auth/register / /auth/login | 占位 tokens / 用户名 | 等待真实 JWT 接入 |
| 上传 | POST /files/upload | 文件基本信息 | 即将返回 Image 完整元数据 |
| 图片列表 | GET /images | 空列表占位结构 | 将补分页/过滤逻辑 |
| 图片详情 | GET /images/{id} | 占位 metadata | 后续加入 OCR / embedding 引用 |
| 文本搜索 | GET /search/text | query + 空结果 | 后续接 Embedding 语义检索 |
| 处理触发 | POST /process/trigger | queued_tasks | 将返回 task_id & 状态查询入口 |
| 统计 | GET /analytics/summary | 空 summary | 聚合逻辑待实现 |

## 4. 演进路线 (优先级建议)

1. 鉴权落地：JWT、密码哈希、保护受限端点 (`users/me`, future downloads)
2. 文件增强：checksum 去重、缩略图、Image 表写入、下载接口安全控制
3. 向量与 OCR：定义 `vector_store.py` + Embedding/OCR 落库 + 搜索真实返回
4. 分析与日志：统计查询、结构化日志、性能指标
5. 测试与质量：pytest 基础用例 + flake8/black + CI

## 5. 约束与注意事项

- 当前返回的 tokens 仅占位，不具备安全性；前端勿长期缓存。
- 上传暂不做重复检查，请不要基于返回判断唯一性。
- 搜索与统计结果为空属正常占位表现，不代表错误。
- 数据库为 SQLite，开发期注意并发写入（任务队列上线后可切 Postgres）。

## 6. 快速引用索引

| 文件 | 作用 |
|------|------|
| app.py | App Factory + 蓝图注册 |
| config.py | 配置（数据库、上传、日志路径） |
| models.py | ORM 模型初版 |
| blueprints/*.py | 各 REST 模块入口 |
| utils/response.py | 统一响应封装 |
| api_spec.yaml | OpenAPI 规范（16 端点） |
| api_conventions.md | 响应/分页/错误/权限约定 |
| db_schema.md | 表结构与索引规划 |
| scripts/init_db.py | 初始化数据库脚本 |
| architecture.md | 架构与逻辑树文档（本文件） |

## 7. 后续补充计划 (占位文件建议)

```
services/
  auth_service.py      # 用户/令牌逻辑
  file_service.py      # 上传、缩略图、校验
  search_service.py    # 组合 OCR + Embedding 检索
  analytics_service.py # 聚合与导出

vector_store.py        # 向量索引抽象接口
security.md            # JWT/令牌策略与刷新规则
logging.md             # 日志字段与分类规范
tests/                 # pytest 用例
```

---
若需针对某层添加更细的时序图或类图，请提出具体场景（例如“上传后异步管线”），我可以在下个迭代附加 UML/PlantUML 描述。
