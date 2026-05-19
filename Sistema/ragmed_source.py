"""
DiseaseSource — protocol and implementations for fetching disease data.

The Protocol decouples the crawler from any specific data source, enabling
dependency injection and in-memory stubs for testing.
"""

import logging
import time
from typing import Protocol
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Wikipedia-specific constants (isolated here, not in the crawler)
# ---------------------------------------------------------------------------

_WIKI_API = "https://en.wikipedia.org/w/api.php"
_WIKI_BASE = "https://en.wikipedia.org"
_HEADERS = {"User-Agent": "RAGMED-Crawler/1.0 (university homework; contact: student)"}
_TIMEOUT = 30
_RATE_LIMIT = 1.5  # seconds between requests (Wikipedia throttles burst traffic)
_MAX_RETRIES = 3  # retries on 429 / 503 with exponential backoff


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


class DiseaseSource(Protocol):
    """Interface for fetching disease names and article extracts."""

    def list_diseases(self, letters: list[str]) -> list[str]:
        """
        Return a deduplicated list of disease names for the given alphabet letters.

        :param letters: Uppercase letters to query, e.g. ``["A", "B"]``.
        :return: Deduplicated list of disease names in discovery order.
        """
        ...

    def fetch_extract(self, name: str) -> str | None:
        """
        Return the plain-text article extract for a disease, or ``None`` if unavailable.

        The text should follow the Wikipedia plain-text format: section headings
        are marked as ``== Section Name ==`` on their own line.

        :param name: Disease name (spaces, not underscores).
        :return: Plain-text extract, or ``None`` on failure or missing article.
        """
        ...


# ---------------------------------------------------------------------------
# Wikipedia implementation
# ---------------------------------------------------------------------------


class WikipediaDiseaseSource:
    """
    Fetches disease names and article extracts from the English Wikipedia.

    Uses the alphabetical list pages for disease discovery and the MediaWiki
    REST API (``explaintext=true``) for article content.
    """

    def list_diseases(self, letters: list[str]) -> list[str]:
        """
        Scrape Wikipedia alphabetical disease-list pages and return disease names.

        :param letters: Uppercase letters to scrape, e.g. ``["A", "B"]``.
        :return: Deduplicated list of disease names in discovery order.
        """
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

        return diseases

    def fetch_extract(self, name: str) -> str | None:
        """
        Call the Wikipedia API and return the plain-text extract for an article.

        Retries up to ``_MAX_RETRIES`` times with exponential backoff on HTTP
        429 and 503 responses.

        :param name: Article title to look up (spaces, not underscores).
        :return: Plain-text extract string, or ``None`` if not found or on error.
        """
        params = {
            "action": "query",
            "prop": "extracts",
            "explaintext": True,
            "titles": name,
            "format": "json",
            "redirects": 1,
        }

        resp = None
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
                        name,
                        attempt,
                        _MAX_RETRIES,
                        wait,
                    )
                    time.sleep(wait)
                    if attempt == _MAX_RETRIES:
                        logger.error("Max retries reached for '%s'", name)
                        return None
                else:
                    logger.error("HTTP error for '%s': %s", name, exc)
                    return None
            except requests.RequestException as exc:
                logger.error("Request error for '%s': %s", name, exc)
                return None

        if resp is None:
            return None

        try:
            data = resp.json()
            page = next(iter(data["query"]["pages"].values()))
        except (KeyError, StopIteration, ValueError) as exc:
            logger.error("Unexpected API response for '%s': %s", name, exc)
            return None

        if page.get("pageid") == -1 or "missing" in page:
            logger.warning("Wikipedia article not found for '%s'", name)
            return None

        extract: str | None = page.get("extract")
        if not extract:
            logger.warning("Empty extract returned for '%s'", name)
            return None

        time.sleep(_RATE_LIMIT)
        return extract
