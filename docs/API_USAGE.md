# API 使用指南 (当前占位实现阶段)

本指南帮助团队快速调用后端接口。正式上线前部分端点仅返回占位数据，其结构已与 `api_spec.yaml` 保持一致，方便前端与其他模块提前集成。

## 目录
1. 基本约定
2. 认证流程 (规划 & 占位)
3. 文件上传示例
4. 图片列表与详情
5. 搜索接口示例
6. 处理任务触发
7. 数据统计接口
8. 错误响应规范
9. 如何导入 OpenAPI 到工具

---
## 1. 基本约定
- Base URL (开发): `http://localhost:5000/api`
- 所有成功响应: `{"success": true, "data": <对象>, "error": null}`
- 错误响应: `{"success": false, "data": null, "error": {"code": <int>, "message": <str>, "details": <可选>}}`
- 分页参数: `page` (默认 1), `page_size` (默认 20, 最大 100)
- 未来鉴权: `Authorization: Bearer <access_token>` (当前未启用)

## 2. 认证流程 (规划 & 占位)

当前阶段：`/auth/register` 与 `/auth/login` 返回占位数据，不写入数据库。后续将：
1. 注册：检查用户名唯一 -> 创建用户 -> 返回用户信息。
2. 登录：验证密码 -> 签发 access/refresh token。
3. 刷新：`/auth/refresh` 用 refresh_token 获取新 access_token。
4. 登出：`/auth/logout` 将 refresh_token 加入黑名单。

示例（占位返回）：
```
POST /api/auth/login
{ "username": "alice", "password": "pass" }
-> {"success": true, "data": {"access_token": "stub-access", "refresh_token": "stub-refresh"}, "error": null}
```

## 3. 文件上传示例
端点：`POST /api/files/upload`

请求 (multipart/form-data):
```
file: <binary image>
category: optional
tags: optional (前端目前可不传，后续改造为数组)
```

响应（当前占位）：
```
{"success": true, "data": {"filename": "cat.png", "path": "<本地绝对路径>"}, "error": null}
```

后续增强：返回 Image 完整元数据 (id, url, checksum, size, created_at 等)。

## 4. 图片列表与详情
- 列表：`GET /api/images?page=1&page_size=20&category=&tags=`
  - 当前返回：空 items + meta 占位
```
{"success": true, "data": {"items": [], "meta": {"page":1,"page_size":20,"total":0}}, "error": null}
```
- 详情：`GET /api/images/123`
  - 当前返回：
```
{"success": true, "data": {"id":123, "metadata": {}}, "error": null}
```

## 5. 搜索接口示例
### 文本搜索 (语义占位)
`GET /api/search/text?q=coffee&k=10`
```
{"success": true, "data": {"query":"coffee","results":[],"k":10}, "error": null}
```
### 相似检索 (占位)
`GET /api/search/similar?image_id=123&k=5`
### OCR 检索 (占位)
`GET /api/search/ocr?q=invoice&page=1&page_size=20`

后续：返回结果 items 数组；每个元素包含 image 基础字段 + score。

## 6. 处理任务触发
`POST /api/process/trigger`
```
{ "image_id": 123, "tasks": ["embedding", "ocr"] }
-> {"success": true, "data": {"image_id":123, "queued_tasks":["embedding","ocr"]}, "error": null}
```
后续：返回 task_id / 状态查询 endpoint。

## 7. 数据统计接口
`GET /api/analytics/summary?window=week`
当前返回：`{"summary":{}}` (尚未套统一响应；计划统一)
后续：
```
{"success": true, "data": {"uploads": 42, "by_category": {"animal":10}, "size_histogram": [...]}, "error": null}
```

## 8. 错误响应规范
常见错误码（占位）：
| code | 含义 |
|------|------|
| 1001 | 参数缺失 / 校验失败 |
| 1002 | 文件名为空 |
| 2001 | 认证失败（规划） |
| 2002 | Token 过期（规划） |
| 3001 | 重复上传（规划） |
| 4001 | 搜索引擎不可用（规划） |

统一处理建议：前端根据 `error.code` 做分支（如重试、跳转登录、提示用户）。

## 9. 如何导入 OpenAPI 到工具
1. 打开 Postman → Import → 选择 `api_spec.yaml`。
2. 或使用 Swagger UI：
   - 在线：访问 https://editor.swagger.io → File → Import File → 选择本地 `api_spec.yaml`。
3. 生成客户端 SDK（可选）：使用 `openapi-generator-cli`，例如：
```
openapi-generator-cli generate -i api_spec.yaml -g python -o sdk-python
```

## 后续计划
- 接入真实 JWT 认证：登录后所有受保护路由需携带 Bearer token。
- 完整 Image 元数据返回：上传 + 列表 + 详情联通。
- 搜索返回结构规范化：`results: [{image: <Image>, score: <float>}, ...]`。
- 统计接口统一响应格式。

## 反馈
如发现文档遗漏或字段不清晰：
- 在 PR 中更新 `api_spec.yaml` 与本文件并 @相关负责人。
