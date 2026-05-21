"""
ragmed_eval.py — batch evaluation runner for RAGMED.

Loads the RAG system once and runs all evaluation questions from
Evaluación/preguntas_ground_truth.md, saving retrieved context and
LLM responses to Evaluación/respuestas_sistema.md.
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ragmed_rag import RAGMED_rag

_REPO_ROOT = Path(__file__).parent.parent
_QUESTIONS_FILE = _REPO_ROOT / "Evaluación" / "preguntas_ground_truth.md"
_OUTPUT_FILE = _REPO_ROOT / "Evaluación" / "respuestas_sistema.md"

# Matches lines like:  **Pregunta (query):** I have a runny nose...
_QUERY_RE = re.compile(r"\*\*Pregunta \(query\):\*\*\s*(.+)")
# Matches section headings like:  ## Q1 — Common cold
_SECTION_RE = re.compile(r"^## (Q\d+ — .+)$", re.MULTILINE)


def _parse_questions(path: Path) -> list[tuple[str, str]]:
    """Return list of (heading, query_text) pairs from the ground truth file."""
    text = path.read_text(encoding="utf-8")
    headings = _SECTION_RE.findall(text)
    queries = _QUERY_RE.findall(text)
    if len(headings) != len(queries):
        raise ValueError(
            f"Mismatch: found {len(headings)} headings but {len(queries)} queries "
            f"in {path}"
        )
    return list(zip(headings, queries))


def main() -> None:
    parser = argparse.ArgumentParser(description="RAGMED batch evaluator")
    parser.add_argument("--corpus", default="diseases.txt", help="Path to diseases.txt")
    parser.add_argument("--top-n", type=int, default=5, help="Top-N chunks to retrieve")
    parser.add_argument("--alpha", type=float, default=0.5, help="Hybrid cosine weight (0–1)")
    parser.add_argument("--language-model", default="", help="Override the generation LLM")
    parser.add_argument(
        "--max-context-chars",
        type=int,
        default=0,
        help="Max chars per retrieved chunk shown to LLM (0 = no limit)",
    )
    parser.add_argument("--output", default="", help="Output file path (default: auto)")
    args = parser.parse_args()

    corpus_path = Path(args.corpus)
    if not corpus_path.exists():
        sys.exit(f"Corpus file not found: {corpus_path}")

    print(f"Loading RAG system from {corpus_path} …")
    rag = RAGMED_rag(
        str(corpus_path),
        similarity_fn="hybrid",
        alpha=args.alpha,
        language_model=args.language_model,
        max_context_chars=args.max_context_chars,
    )

    questions = _parse_questions(_QUESTIONS_FILE)
    print(f"\nLoaded {len(questions)} evaluation questions. Starting evaluation …\n")

    effective_model = args.language_model or rag.LANGUAGE_MODEL
    ctx_note = f", max-context-chars={args.max_context_chars}" if args.max_context_chars else ""

    output_path = Path(args.output) if args.output else _OUTPUT_FILE
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as out:
        out.write("# RAGMED — Respuestas del sistema\n\n")
        out.write(
            f"**Corpus:** {corpus_path}  \n"
            f"**Función de recuperación:** hybrid (α = {args.alpha})  \n"
            f"**Top-N:** {args.top_n}  \n"
            f"**Modelo de generación:** {effective_model}{ctx_note}\n\n"
            "---\n\n"
        )

        for heading, query in questions:
            print(f"[{heading}]")
            print(f"  Query: {query}")

            retrieved = rag.retrieve_function(query, args.top_n)
            response_tokens: list[str] = []
            for token in rag.ask_question_stream(query, args.top_n):
                response_tokens.append(token)
                print(token, end="", flush=True)
            print()
            response = "".join(response_tokens).strip()

            out.write(f"## {heading}\n\n")
            out.write(f"**Pregunta:** {query}\n\n")
            out.write(f"### Contexto recuperado (top-{args.top_n})\n\n")
            for chunk, score in retrieved:
                preview = chunk[:250].replace("\n", " ")
                out.write(f"- `{score:.4f}` {preview}\n")
            out.write(f"\n### Respuesta del sistema\n\n{response}\n\n---\n\n")
            out.flush()
            print(f"  → saved\n")

    print(f"\nEvaluation complete. Results saved to {output_path}")


if __name__ == "__main__":
    main()
