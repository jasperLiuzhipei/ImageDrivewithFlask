# API Conventions

本文件定义 WebImageDrive 项目的通用 API 约定：响应封包结构、错误码、分页与过滤、鉴权与安全、上传规则、搜索行为以及速率限制预留。

## 1. 统一响应结构

所有成功或失败响应均使用统一 JSON 封包：

```jsonc
{
  "success": true,            // bool: 请求是否成功
  "data": { /* 任意数据 */ }, // 成功时的主体数据；失败时为 null
  "error": {                  // 失败时包含错误细节；成功时为 null
    "code": 2001,             // 业务错误码（非 HTTP status）
    "message": "Invalid credentials", // 简明错误描述（可直接展示）
    "details": { /* 可选：字段错误列表、调试信息（生产环境避免泄露） */ }
  }
}
```

约束：
- HTTP status 表示协议级语义（200, 201, 400, 401, 404, 500 等）。
- `error.code` 为业务码，用于前端区分具体错误类别；命名空间按千位划分。

## 2. 错误码设计（初稿）

| 范围      | 类别                 | 示例 |
|-----------|----------------------|------|
| 1000-1099 | 参数与校验错误       | 1001=MissingParameter, 1002=InvalidFormat |
| 2000-2099 | 认证与授权错误       | 2001=InvalidCredentials, 2002=TokenExpired, 2003=PermissionDenied |
| 3000-3099 | 文件与资源错误       | 3001=FileNotFound, 3002=DuplicateChecksum, 3003=UnsupportedMedia |
| 4000-4099 | 处理任务相关错误     | 4001=TaskNotFound, 4002=TaskFailed, 4003=AlreadyQueued |
| 5000-5099 | 索引/搜索相关错误    | 5001=VectorIndexUnavailable, 5002=FTSNotReady |
| 9000-9099 | 系统内部/未知错误    | 9000=InternalError |

前端根据 `error.code` 决定提示与重试策略。日志中需同时记录 HTTP status 与业务错误码。

## 3. 分页与过滤

通用查询参数：
- `page`: 1-based，默认 1。
- `page_size`: 默认 20，最大 100（超出则强制设为 100）。
- `sort`: 排序字段，前缀 `-` 表示降序（例：`-created_at`，`size`）。
- `category`: 单分类过滤。
- `tags`: 逗号分隔标签列表（后端按包含任意或全部，可在文档标注策略——此实现采用包含任意标签）。

分页响应示例：

```jsonc
{
  "success": true,
  "data": {
    "items": [ { "id": 1, "filename": "a.jpg" } ],
    "meta": { "page": 1, "page_size": 20, "total": 57 }
  },
  "error": null
}
```

## 4. 鉴权与安全

- 所有需要身份的端点使用 JWT Bearer：`Authorization: Bearer <access_token>`。
- `access_token` 有效期建议 15~30 分钟；`refresh_token` 有效期 7~30 天（可配置）。
- 刷新流程：`/auth/refresh` 仅接收 refresh token（不需 Authorization 头），返回新 access token。
- 登出流程：`/auth/logout` 将 refresh token 加入黑名单（内存结构或持久化表）。
- 密码哈希：使用 `passlib` 的 bcrypt；成本因子（rounds）保持默认或配置化（记录在 `security.md`）。
- 限制敏感日志：不记录明文密码、完整 token；仅截取 token 前 8 字符用于追踪。

## 5. 上传与文件处理

- 接口：`POST /files/upload`，multipart/form-data，字段：`file`, 可选 `category`, 可选 `tags[]`。
- 去重策略：计算文件内容 checksum（SHA256），若重复则返回已存在资源的 metadata（错误码或普通 200，采用普通成功 + 标注 `duplicate: true` 更易用）。
- 缩略图：后续扩展 `thumbnails/<id>_sm.jpg`，接口可在 `Image` 元数据中增加 `thumb_url` 字段。暂未写入规范，可第二阶段添加。

## 6. 搜索行为说明

- 文本语义搜索：`GET /search/text?q=...&k=` 使用嵌入向量最近邻（需 embedding 准备完成）。
- 图像相似：`GET /search/similar?image_id=...` 或传 `embedding_ref`。若向量索引尚未就绪，返回 `success=false` 并附 `error.code=5001`。
- OCR 文本搜索：`GET /search/ocr?q=...` 基于 FTS 或 LIKE；支持分页；可后续扩展高亮返回。

## 7. 处理任务（Embedding / OCR）

- `POST /process/trigger` 的 `tasks` 数组支持 `embedding` 与 `ocr`，后端入队异步任务。
- `GET /process/status?image_id=` 返回各任务状态：`{"embedding":"done|pending|failed", "ocr":"done|pending|failed"}`。
- 幂等：重复触发已完成任务时返回已完成状态，不重新排队（除非显式 `force=true` 未来扩展）。

## 8. 分析端点

- `GET /analytics/summary` 聚合：类别分布、上传趋势（按 window）、大小分布（bucket）。
- `GET /analytics/export?format=csv|json` 返回与 summary 相同数据的导出形式。CSV 采用 `text/csv`；JSON 同统一封包。

## 9. 速率限制（预留）

暂未实现；未来可在网关或 Flask 中添加基于 IP + 用户的令牌桶：如登录与注册端点限制每分钟 10 次。

## 10. 版本与兼容策略

- 当前仅一个 API 版本（`/api`），若后续出现重大不兼容可采用 `/api/v2` 路径并保留旧版本一段时间。

## 11. 示例错误响应

```json
{
  "success": false,
  "data": null,
  "error": { "code": 2002, "message": "Token expired", "details": null }
}
```

## 12. 后续扩展建议

- 增加批量上传：`POST /files/batch` 接收多个文件；响应中提供逐项状态。
- 增加删除与软删除：`DELETE /images/{id}` + 标记软删除字段用于审计恢复。
- 为搜索结果添加 `score` 字段（浮点，归一化到 0~1）与可选阈值过滤。
- 增加高亮 OCR 片段：返回匹配跨度和上下文。
