"""Jaccard token-overlap retrieval strategy."""

from .base import SimilarityFunction


class JaccardSimilarity(SimilarityFunction):
    """Sparse retrieval using Jaccard coefficient over token sets.

    Does not require embeddings, so no model call is made at retrieval time.
    """

    @staticmethod
    def _score(query_tokens: list[str], chunk: str) -> float:
        qs = set(query_tokens)
        cs = set(chunk.lower().split())
        union = qs | cs
        return len(qs & cs) / len(union) if union else 0.0

    def retrieve(
        self,
        query: str,
        chunks: list[str],
        embeddings: list[list[float]],
        top_n: int,
    ) -> list[tuple[str, float]]:
        """Rank chunks by Jaccard overlap with the query token set."""
        qt = query.lower().split()
        scores = [(c, self._score(qt, c)) for c in chunks]
        return sorted(scores, key=lambda x: x[1], reverse=True)[:top_n]
