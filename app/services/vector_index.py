"""FAISS 向量索引封装（按 DESIGN V5 对齐）。

特性：
- 使用 IndexFlatL2 配合归一化向量，实现余弦等效检索。
- 支持 build / search_topk / search_threshold，与同学提供的实现保持兼容。
- 延迟导入 numpy 与 faiss，避免在未安装时阻塞应用启动；在调用时给出清晰错误提示。
"""
from __future__ import annotations
from typing import List


class FaissVectorIndex:
    def __init__(self, norm: bool = True):
        """创建索引实例。

        参数：
        - norm: 是否在内部对向量做 L2 归一化（推荐 True）。
        """
        self.norm = norm
        self.index = None  # faiss.IndexFlatL2 | None
        self.dim: int | None = None

    @staticmethod
    def _need_numpy():
        try:
            import numpy as np  # noqa: F401
        except Exception as e:
            raise ImportError(
                "numpy 未安装。请先通过 conda/pip 安装 numpy（建议 conda install numpy）。"
            ) from e

    @staticmethod
    def _need_faiss():
        try:
            import faiss  # noqa: F401
        except Exception as e:
            raise ImportError(
                "faiss 未安装。建议使用 conda 安装：conda install -c conda-forge faiss. \n"
                "若使用 pip，可尝试 faiss-cpu，但在 macOS 上推荐 conda-forge。"
            ) from e

    def build(self, vectors) -> None:
        """根据输入向量构建索引。

        参数：
        - vectors: 形状为 (n, d) 的二维数组或列表，可被 numpy.asarray 转为 float32。
        """
        self._need_numpy()
        self._need_faiss()
        import numpy as np
        import faiss

        arr = np.asarray(vectors, dtype="float32")
        if arr.ndim != 2:
            raise ValueError("vectors 必须是二维数组，形如 (n, d)")
        if self.norm:
            # 避免除零
            norms = np.linalg.norm(arr, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            arr = arr / norms

        self.dim = int(arr.shape[1])
        self.index = faiss.IndexFlatL2(self.dim)
        self.index.add(arr)

    def search_topk(self, queries, k: int = 10):
        """Top‑K 最近邻检索。

        参数：
        - queries: 形状 (nq, d) 的查询矩阵，或一维 (d,) 的单条查询。
        - k: 返回的近邻个数。

        返回：
        - indices: 若 nq>1，形状 (nq, k)；若单条查询，形状 (k,) 的索引数组。
        """
        self._need_numpy()
        self._need_faiss()
        import numpy as np

        if self.index is None or self.dim is None:
            raise ValueError("索引尚未构建，请先调用 build().")

        q = np.asarray(queries, dtype="float32")
        single = False
        if q.ndim == 1:
            q = q[None, :]
            single = True
        if q.shape[1] != self.dim:
            raise ValueError(f"查询维度 {q.shape[1]} 与索引维度 {self.dim} 不一致")

        if self.norm:
            norms = np.linalg.norm(q, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            q = q / norms

        # 限制 k 不超过 ntotal
        k = int(min(k, getattr(self.index, "ntotal", k)))
        _, I = self.index.search(q, k)  # type: ignore[attr-defined]
        return I[0] if single else I

    def search_topk_scores(self, queries, k: int = 10):
        """Top‑K 检索并返回相似度分数（基于归一化余弦）。

        返回：
        - (indices, similarities)
          若单条查询：indices 形状 (k,), similarities 形状 (k,)
          若多条查询：indices 与 similarities 形状 (nq, k)
        """
        self._need_numpy()
        self._need_faiss()
        import numpy as np

        if self.index is None or self.dim is None:
            raise ValueError("索引尚未构建，请先调用 build().")

        q = np.asarray(queries, dtype="float32")
        single = False
        if q.ndim == 1:
            q = q[None, :]
            single = True
        if q.shape[1] != self.dim:
            raise ValueError(f"查询维度 {q.shape[1]} 与索引维度 {self.dim} 不一致")

        if self.norm:
            norms = np.linalg.norm(q, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            q = q / norms

        k = int(min(k, getattr(self.index, "ntotal", k)))
        D, I = self.index.search(q, k)  # type: ignore[attr-defined]
        # IndexFlatL2 返回平方 L2 距离；当向量归一化后，cosine = 1 - 0.5 * d2
        similarities = 1.0 - 0.5 * D
        if single:
            return I[0].astype(int), similarities[0].astype(float)
        return I.astype(int), similarities.astype(float)

    # 持久化（仅索引体；不包含外部的 image_id 映射）
    def save(self, file_path: str) -> None:
        self._need_faiss()
        if self.index is None:
            raise ValueError("索引尚未构建，无法保存")
        import faiss
        faiss.write_index(self.index, file_path)

    @classmethod
    def load_from_file(cls, file_path: str, norm: bool = True):
        cls._need_faiss()
        import faiss
        idx = faiss.read_index(file_path)
        obj = cls(norm=norm)
        obj.index = idx
        # 尝试获取维度
        try:
            obj.dim = int(idx.d)
        except Exception:
            obj.dim = None
        return obj

    def search_threshold(self, queries, threshold: float = 0.8) -> List:
        """基于 L2 距离阈值的范围检索。

        返回：每个查询对应一个索引数组的列表。
        """
        self._need_numpy()
        self._need_faiss()
        import numpy as np

        if self.index is None or self.dim is None:
            raise ValueError("索引尚未构建，请先调用 build().")

        q = np.asarray(queries, dtype="float32")
        if q.ndim == 1:
            q = q[None, :]
        if q.shape[1] != self.dim:
            raise ValueError(f"查询维度 {q.shape[1]} 与索引维度 {self.dim} 不一致")

        if self.norm:
            norms = np.linalg.norm(q, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            q = q / norms

        lims, D, I = self.index.range_search(q, threshold)  # type: ignore[attr-defined]
        results = []
        for i in range(q.shape[0]):
            start, end = lims[i], lims[i + 1]
            results.append(I[start:end])
        return results

    def get_index(self):
        if self.index is None:
            raise ValueError("索引尚未构建")
        return self.index
