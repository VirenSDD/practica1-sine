# IR Method Comparison — RAGMED

**Task:** T2.1  
**Agent:** Researcher  
**Date:** 2026-05-19  

---

## 1. Methods Overview

| Method | Type | Vocabulary-aware | Semantic | Length norm. | Use case fit |
|---|---|---|---|---|---|
| Cosine similarity (dense) | Dense vector | No (latent) | Yes | Yes (unit vectors) | Good (synonyms) |
| BM25 (Okapi BM25) | Sparse / probabilistic | Yes | No | Yes (b parameter) | Good (exact terms) |
| TF-IDF + cosine | Sparse vector | Yes | No | Yes (cosine norm) | Moderate |
| Jaccard similarity | Set overlap | Yes | No | Implicit (set size) | Weak |
| Hybrid BM25 + embedding cosine | Hybrid | Yes + latent | Yes | Both | **Best** |

---

## 2. Method Details

### 2.1 Cosine Similarity (Dense Embeddings)

**Summary.** Documents and the query are encoded into high-dimensional dense vectors by a neural embedding model (here `bge-base-en-v1.5-gguf` via Ollama). Relevance is measured as the cosine of the angle between the query vector and each document vector: a score of 1 means identical direction (maximum similarity) and 0 means orthogonal (no similarity). Because both vectors are L2-normalised by the embedding model, the cosine reduces to the dot product. This is the approach used in the reference implementation `SINE_Pract_2025_2026.py`.

**Strengths for symptom→disease matching.**
- Captures semantic equivalences automatically: "shortness of breath" and "dyspnea" map to nearby regions of the embedding space, so a query containing one will match documents containing the other without any query expansion.
- Robust to paraphrasing and variation in symptom terminology across different Wikipedia editors.
- Single hyperparameter: the embedding model itself.

**Weaknesses for symptom→disease matching.**
- Vocabulary mismatch in the *opposite* direction: very rare, precise clinical terms (e.g., "Koplik spots") may not be reliably encoded in a general-purpose embedding model's latent space.
- Computationally more expensive at index time (requires running every chunk through the neural model) and at query time (all-pairs dot products over the full chunk set unless an ANN index is used).
- Dense vectors are not interpretable; it is difficult to diagnose why a particular chunk was retrieved.
- No explicit term-frequency signal: a chunk that mentions "fever" once and a chunk that mentions "fever" twenty times receive similar embedding vectors if surrounding context is similar.

**Source.** Croft, Metzler & Strohman, *Search Engines: Information Retrieval in Practice*, Ch. 7, §7.1.2 (Vector Space Model and cosine measure), pp. 237–242.

---

### 2.2 BM25 (Okapi BM25)

**Summary.** BM25 is a probabilistic ranking function derived from the binary independence model. For each query term *i*, it computes a weight that combines an IDF-like component with a saturating term-frequency component and a document-length normalisation factor. The full scoring formula is:

```
BM25(Q, D) = Σ_{i∈Q}  log[(r_i+0.5)/(R-r_i+0.5) / (n_i-r_i+0.5)/(N-n_i-R+r_i+0.5)]
             × (k1+1)·f_i / (K + f_i)
             × (k2+1)·qf_i / (k2 + qf_i)
```

where `K = k1·((1-b) + b·dl/avdl)`. The parameter `k1` (typically 1.2) controls TF saturation so that term frequency increases the score with diminishing returns; `b` (typically 0.75) controls length normalisation so that longer documents are not unfairly penalised or favoured; `k2` (typically 0–1000) controls query-term frequency weighting. Without relevance information, `r` and `R` are set to zero and the IDF component approximates `log(N/n_i)`.

**Strengths for symptom→disease matching.**
- Directly rewards exact matches of rare clinical terms that are highly discriminative (high IDF), such as "haemoptysis", "cyanosis", or "petechiae".
- The TF saturation parameter prevents a chunk that mentions a common symptom word many times from dominating over a chunk with diverse symptom coverage.
- Length normalisation is important because disease Wikipedia sections vary widely in length (a lead section may be three sentences; a Signs and Symptoms section may be several paragraphs).
- Fast to compute using an inverted index; well-suited to large corpora.
- Strong, well-understood empirical track record on TREC benchmarks.

**Weaknesses for symptom→disease matching.**
- Purely lexical: if the user writes "difficulty breathing" and the document says "dyspnoea", BM25 assigns zero weight to that term pair.
- Bag-of-words model: term order and phrase structure are ignored.
- Requires tuning of `k1`, `b`, and `k2` for the specific corpus; defaults may not be optimal for short Wikipedia sections.

**Source.** Croft, Metzler & Strohman, *Search Engines: Information Retrieval in Practice*, Ch. 7, §7.2.2 (The BM25 Ranking Algorithm), pp. 250–252.

---

### 2.3 TF-IDF + Cosine

**Summary.** In the classical vector space model, both documents and queries are represented as sparse vectors of TF-IDF weights. The weight for term *k* in document *D_i* is:

```
d_ik = (log(f_ik) + 1) · log(N / n_k)  /  √[ Σ_k ((log(f_ik)+1)·log(N/n_k))² ]
```

where `f_ik` is the raw term count, `n_k` is the document frequency of term *k*, and the denominator normalises the vector to unit length. Relevance is then measured with the cosine of the angle between the document vector and the query vector (also weighted by TF-IDF), which, given unit-length vectors, reduces to the dot product.

**Strengths for symptom→disease matching.**
- Simple, transparent, and well-understood; easy to inspect which terms drove a particular score.
- Rewards discrimination: a term like "opisthotonus" that appears in only one or two disease articles receives very high IDF and strongly identifies relevant documents.
- No training required; computable directly from the corpus statistics.

**Weaknesses for symptom→disease matching.**
- Suffers the same vocabulary mismatch problem as BM25 but without BM25's more principled probabilistic derivation and TF saturation.
- The logarithmic TF component with no upper saturation can still be dominated by documents with very high term counts.
- No length normalisation independent of the cosine; long documents naturally accumulate more term weight.
- Performs worse than BM25 on most TREC benchmarks; BM25 supersedes it as the sparse keyword baseline.

**Source.** Croft, Metzler & Strohman, *Search Engines: Information Retrieval in Practice*, Ch. 7, §7.1.2 (The Vector Space Model), pp. 237–242. TF-IDF weighting formula: pp. 241–242.

---

### 2.4 Jaccard Similarity

**Summary.** Jaccard similarity measures the set overlap between the tokens of the query *Q* and the tokens of a document chunk *D*:

```
Jaccard(Q, D) = |Q ∩ D| / |Q ∪ D|
```

where *Q* and *D* are treated as sets of unique, unweighted tokens (after tokenisation and stop-word removal). A score of 1 means the query and document share all tokens; a score of 0 means no overlap. Because the sets contain only unique token types (not counts), Jaccard ignores term frequency entirely.

**Strengths for symptom→disease matching.**
- Computationally trivial; no index beyond a vocabulary set is needed.
- Intuitive and easy to interpret.

**Weaknesses for symptom→disease matching.**
- No weighting: the word "fever" (extremely common across diseases) contributes the same as the word "xerostomia" (highly discriminative). This severely undermines the ability to separate diseases.
- No term-frequency information: whether a symptom is mentioned once or thirty times is irrelevant.
- No semantic component: vocabulary mismatch is completely unaddressed.
- Very short queries receive artificially low scores because the union `|Q ∪ D|` is dominated by document tokens.
- Jaccard is the weakest of the five candidates for this task; it is included for comparison purposes only.

**Source.** Jaccard similarity is not covered as a ranking model in Croft, Metzler & Strohman — its absence from their retrieval model chapter (Ch. 7) reflects its unsuitability for ranked retrieval. The Boolean retrieval model (which Jaccard resembles structurally) is discussed in §7.1.1, pp. 235–237, and its limitations relative to ranked models are described there.

---

### 2.5 Hybrid: BM25 + Embedding Cosine

**Summary.** The hybrid retrieval score is a weighted linear combination of the normalised BM25 score and the embedding cosine similarity:

```
score_hybrid(Q, D) = alpha · cosine_emb(Q, D) + (1 - alpha) · BM25_norm(Q, D)
```

where `alpha ∈ [0, 1]` is a tunable mixing parameter, `cosine_emb` is the cosine similarity between query and document dense embeddings (range [0, 1] for non-negative embeddings), and `BM25_norm` is the BM25 score normalised to [0, 1] across the candidate set (e.g., by dividing by the maximum BM25 score in the current batch or by min-max scaling). This approach is often called *late fusion* or *score-level fusion* in the hybrid retrieval literature.

**Strengths for symptom→disease matching.**
- Combines the complementary strengths of both components (see Section 3 for detailed justification).
- A single parameter `alpha` controls the trade-off and can be tuned empirically on a held-out query set.
- No additional model training is needed beyond what is required for the two individual components.
- Robust to the failure modes of each individual component: when BM25 misses a synonym, the embedding component rescues it; when the embedding model hallucinates a spurious semantic link, the BM25 component acts as a lexical anchor.

**Weaknesses for symptom→disease matching.**
- Requires computing and storing both a sparse inverted index (for BM25) and dense vectors (for embeddings), roughly doubling storage and query-time compute compared to either single method.
- Score normalisation strategy for BM25 must be chosen carefully; raw BM25 scores are unbounded and corpus-dependent, making direct combination with bounded cosine scores non-trivial.
- The optimal `alpha` depends on the query distribution; without labelled relevance judgements it must be estimated heuristically (a reasonable default is `alpha = 0.5`).

**Source.** The combining evidence framework is introduced in Croft, Metzler & Strohman, Ch. 7, §7.4 (Complex Queries and Combining Evidence), p. 267. The individual components are grounded in §7.1.2 (cosine, pp. 237–242) and §7.2.2 (BM25, pp. 250–252).

---

## 3. Justification for Hybrid Retrieval

The RAGMED retrieval task presents a fundamental dual challenge that no single method handles adequately on its own:

**The exact-term challenge.** Disease Wikipedia articles use precise, standardised clinical vocabulary. When a user query contains a specific symptom term — "fever", "dyspnea", "petechiae", "epistaxis" — the most discriminative signal is often a direct lexical match in the Signs and Symptoms or Lead sections of a specific disease article. BM25 excels here: its IDF component assigns very high weight to rare clinical terms, and its TF saturation prevents a chunk that mentions "fever" many times from artificially outranking a more specific chunk that mentions "fever" alongside several other rarer co-occurring symptoms.

**The synonym and paraphrase challenge.** Lay users describing symptoms do not necessarily use the clinical term. "Shortness of breath" and "difficulty breathing" are lay descriptions of the same phenomenon as the clinical term "dyspnea". "Chest tightness" overlaps with "angina". "Yellowing of the skin" maps to "jaundice". A pure BM25 system assigns a score of zero to any of these pairs if the query and document happen to use different surface forms. Dense embeddings trained on large biomedical or general text corpora learn that these expressions are semantically equivalent and will correctly assign high cosine similarity across the vocabulary gap.

**Why the combination is strictly better.** The two components are complementary by construction. BM25 operates on the discrete, sparse term-occurrence space; embeddings operate on a continuous, dense semantic space. Their failure modes are largely orthogonal: BM25 fails on synonymy and paraphrase; embeddings can produce high similarity between topically related but non-relevant documents (e.g., two inflammatory diseases may be embedded nearby even when their symptom profiles differ). The weighted sum `alpha · cosine + (1 - alpha) · BM25_norm` captures exact-term precision from BM25 while simultaneously closing the vocabulary gap through embeddings. This design follows the general principle described in Croft, Metzler & Strohman §7.4 that effective retrieval requires combining multiple evidence sources, with different sources compensating for each other's weaknesses (p. 267).

**Practical evidence.** The hybrid BM25 + dense retrieval pattern has become the standard first-stage retrieval approach in modern dense retrieval pipelines (e.g., the Retrieve-and-Rerank architecture used in systems like DPR + BM25, ColBERT, and commercial search engines). While such systems are described in research literature beyond the scope of this textbook, their effectiveness is well established and the theoretical motivation is directly traceable to the combining-evidence framework in §7.4.

---

## 4. Implementation Notes

### BM25 Library

The implementation uses the `rank_bm25` Python library, specifically the `BM25Okapi` variant. `BM25Okapi` implements the standard Okapi BM25 formula described in §7.2.2 of the textbook with default parameters `k1=1.5`, `b=0.75`. The library accepts a tokenised corpus (list of token lists) at construction time and provides a `get_scores(query_tokens)` method that returns a raw BM25 score for each document.

### Tokenisation

The same tokenisation pipeline is applied to both the BM25 corpus and the query: lowercase conversion, whitespace splitting, and optionally stop-word removal. This ensures that query and document token vocabularies are consistent.

### Score Normalisation

Raw BM25 scores are non-negative but unbounded. Before combining with cosine similarity scores (which are bounded in [−1, 1] and in practice in [0, 1] for non-negative embeddings), the BM25 scores are normalised per query:

```python
bm25_scores_norm = bm25_scores / (bm25_scores.max() + 1e-8)
```

This maps the highest-scoring document to 1.0 and preserves relative orderings. An alternative is min-max normalisation across the full candidate set.

### Mixing Parameter

The default mixing parameter is `alpha = 0.5`, giving equal weight to both components. This value can be tuned on a held-out development set if relevance labels are available.

### Embedding Model

The dense embeddings are produced by `bge-base-en-v1.5-gguf` served via Ollama, which outputs 768-dimensional L2-normalised vectors. Cosine similarity therefore reduces to the dot product.

---

## 5. References

[1] W. B. Croft, D. Metzler, and T. Strohman, *Search Engines: Information Retrieval in Practice*. Pearson Education, Inc., 2015.  
— §7.1.2 "The Vector Space Model" (cosine similarity, TF-IDF weighting), pp. 237–242.  
— §7.2.2 "The BM25 Ranking Algorithm" (probabilistic ranking, TF saturation, length normalisation), pp. 250–252.  
— §7.4 "Complex Queries and Combining Evidence" (evidence combination framework), p. 267.  
— §7.1.1 "Boolean Retrieval" (limitations of set-based matching, context for Jaccard), pp. 235–237.

[2] S. E. Robertson and S. Walker, "Some simple effective approximations to the 2-Poisson model for probabilistic weighted retrieval," in *Proc. ACM SIGIR*, 1994, pp. 232–241. (Original BM25 paper, cited as Robertson & Walker, 1994 in footnote 7, p. 249 of [1].)

[3] `rank_bm25` Python library. BM25Okapi implementation. Available: https://github.com/dorianbrown/rank_bm25

[4] BAAI, "bge-base-en-v1.5," Hugging Face Model Hub. Available: https://huggingface.co/BAAI/bge-base-en-v1.5 (served via Ollama as `hf.co/CompendiumLabs/bge-base-en-v1.5-gguf`).
