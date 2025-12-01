# Web Image Drive

简洁的使用说明，覆盖启动、管理员设置与基本操作。

## 先决条件

- Python 3.x（建议使用虚拟环境）
- Node.js 和 npm
- 可选：`jq` 用于命令行解析 JSON

## 快速启动

```bash
# 进入你的 Python 虚拟环境后
python3 -m pip install -r requirements.txt
bash scripts/dev.sh
```

说明：
- 当前终端后台运行后端（5000 端口），并进行健康检查
- 新 Terminal 窗口（macOS）或当前终端（Linux/Windows）运行前端开发服务（5173 端口）
- 访问前端：`http://localhost:5173`
- 停止：在运行脚本的终端按 `Ctrl+C`（会结束后端进程）

手动方式（两终端）：
```bash
# 终端 A（后端）
python3 app.py

# 终端 B（前端）
cd frontend && npm run build && npm run dev
```

可选：初始化默认管理员与示例用户

```bash
python3 -m scripts.seed
```

## 管理员权限

- 通过环境变量配置（支持 `.env`）：
  - `ADMIN_USER_IDS`：逗号分隔的用户 ID 列表，例如 `ADMIN_USER_IDS=1,2`
  - `ADMIN_USERS`：逗号分隔的用户名列表，例如 `ADMIN_USERS=alice,bob`
- 登录流程不变：管理员身份由后端运行时判定，无需单独的“管理员登录”。
- 访问规则：管理员可查看所有用户的图片与日志；普通用户仅能访问自己数据。

默认管理员账号：

- 用户名：`admin`
- 密码：`admin`
- 已由 `scripts/seed.py` 持久化创建，且在未显式配置环境变量时，用户名为 `admin` 的用户默认视为管理员。

临时设置管理员（当前会话生效）：

```bash
# 临时设置（当前终端会话生效）
export ADMIN_USER_IDS=1,2
export ADMIN_USERS=alice,bob
# 重启后端
bash scripts/dev.sh
```

写入 .env（持久化，可覆盖默认）：

```bash
printf "ADMIN_USER_IDS=1,2\nADMIN_USERS=alice,bob\n" >> .env
# 重启后端
bash scripts/dev.sh
```

查询自己的 user_id（示例）：

```bash
# 获取访问令牌
TOKEN=$(curl -s -X POST http://127.0.0.1:5000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"<your_password>"}' | jq -r '.data.access_token')

# 查询当前用户信息（含 user_id）
curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:5000/api/v1/auth/me

# 判断是否管理员（is_admin=true 表示管理员）
curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:5000/api/v1/auth/me | jq '.data.is_admin'
```

## 会话与安全

会话策略：
- 短期刷新保持登录；首次加载会自动恢复用户信息用于导航显示
- 长期不活动或断网太久后刷新，强制重登录（默认 30 分钟，可通过 `VITE_INACTIVITY_LIMIT_MINUTES` 配置）
- 前端构建变化或后端版本变化时刷新，强制重登录以保证隐私
- 未登录访问受保护页面自动跳转登录；401 会清空令牌并跳转登录
相关实现：
- 路由守卫：`frontend/src/router.ts`
- 401 拦截与活跃时间：`frontend/src/api.ts`
- 策略逻辑：`frontend/src/session.ts`
- 刷新恢复用户：`frontend/src/main.ts`

## 健康检查

- 后端健康接口：`GET /api/v1/health`
- 启动后可执行：
```bash
curl -s http://127.0.0.1:5000/api/v1/health
```

## 目录与端口

- 后端：`python3 app.py` 默认监听 `0.0.0.0:5000`
- 前端：`npm run dev` 默认监听 `localhost:5173`
- 开发代理：`frontend/vite.config.ts` 将 `'/api/v1'` 代理到 `http://127.0.0.1:5000`

## 常见问题

- 刷新后右上角显示“Login/Register”：应用会在启动时自动调用 `auth.me()` 恢复用户；如果仍未恢复，请确认令牌未过期
- 管理员设置不生效：需在启动前设置变量并重启后端；使用 `ADMIN_USER_IDS` 更稳妥（避免大小写问题）
- Linux/Windows 新窗口：脚本在非 macOS 下会在当前终端运行前端；如需新窗口，可手动在另一个终端执行前端命令

## Notes

- 若需使用 PostgreSQL、数据库迁移等，请参考代码中的 `app/config.py` 与 `flask-migrate`；默认使用 SQLite `./instance/app.db`。
