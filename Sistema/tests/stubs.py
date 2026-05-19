"""
In-memory stubs for testing the RAGMED crawler without network calls.
"""

# ---------------------------------------------------------------------------
# Canonical fake extracts in Wikipedia plain-text API format.
# Section headers must be exactly "== Name ==" on their own line.
# ---------------------------------------------------------------------------

FLU_EXTRACT = (
    "The flu is a viral respiratory infection.\n\n"
    "== Signs and symptoms ==\n"
    "Fever, cough, and body aches.\n\n"
    "== Causes ==\n"
    "Influenza A or B virus.\n\n"
    "== Treatment ==\n"
    "Rest, fluids, and antivirals.\n"
)

DIABETES_EXTRACT = (
    "Diabetes mellitus is a chronic metabolic disease.\n\n"
    "== Signs and symptoms ==\n"
    "Excessive thirst and frequent urination.\n\n"
    "== Causes ==\n"
    "Insufficient insulin production or resistance.\n"
    # No Treatment section — exercises the "(No information available.)" fallback
)


class InMemoryDiseaseSource:
    """
    In-memory stub implementing the DiseaseSource Protocol.

    :param diseases: Mapping of disease name to plain-text extract (or ``None``
        to simulate a missing Wikipedia article).
    """

    def __init__(self, diseases: dict[str, str | None]) -> None:
        self._diseases = diseases

    def list_diseases(self, letters: list[str]) -> list[str]:
        letter_set = {letter.upper() for letter in letters}
        return [name for name in self._diseases if name[0].upper() in letter_set]

    def fetch_extract(self, name: str) -> str | None:
        return self._diseases.get(name)
