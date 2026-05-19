"""Similarity function implementations for the RAGMED retrieval module."""

from .base import EMBEDDING_MODEL, SimilarityFn, SimilarityFunction, cosine_score
from .cosine import CosineSimilarity
from .euclidean import EuclideanSimilarity
from .hybrid import HybridSimilarity
from .jaccard import JaccardSimilarity

__all__ = [
    "EMBEDDING_MODEL",
    "SimilarityFn",
    "SimilarityFunction",
    "cosine_score",
    "CosineSimilarity",
    "EuclideanSimilarity",
    "HybridSimilarity",
    "JaccardSimilarity",
]
