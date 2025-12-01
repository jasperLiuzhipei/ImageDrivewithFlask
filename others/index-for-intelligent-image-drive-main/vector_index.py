import numpy as np
from numpy.typing import NDArray
import faiss

class FaissVectorIndex:
    """
    FAISS vector index wrapper supporting building and two types of search:
        1. Top-k nearest neighbor search
        2. Threshold-based search (L2 distance, using range_search)
    Optional normalization for achieving cosine similarity.
    """

    def __init__(self, norm: bool = True):
        """
        Args:
            norm (bool): Whether to normalize vectors for cosine similarity.
        """
        self.norm = norm
        self.index: faiss.IndexFlatL2 | None = None
        self.dim: int | None = None

    def build(self, vectors: NDArray) -> None:
        """
        Build the FAISS index from input vectors.

        Args:
            vectors (NDArray): Input vectors of shape (n, d).
                n is the number of images, d is the dimension.
        """
        vectors = vectors.astype("float32")
        if self.norm:
            vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)

        self.dim = vectors.shape[1]
        self.index = faiss.IndexFlatL2(self.dim)
        self.index.add(vectors)

    def search_topk(self, queries: NDArray, k: int = 10) -> NDArray:
        """
        Top-k nearest neighbor search.

        Args:
            queries (NDArray): Query vectors of shape (nq, d).
                nq is the number of queries, d is the dimension. d must match the dim of index.
            k (int): Number of nearest neighbors to return.

        Returns:
            NDArray: Indices of top-k neighbors, shape (nq, k).
        """
        if self.index is None:
            raise ValueError("Index has not been built yet!")
        if queries.shape[1] != self.dim:
            raise ValueError(f"Query dim {queries.shape[1]} does not match index dim {self.dim}!")

        queries = queries.astype("float32")
        if self.norm:
            queries = queries / np.linalg.norm(queries, axis=1, keepdims=True)

        k = min(k, self.index.ntotal)
        _, I = self.index.search(queries, k)
        return I

    def search_threshold(self, queries: NDArray, threshold: float = 0.8) -> list[NDArray]:
        """
        Threshold-based search: returns all neighbors within L2 distance <= threshold.

        Args:
            queries (NDArray): Query vectors of shape (nq, d)
            threshold (float): L2 distance threshold

        Returns:
            list[NDArray]: List of arrays, each containing indices of neighbors within threshold
        """
        if self.index is None:
            raise ValueError("Index has not been built yet!")
        if queries.shape[1] != self.dim:
            raise ValueError(f"Query dim {queries.shape[1]} does not match index dim {self.dim}!")

        queries = queries.astype("float32")
        if self.norm:
            queries = queries / np.linalg.norm(queries, axis=1, keepdims=True)

        # range_search returns: lims, distances, indices
        lims, D, I = self.index.range_search(queries, threshold)

        results = []
        for i in range(len(queries)):
            start, end = lims[i], lims[i + 1]
            results.append(I[start:end])
        return results

    def get_index(self) -> faiss.IndexFlatL2:
        """Return the underlying FAISS index object."""
        if self.index is None:
            raise ValueError("Index has not been built yet!")
        return self.index
