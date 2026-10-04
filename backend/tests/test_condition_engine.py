"""
Tests for the condition engine.
"""
import pytest
from app.services.condition_engine import ConditionEngine


class TestConditionEngine:
    def test_and_all_pass(self):
        config = {
            "logic": "AND",
            "conditions": [
                {"field": "tag", "operator": "contains", "value": "JEE"},
                {"field": "link_clicked", "operator": "equals", "value": False},
            ],
        }
        context = {"contact_tags": ["JEE", "FREE"], "link_clicked": False}
        assert ConditionEngine.evaluate(config, context) is True

    def test_and_one_fails(self):
        config = {
            "logic": "AND",
            "conditions": [
                {"field": "tag", "operator": "contains", "value": "JEE"},
                {"field": "link_clicked", "operator": "equals", "value": True},
            ],
        }
        context = {"contact_tags": ["JEE"], "link_clicked": False}
        assert ConditionEngine.evaluate(config, context) is False

    def test_or_one_passes(self):
        config = {
            "logic": "OR",
            "conditions": [
                {"field": "email", "operator": "exists", "value": None},
                {"field": "tag", "operator": "contains", "value": "PREMIUM"},
            ],
        }
        context = {"contact": {"email": "test@example.com"}, "contact_tags": []}
        assert ConditionEngine.evaluate(config, context) is True

    def test_empty_conditions_always_pass(self):
        assert ConditionEngine.evaluate({"logic": "AND", "conditions": []}, {}) is True

    def test_opted_out_field(self):
        config = {
            "logic": "AND",
            "conditions": [
                {"field": "opted_out", "operator": "is_false"},
            ],
        }
        context = {"contact": {"opted_out": False}}
        assert ConditionEngine.evaluate(config, context) is True

    def test_custom_metadata_field(self):
        config = {
            "logic": "AND",
            "conditions": [
                {"field": "meta.course", "operator": "equals", "value": "JEE"},
            ],
        }
        context = {"contact": {"metadata_": {"course": "JEE"}}}
        assert ConditionEngine.evaluate(config, context) is True
