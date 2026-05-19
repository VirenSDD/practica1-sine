"""
Pipeline tests for RAGMED_crawler.

All tests use InMemoryDiseaseSource (no network) and pytest's tmp_path
fixture to isolate file output from the working directory.
"""

import pytest

from ragmed_crawler import RAGMED_crawler
from stubs import InMemoryDiseaseSource


def make_crawler(source, tmp_path, max_diseases=None):
    return RAGMED_crawler(source=source, max_diseases=max_diseases, work_dir=str(tmp_path))


def run(crawler, **kwargs):
    crawler.build_corpus(list_file="disease_list.txt", corpus_file="diseases.txt", **kwargs)


# ---------------------------------------------------------------------------
# File creation
# ---------------------------------------------------------------------------


def test_list_file_written(fake_source, tmp_path):
    run(make_crawler(fake_source, tmp_path))
    assert (tmp_path / "disease_list.txt").exists()


def test_corpus_file_written(fake_source, tmp_path):
    run(make_crawler(fake_source, tmp_path))
    assert (tmp_path / "diseases.txt").exists()


def test_diseases_subdir_created(fake_source, tmp_path):
    run(make_crawler(fake_source, tmp_path))
    assert (tmp_path / "diseases").is_dir()


# ---------------------------------------------------------------------------
# List file content
# ---------------------------------------------------------------------------


def test_list_file_contains_disease_names(fake_source, tmp_path):
    run(make_crawler(fake_source, tmp_path))
    names = (tmp_path / "disease_list.txt").read_text().splitlines()
    assert "Flu" in names
    assert "Diabetes" in names


def test_missing_extract_still_in_list_file(fake_source, tmp_path):
    """'Broken arm' has no extract but should still appear in the name list."""
    run(make_crawler(fake_source, tmp_path))
    names = (tmp_path / "disease_list.txt").read_text().splitlines()
    assert "Broken arm" in names


# ---------------------------------------------------------------------------
# Corpus format
# ---------------------------------------------------------------------------


def test_corpus_contains_disease_name_header(fake_source, tmp_path):
    run(make_crawler(fake_source, tmp_path))
    corpus = (tmp_path / "diseases.txt").read_text()
    assert "Flu\n" + "=" * len("Flu") in corpus
    assert "Diabetes\n" + "=" * len("Diabetes") in corpus


def test_corpus_contains_section_headers(fake_source, tmp_path):
    run(make_crawler(fake_source, tmp_path))
    corpus = (tmp_path / "diseases.txt").read_text()
    assert "Signs and symptoms" in corpus
    assert "Causes" in corpus
    assert "Treatment" in corpus


def test_corpus_contains_extract_content(fake_source, tmp_path):
    run(make_crawler(fake_source, tmp_path))
    corpus = (tmp_path / "diseases.txt").read_text()
    assert "Influenza A or B virus." in corpus
    assert "Excessive thirst" in corpus


# ---------------------------------------------------------------------------
# Missing section fallback
# ---------------------------------------------------------------------------


def test_missing_section_gets_fallback(fake_source, tmp_path):
    """Diabetes has no Treatment section — should use the placeholder text."""
    run(make_crawler(fake_source, tmp_path))
    corpus = (tmp_path / "diseases.txt").read_text()
    assert "(No information available.)" in corpus


# ---------------------------------------------------------------------------
# Missing extract skipped from corpus
# ---------------------------------------------------------------------------


def test_missing_extract_absent_from_corpus(fake_source, tmp_path):
    run(make_crawler(fake_source, tmp_path))
    corpus = (tmp_path / "diseases.txt").read_text()
    assert "Broken arm" not in corpus


# ---------------------------------------------------------------------------
# max_diseases cap
# ---------------------------------------------------------------------------


def test_max_diseases_limits_list(fake_source, tmp_path):
    run(make_crawler(fake_source, tmp_path, max_diseases=1))
    names = (tmp_path / "disease_list.txt").read_text().splitlines()
    assert len(names) == 1


def test_max_diseases_limits_corpus(fake_source, tmp_path):
    run(make_crawler(fake_source, tmp_path, max_diseases=1))
    corpus = (tmp_path / "diseases.txt").read_text()
    # Each disease block has exactly one "Lead:" line
    lead_lines = [line for line in corpus.splitlines() if line.startswith("Lead:")]
    assert len(lead_lines) == 1


# ---------------------------------------------------------------------------
# Letter filtering
# ---------------------------------------------------------------------------


def test_letters_filter_restricts_diseases(tmp_path):
    source = InMemoryDiseaseSource({"Flu": "text", "Dengue": "text", "Anthrax": "text"})
    run(make_crawler(source, tmp_path), letters=["D"])
    names = (tmp_path / "disease_list.txt").read_text().splitlines()
    assert names == ["Dengue"]
