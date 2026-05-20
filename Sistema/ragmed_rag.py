"""
RAGMED_rag — retrieval-augmented generation module for the RAGMED system.

Retrieval is delegated to a :class:`~similarity.base.SimilarityFunction`
implementation selected via the :class:`~similarity.base.SimilarityFn` enum.
"""

import re
from collections.abc import Iterator

import ollama
from rank_bm25 import BM25Okapi

from _helpers import NO_INFO, SectionHeader
from similarity import (
    CosineSimilarity,
    EuclideanSimilarity,
    HybridSimilarity,
    JaccardSimilarity,
    SimilarityFn,
    SimilarityFunction,
)

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

_UNDERLINE_RE = re.compile(r"^=+$", re.MULTILINE)

#: Section header names to exclude when splitting the corpus into disease blocks.
_SECTION_HEADER_VALUES: frozenset[str] = frozenset(h.value for h in SectionHeader)

# bge-base-en-v1.5-gguf has a 512-token context window.  Medical text is
# subword-heavy, so we cap at 1 500 characters to stay safely under the limit.
_MAX_CHUNK_CHARS = 1500


def _truncate(text: str, max_chars: int = _MAX_CHUNK_CHARS) -> str:
    """Truncate *text* to at most *max_chars* characters at a word boundary."""
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    boundary = cut.rfind(" ")
    return cut[:boundary] if boundary != -1 else cut


# ---------------------------------------------------------------------------
# Factory: maps enum value → similarity class (with optional kwargs)
# ---------------------------------------------------------------------------

_SIMILARITY_REGISTRY: dict[SimilarityFn, type[SimilarityFunction]] = {
    SimilarityFn.COSINE: CosineSimilarity,
    SimilarityFn.EUCLIDEAN: EuclideanSimilarity,
    SimilarityFn.JACCARD: JaccardSimilarity,
    SimilarityFn.HYBRID: HybridSimilarity,
}


class RAGMED_rag:
    """
    Retrieval-Augmented Generation system for disease information lookup.

    Builds a vector store from a structured diseases corpus and supports four
    retrieval strategies: cosine, euclidean, jaccard, and hybrid (BM25 + cosine).
    """

    EMBEDDING_MODEL = "hf.co/CompendiumLabs/bge-base-en-v1.5-gguf"
    LANGUAGE_MODEL = "hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF"

    def __init__(
        self, dataset_file: str, similarity_fn: str = "hybrid", alpha: float = 0.5
    ) -> None:
        """
        Initialise the RAG system and load the corpus.

        :param dataset_file: Path to the diseases.txt corpus file.
        :param similarity_fn: Retrieval strategy — one of ``'cosine'``,
            ``'euclidean'``, ``'jaccard'``, ``'hybrid'``.
            Invalid values raise :class:`ValueError` via the enum.
        :param alpha: Cosine weight in hybrid mode (``1 - alpha`` goes to BM25).
        """
        self.similarity_fn = SimilarityFn(similarity_fn)

        fn_cls = _SIMILARITY_REGISTRY[self.similarity_fn]
        kwargs = {"alpha": alpha} if self.similarity_fn is SimilarityFn.HYBRID else {}
        self._retriever: SimilarityFunction = fn_cls(**kwargs)

        self.chunks: list[str] = []
        self.embeddings: list[list[float]] = []
        self.bm25: BM25Okapi | None = None
        self.load_dataset(dataset_file)

    # ------------------------------------------------------------------
    # Dataset loading
    # ------------------------------------------------------------------

    def load_dataset(self, dataset_file: str) -> None:
        """
        Load corpus, embed chunks, and build BM25 index.

        Parses diseases.txt into section-level chunks (lead, signs and symptoms,
        causes, treatment), embeds each with the embedding model, and builds a
        BM25Okapi index for keyword-based retrieval.

        :param dataset_file: Path to the diseases.txt corpus file.
        """
        with open(dataset_file, "r", encoding="utf-8") as fh:
            raw = fh.read()

        self.chunks = self._parse_chunks(raw)
        print(f"Loaded {len(self.chunks)} chunks from {dataset_file}")

        for i, chunk in enumerate(self.chunks):
            embedding = ollama.embed(
                model=self.EMBEDDING_MODEL,
                input=_truncate(chunk),
            )["embeddings"][0]
            self.embeddings.append(embedding)
            print(f"Embedded chunk {i+1}/{len(self.chunks)}")

        tokenised = [chunk.lower().split() for chunk in self.chunks]
        self.bm25 = BM25Okapi(tokenised)

    # ------------------------------------------------------------------
    # Corpus parsing
    # ------------------------------------------------------------------

    def _parse_chunks(self, raw: str) -> list[str]:
        """
        Parse the raw corpus text into section-level chunks.

        Each disease block in diseases.txt has the structure::

            {Disease Name}
            ==============
            Lead: {lead text}

            Signs and symptoms
            ==================
            {text}

            Causes
            ======
            {text}

            Treatment
            =========
            {text}

        Produces up to four chunks per disease, skipping sections whose text
        is blank or equals :data:`~_helpers.NO_INFO`.

        :param raw: Full content of the diseases.txt corpus file.
        :return: List of chunk strings ready for embedding.
        """
        chunks: list[str] = []
        block_pattern = re.compile(r"^(.+)\n=+\n", re.MULTILINE)

        # The same underline pattern matches both disease name headers and the
        # fixed section headers ("Signs and symptoms", "Causes", "Treatment").
        # Filter section headers out so each match is exactly one disease block.
        all_matches = list(block_pattern.finditer(raw))
        matches = [
            m for m in all_matches if m.group(1).strip() not in _SECTION_HEADER_VALUES
        ]

        for idx, match in enumerate(matches):
            disease_name = match.group(1).strip()
            block_start = match.end()
            block_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(raw)
            block_body = raw[block_start:block_end]
            chunks.extend(self._extract_disease_chunks(disease_name, block_body))

        return chunks

    def _extract_disease_chunks(self, disease_name: str, block_body: str) -> list[str]:
        """
        Extract section-level chunks from a single disease block body.

        :param disease_name: Disease name used as the chunk prefix.
        :param block_body: Text that follows the disease name + underline header.
        :return: List of chunk strings for this disease (0–4 items).
        """
        chunks: list[str] = []
        paragraphs = [p.strip() for p in re.split(r"\n{2,}", block_body) if p.strip()]

        i = 0
        while i < len(paragraphs):
            para = paragraphs[i]

            if para.startswith("Lead:"):
                lead_text = para[len("Lead:") :].strip()
                if lead_text and lead_text != NO_INFO:
                    chunks.append(f"{disease_name} — Lead: {lead_text}")
                i += 1

            elif _UNDERLINE_RE.search(para):
                lines = para.splitlines()
                underline_idx = next(
                    (j for j, ln in enumerate(lines) if _UNDERLINE_RE.match(ln)), None
                )
                if underline_idx is not None and underline_idx > 0:
                    section_name = " ".join(lines[:underline_idx]).strip()
                    body_after = "\n".join(lines[underline_idx + 1 :]).strip()
                    if body_after:
                        body = body_after
                    elif i + 1 < len(paragraphs):
                        i += 1
                        body = paragraphs[i]
                    else:
                        body = ""

                    body = body.strip()
                    if body and body != NO_INFO:
                        chunks.append(f"{disease_name} — {section_name}: {body}")
                i += 1

            else:
                i += 1

        return chunks

    # ------------------------------------------------------------------
    # Retrieval and generation
    # ------------------------------------------------------------------

    def retrieve_function(self, query: str, top_n: int = 5) -> list[tuple[str, float]]:
        """
        Return the *top_n* most relevant ``(chunk, score)`` pairs for *query*.

        Delegates to the :class:`~similarity.base.SimilarityFunction` selected
        at construction time.

        :param query: Free-text symptom description.
        :param top_n: Maximum number of results to return.
        :return: List of ``(chunk, score)`` tuples sorted by score descending.
        """
        return self._retriever.retrieve(
            query, self.chunks, self.embeddings, self.bm25, top_n
        )

    def _swap_retriever(self, similarity_fn: str, alpha: float) -> None:
        """Replace the retriever without rebuilding embeddings or BM25."""
        new_fn = SimilarityFn(similarity_fn)
        if new_fn == self.similarity_fn and alpha == getattr(self._retriever, "alpha", None):
            return
        self.similarity_fn = new_fn
        fn_cls = _SIMILARITY_REGISTRY[new_fn]
        kwargs = {"alpha": alpha} if new_fn is SimilarityFn.HYBRID else {}
        self._retriever = fn_cls(**kwargs)

    def ask_question_stream(
        self, query: str, max_results_ranking: int = 5
    ) -> Iterator[str]:
        """
        Yield partial LLM response tokens for *query*.

        Retrieves relevant chunks then streams the language model response
        token-by-token so callers (e.g. a Gradio chat interface) can display
        incremental output without waiting for the full answer.

        :param query: Free-text description of the patient's symptoms.
        :param max_results_ranking: Number of top chunks to pass as context.
        :return: Iterator of partial token strings.
        """
        retrieved_knowledge = self.retrieve_function(query, max_results_ranking)

        instruction_prompt = (
            "You are a helpful medical information assistant.\n"
            "Use ONLY the following context passages to answer the question.\n"
            "Do not invent information not present in the context.\n"
            "Context:\n" + "\n".join(f" - {chunk}" for chunk, _ in retrieved_knowledge)
        )

        stream = ollama.chat(
            model=self.LANGUAGE_MODEL,
            messages=[
                {"role": "system", "content": instruction_prompt},
                {"role": "user", "content": query},
            ],
            stream=True,
        )
        for chunk in stream:
            yield chunk["message"]["content"]

    def ask_question(self, query: str, max_results_ranking: int = 5) -> None:
        """
        Retrieve relevant chunks and stream an LLM answer to stdout.

        :param query: Free-text description of the patient's symptoms.
        :param max_results_ranking: Number of top chunks to pass as context.
        """
        retrieved_knowledge = self.retrieve_function(query, max_results_ranking)

        print("Retrieved knowledge:")
        for chunk, score in retrieved_knowledge:
            print(f" - (score: {score:.4f}) {chunk}")

        instruction_prompt = (
            "You are a helpful medical information assistant.\n"
            "Use ONLY the following context passages to answer the question.\n"
            "Do not invent information not present in the context.\n"
            "Context:\n" + "\n".join(f" - {chunk}" for chunk, _ in retrieved_knowledge)
        )

        stream = ollama.chat(
            model=self.LANGUAGE_MODEL,
            messages=[
                {"role": "system", "content": instruction_prompt},
                {"role": "user", "content": query},
            ],
            stream=True,
        )

        print("Chatbot response:")
        for chunk in stream:
            print(chunk["message"]["content"], end="", flush=True)
        print()
