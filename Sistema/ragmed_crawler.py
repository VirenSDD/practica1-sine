"""
RAGMED Crawler — orchestrates the pipeline that builds the disease corpus.

All network I/O is delegated to a DiseaseSource implementation, making this
class fully testable without any HTTP calls.
"""

import logging
import os
import random

from _helpers import NO_INFO, SectionHeader, find_section, parse_sections, safe_filename
from ragmed_source import DiseaseSource

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

_ALL_LETTERS = [chr(ord("A") + i) for i in range(26)]

_SYMPTOM_SECTIONS = [SectionHeader.SIGNS_AND_SYMPTOMS]
_CAUSE_SECTIONS = [SectionHeader.CAUSES]
_TREATMENT_SECTIONS = [SectionHeader.TREATMENT, SectionHeader.MANAGEMENT, SectionHeader.PREVENTION]


class RAGMED_crawler:
    """
    Orchestrates the disease corpus pipeline.

    Delegates all data fetching to the injected ``DiseaseSource`` and handles
    only file I/O and text processing.
    """

    def __init__(
        self,
        source: DiseaseSource,
        max_diseases: int | None = None,
        work_dir: str = ".",
    ) -> None:
        """
        Initialise the crawler.

        :param source: Data source used to fetch disease names and extracts.
        :param max_diseases: Maximum number of diseases to process. If ``None``,
            all discovered diseases are processed.
        :param work_dir: Directory where output files are written. Defaults to
            the current working directory. Useful for isolating test output.
        """
        self._source = source
        self.max_diseases = max_diseases
        self._work_dir = work_dir
        self.disease_list: list[str] = []

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def build_corpus(
        self,
        letters: list[str] | None = None,
        shuffle: bool = False,
        list_file: str = "disease_list.txt",
        corpus_file: str = "diseases.txt",
    ) -> None:
        """
        Run the full pipeline: fetch names → download extracts → clean → consolidate.

        :param letters: Uppercase letters to scrape (default: A–Z).
        :param shuffle: Randomise order before applying the ``max_diseases`` cap,
            so repeated runs with a limit return a varied sample.
        :param list_file: Output path for the disease name list (relative to ``work_dir``).
        :param corpus_file: Output path for the consolidated corpus (relative to ``work_dir``).
        """
        self._download_disease_list(letters=letters, output_file=list_file, shuffle=shuffle)
        self._download_disease_info()
        for name in self.disease_list:
            self._clean_disease_page(name)
        self._generate_disease_summary(output_file=corpus_file)

    # ------------------------------------------------------------------
    # Private pipeline steps
    # ------------------------------------------------------------------

    def _download_disease_list(
        self,
        letters: list[str] | None = None,
        output_file: str = "disease_list.txt",
        shuffle: bool = False,
    ) -> None:
        diseases = self._source.list_diseases(letters or _ALL_LETTERS)

        if shuffle:
            random.shuffle(diseases)

        if self.max_diseases is not None:
            diseases = diseases[: self.max_diseases]

        self.disease_list = diseases

        path = self._resolve(output_file)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.writelines(name + "\n" for name in self.disease_list)

        logger.info("Disease list saved to %s (%d diseases)", path, len(self.disease_list))

    def _download_disease_info(self) -> None:
        diseases_dir = os.path.join(self._work_dir, "diseases")
        os.makedirs(diseases_dir, exist_ok=True)

        for name in self.disease_list:
            output_path = os.path.join(diseases_dir, f"{safe_filename(name)}.txt")
            logger.info("Fetching extract for '%s'", name)

            extract = self._source.fetch_extract(name)
            if extract is None:
                logger.warning("Skipping '%s' — no extract retrieved.", name)
                continue

            with open(output_path, "w", encoding="utf-8") as fh:
                fh.write(extract)
            logger.info("Saved raw extract to %s", output_path)

    def _clean_disease_page(self, disease_name: str) -> None:
        diseases_dir = os.path.join(self._work_dir, "diseases")
        input_path = os.path.join(diseases_dir, f"{safe_filename(disease_name)}.txt")
        output_path = os.path.join(diseases_dir, f"{safe_filename(disease_name)}_clean.txt")

        if not os.path.exists(input_path):
            logger.warning("Raw file not found for '%s'", disease_name)
            return

        with open(input_path, encoding="utf-8") as fh:
            raw_text = fh.read()

        lead, sections = parse_sections(raw_text)

        def _text(section_names: list[SectionHeader]) -> str:
            value = find_section(sections, section_names)
            return value.strip() if value and value.strip() else NO_INFO

        def _header(h: SectionHeader) -> str:
            return f"{h}\n{'=' * len(h)}"

        parts = [
            f"Lead: {lead.strip() or NO_INFO}",
            f"{_header(SectionHeader.SIGNS_AND_SYMPTOMS)}\n{_text(_SYMPTOM_SECTIONS)}",
            f"{_header(SectionHeader.CAUSES)}\n{_text(_CAUSE_SECTIONS)}",
            f"{_header(SectionHeader.TREATMENT)}\n{_text(_TREATMENT_SECTIONS)}",
        ]

        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write("\n\n".join(parts) + "\n")
        logger.info("Cleaned page saved to %s", output_path)

    def _generate_disease_summary(self, output_file: str = "diseases.txt") -> None:
        diseases_dir = os.path.join(self._work_dir, "diseases")
        path = self._resolve(output_file)

        with open(path, "w", encoding="utf-8") as summary_fh:
            for name in self.disease_list:
                clean_path = os.path.join(diseases_dir, f"{safe_filename(name)}_clean.txt")
                if not os.path.exists(clean_path):
                    logger.warning("Clean file missing for '%s', skipping.", name)
                    continue
                with open(clean_path, encoding="utf-8") as fh:
                    content = fh.read()
                summary_fh.write(f"{name}\n{'=' * len(name)}\n{content}\n\n")

        logger.info("Disease summary written to %s", path)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve(self, path: str) -> str:
        """Resolve a relative path against work_dir; leave absolute paths unchanged."""
        if os.path.isabs(path):
            return path
        return os.path.join(self._work_dir, path)
