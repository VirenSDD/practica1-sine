"""
RAGMED — main entry point.

Phase 1: runs the crawler pipeline via CLI arguments.
Phase 2: interactive RAG chatbot loop powered by RAGMED_rag.
"""

import argparse
import os

from ragmed_crawler import RAGMED_crawler
from ragmed_rag import RAGMED_rag
from ragmed_source import WikipediaDiseaseSource


def run_ragmed() -> None:
    """Entry point for the RAGMED disease RAG system."""
    parser = argparse.ArgumentParser(
        description="RAGMED — suggest diseases from symptoms using a local RAG system.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--max-diseases",
        type=int,
        default=None,
        metavar="N",
        help="Maximum number of diseases to crawl (default: all)",
    )
    parser.add_argument(
        "--letters",
        nargs="+",
        metavar="LETTER",
        help="Restrict crawl to specific letters, e.g. --letters A B C (default: A–Z)",
    )
    parser.add_argument(
        "--shuffle",
        action="store_true",
        help="Randomise disease order before applying --max-diseases, for varied samples",
    )
    parser.add_argument(
        "--corpus-file",
        default="diseases.txt",
        metavar="PATH",
        help="Output path for the consolidated corpus",
    )
    parser.add_argument(
        "--list-file",
        default="disease_list.txt",
        metavar="PATH",
        help="Output path for the disease name list",
    )
    parser.add_argument(
        "--skip-crawler",
        action="store_true",
        help="Skip crawling and use an existing corpus file",
    )
    parser.add_argument(
        '--similarity-fn',
        default='hybrid',
        choices=['cosine', 'euclidean', 'jaccard', 'hybrid'],
        help='Similarity function for retrieval',
    )
    parser.add_argument(
        '--alpha',
        type=float,
        default=0.5,
        help='Cosine weight in hybrid mode (0–1)',
    )
    parser.add_argument(
        '--top-n',
        type=int,
        default=5,
        help='Number of chunks to retrieve per query',
    )
    args = parser.parse_args()

    if args.skip_crawler:
        if not os.path.exists(args.corpus_file):
            parser.error(
                f"Corpus file '{args.corpus_file}' not found — "
                "run without --skip-crawler to generate it first."
            )
    else:
        RAGMED_crawler(
            source=WikipediaDiseaseSource(),
            max_diseases=args.max_diseases,
        ).build_corpus(
            letters=args.letters or None,
            shuffle=args.shuffle,
            list_file=args.list_file,
            corpus_file=args.corpus_file,
        )

    print(f"\nCorpus ready at '{args.corpus_file}'. Starting RAG chatbot...")
    rag = RAGMED_rag(args.corpus_file,
                     similarity_fn=args.similarity_fn,
                     alpha=args.alpha)
    while True:
        query = input("\nDescribe your symptoms (or 'stop' to quit): ")
        if query.strip().lower() == 'stop':
            print("Goodbye!")
            break
        rag.ask_question(query, max_results_ranking=args.top_n)


if __name__ == "__main__":
    run_ragmed()
