"""
Base class and enum for RAGMED similarity functions.
"""

from abc import ABC, abstractmethod
from enum import Enum

import ollama

EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'


class SimilarityFn(str, Enum):
    """Valid retrieval strategies for RAGMED_rag.

    Inheriting from ``str`` allows passing plain string values (e.g. from CLI
    args) directly to ``SimilarityFn(value)`` for validation.
    """

    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    JACCARD = "jaccard"
    HYBRID = "hybrid"


def cosine_score(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two L2-normalised embedding vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x ** 2 for x in a) ** 0.5
    nb = sum(x ** 2 for x in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


class SimilarityFunction(ABC):
    """Abstract base for retrieval similarity strategies.

    Subclasses implement :meth:`retrieve` and may call :meth:`_embed` to
    obtain a query embedding without duplicating the model name.
    """

    EMBEDDING_MODEL: str = EMBEDDING_MODEL

    def _embed(self, text: str) -> list[float]:
        """Return the embedding vector for *text* using the shared model."""
        return ollama.embed(model=self.EMBEDDING_MODEL, input=text)['embeddings'][0]

    @abstractmethod
    def retrieve(
        self,
        query: str,
        chunks: list[str],
        embeddings: list[list[float]],
        bm25,
        top_n: int,
    ) -> list[tuple[str, float]]:
        """Return the *top_n* most relevant ``(chunk, score)`` pairs.

        :param query: Free-text symptom description from the user.
        :param chunks: Full corpus chunk strings (used for display and Jaccard).
        :param embeddings: Pre-computed embedding for each chunk (parallel to *chunks*).
        :param bm25: BM25Okapi index built over the tokenised chunks, or ``None``.
        :param top_n: Maximum number of results to return.
        :return: List of ``(chunk, score)`` tuples sorted by score descending.
        """
