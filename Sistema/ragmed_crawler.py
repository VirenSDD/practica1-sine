"""
RAGMED Crawler — scrapes Wikipedia disease articles and produces a clean
diseases.txt file for the RAGMED RAG system to consume.
"""

import logging
import os
import random
import time
from urllib.parse import unquote

import requests
from _helpers import find_section, parse_sections, safe_filename
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# HTTP / rate-limit constants
# ---------------------------------------------------------------------------

_WIKI_API = "https://en.wikipedia.org/w/api.php"
_WIKI_BASE = "https://en.wikipedia.org"
_HEADERS = {"User-Agent": "RAGMED-Crawler/1.0 (university homework; contact: student)"}
_TIMEOUT = 30
_RATE_LIMIT = 1.5  # seconds between requests (Wikipedia throttles burst traffic)
_MAX_RETRIES = 3  # retries on 429 / 503 with exponential backoff

# ---------------------------------------------------------------------------
# Domain-specific section name constants
# ---------------------------------------------------------------------------

_SYMPTOM_SECTIONS = ["Signs and symptoms"]
_CAUSE_SECTIONS = ["Causes"]
_TREATMENT_SECTIONS = ["Treatment", "Management", "Prevention"]


class RAGMED_crawler:
    """Crawler that downloads Wikipedia disease articles and formats them for RAG."""

    def __init__(self, max_diseases: int | None = None) -> None:
        """
        Initialise the crawler.

        :param max_diseases: Maximum number of diseases to process. If ``None``,
            all discovered diseases are processed.
        """
        self.max_diseases = max_diseases
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
        :param list_file: Output path for the disease name list.
        :param corpus_file: Output path for the consolidated corpus.
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
        """
        Scrape the Wikipedia alphabetical disease-list pages and save names to a file.

        :param letters: Uppercase letters to scrape, e.g. ``["A", "B"]``.
            Defaults to all 26 letters of the alphabet.
        :param output_file: Path of the text file where disease names are saved.
        :param shuffle: If ``True``, randomise the list before applying ``max_diseases``.
        """
        if letters is None:
            letters = [chr(ord("A") + i) for i in range(26)]

        seen: set[str] = set()
        diseases: list[str] = []

        for letter in letters:
            url = f"{_WIKI_BASE}/wiki/List_of_diseases_({letter})"
            logger.info("Fetching disease list for letter %s", letter)
            try:
                resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
                resp.raise_for_status()
            except requests.RequestException as exc:
                logger.warning("Could not fetch list page for letter %s: %s", letter, exc)
                continue

            soup = BeautifulSoup(resp.text, "lxml")
            content_div = soup.find(id="mw-content-text")
            if content_div is None:
                logger.warning("No content div found for letter %s", letter)
                continue

            # Strip navigation noise before iterating links
            for noise in content_div.find_all(
                class_=["navbox", "toc", "mw-references-wrap", "hatnote"]
            ):
                noise.decompose()

            for li in content_div.find_all("li"):
                anchor = li.find("a", href=True)
                if anchor is None:
                    continue
                href: str = anchor["href"]
                # Skip red links and Wikipedia special-namespace pages
                if not href.startswith("/wiki/") or ":" in href or href.startswith("/w/"):
                    continue
                name = unquote(href[len("/wiki/") :]).replace("_", " ").split("#")[0].strip()
                if name and name not in seen:
                    seen.add(name)
                    diseases.append(name)

            time.sleep(_RATE_LIMIT)

        if shuffle:
            random.shuffle(diseases)

        if self.max_diseases is not None:
            diseases = diseases[: self.max_diseases]

        self.disease_list = diseases

        parent = os.path.dirname(output_file)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as fh:
            fh.writelines(name + "\n" for name in self.disease_list)

        logger.info("Disease list saved to %s (%d diseases)", output_file, len(self.disease_list))

    def _download_disease_info(self) -> None:
        """
        Download the plain-text Wikipedia extract for each disease in ``self.disease_list``.

        Saves each extract to ``diseases/{name}.txt``. Diseases that cannot be
        fetched are logged and skipped without raising an exception.
        """
        os.makedirs("diseases", exist_ok=True)

        for name in self.disease_list:
            output_path = os.path.join("diseases", f"{safe_filename(name)}.txt")
            logger.info("Downloading extract for '%s'", name)

            extract = self._fetch_wikipedia_extract(name)
            if extract is None:
                logger.warning("Skipping '%s' — no extract retrieved.", name)
                continue

            with open(output_path, "w", encoding="utf-8") as fh:
                fh.write(extract)
            logger.info("Saved raw extract to %s", output_path)
            time.sleep(_RATE_LIMIT)

    def _clean_disease_page(self, disease_name: str) -> None:
        """
        Parse a raw Wikipedia extract and write the structured clean version.

        Extracts the lead paragraph plus Signs and symptoms, Causes, and
        Treatment sections, writing ``diseases/{name}_clean.txt``.

        :param disease_name: Disease name matching an existing raw extract file.
        """
        input_path = os.path.join("diseases", f"{safe_filename(disease_name)}.txt")
        output_path = os.path.join("diseases", f"{safe_filename(disease_name)}_clean.txt")

        if not os.path.exists(input_path):
            logger.warning("Raw file not found for '%s'", disease_name)
            return

        with open(input_path, encoding="utf-8") as fh:
            raw_text = fh.read()

        lead, sections = parse_sections(raw_text)

        def _text(section_names: list[str]) -> str:
            value = find_section(sections, section_names)
            return value.strip() if value and value.strip() else "(No information available.)"

        parts = [
            f"Lead: {lead.strip() or '(No information available.)'}",
            f"Signs and symptoms\n{'=' * 18}\n{_text(_SYMPTOM_SECTIONS)}",
            f"Causes\n{'=' * 6}\n{_text(_CAUSE_SECTIONS)}",
            f"Treatment\n{'=' * 9}\n{_text(_TREATMENT_SECTIONS)}",
        ]

        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write("\n\n".join(parts) + "\n")
        logger.info("Cleaned page saved to %s", output_path)

    def _generate_disease_summary(self, output_file: str = "diseases.txt") -> None:
        """
        Combine all per-disease clean files into a single corpus file.

        Only diseases in ``self.disease_list`` that have a corresponding
        ``_clean.txt`` file are included. Missing files are logged and skipped.

        :param output_file: Path of the combined output file.
        """
        with open(output_file, "w", encoding="utf-8") as summary_fh:
            for name in self.disease_list:
                clean_path = os.path.join("diseases", f"{safe_filename(name)}_clean.txt")
                if not os.path.exists(clean_path):
                    logger.warning("Clean file missing for '%s', skipping.", name)
                    continue
                with open(clean_path, encoding="utf-8") as fh:
                    content = fh.read()
                summary_fh.write(f"{name}\n{'=' * len(name)}\n{content}\n\n")

        logger.info("Disease summary written to %s", output_file)

    # ------------------------------------------------------------------
    # Private HTTP helper
    # ------------------------------------------------------------------

    def _fetch_wikipedia_extract(self, disease_name: str) -> str | None:
        """
        Call the Wikipedia API and return the plain-text extract for an article.

        Retries up to ``_MAX_RETRIES`` times with exponential backoff on HTTP
        429 and 503 responses.

        :param disease_name: Article title to look up (spaces, not underscores).
        :return: Plain-text extract string, or ``None`` if not found or on error.
        """
        params = {
            "action": "query",
            "prop": "extracts",
            "explaintext": True,
            "titles": disease_name,
            "format": "json",
            "redirects": 1,
        }

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                resp = requests.get(_WIKI_API, params=params, headers=_HEADERS, timeout=_TIMEOUT)
                resp.raise_for_status()
                break
            except requests.HTTPError as exc:
                if exc.response is not None and exc.response.status_code in (429, 503):
                    wait = 2**attempt
                    logger.warning(
                        "Rate limited on '%s' (attempt %d/%d), retrying in %ds",
                        disease_name,
                        attempt,
                        _MAX_RETRIES,
                        wait,
                    )
                    time.sleep(wait)
                    if attempt == _MAX_RETRIES:
                        logger.error("Max retries reached for '%s'", disease_name)
                        return None
                else:
                    logger.error("HTTP error for '%s': %s", disease_name, exc)
                    return None
            except requests.RequestException as exc:
                logger.error("Request error for '%s': %s", disease_name, exc)
                return None

        try:
            data = resp.json()
            page = next(iter(data["query"]["pages"].values()))
        except (KeyError, StopIteration, ValueError) as exc:
            logger.error("Unexpected API response for '%s': %s", disease_name, exc)
            return None

        if page.get("pageid") == -1 or "missing" in page:
            logger.warning("Wikipedia article not found for '%s'", disease_name)
            return None

        extract: str | None = page.get("extract")
        if not extract:
            logger.warning("Empty extract returned for '%s'", disease_name)
            return None

        return extract
