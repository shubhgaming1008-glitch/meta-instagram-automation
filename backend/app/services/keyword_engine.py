"""
Keyword matching engine — handles all trigger keyword matching logic.
"""
import re
from enum import Enum
from typing import Optional


class MatchMode(str, Enum):
    EXACT = "exact"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ANY = "any"              # Matches any non-empty text
    REGEX = "regex"          # Advanced: regex pattern


def normalize(text: str) -> str:
    """Lowercase and strip whitespace."""
    return text.strip().lower()


def match_keyword(
    text: str,
    keywords: list[str],
    mode: MatchMode,
    case_insensitive: bool = True,
    excluded_keywords: Optional[list[str]] = None,
) -> bool:
    """
    Check if `text` matches the keyword configuration.

    Args:
        text: The comment/DM text to check.
        keywords: List of keywords to match against.
        mode: Matching mode (exact, contains, starts_with, any).
        case_insensitive: If True, compare after lowercasing.
        excluded_keywords: If text contains any of these, return False.

    Returns:
        True if the text matches the rule, False otherwise.
    """
    if not text:
        return False

    check_text = normalize(text) if case_insensitive else text.strip()

    # Check excluded keywords first
    if excluded_keywords:
        for exc in excluded_keywords:
            exc_check = normalize(exc) if case_insensitive else exc.strip()
            if exc_check in check_text:
                return False

    # ANY mode: match any non-empty text
    if mode == MatchMode.ANY:
        return bool(check_text)

    # No keywords provided for keyword-based modes
    if not keywords:
        return False

    normalized_keywords = [normalize(k) if case_insensitive else k.strip() for k in keywords]

    if mode == MatchMode.EXACT:
        return check_text in normalized_keywords

    if mode == MatchMode.CONTAINS:
        return any(kw in check_text for kw in normalized_keywords)

    if mode == MatchMode.STARTS_WITH:
        return any(check_text.startswith(kw) for kw in normalized_keywords)

    if mode == MatchMode.REGEX:
        flags = re.IGNORECASE if case_insensitive else 0
        return any(
            re.search(kw, check_text, flags) is not None
            for kw in keywords  # Use raw keywords for regex
        )

    return False


def match_trigger_config(text: str, trigger_config: dict) -> bool:
    """
    Evaluate a trigger_config dict (from Automation.trigger_config) against text.

    Expected trigger_config structure:
    {
        "match_mode": "any" | "exact" | "contains" | "starts_with",
        "keywords": ["LINK", "PDF", "NOTES"],
        "case_insensitive": true,
        "excluded_keywords": ["spam"],
        "keyword_groups": [                        # Optional: groups with OR logic
            {"keywords": ["LINK", "URL"], "mode": "contains"},
            {"keywords": ["PDF"], "mode": "exact"},
        ]
    }
    """
    mode = MatchMode(trigger_config.get("match_mode", "any"))
    keywords = trigger_config.get("keywords", [])
    case_insensitive = trigger_config.get("case_insensitive", True)
    excluded = trigger_config.get("excluded_keywords", [])
    keyword_groups = trigger_config.get("keyword_groups", [])

    # Simple match
    if match_keyword(text, keywords, mode, case_insensitive, excluded):
        return True

    # Keyword groups (OR logic between groups)
    for group in keyword_groups:
        group_mode = MatchMode(group.get("mode", "contains"))
        group_keywords = group.get("keywords", [])
        if match_keyword(text, group_keywords, group_mode, case_insensitive, excluded):
            return True

    return False
