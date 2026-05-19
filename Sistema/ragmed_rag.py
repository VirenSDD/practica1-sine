"""
RAGMED_rag — retrieval-augmented generation module for the RAGMED system.

Supports multiple similarity functions: cosine, euclidean, jaccard, hybrid.
Hybrid mode combines BM25 sparse scoring with dense embedding cosine similarity.
"""

import re

import ollama
from rank_bm25 import BM25Okapi

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_NO_INFO = "(No information available.)"

_UNDERLINE_RE = re.compile(r"^=+$", re.MULTILINE)

# Fixed section header names produced by the crawler — excluded from disease-block detection.
_SECTION_HEADERS = {"Signs and symptoms", "Causes", "Treatment", "Management", "Prevention"}

# bge-base-en-v1.5-gguf has a 512-token context window.  Medical text is subword-heavy,
# so we cap at 1500 characters (~250-350 tokens in practice) to stay safely under the limit.
_MAX_CHUNK_CHARS = 1500


def _truncate(text: str, max_chars: int = _MAX_CHUNK_CHARS) -> str:
    """Truncate text to at most max_chars characters, breaking on a word boundary."""
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    boundary = cut.rfind(" ")
    return cut[:boundary] if boundary != -1 else cut


class RAGMED_rag:
    """
    Retrieval-Augmented Generation system for disease information lookup.

    Builds a vector store from a structured diseases corpus and supports four
    retrieval strategies: cosine, euclidean, jaccard, and hybrid (BM25 + cosine).
    """

    EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'
    LANGUAGE_MODEL  = 'hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF'

    def __init__(self, dataset_file: str, similarity_fn: str = 'hybrid', alpha: float = 0.5) -> None:
        """
        Initialise the RAG system and load the corpus.

        :param dataset_file: Path to the diseases.txt corpus file.
        :param similarity_fn: One of 'cosine', 'euclidean', 'jaccard', 'hybrid'.
        :param alpha: Weight for cosine in hybrid mode (1-alpha goes to BM25). Default 0.5.
        """
        self.similarity_fn = similarity_fn
        self.alpha = alpha
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

        Parses the diseases.txt corpus into section-level chunks (lead, signs and
        symptoms, causes, treatment) and embeds each chunk using the embedding model.
        A BM25 index is built over all chunks after embedding is complete.

        :param dataset_file: Path to the diseases.txt corpus file.
        """
        with open(dataset_file, 'r', encoding='utf-8') as fh:
            raw = fh.read()

        self.chunks = self._parse_chunks(raw)
        print(f'Loaded {len(self.chunks)} chunks from {dataset_file}')

        for i, chunk in enumerate(self.chunks):
            embedding = ollama.embed(model=self.EMBEDDING_MODEL, input=_truncate(chunk))['embeddings'][0]
            self.embeddings.append(embedding)
            print(f'Embedded chunk {i+1}/{len(self.chunks)}')

        # Build BM25 index over tokenised chunks.
        tokenised = [chunk.lower().split() for chunk in self.chunks]
        self.bm25 = BM25Okapi(tokenised)

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

        This method produces up to four chunks per disease, skipping any section
        whose text is blank or equals '(No information available.)'.

        :param raw: Full content of the diseases.txt corpus file.
        :return: List of chunk strings ready for embedding.
        """
        chunks: list[str] = []

        # Split the corpus into disease blocks.  Each block starts with the disease
        # name on its own line followed by an underline of '=' characters.  We split
        # on the underline lines, then pair each underline with the preceding name.
        # Strategy: use regex to find all (name, block_body) pairs.
        # The corpus format produced by the crawler is:
        #   {name}\n{'='*len(name)}\n{body}\n\n
        # We split on that pattern.
        block_pattern = re.compile(
            r"^(.+)\n=+\n",   # name line + underline line
            re.MULTILINE,
        )

        # The same underline pattern matches both disease headers AND the fixed section
        # headers written by the crawler ("Signs and symptoms", "Causes", "Treatment").
        # Filter those out so each match corresponds to exactly one disease block.
        all_matches = list(block_pattern.finditer(raw))
        matches = [m for m in all_matches if m.group(1).strip() not in _SECTION_HEADERS]

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

        :param disease_name: Name of the disease (used as chunk prefix).
        :param block_body: The text that follows the disease name + underline header.
        :return: List of chunk strings for this disease (0–4 items).
        """
        chunks: list[str] = []

        # Split body into paragraphs separated by blank lines.
        paragraphs = [p.strip() for p in re.split(r'\n{2,}', block_body) if p.strip()]

        # The crawler writes sections in order:
        #   "Lead: {text}"
        #   "Signs and symptoms\n==================\n{text}"
        #   "Causes\n======\n{text}"
        #   "Treatment\n=========\n{text}"
        # We parse each paragraph to identify which section it belongs to.

        i = 0
        while i < len(paragraphs):
            para = paragraphs[i]

            # Lead paragraph starts with "Lead:"
            if para.startswith("Lead:"):
                lead_text = para[len("Lead:"):].strip()
                if lead_text and lead_text != _NO_INFO:
                    chunks.append(f"{disease_name} — Lead: {lead_text}")
                i += 1

            # Section headings: the paragraph is just the section name and its underline.
            # The next paragraph (if present) is the section body.
            elif _UNDERLINE_RE.search(para):
                # The section name is the line(s) before the underline.
                lines = para.splitlines()
                # Find the underline line index.
                underline_idx = next(
                    (j for j, ln in enumerate(lines) if _UNDERLINE_RE.match(ln)), None
                )
                if underline_idx is not None and underline_idx > 0:
                    section_name = " ".join(lines[:underline_idx]).strip()
                    # The body may be in the same paragraph (after the underline) or the next one.
                    body_after_underline = "\n".join(lines[underline_idx + 1:]).strip()
                    if body_after_underline:
                        body = body_after_underline
                    elif i + 1 < len(paragraphs):
                        i += 1
                        body = paragraphs[i]
                    else:
                        body = ""

                    body = body.strip()
                    if body and body != _NO_INFO:
                        chunks.append(f"{disease_name} — {section_name}: {body}")
                i += 1
            else:
                i += 1

        return chunks

    # ------------------------------------------------------------------
    # Similarity functions
    # ------------------------------------------------------------------

    def cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """
        Cosine similarity between two embedding vectors.

        :param a: First embedding vector.
        :param b: Second embedding vector.
        :return: Cosine similarity score in the range [-1, 1].
        """
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x ** 2 for x in a) ** 0.5
        norm_b = sum(x ** 2 for x in b) ** 0.5
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    def euclidean_similarity(self, a: list[float], b: list[float]) -> float:
        """
        Euclidean-distance-based similarity: 1 / (1 + distance).

        Higher values indicate greater similarity (maximum 1.0 when a == b).

        :param a: First embedding vector.
        :param b: Second embedding vector.
        :return: Similarity score in the range (0, 1].
        """
        distance = sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5
        return 1.0 / (1.0 + distance)

    def jaccard_similarity(self, query_tokens: list[str], chunk: str) -> float:
        """
        Jaccard coefficient between the query token set and the chunk token set.

        :param query_tokens: Tokenised (lowercased) query words.
        :param chunk: Chunk text to compare against.
        :return: Jaccard similarity score in the range [0, 1].
        """
        query_set = set(query_tokens)
        chunk_set = set(chunk.lower().split())
        intersection = query_set & chunk_set
        union = query_set | chunk_set
        if not union:
            return 0.0
        return len(intersection) / len(union)

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def retrieve_function(self, query: str, top_n: int = 5) -> list[tuple[str, float]]:
        """
        Return the top_n most relevant (chunk, score) pairs for the given query.

        The retrieval strategy is determined by ``self.similarity_fn``:

        - ``'cosine'``    — dense cosine similarity on embeddings.
        - ``'euclidean'`` — 1/(1+euclidean distance) on embeddings.
        - ``'jaccard'``   — token-overlap Jaccard coefficient (no embeddings needed).
        - ``'hybrid'``    — weighted combination of cosine and normalised BM25.

        :param query: Free-text query describing the patient's symptoms.
        :param top_n: Maximum number of results to return.
        :return: List of (chunk, score) tuples sorted by score descending.
        """
        fn = self.similarity_fn

        if fn == 'hybrid':
            query_embedding = ollama.embed(model=self.EMBEDDING_MODEL, input=query)['embeddings'][0]
            cosine_scores = [self.cosine_similarity(query_embedding, emb) for emb in self.embeddings]

            query_tokens = query.lower().split()
            bm25_scores = self.bm25.get_scores(query_tokens)
            bm25_max = max(bm25_scores) if max(bm25_scores) > 0 else 1.0
            bm25_norm = [s / bm25_max for s in bm25_scores]

            hybrid_scores = [
                self.alpha * c + (1 - self.alpha) * b
                for c, b in zip(cosine_scores, bm25_norm)
            ]
            results = sorted(zip(self.chunks, hybrid_scores), key=lambda x: x[1], reverse=True)
            return results[:top_n]

        elif fn == 'cosine':
            query_embedding = ollama.embed(model=self.EMBEDDING_MODEL, input=query)['embeddings'][0]
            scores = [
                (chunk, self.cosine_similarity(query_embedding, emb))
                for chunk, emb in zip(self.chunks, self.embeddings)
            ]
            scores.sort(key=lambda x: x[1], reverse=True)
            return scores[:top_n]

        elif fn == 'euclidean':
            query_embedding = ollama.embed(model=self.EMBEDDING_MODEL, input=query)['embeddings'][0]
            scores = [
                (chunk, self.euclidean_similarity(query_embedding, emb))
                for chunk, emb in zip(self.chunks, self.embeddings)
            ]
            scores.sort(key=lambda x: x[1], reverse=True)
            return scores[:top_n]

        elif fn == 'jaccard':
            query_tokens = query.lower().split()
            scores = [
                (chunk, self.jaccard_similarity(query_tokens, chunk))
                for chunk in self.chunks
            ]
            scores.sort(key=lambda x: x[1], reverse=True)
            return scores[:top_n]

        else:
            raise ValueError(f"Unknown similarity function: '{fn}'. "
                             "Choose from 'cosine', 'euclidean', 'jaccard', 'hybrid'.")

    # ------------------------------------------------------------------
    # Question answering
    # ------------------------------------------------------------------

    def ask_question(self, query: str, max_results_ranking: int = 5) -> None:
        """
        Retrieve relevant chunks and stream an LLM answer to stdout.

        Mirrors the style of SINE_rag.ask_question: prints retrieved knowledge
        with scores, then streams the language model response token by token.

        :param query: Free-text description of the patient's symptoms.
        :param max_results_ranking: Number of top chunks to pass as context.
        """
        retrieved_knowledge = self.retrieve_function(query, max_results_ranking)

        print('Retrieved knowledge:')
        for chunk, score in retrieved_knowledge:
            print(f' - (score: {score:.4f}) {chunk}')

        instruction_prompt = f"""You are a helpful medical information assistant.
Use ONLY the following context passages to answer the question.
Do not invent information not present in the context.
Context:
{chr(10).join([f' - {chunk}' for chunk, _ in retrieved_knowledge])}"""

        stream = ollama.chat(
            model=self.LANGUAGE_MODEL,
            messages=[
                {'role': 'system', 'content': instruction_prompt},
                {'role': 'user', 'content': query},
            ],
            stream=True,
        )

        print('Chatbot response:')
        for chunk in stream:
            print(chunk['message']['content'], end='', flush=True)
        print()  # Newline after streamed response.
