"""
Tests for ModelRouter alternating between paid/free Tongyi models.
"""
import pytest
from unittest.mock import Mock, patch

from config import ModelRouter


class TestModelRouter:
    """Test suite for ModelRouter behavior."""

    def test_router_alternates_models_at_interval(self):
        """Router should return primary model then free model on the Nth call."""
        router = ModelRouter(
            primary_model="alibaba/tongyi-deepresearch-30b-a3b",
            free_model="alibaba/tongyi-deepresearch-30b-a3b:free",
            free_interval=3,
        )
        expected_sequence = [
            "alibaba/tongyi-deepresearch-30b-a3b",
            "alibaba/tongyi-deepresearch-30b-a3b",
            "alibaba/tongyi-deepresearch-30b-a3b:free",
            "alibaba/tongyi-deepresearch-30b-a3b",
            "alibaba/tongyi-deepresearch-30b-a3b",
            "alibaba/tongyi-deepresearch-30b-a3b:free",
        ]
        actual_sequence = [router.next_model() for _ in range(6)]
        assert actual_sequence == expected_sequence

    def test_router_respects_interval_zero_always_primary(self):
        """If free_interval is 0 or None, always return primary model."""
        router_zero = ModelRouter(
            primary_model="paid",
            free_model="free",
            free_interval=0,
        )
        router_none = ModelRouter(
            primary_model="paid",
            free_model="free",
            free_interval=None,
        )
        for _ in range(5):
            assert router_zero.next_model() == "paid"
            assert router_none.next_model() == "paid"

    def test_router_with_no_free_model_always_primary(self):
        """If free_model is None/empty, always return primary model."""
        router_none = ModelRouter(
            primary_model="paid",
            free_model=None,
            free_interval=3,
        )
        router_empty = ModelRouter(
            primary_model="paid",
            free_model="  ",
            free_interval=3,
        )
        for _ in range(5):
            assert router_none.next_model() == "paid"
            assert router_empty.next_model() == "paid"

    def test_router_reset(self):
        """Reset should restart the counter from zero."""
        router = ModelRouter(
            primary_model="paid",
            free_model="free",
            free_interval=2,
        )
        # Advance a few steps
        router.next_model()
        router.next_model()
        router.next_model()
        # Reset and verify sequence restarts
        router.reset()
        assert router.next_model() == "paid"
        assert router.next_model() == "free"

    def test_router_strips_whitespace(self):
        """Router should strip whitespace from model names."""
        router = ModelRouter(
            primary_model="  paid  ",
            free_model="  free  ",
            free_interval=2,
        )
        assert router.next_model() == "paid"
        assert router.next_model() == "free"

    def test_default_router_configuration(self):
        """DEFAULT_MODEL_ROUTER should use the expected interval and models."""
        from config import DEFAULT_MODEL_ROUTER, DEFAULT_TONGYI_CONFIG
        assert DEFAULT_MODEL_ROUTER.primary_model == DEFAULT_TONGYI_CONFIG.model_name
        assert DEFAULT_MODEL_ROUTER.free_model == DEFAULT_TONGYI_CONFIG.free_model_name
        assert DEFAULT_MODEL_ROUTER.free_interval == DEFAULT_TONGYI_CONFIG.free_call_interval
        # Verify it alternates at the configured interval
        sequence = [DEFAULT_MODEL_ROUTER.next_model() for _ in range(6)]
        assert sequence[2] == DEFAULT_TONGYI_CONFIG.free_model_name
        assert sequence[5] == DEFAULT_TONGYI_CONFIG.free_model_name
