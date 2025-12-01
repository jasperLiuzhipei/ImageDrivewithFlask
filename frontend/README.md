# WebImageDrive Frontend

## 快速开始（本地开发）

要求：Node.js >= 18（推荐 20+）

```zsh
# 安装依赖
cd frontend
npm install

# 启动开发服务器（默认端口 5173）
npm run dev
```

打开浏览器访问 http://localhost:5173

- 首次使用：到“注册/登录”页面注册或登录；成功后 token 会保存在 localStorage。
- 上传：在“上传”页面选择图片提交，返回的 `image_id` 可用于相似检索与 OCR。
- 文本搜索：在“文本搜索”页面输入查询词，返回相似图片及分数。
- OCR：在“OCR 搜索”和“OCR 入库（通过上传自动/或单图/批量）”页面使用。
- 健康检查：在“健康检查”查看后端状态（嵌入后端、维度等）。

## API 基址与代理

- 开发模式默认走代理，`/api/v1` 由 Vite 代理到 `http://127.0.0.1:5000`（见 `vite.config.ts`）。
- 若需直连后端或生产部署，请提供环境变量覆盖：

```zsh
# 方式一：临时设置
VITE_API_BASE="https://your-server.example.com/api/v1" npm run dev

# 方式二：写入 .env 文件
# 新建 frontend/.env 或 .env.production:
VITE_API_BASE=https://your-server.example.com/api/v1
```

> 生产环境构建：
>
> ```zsh
> npm run build
> npm run preview # 本地预览静态产物
> ```

## 常见问题

- CORS 跨域：开发模式默认通过 Vite 代理规避，无需改后端。
- 401 未认证：确认已在“登录”页面成功登录；或清除浏览器 localStorage 后重试。
- 后端地址：后端在本机 5000 端口，确保 Flask 已启动（见项目根 README）。
