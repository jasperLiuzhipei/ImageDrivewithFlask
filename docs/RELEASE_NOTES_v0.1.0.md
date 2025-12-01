# v0.1.0 — Initial public release

- Backend:
  - Flask 应用工厂 + Blueprints（Auth/Files/Search/OCR/Health）
  - 向量检索：FAISS 持久化（每用户），归一化 512 维向量，相似度返回
  - 嵌入运行时：默认对接队友 EmbeddingProcessor，支持切换，健康检查显示维度/后端
  - OCR：单图/批量入库与搜索，批量优先使用 process_image_batch
  - 统一 JSON 响应与错误码（基本版），上传自动提取嵌入与 OCR（尽力而为）
- Frontend:
  - Vue 3 + Vite + Element Plus，提供 登录/注册、上传、文本检索、OCR 检索、以图搜图、健康检查
  - 美化导航与结果展示，支持“查看相似”、相似度进度条、空状态与骨架屏
  - 本地代理联调：`/api/v1` 代理 `http://127.0.0.1:5000`
- Tooling:
  - Postman 集合与本地环境文件
  - CI: flake8 + 前端构建 + 轻量健康检查（容忍缺少重依赖）

## 快速开始（本地）

- 后端（Python 3.12，详见 requirements/environment）：
```zsh
python3 app.py
```
- 前端（Node 18+/20）：
```zsh
cd frontend
npm install
npm run dev
```
浏览器打开 http://localhost:5173

## 关键接口
- Auth: `/api/v1/auth/register|login|me`
- 上传: `POST /api/v1/files/upload`（multipart，返回 image_id）
- 文本检索: `POST /api/v1/search/text`（参数 `query`, `top_k`）
- 以图搜图: `GET /api/v1/search/image/{image_id}/similar?top_k=10`
- OCR 入库: `POST /api/v1/ingest/ocr`、`POST /api/v1/ingest/ocr/batch`（支持 `items` 或 `image_ids`）
- OCR 检索: `POST /api/v1/search/ocr`（参数 `query`, `top_k`）
- 健康: `GET /api/v1/health`

## 已知事项
- 缩略图/预览接口尚未提供；建议后续补充文件下载与缩略图生成
- 大规模 OCR/Embedding 建议使用任务队列（异步处理 + 进度轮询）
