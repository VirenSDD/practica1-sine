"""Shared pytest fixtures for the RAGMED test suite."""

import pytest

from stubs import DIABETES_EXTRACT, FLU_EXTRACT, InMemoryDiseaseSource


@pytest.fixture
def fake_source() -> InMemoryDiseaseSource:
    """Disease source with two real extracts and one missing article."""
    return InMemoryDiseaseSource(
        {
            "Flu": FLU_EXTRACT,
            "Diabetes": DIABETES_EXTRACT,
            "Broken arm": None,  # simulates a Wikipedia article not found
        }
    )
