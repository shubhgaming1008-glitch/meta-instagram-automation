"""
Tests for the keyword matching engine.
"""
import pytest
from app.services.keyword_engine import MatchMode, match_keyword, match_trigger_config


class TestMatchKeyword:
    def test_any_mode_matches_any_text(self):
        assert match_keyword("hello", [], MatchMode.ANY) is True
        assert match_keyword("wow nice", [], MatchMode.ANY) is True
        assert match_keyword("?", [], MatchMode.ANY) is True

    def test_any_mode_rejects_empty(self):
        assert match_keyword("", [], MatchMode.ANY) is False

    def test_exact_match(self):
        assert match_keyword("LINK", ["LINK"], MatchMode.EXACT) is True
        assert match_keyword("link", ["LINK"], MatchMode.EXACT, case_insensitive=True) is True
        assert match_keyword("get link", ["LINK"], MatchMode.EXACT) is False

    def test_contains_match(self):
        assert match_keyword("I want the PDF please", ["PDF"], MatchMode.CONTAINS) is True
        assert match_keyword("nothing here", ["PDF"], MatchMode.CONTAINS) is False

    def test_starts_with_match(self):
        assert match_keyword("LINK me up", ["LINK"], MatchMode.STARTS_WITH) is True
        assert match_keyword("send LINK", ["LINK"], MatchMode.STARTS_WITH) is False

    def test_case_insensitive(self):
        assert match_keyword("pdf", ["PDF"], MatchMode.EXACT, case_insensitive=True) is True
        assert match_keyword("pdf", ["PDF"], MatchMode.EXACT, case_insensitive=False) is False

    def test_excluded_keywords(self):
        assert match_keyword("nice video", [], MatchMode.ANY, excluded_keywords=["spam"]) is True
        assert match_keyword("spam comment", [], MatchMode.ANY, excluded_keywords=["spam"]) is False

    def test_multiple_keywords(self):
        assert match_keyword("NOTES", ["PDF", "NOTES", "LINK"], MatchMode.EXACT) is True
        assert match_keyword("VIDEO", ["PDF", "NOTES", "LINK"], MatchMode.EXACT) is False


class TestMatchTriggerConfig:
    def test_any_mode(self):
        config = {"match_mode": "any"}
        assert match_trigger_config("hello", config) is True
        assert match_trigger_config("wow", config) is True

    def test_keyword_groups_or_logic(self):
        config = {
            "match_mode": "any",
            "keywords": [],
            "keyword_groups": [
                {"keywords": ["LINK", "URL"], "mode": "contains"},
                {"keywords": ["PDF"], "mode": "exact"},
            ],
        }
        assert match_trigger_config("I want the LINK", config) is True
        assert match_trigger_config("PDF", config) is True
        assert match_trigger_config("random stuff", config) is False
