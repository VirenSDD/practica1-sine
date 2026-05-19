"""
RAGMED — main entry point.

Phase 1: runs the crawler pipeline via CLI arguments.
Phase 2 (TODO): adds the interactive RAG chatbot loop.
"""

import argparse
import os

from ragmed_crawler import RAGMED_crawler


def _run_crawler(args: argparse.Namespace) -> None:
    crawler = RAGMED_crawler(max_diseases=args.max_diseases)
    crawler.download_disease_list(
        letters=args.letters or None,
        output_file=args.list_file,
        shuffle=args.shuffle,
    )
    crawler.download_disease_info()
    for name in crawler.disease_list:
        crawler.clean_disease_page(name)
    crawler.generate_disease_summary(output_file=args.corpus_file)


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
    args = parser.parse_args()

    if args.skip_crawler:
        if not os.path.exists(args.corpus_file):
            parser.error(
                f"Corpus file '{args.corpus_file}' not found — "
                "run without --skip-crawler to generate it first."
            )
    else:
        _run_crawler(args)

    # Phase 2 — interactive chatbot loop will be added here once ragmed_rag.py is implemented
    print(f"\nCorpus ready at '{args.corpus_file}'. RAG chatbot coming in Phase 2.")


if __name__ == "__main__":
    run_ragmed()
