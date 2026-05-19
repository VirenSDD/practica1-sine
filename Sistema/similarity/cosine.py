"""Cosine similarity retrieval strategy."""

from .base import SimilarityFunction, cosine_score


class CosineSimilarity(SimilarityFunction):
    """Dense retrieval using cosine similarity over embedding vectors."""

    def retrieve(
        self,
        query: str,
        chunks: list[str],
        embeddings: list[list[float]],
        bm25,
        top_n: int,
    ) -> list[tuple[str, float]]:
        """Rank chunks by cosine similarity to the embedded query."""
        qe = self._embed(query)
        scores = [(c, cosine_score(qe, e)) for c, e in zip(chunks, embeddings)]
        return sorted(scores, key=lambda x: x[1], reverse=True)[:top_n]
