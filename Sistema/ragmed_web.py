"""
RAGMED web interface — Gradio chatbot with retrieval configuration panel.

Run locally:
    uv run python Sistema/ragmed_web.py

Deploy to Hugging Face Spaces:
    gradio deploy  (from the Sistema/ directory)
"""

import os

import gradio as gr

from ragmed_rag import RAGMED_rag

# ---------------------------------------------------------------------------
# Corpus path: env var → default fallback
# ---------------------------------------------------------------------------

_CORPUS_FILE = os.environ.get("RAGMED_CORPUS", "diseases.txt")

# ---------------------------------------------------------------------------
# Load the RAG system once at startup (embeddings are expensive)
# ---------------------------------------------------------------------------

_rag: RAGMED_rag | None = None
_corpus_path: str = ""


def _load_rag(corpus_file: str, similarity_fn: str, alpha: float) -> RAGMED_rag:
    return RAGMED_rag(corpus_file, similarity_fn=similarity_fn, alpha=alpha)


# ---------------------------------------------------------------------------
# Gradio handlers
# ---------------------------------------------------------------------------


def initialise(corpus_file: str, similarity_fn: str, alpha: float, top_n: int):
    """Load (or reload) the corpus. Called on app start and when config changes."""
    global _rag, _corpus_path

    corpus_file = corpus_file.strip() or _CORPUS_FILE

    if _rag is None or corpus_file != _corpus_path:
        _rag = _load_rag(corpus_file, similarity_fn, alpha)
        _corpus_path = corpus_file
    else:
        _rag._swap_retriever(similarity_fn, alpha)

    return f"Corpus loaded: {_corpus_path} ({len(_rag.chunks)} chunks)"


def chat(
    message: str,
    history: list,
    corpus_file: str,
    similarity_fn: str,
    alpha: float,
    top_n: int,
):
    """Stream the RAG answer for *message* into the Gradio chat bubble."""
    global _rag, _corpus_path

    corpus_file = corpus_file.strip() or _CORPUS_FILE

    if _rag is None or corpus_file != _corpus_path:
        _rag = _load_rag(corpus_file, similarity_fn, alpha)
        _corpus_path = corpus_file
    else:
        _rag._swap_retriever(similarity_fn, alpha)

    partial = ""
    for token in _rag.ask_question_stream(message, max_results_ranking=top_n):
        partial += token
        yield partial


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

with gr.Blocks(title="RAGMED — Disease Chatbot") as demo:
    gr.Markdown("# RAGMED — Disease Chatbot\nDescribe your symptoms and get possible diagnoses.")

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.ChatInterface(
                fn=chat,
                additional_inputs_accordion=gr.Accordion("Configuration", open=False),
                additional_inputs=[
                    gr.Textbox(
                        label="Corpus file",
                        value=_CORPUS_FILE,
                        placeholder="Path to diseases.txt",
                    ),
                    gr.Dropdown(
                        choices=["hybrid", "cosine", "euclidean", "jaccard"],
                        value="hybrid",
                        label="Similarity function",
                    ),
                    gr.Slider(
                        minimum=0.0,
                        maximum=1.0,
                        step=0.05,
                        value=0.5,
                        label="Alpha (hybrid cosine weight)",
                    ),
                    gr.Slider(
                        minimum=1,
                        maximum=20,
                        step=1,
                        value=5,
                        label="Top N chunks",
                    ),
                ],
            )

if __name__ == "__main__":
    demo.launch()
