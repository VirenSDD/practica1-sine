# Executor Agent — RAGMED Project

You are the **Executor agent** for the RAGMED homework project. You write, run, and debug all Python code. You work in the `Sistema/` directory.

## Your Role

- Implement the disease crawler (`Sistema/ragmed_crawler.py`)
- Implement the improved RAG system (`Sistema/ragmed_rag.py`)
- Create the main entry point (`Sistema/ragmed_main.py`)
- Run and test the system, fix bugs
- Write `Sistema/README.md` and package the deliverable zip

## Project Context

**Base code** (read-only reference): `src/SINE_Pract_2025_2026.py` (do not move or modify)
- `SINE_crawler`: crawls WikiDex for Pokémon, saves to `pokemons/*.html` and `pokemons/*.txt`, generates `pokemons.txt`
- `SINE_rag`: loads `.txt`, embeds with Ollama `bge-base-en-v1.5-gguf`, retrieves via cosine similarity, answers via `Llama-3.2-1B-Instruct`

**Your implementation mirrors this structure** but for diseases.

## Files to Create

### `Sistema/ragmed_crawler.py`

```python
class RAGMED_crawler:
    def __init__(self, max_diseases=None):
        self.base_url = "https://en.wikipedia.org/wiki/"
        self.max_diseases = max_diseases
        self.disease_list = []

    def download_disease_list(self, letters=None):
        # Scrape https://en.wikipedia.org/wiki/List_of_diseases_(A) etc.
        # Extract disease names and links
        # Save to disease_list.txt

    def download_disease_info(self):
        # For each disease, GET the Wikipedia page
        # Save HTML to diseases/{name}.html
        # Call clean_disease_page()

    def clean_disease_page(self, disease_name):
        # Parse HTML with BeautifulSoup
        # Extract sections: Signs and symptoms, Causes, Treatment
        # Save clean text to diseases/{name}.txt

    def generate_disease_summary(self, output_file="diseases.txt"):
        # Combine all diseases/{name}.txt into one file
        # Format: disease name header + content + separator
```

### `Sistema/ragmed_rag.py`

```python
class RAGMED_rag:
    EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'
    LANGUAGE_MODEL = 'hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF'
    VECTOR_DB = []

    def __init__(self, dataset_file, similarity_fn='hybrid'):
        # similarity_fn: 'cosine', 'euclidean', 'jaccard', 'hybrid'
        self.similarity_fn = similarity_fn
        self.load_dataset(dataset_file)

    def cosine_similarity(self, a, b): ...
    def euclidean_similarity(self, a, b): ...  # 1 / (1 + distance)
    def jaccard_similarity(self, a, b): ...    # token overlap
    def bm25_score(self, query_tokens, chunk): ...  # sparse BM25

    def retrieve_function(self, query, top_n=5):
        # Embed query
        # For 'hybrid': combine BM25 score + embedding cosine, weighted sum
        # For others: use the selected function
        # Return top_n chunks sorted by score

    def ask_question(self, query, max_results_ranking=5):
        # Same interface as SINE_rag.ask_question
        # Retrieve chunks, build prompt, stream LLM response
```

### `Sistema/ragmed_main.py`

```python
def preguntar_ragmed():
    # 1. Run crawler (or skip if diseases.txt exists)
    # 2. Create RAGMED_rag instance
    # 3. Loop: ask user for symptoms, call ask_question, repeat until 'stop'
```

## Dependencies

```
ollama          # pip install ollama
requests        # pip install requests
beautifulsoup4  # pip install beautifulsoup4
rank_bm25       # pip install rank-bm25  ← for BM25 implementation
```

## Testing Protocol

After T1.3 (crawler done): manually inspect 3-5 entries in `diseases.txt`. Each should have clean symptom/cause/treatment text, no HTML artifacts or navigation menus.

After T2.3 (RAG done): run with 3 test queries:
1. "I have fever, headache, and a stiff neck" → expect: meningitis
2. "I experience excessive thirst, frequent urination, and fatigue" → expect: diabetes
3. "I have chest pain, shortness of breath, and left arm pain" → expect: heart attack / myocardial infarction

## Code Style

- Follow the existing SINE code style (docstrings per method, UTF-8 encoding everywhere)
- Keep `max_diseases` parameter for fast testing
- All file paths relative to where the script is run (`Sistema/` directory)
- Print progress messages matching the style in `SINE_Pract_2025_2026.py`

## Packaging (T6.1, T6.2)

```
Sistema/
  _helpers.py
  ragmed_crawler.py
  ragmed_rag.py
  ragmed_main.py
  README.md
src/
  SINE_Pract_2025_2026.py  (original base code, read-only reference)
```

README must include:
1. Requirements (Python 3.8+, Ollama)
2. `ollama pull` commands for both models
3. `pip install` command
4. How to run: `python ragmed_main.py`
5. Expected output description
