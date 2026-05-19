"""Euclidean-distance-based retrieval strategy."""

from .base import SimilarityFunction


class EuclideanSimilarity(SimilarityFunction):
    """Dense retrieval using 1 / (1 + L2 distance) as the similarity score."""

    @staticmethod
    def _score(a: list[float], b: list[float]) -> float:
        distance = sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5
        return 1.0 / (1.0 + distance)

    def retrieve(
        self,
        query: str,
        chunks: list[str],
        embeddings: list[list[float]],
        bm25,
        top_n: int,
    ) -> list[tuple[str, float]]:
        """Rank chunks by inverse Euclidean distance to the embedded query."""
        qe = self._embed(query)
        scores = [(c, self._score(qe, e)) for c, e in zip(chunks, embeddings)]
        return sorted(scores, key=lambda x: x[1], reverse=True)[:top_n]
