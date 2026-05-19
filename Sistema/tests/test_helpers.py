"""Unit tests for _helpers.py — pure utility functions, no I/O."""

from _helpers import find_section, parse_sections, safe_filename


class TestSafeFilename:
    def test_spaces_become_underscores(self):
        assert safe_filename("Hello World") == "Hello_World"

    def test_special_chars_removed(self):
        assert safe_filename('a<>:"/\\|?*b') == "ab"

    def test_plain_name_unchanged(self):
        assert safe_filename("Diabetes") == "Diabetes"

    def test_spaces_and_special_chars(self):
        result = safe_filename("Heart: failure")
        assert " " not in result
        assert ":" not in result


class TestParseSections:
    def test_lead_only_text(self):
        text = "Just a description with no sections."
        lead, sections = parse_sections(text)
        assert lead == text
        assert sections == {}

    def test_single_section(self):
        text = "Lead text.\n\n== Signs and symptoms ==\nFever.\n"
        lead, sections = parse_sections(text)
        assert "Lead text." in lead
        assert "Signs and symptoms" in sections
        assert "Fever." in sections["Signs and symptoms"]

    def test_multiple_sections(self):
        text = "Lead.\n\n== Causes ==\nVirus.\n\n== Treatment ==\nRest.\n"
        _, sections = parse_sections(text)
        assert "Causes" in sections
        assert "Treatment" in sections
        assert "Virus." in sections["Causes"]
        assert "Rest." in sections["Treatment"]

    def test_lead_is_text_before_first_heading(self):
        text = "Intro paragraph.\n\n== Section ==\nContent.\n"
        lead, _ = parse_sections(text)
        assert lead.strip() == "Intro paragraph."


class TestFindSection:
    def test_returns_first_matching_candidate(self):
        sections = {"Treatment": "Take medicine.", "Management": "Other text."}
        assert find_section(sections, ["Treatment", "Management"]) == "Take medicine."

    def test_skips_to_next_candidate_when_first_missing(self):
        sections = {"Management": "Manage it."}
        assert find_section(sections, ["Treatment", "Management", "Prevention"]) == "Manage it."

    def test_returns_none_when_no_candidate_matches(self):
        sections = {"History": "Long history."}
        assert find_section(sections, ["Treatment", "Management"]) is None

    def test_empty_sections_returns_none(self):
        assert find_section({}, ["Treatment"]) is None
