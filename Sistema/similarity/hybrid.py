"""Hybrid BM25 + embedding cosine retrieval strategy."""

from rank_bm25 import BM25Okapi

from .base import SimilarityFunction, cosine_score


class HybridSimilarity(SimilarityFunction):
    """Hybrid retrieval combining normalised BM25 and embedding cosine scores.

    The final score is::

        alpha * cosine_emb(Q, D) + (1 - alpha) * BM25_norm(Q, D)

    where BM25 scores are normalised by the batch maximum so both components
    fall in [0, 1] before the weighted sum.

    :param alpha: Weight for the cosine component (default 0.5).
    """

    def __init__(self, alpha: float = 0.5) -> None:
        self.alpha = alpha
        self._bm25: BM25Okapi | None = None
        self._indexed_chunks: list[str] | None = None

    def retrieve(
        self,
        query: str,
        chunks: list[str],
        embeddings: list[list[float]],
        top_n: int,
    ) -> list[tuple[str, float]]:
        """Rank chunks by the weighted hybrid score."""
        if self._bm25 is None or chunks is not self._indexed_chunks:
            self._bm25 = BM25Okapi([c.lower().split() for c in chunks])
            self._indexed_chunks = chunks

        qe = self._embed(query)
        cosine_scores = [cosine_score(qe, e) for e in embeddings]

        qt = query.lower().split()
        bm25_raw = self._bm25.get_scores(qt)
        bm25_max = max(bm25_raw) if max(bm25_raw) > 0 else 1.0
        bm25_norm = [s / bm25_max for s in bm25_raw]

        hybrid_scores = [
            self.alpha * c + (1 - self.alpha) * b
            for c, b in zip(cosine_scores, bm25_norm)
        ]
        return sorted(zip(chunks, hybrid_scores), key=lambda x: x[1], reverse=True)[:top_n]
