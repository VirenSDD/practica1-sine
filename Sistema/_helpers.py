"""
Shared pure-utility functions and domain constants for the RAGMED pipeline.

All functions here are stateless and have no side effects, making them easy
to unit-test independently of the crawler and RAG modules.
"""

import re
from enum import Enum

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

#: Placeholder written into corpus sections that have no Wikipedia content.
NO_INFO = "(No information available.)"


class SectionHeader(str, Enum):
    """Section headers written by the crawler into the disease corpus.

    Inheriting from ``str`` means enum members compare equal to their string
    values and can be used directly wherever a plain string is expected.
    ``__str__`` is overridden because Python 3.12+ changed the default
    ``str(StrMixin | Enum)`` to return ``ClassName.member_name``.
    """

    SIGNS_AND_SYMPTOMS = "Signs and symptoms"
    CAUSES = "Causes"
    TREATMENT = "Treatment"
    MANAGEMENT = "Management"
    PREVENTION = "Prevention"

    def __str__(self) -> str:
        return self.value

# Regex to detect h2-level headings in Wikipedia plain-text API extracts.
# The API uses == Section Name == (with surrounding spaces) as markers.
_H2_PATTERN = re.compile(r"^== (.+?) ==$", re.MULTILINE)


def safe_filename(name: str) -> str:
    """
    Convert a human-readable name into a filesystem-safe string.

    :param name: Display name (may contain spaces and special characters).
    :return: String with spaces replaced by underscores and characters that
        are problematic on common filesystems (``< > : " / \\ | ? *``) removed.
    """
    safe = name.replace(" ", "_")
    safe = re.sub(r'[<>:"/\\|?*]', "", safe)
    return safe


def parse_sections(text: str) -> tuple[str, dict[str, str]]:
    """
    Split a Wikipedia plain-text extract into a lead paragraph and named sections.

    The Wikipedia API ``explaintext=true`` format uses ``== Section Name ==``
    for h2 headings.  Text before the first heading is returned as the *lead*.

    :param text: Full plain-text extract returned by the Wikipedia API.
    :return: Tuple of (lead_text, {section_name: section_body}).
    """
    parts = _H2_PATTERN.split(text)
    lead = parts[0]
    sections: dict[str, str] = {}
    it = iter(parts[1:])
    for section_name, section_body in zip(it, it, strict=False):
        sections[section_name.strip()] = section_body
    return lead, sections


def find_section(sections: dict[str, str], candidates: list[str]) -> str | None:
    """
    Return the body of the first matching section from a prioritised name list.

    :param sections: Mapping of section name to body text (from :func:`parse_sections`).
    :param candidates: Ordered list of section names to try, e.g.
        ``["Treatment", "Management", "Prevention"]``.
    :return: Body text of the first found section, or ``None`` if none match.
    """
    for candidate in candidates:
        if candidate in sections:
            return sections[candidate]
    return None
