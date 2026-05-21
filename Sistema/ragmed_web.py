"""
RAGMED web interface — Gradio chatbot with retrieval context panel.

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
# RAG singleton — loaded once, reused across requests
# ---------------------------------------------------------------------------

_rag: RAGMED_rag | None = None
_corpus_path: str = ""


def _ensure_rag(corpus_file: str, similarity_fn: str, alpha: float) -> RAGMED_rag:
    global _rag, _corpus_path
    corpus_file = corpus_file.strip() or _CORPUS_FILE
    if _rag is None or corpus_file != _corpus_path:
        _rag = RAGMED_rag(corpus_file, similarity_fn=similarity_fn, alpha=alpha)
        _corpus_path = corpus_file
    else:
        _rag._swap_retriever(similarity_fn, alpha)
    return _rag


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CONTEXT_PLACEHOLDER = "*Send a message to see which document fragments were used to generate the answer.*"


def _format_context(retrieved: list[tuple[str, float]], top_n: int) -> str:
    if not retrieved:
        return "*No fragments were retrieved for this query.*"
    lines = [f"**Top-{top_n} retrieved fragments** — ranked by similarity score\n\n---\n"]
    for i, (chunk, score) in enumerate(retrieved, 1):
        preview = chunk[:500].replace("\n", " ")
        lines.append(f"**[{i}]** &nbsp; score `{score:.4f}`\n\n> {preview}\n")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Event handler (generator → streams both chat and context)
# ---------------------------------------------------------------------------


def respond(
    message: str,
    history: list,
    corpus_file: str,
    similarity_fn: str,
    alpha: float,
    top_n: int,
):
    if not message.strip():
        yield history, gr.update()
        return

    rag = _ensure_rag(corpus_file, similarity_fn, int(top_n))
    retrieved = rag.retrieve_function(message, int(top_n))
    context_md = _format_context(retrieved, int(top_n))

    history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": ""},
    ]
    for token in rag.ask_question_stream(message, max_results_ranking=int(top_n)):
        history[-1]["content"] += token
        yield history, context_md


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

CSS = """
footer { display: none !important; }

#ragmed-title {
    text-align: center;
    padding: 2rem 0 1rem;
}
#ragmed-title h1 {
    font-size: 2.2rem;
    font-weight: 700;
    letter-spacing: -0.5px;
    margin: 0 0 0.4rem;
}
#ragmed-title p {
    color: var(--body-text-color-subdued, #6b7280);
    margin: 0;
    font-size: 0.95rem;
}

/* Keep send/clear buttons vertically aligned with the textarea */
#btn-col {
    justify-content: flex-end;
    padding-bottom: 4px;
}
"""

# ---------------------------------------------------------------------------
# UI layout
# ---------------------------------------------------------------------------

with gr.Blocks(title="RAGMED — Medical Symptom Assistant") as demo:

    with gr.Column(elem_id="ragmed-title"):
        gr.HTML(
            "<h1>🏥 RAGMED</h1>"
            "<p>Describe your symptoms and I'll suggest possible conditions "
            "based on a corpus of medical literature.</p>"
        )

    chatbot = gr.Chatbot(
        value=[],
        label="",
        height=480,
        layout="bubble",
        buttons=["copy"],
        placeholder="<strong>RAGMED</strong> — Start by describing your symptoms below.",
    )

    with gr.Row():
        msg_box = gr.Textbox(
            placeholder="e.g. I have a fever, sore throat, and severe body aches since yesterday...",
            label="",
            lines=2,
            max_lines=6,
            scale=9,
            show_label=False,
            submit_btn=False,
        )
        with gr.Column(scale=1, min_width=110, elem_id="btn-col"):
            send_btn = gr.Button("Send ↵", variant="primary")
            clear_btn = gr.Button("Clear", variant="secondary", size="sm")

    with gr.Accordion("🔍  Retrieved context", open=False):
        context_box = gr.Markdown(value=_CONTEXT_PLACEHOLDER)

    with gr.Accordion("⚙️  Configuration", open=False):
        with gr.Row():
            corpus_in = gr.Textbox(
                value=_CORPUS_FILE,
                label="Corpus file",
                placeholder="Path to diseases.txt",
                scale=2,
            )
            sim_fn = gr.Dropdown(
                choices=["hybrid", "cosine", "euclidean", "jaccard"],
                value="hybrid",
                label="Retrieval function",
                scale=1,
            )
        with gr.Row():
            alpha_sl = gr.Slider(
                minimum=0.0, maximum=1.0, step=0.05, value=0.5,
                label="Alpha (cosine weight in hybrid)",
            )
            topn_sl = gr.Slider(
                minimum=1, maximum=20, step=1, value=5,
                label="Top-N chunks",
            )

    # ---------------------------------------------------------------------------
    # Event wiring
    # ---------------------------------------------------------------------------

    _inputs = [msg_box, chatbot, corpus_in, sim_fn, alpha_sl, topn_sl]
    _outputs = [chatbot, context_box]

    send_btn.click(respond, inputs=_inputs, outputs=_outputs).then(
        fn=lambda: "", inputs=None, outputs=msg_box
    )
    msg_box.submit(respond, inputs=_inputs, outputs=_outputs).then(
        fn=lambda: "", inputs=None, outputs=msg_box
    )
    clear_btn.click(
        fn=lambda: ([], _CONTEXT_PLACEHOLDER),
        inputs=None,
        outputs=[chatbot, context_box],
    )

if __name__ == "__main__":
    demo.launch(
        theme=gr.themes.Soft(
            primary_hue="blue",
            neutral_hue="slate",
            font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "sans-serif"],
        ),
        css=CSS,
    )
