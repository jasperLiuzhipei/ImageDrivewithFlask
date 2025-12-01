# 模块（二）：CLIP 图像与文本嵌入模块

本项目为 STAT7008A Topic 3 的核心 AI 模块之一，由 **LI-Ricardo** 负责。

根据团队分工，本模块的职责是提供一个统一的 CLIP 嵌入流水线。

## 模块功能

本模块提供了 `EmbeddingProcessor` 类，它封装了 CLIP 模型，并提供三个主要接口：

1. `embed_image(image_path)`: (在线) 为单张上传的图片生成向量。
2. `embed_text(text_query)`: (在线) 为用户的文本搜索词生成向量。
3. `embed_batch(image_paths)`: (离线) 批量为基础数据集生成向量。

**本项目不包含 OCR 功能**，OCR 将由模块（三）的负责人提供。

## 1. 环境依赖

请在你们的项目主 `requirements.txt` 中加入以下依赖，并安装：

```text
sentence-transformers
torch
Pillow
numpy
tqdm
```

安装命令:
```bash
python3 -m pip install -r requirements.txt
```

建议使用 conda/miniforge（特别是 macOS Apple Silicon）来安装 PyTorch，参考 https://pytorch.org/get-started/locally 获取针对你平台的正确安装命令。

## 2. 如何使用（给 Flask 和索引组员）

你们只需要从 `clip_pipeline.processor` 导入 `EmbeddingProcessor` 类。

### A. 给 Flask 负责人 (后端集成)

在程序启动时初始化一次 `EmbeddingProcessor`（只执行一次，避免重复加载模型）：

```python
from clip_pipeline.processor import EmbeddingProcessor

clip_processor = EmbeddingProcessor(model_name='clip-ViT-B-32')
```

文件上传时调用：
```python
embedding_vector = clip_processor.embed_image(saved_image_path)
```

文本搜索时调用：
```python
text_vector = clip_processor.embed_text(query)
```

### B. 给索引负责人 (FAISS)

需要的交付文件（由本模块生成）:
1. `data/output/embeddings.npy` — NumPy 矩阵，形状 (N, 512)
2. `data/output/image_metadata.json` — 包含 N 个图片元信息（index/path/synset/class_name）的列表

索引构建流程示例：
```python
import numpy as np
import json

embeddings = np.load('data/output/embeddings.npy')
with open('data/output/image_metadata.json', 'r') as f:
    image_metadata = json.load(f)

# 使用 faiss 构建索引，image_metadata[i] 对应 embeddings[i]
```

## 3. ImageNet 下载与准备（详细操作步骤）

下面的步骤假定你将使用官方 ImageNet 数据并把解压后的目录结构组织为：

```
data/imagenet_base/
  n01440764/
    img1.JPEG
    img2.JPEG
  n01662784/
    img1.JPEG
    ...
```

若你使用的是 Tiny ImageNet 或其他镜像集，按相同目录结构组织每个类即可.

步骤一：下载 ImageNet 数据
- 从 http://www.image-net.org 按说明申请并下载（需要注册）。
- 解压并把需要的类放到仓库的 `data/imagenet_base/` 下，确保每个 synset（例如 `n01440764`）为一个子文件夹。

步骤二：（可选，但推荐）清洗与统一图片格式
- 作用：把图片统一转为 RGB JPEG，删除损坏文件，并可选地缩放最大边长，减少后续内存压力。
- 使用仓库中的脚本：

```bash
# 在项目根目录
python3 scripts/prepare_images.py --data_dir data/imagenet_base --max_size 1024
```

参数说明：
- --data_dir：ImageNet 基础目录（默认 data/imagenet_base）
- --max_size：可选，最大边长（像素），若设置为 1024 则将图像最长边缩放到 1024

步骤三：批量生成嵌入并保存 metadata
- 使用改进后的批处理脚本，它会按 chunk 分块保存 embeddings 与 metadata，支持断点续跑与合并：

```bash
python3 scripts/batch_process_imagenet.py \
  --base_dir data/imagenet_base \
  --output_dir data/output \
  --model clip-ViT-B-32 \
  --batch_size 64 \
  --chunk_size 2000 \
  --mapping scripts/synset_words.txt \
  --merge
```

常用参数说明：
- --model：sentence-transformers 中的模型名称（默认 clip-ViT-B-32）。
- --batch_size：每次送入模型的图片数（显存/内存受限时调小，例如 8/16）。
- --chunk_size：每个保存分块包含的图片数（避免一次性写入过大文件）。
- --mapping：可选的 synset->class_name 映射文件（JSON 或每行 "n01440764 tench" 的文本），若不设置，class_name 将使用文件夹名。
- --resume：若中断，可加 --resume 跳过已存在的 parts 并继续处理。
- --merge：在所有 parts 生成后，合并成 data/output/embeddings.npy 与 data/output/image_metadata.json。

运行建议（调试与生产）：
- 首次在少量文件上测试：
  ```bash
  python3 scripts/batch_process_imagenet.py --base_dir data/imagenet_base --output_dir data/output --batch_size 8 --chunk_size 100
  ```
- 在 MacBook 或内存受限机器上，把 --batch_size 设置小（如 4/8/16）并减小 --chunk_size。
- 批量处理大量图片时，优先在带 CUDA 的 GPU 服务器上运行以节省时间。

步骤四：交付给索引组员
- 合并后你会得到：
  - data/output/embeddings.npy
  - data/output/image_metadata.json
- 把上述两个文件交给 FAISS 组，他们可据此构建索引并通过 metadata 映射到具体图片/类。

合规与隐私注意事项
- 官方 ImageNet 有使用条款，请确保你的使用符合许可（学术用途通常允许但需遵守规定）。
- 通常不要把带版权的原始图片公开上传到公共仓库；可只分享 embeddings 与 metadata。

## 4. 如何运行（模块二负责人）

1. 将 10 个类别的 ImageNet 数据放入 `data/imagenet_base/`：每个类别一个子文件夹。
2. 在项目根目录下运行：
```bash
python3 scripts/batch_process_imagenet.py
```
3. 交付 `data/output/` 文件夹（包含 embeddings.npy 和 image_metadata.json）给索引负责人。
4. 将 `clip_pipeline/` 目录交付给 Flask 负责人（他们只需 import EmbeddingProcessor）。

## 5. 备注
- 如果你们有 GPU，processor 会自动使用 CUDA（如果可用）。
- 如果你的团队想要更高精度，可选择 `'clip-ViT-L-14'` 等更大模型，但需更多显存。
