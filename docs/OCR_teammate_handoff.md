# OCR 集成对接说明（给 OCR 同学）

**目标**
- 提供稳健的 OCR 单图与批处理能力，支持可选语言/设备配置，返回稳定可检索的纯文本。
- 本仓库通过一个适配层动态加载你的 `ocr_pipeline.py`，并负责将结果入库与检索。

**分工与改动入口**
- 你需要修改你自己的仓库文件：`others/imagedrive--OCR-main/ocr_pipeline.py`
  - 对外导出稳定函数：`process_image` 与 `process_image_batch`（见下方签名与约定）。
  - 在函数内部实现 lang/device/batch 能力，做好错误与边界处理。
- 本仓库已对接点（无需你直接改）：
  - `app/services/ocr.py`：动态加载并调用你的函数（已兼容不同命名，优先 `process_image`/`process_image_batch`）。
  - `app/blueprints/ingest/__init__.py`：提供单图/批量 OCR 入库接口，写入表 `OCRText`。
  - `app/blueprints/search_ocr/__init__.py`：基于 `OCRText` 的简单文本搜索，返回命中片段。

---

## 1) 你需要提供的接口（强烈建议保持以下签名与语义）

- `process_image(path: str, lang: str | None = None, device: str | None = None) -> str`
  - 输入：本地图片路径；可选语言与设备参数。
  - 返回：稳定字符串；无文本时返回空字符串 ""（不要返回 None，不要抛异常到调用方）。

- `process_image_batch(paths: list[str], batch_size: int = 32, lang: str | None = None, device: str | None = None) -> list[str]`
  - 输入：本地图片路径列表；可选批大小、语言、设备。
  - 返回：长度与输入一致的字符串列表；逐项出错或无文本时返回 ""，不可因个别失败导致整体异常或长度错位。

可选为了兼容旧代码，你也可以提供别名：
```python
extract_text_from_image_path = process_image
```

---

## 2) 错误与边界处理（务必做到“可控不崩溃”）
- 非图片/文件不可读：返回 ""；记录日志即可，不要向外抛异常导致 500。
- 识别为空（纯图形/无文本）：返回 ""。
- `device` 不可用（如 cuda/mps）：自动降级到 CPU 并给出一次性警告日志。
- `lang` 未支持：忽略并走默认模型/策略，不报错。
- 批处理：任何单项失败仅影响该项，返回列表长度总是等于输入长度，顺序一致。

---

## 3) 性能与参数建议
- 优先实现批推理（`process_image_batch`），内部可对超长列表分块以控制显存/内存。
- `batch_size` 可调；设备优先使用可用的 `cuda`/`mps`，否则自动 `cpu`。
- 可以在内部做文本清洗（去多余空白、统一换行），保持检索友好。

---

## 4) 返回文本规范
- 始终返回 UTF-8 字符串。
- 无文本返回 ""；不要返回 None，不要返回复杂结构（位置/置信度等后续再扩展）。
- 尽量保留基本标点，去除控制字符；可以做适度空白归一化。

---

## 5) 本仓库对接逻辑（已实现）
- `app/services/ocr.py`
  - 动态加载 `others/imagedrive--OCR-main/ocr_pipeline.py`。
  - 现已优先调用 `process_image`/`process_image_batch`，若不存在再回退旧命名 `extract_text_from_image_path` 或逐张处理。
  - 批处理对不同签名做了兼容：尝试 `batch_size` 关键字、位置参数或不带该参数的调用。
  - 对任何异常进行温和降级：单图返回 `None`；批处理返回等长的 `None` 列表（上层会按空文本处理）。

- `app/blueprints/ingest/__init__.py`
  - `POST /api/v1/ingest/ocr`：单图 OCR 入库，返回 `has_text`、`created`，可选 `text_preview`。
  - `POST /api/v1/ingest/ocr/batch`：批处理 OCR 入库，逐项返回 `ok/has_text/text_preview`。
  - 仅处理当前用户拥有且为本地存储（`local://...`）的图片；找不到或无权限会返回对应错误项。

- `app/blueprints/search_ocr/__init__.py`
  - `POST /api/v1/search/ocr`：在当前用户的 OCR 文本上做包含查询（`ilike`），返回命中上下文片段 `snippet` 与 `image_id`。

---

## 6) 两种实施路径
- 方案 A（最小改动，优先稳定）
  - 你只需按上述签名实现 `process_image`/`process_image_batch`，本仓库无需改参数即可直接受益（OCR 更稳、更快）。

- 方案 B（透传高级参数）
  - 在 A 的基础上，本仓库可把 `lang/device` 作为可选参数透传给你：
    - 在 `app/services/ocr.py` 增强 `extract_text*` 以透传；
    - 在 `POST /api/v1/ingest/ocr` 与 `/ocr/batch` 读取 `lang/device` 并传下去；
    - 前端/文档补充可选参数区。

> 当前状态：我们已完成 A 的关键对接与兼容；若你按以上签名实现，后端即刻可用。若需要 B，请告知，我们将补充透传与前端选项。

---

## 7) 快速验证

后端已启动并完成登录（拿到 `JWT`）后：

```bash
# 单图 OCR 入库
curl -X POST http://127.0.0.1:5000/api/v1/ingest/ocr \
  -H "Authorization: Bearer <JWT>" -H "Content-Type: application/json" \
  -d '{"image_id": 1, "include_text": true, "snippet_len": 120}'

# 批处理 OCR 入库
curl -X POST http://127.0.0.1:5000/api/v1/ingest/ocr/batch \
  -H "Authorization: Bearer <JWT>" -H "Content-Type: application/json" \
  -d '{"image_ids": [1,2,3], "batch_size": 16, "include_text": true}'

# OCR 文本搜索
curl -X POST http://127.0.0.1:5000/api/v1/search/ocr \
  -H "Authorization: Bearer <JWT>" -H "Content-Type: application/json" \
  -d '{"query": "invoice", "top_k": 20}'
```

你在自己仓库最小自测（无需跑后端）：

```python
# 在 others/imagedrive--OCR-main 目录下
import ocr_pipeline as m
print(m.process_image("/abs/path/sample.jpg"))
print(m.process_image_batch(["/abs/path/1.jpg","/abs/path/2.jpg"], batch_size=16))
```

---

## 8) 相关文件速览（本仓库）
- `app/services/ocr.py`：适配层（动态加载 + 命名兼容 + 兜底）。
- `app/blueprints/ingest/__init__.py`：单图/批量 OCR 入库接口。
- `app/blueprints/search_ocr/__init__.py`：OCR 文本搜索接口。
- `others/imagedrive--OCR-main/ocr_pipeline.py`：你的实现文件（需导出 `process_image`/`process_image_batch`）。

如需我们开启参数透传（lang/device）或前端开关，请直接告知，我们可以在此基础上继续补齐。
