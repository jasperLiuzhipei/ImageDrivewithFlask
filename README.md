# WebImageDrive (Flask) — 项目脚手架

最小可运行的 Flask 项目骨架，包含认证、文件、搜索、处理、分析等蓝图的占位实现。

## 文档入口
- 项目结构（带注释）：`docs/PROJECT_STRUCTURE.md`
- 架构逻辑树：`architecture.md`
- API 规范（OpenAPI）：`api_spec.yaml`
- API 使用指南（示例/导入）：`docs/API_USAGE.md`
- 数据库结构与使用说明：`db_schema.md`
- 统一约定（响应/分页/错误/权限）：`api_conventions.md`

快速开始（开发）

1. 创建虚拟环境并安装依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. 运行开发服务器：

```bash
export FLASK_APP=app:create_app
flask run
```

或：

```bash
python app.py
```

说明
- `app.py` - 应用工厂并注册蓝图
- `config.py` - 配置
- `models.py` - SQLAlchemy 模型（草稿）
- `blueprints/` - 各功能蓝图占位文件
- `requirements.txt` - 依赖列表
 - `docs/` - 二级文档（项目结构与 API 使用指南）

下一步建议
- 完成 `api_spec.yaml` 并实现认证、数据库迁移脚本、文件上传完整实现与测试。
