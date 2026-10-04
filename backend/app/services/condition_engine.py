"""
ConditionEngine — evaluates AND/OR condition trees against execution context.

Conditions are stored as JSON in workflow node config:
{
    "logic": "AND",  // "AND" | "OR"
    "conditions": [
        {
            "field": "tag",
            "operator": "exists",
            "value": "JEE"
        },
        {
            "field": "link_clicked",
            "operator": "equals",
            "value": false
        }
    ]
}

Supported fields:
  tag, email, link_clicked, button_clicked, follower_status,
  campaign, automation_history, custom_metadata, contact_status

Supported operators:
  equals, not_equals, contains, starts_with, exists, not_exists,
  greater_than, less_than, is_true, is_false
"""
from typing import Any, Optional


class ConditionEngine:
    @classmethod
    def evaluate(cls, condition_config: dict, context: dict) -> bool:
        """
        Evaluate a condition block against the execution context.

        context contains contact data, collected values, automation history, etc.
        """
        logic = condition_config.get("logic", "AND").upper()
        conditions = condition_config.get("conditions", [])

        if not conditions:
            return True  # No conditions = always pass

        results = [cls._evaluate_single(c, context) for c in conditions]

        if logic == "AND":
            return all(results)
        elif logic == "OR":
            return any(results)
        return False

    @classmethod
    def _evaluate_single(cls, condition: dict, context: dict) -> bool:
        field = condition.get("field", "")
        operator = condition.get("operator", "equals")
        expected = condition.get("value")

        actual = cls._resolve_field(field, context)

        return cls._apply_operator(actual, operator, expected)

    @classmethod
    def _resolve_field(cls, field: str, context: dict) -> Any:
        """Resolve a field name to its value from context."""
        field_map = {
            "email": context.get("contact", {}).get("email"),
            "tag": context.get("contact_tags", []),
            "link_clicked": context.get("link_clicked", False),
            "button_clicked": context.get("button_clicked"),
            "follower_status": context.get("follower_status"),
            "campaign": context.get("campaign_id"),
            "contact_status": context.get("contact", {}).get("status"),
            "opted_out": context.get("contact", {}).get("opted_out", False),
            "email_collected": bool(context.get("contact", {}).get("email")),
        }

        if field in field_map:
            return field_map[field]

        # Custom metadata fields: "meta.key"
        if field.startswith("meta."):
            key = field[5:]
            return context.get("contact", {}).get("metadata_", {}).get(key)

        # Collected values: "collected.key"
        if field.startswith("collected."):
            key = field[10:]
            return context.get("collected", {}).get(key)

        return None

    @classmethod
    def _apply_operator(cls, actual: Any, operator: str, expected: Any) -> bool:
        if operator == "equals":
            return actual == expected
        if operator == "not_equals":
            return actual != expected
        if operator == "contains":
            if isinstance(actual, list):
                return expected in actual
            if isinstance(actual, str):
                return str(expected).lower() in actual.lower()
            return False
        if operator == "starts_with":
            return isinstance(actual, str) and actual.lower().startswith(str(expected).lower())
        if operator == "exists":
            if isinstance(actual, list):
                return expected in actual if expected else len(actual) > 0
            return actual is not None and actual != "" and actual is not False
        if operator == "not_exists":
            if isinstance(actual, list):
                return expected not in actual if expected else len(actual) == 0
            return actual is None or actual == ""
        if operator == "is_true":
            return bool(actual)
        if operator == "is_false":
            return not bool(actual)
        if operator == "greater_than":
            try:
                return float(actual) > float(expected)
            except (TypeError, ValueError):
                return False
        if operator == "less_than":
            try:
                return float(actual) < float(expected)
            except (TypeError, ValueError):
                return False
        return False
