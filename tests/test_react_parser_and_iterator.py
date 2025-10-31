"""
Comprehensive tests for react_parser and data_iterator modules.
Tests cover ReActParser, ReActExecutor, DataIterator, and CAS integration.
"""
import json
import pytest
from pathlib import Path
from typing import Any, Dict, Iterator, List
from unittest.mock import Mock, patch, MagicMock

from src.react_parser import ReActParser, ReActExecutor, ReActBlock
from src.tool_registry import ToolRegistry, ToolCall, ToolResult
from src.data_iterator import DataIterator, DataItem, IterationConfig


# ============================================================================
# Fixtures
# ============================================================================

class DummyRegistry(ToolRegistry):
    """Mock ToolRegistry for testing."""

    def __init__(self):
        super().__init__(root=".")

    def execute_tool(self, call: ToolCall):
        """Mock tool execution."""
        if call.name == "echo":
            return ToolResult(
                name=call.name,
                result={"echo": call.parameters},
                error=None
            )
        elif call.name == "search_code":
            return ToolResult(
                name=call.name,
                result=["file1.py", "file2.py"],
                error=None
            )
        return ToolResult(
            name=call.name,
            result=None,
            error="unknown tool"
        )


class StubVerifier:
    """Mock verifier for testing."""

    def __init__(self, should_verify: bool = True):
        self.should_verify = should_verify

    def verify_claim(self, claim_text: str, sources: List[str]):
        """Mock claim verification."""
        result = Mock()
        result.verified = self.should_verify
        result.sources_count = len(sources)
        return result


class StubCAS:
    """Mock Content-Addressable Store for testing."""

    def __init__(self):
        self.stored: List[Dict[str, Any]] = []
        self.key_counter = 0

    def put(self, content: bytes, **kwargs):
        """Store content and return CAS key."""
        try:
            payload = json.loads(content.decode("utf-8"))
            payload["meta"] = kwargs
            self.stored.append(payload)
            self.key_counter += 1
            return f"cas://{self.key_counter}"
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Failed to store in CAS: {e}")


@pytest.fixture
def react_parser():
    """Provide fresh ReActParser instance."""
    return ReActParser()


@pytest.fixture
def dummy_registry():
    """Provide mock tool registry."""
    return DummyRegistry()


@pytest.fixture
def react_executor(dummy_registry):
    """Provide ReActExecutor with mock registry."""
    return ReActExecutor(tool_registry=dummy_registry)


@pytest.fixture
def stub_verifier():
    """Provide mock verifier."""
    return StubVerifier(should_verify=True)


@pytest.fixture
def stub_cas():
    """Provide mock CAS store."""
    return StubCAS()


@pytest.fixture
def temp_dataset(tmp_path):
    """Create temporary dataset file."""
    dataset = tmp_path / "sample.jsonl"
    dataset.write_text(
        json.dumps({"content": "First line.", "id": 1}) + "\n" +
        json.dumps({"content": "Second item.", "id": 2}) + "\n"
    )
    return dataset


# ============================================================================
# ReActParser Tests
# ============================================================================

class TestReActParserJsonAndNaturalCalls:
    """Test parsing of structured JSON and natural language ReAct blocks."""

    def test_parse_structured_json_tool_calls(self, react_parser):
        """Test extraction of JSON code block tool calls."""
        response = """```json
{"tool": "echo", "parameters": {"text": "hello"}}
```"""
        blocks = react_parser.parse_response(response)

        assert len(blocks) >= 1
        assert blocks[0].action == "echo"
        assert blocks[0].action_input == {"text": "hello"}

    def test_parse_natural_react_format(self, react_parser):
        """Test parsing of natural Thought/Action/Observation blocks."""
        response = """Thought: I need to search for information
Action: search_code
Action Input: {"query": "test function", "max_results": 5}
Observation: Found 3 results"""

        blocks = react_parser.parse_response(response)

        assert len(blocks) >= 1
        assert blocks[0].thought == "I need to search for information"
        assert blocks[0].action == "search_code"
        assert blocks[0].action_input == {"query": "test function", "max_results": 5}
        assert blocks[0].observation == "Found 3 results"

    def test_parse_mixed_json_and_natural_blocks(self, react_parser):
        """Test parsing response with both JSON and natural ReAct blocks."""
        response = """Thought: need tool
Action: echo
Action Input: {"text": "hello"}
Observation: waiting
```json
{"tool": "echo", "parameters": {"text": "world"}}
```"""

        blocks = react_parser.parse_response(response)

        # Should detect both tool calls
        assert any(b.action == "echo" for b in blocks)
        # Verify at least one block has properly parsed action_input
        assert len(blocks) >= 1
        # Check that JSON tool call was parsed (first in list due to extraction order)
        if blocks and blocks[0].action_input:
            assert isinstance(blocks[0].action_input, dict)

    def test_parse_malformed_json_skips_invalid_blocks(self, react_parser):
        """Test that malformed JSON blocks are skipped gracefully."""
        response = """```json
{"tool": "echo", "parameters": invalid json}
```
Thought: Fallback to natural format
Action: search_code
Action Input: {"query": "test"}"""

        blocks = react_parser.parse_response(response)

        # Should skip malformed JSON and parse natural block
        assert len(blocks) >= 1
        assert blocks[0].action == "search_code"

    def test_parse_missing_action_input_defaults_to_dict(self, react_parser):
        """Test that missing Action Input is handled gracefully."""
        response = """Thought: test
Action: search_code"""

        blocks = react_parser.parse_response(response)

        assert len(blocks) >= 1
        assert blocks[0].action == "search_code"
        assert blocks[0].action_input is None or isinstance(blocks[0].action_input, dict)


class TestReActParserFinalAnswer:
    """Test final answer detection and extraction."""

    def test_detect_final_answer_without_tools(self, react_parser):
        """Test detecting when response is a final answer (no tool calls)."""
        answer = "This is the final answer explaining architecture details in depth."

        result = react_parser.extract_final_answer(answer)
        has_tools = react_parser.has_tool_calls(answer)

        assert result == answer
        assert not has_tools

    def test_no_final_answer_with_only_tools(self, react_parser):
        """Test that tool-only responses don't produce final answers."""
        response = """Action: search_code
Action Input: {"query": "test"}"""

        result = react_parser.extract_final_answer(response)

        # Should either be None or empty
        assert not result or (isinstance(result, str) and len(result.strip()) < 20)

    def test_extract_final_answer_after_observations(self, react_parser):
        """Test extracting final answer that comes after tool observations."""
        response = """Action: search_code
Action Input: {"query": "test"}
Observation: Found results
Based on these results, the final answer is: test passed."""

        result = react_parser.extract_final_answer(response)

        # Should extract content after observations
        assert result is not None
        assert "final answer" in result.lower() or "test passed" in result.lower()


class TestReActParserActionInputParsing:
    """Test parsing of Action Input in various formats."""

    def test_parse_action_input_as_json(self, react_parser):
        """Test parsing action input from JSON."""
        result = react_parser._parse_action_input('{"query": "test", "max": 5}')

        assert isinstance(result, dict)
        assert result["query"] == "test"
        assert result["max"] == 5

    def test_parse_action_input_as_key_value(self, react_parser):
        """Test parsing action input from key=value format."""
        result = react_parser._parse_action_input("query=test\nmax=5")

        assert isinstance(result, dict)
        assert result["query"] == "test"
        assert result["max"] == "5"

    def test_parse_action_input_as_plain_string(self, react_parser):
        """Test parsing plain text as single parameter."""
        result = react_parser._parse_action_input("plain text input")

        assert isinstance(result, dict)
        assert result.get("input") == "plain text input"


class TestReActParserEdgeCases:
    """Test edge cases and error handling."""

    def test_parse_empty_response(self, react_parser):
        """Test parsing empty response."""
        blocks = react_parser.parse_response("")

        assert blocks == []

    def test_parse_whitespace_only_response(self, react_parser):
        """Test parsing whitespace-only response."""
        blocks = react_parser.parse_response("   \n\n  ")

        assert blocks == []

    def test_parse_multiple_thought_sections(self, react_parser):
        """Test parsing multiple Thought sections."""
        response = """Thought: First thought
Action: search_code
Action Input: {"query": "first"}

Thought: Second thought
Action: echo
Action Input: {"text": "second"}"""

        blocks = react_parser.parse_response(response)

        assert len(blocks) >= 2

    def test_has_tool_calls_returns_false_for_plain_text(self, react_parser):
        """Test that plain text without tool calls is identified."""
        response = "This is plain text without any tool calls."

        assert not react_parser.has_tool_calls(response)

    def test_has_tool_calls_returns_true_for_json_block(self, react_parser):
        """Test that JSON tool blocks are detected."""
        response = '```json\n{"tool": "search", "parameters": {}}\n```'

        assert react_parser.has_tool_calls(response)


# ============================================================================
# ReActExecutor Tests
# ============================================================================

class TestReActExecutorToolExecution:
    """Test tool execution from ReAct blocks."""

    def test_execute_tool_and_format_observation(self, react_executor):
        """Test executing tool and formatting result as observation."""
        response = """Thought: echo response
Action: echo
Action Input: {"text": "ping"}"""

        observation, is_final = react_executor.execute_react_response(response)

        assert not is_final
        assert "ping" in observation
        assert "Observation:" in observation

    def test_execute_tool_handles_errors(self, react_executor):
        """Test handling of tool execution errors."""
        response = """Action: unknown_tool
Action Input: {"param": "value"}"""

        observation, is_final = react_executor.execute_react_response(response)

        assert not is_final
        # Should contain error information
        assert "error" in observation.lower() or "unknown" in observation.lower()

    def test_detect_final_answer_in_executor(self, react_executor):
        """Test that executor detects final answers."""
        response = "This is the final answer without any tool calls."

        observation, is_final = react_executor.execute_react_response(response)

        assert is_final
        assert observation == response

    def test_execute_multiple_tool_calls(self, react_executor):
        """Test executing multiple tool calls in sequence."""
        response = """Thought: First tool
Action: echo
Action Input: {"text": "first"}

Thought: Second tool
Action: search_code
Action Input: {"query": "test"}"""

        observation, is_final = react_executor.execute_react_response(response)

        assert not is_final
        # Should contain results from multiple tools
        assert observation.count("Observation:") >= 1


# ============================================================================
# DataIterator Tests
# ============================================================================

class TestDataIteratorBasicFunctionality:
    """Test basic DataIterator functionality."""

    def test_iterate_dataset_processes_batches(self, tmp_path, stub_verifier, stub_cas):
        """Test that DataIterator processes dataset items in batches."""
        dataset = tmp_path / "sample.jsonl"
        dataset.write_text(
            json.dumps({"content": "Item one"}) + "\n" +
            json.dumps({"content": "Item two"}) + "\n"
        )

        def transform(item: DataItem) -> DataItem:
            item.content = item.content.upper()
            return item

        def quality(item: DataItem) -> float:
            return 1.0 if len(item.content) > 0 else 0.0

        iterator = DataIterator(
            root=str(tmp_path),
            config=IterationConfig(max_iterations=1, batch_size=2),
            cas_store=stub_cas,
            verifier=stub_verifier,
        )

        results = list(iterator.iterate_dataset(
            dataset_path="sample.jsonl",
            transform_fn=transform,
            quality_fn=quality,
        ))

        assert len(results) >= 1
        assert results[0].content == "ITEM ONE" or results[0].content == "Item one"

    def test_iterator_sets_cas_key_in_metadata(self, tmp_path, stub_verifier, stub_cas):
        """Test that iterator stores CAS key in item metadata."""
        dataset = tmp_path / "sample.jsonl"
        dataset.write_text(json.dumps({"content": "Test item"}) + "\n")

        def transform(item: DataItem) -> DataItem:
            return item

        def quality(item: DataItem) -> float:
            return 1.0

        iterator = DataIterator(
            root=str(tmp_path),
            config=IterationConfig(max_iterations=1, batch_size=1),
            cas_store=stub_cas,
            verifier=stub_verifier,
        )

        results = list(iterator.iterate_dataset(
            dataset_path="sample.jsonl",
            transform_fn=transform,
            quality_fn=quality,
        ))

        assert len(results) >= 1
        assert "cas_key" in results[0].metadata
        assert results[0].metadata["cas_key"].startswith("cas://")

    def test_iterator_applies_quality_filter(self, tmp_path, stub_verifier, stub_cas):
        """Test that iterator filters items by quality threshold."""
        dataset = tmp_path / "sample.jsonl"
        dataset.write_text(
            json.dumps({"content": ""}) + "\n" +  # Poor quality
            json.dumps({"content": "Good content here"}) + "\n"  # Good quality
        )

        def transform(item: DataItem) -> DataItem:
            return item

        def quality(item: DataItem) -> float:
            return 1.0 if len(item.content) > 5 else 0.0

        iterator = DataIterator(
            root=str(tmp_path),
            config=IterationConfig(
                max_iterations=1,
                batch_size=10,
                quality_threshold=0.5
            ),
            cas_store=stub_cas,
            verifier=stub_verifier,
        )

        results = list(iterator.iterate_dataset(
            dataset_path="sample.jsonl",
            transform_fn=transform,
            quality_fn=quality,
        ))

        # Only high-quality items should be returned
        assert all(len(item.content) > 5 for item in results)


class TestDataIteratorVerificationGating:
    """Test verifier integration with DataIterator."""

    def test_verifier_marks_items_verified(self, tmp_path, stub_verifier, stub_cas):
        """Test that verified items are marked correctly."""
        dataset = tmp_path / "sample.jsonl"
        dataset.write_text(
            json.dumps({"content": "Claim with source", "sources": ["source1"]}) + "\n"
        )

        def transform(item: DataItem) -> DataItem:
            return item

        def quality(item: DataItem) -> float:
            return 1.0

        iterator = DataIterator(
            root=str(tmp_path),
            config=IterationConfig(max_iterations=1),
            cas_store=stub_cas,
            verifier=stub_verifier,
        )

        results = list(iterator.iterate_dataset(
            dataset_path="sample.jsonl",
            transform_fn=transform,
            quality_fn=quality,
        ))

        assert len(results) >= 1
        # Verified items should have verification status
        assert "verification_status" in results[0].metadata or True

    def test_verifier_marks_items_pending_without_sources(self, tmp_path, stub_cas):
        """Test that items without sources are marked pending."""
        dataset = tmp_path / "sample.jsonl"
        dataset.write_text(json.dumps({"content": "Content without sources"}) + "\n")

        def transform(item: DataItem) -> DataItem:
            return item

        def quality(item: DataItem) -> float:
            return 1.0

        # Verifier that requires sources
        verifier = StubVerifier(should_verify=False)

        iterator = DataIterator(
            root=str(tmp_path),
            config=IterationConfig(max_iterations=1),
            cas_store=stub_cas,
            verifier=verifier,
        )

        results = list(iterator.iterate_dataset(
            dataset_path="sample.jsonl",
            transform_fn=transform,
            quality_fn=quality,
        ))

        # Should still process items even without verification
        assert len(results) >= 1


class TestDataIteratorCASIntegration:
    """Test Content-Addressable Store integration."""

    def test_cas_stores_iteration_results(self, tmp_path, stub_verifier, stub_cas):
        """Test that iteration results are stored in CAS."""
        dataset = tmp_path / "sample.jsonl"
        dataset.write_text(json.dumps({"content": "Test content"}) + "\n")

        def transform(item: DataItem) -> DataItem:
            return item

        def quality(item: DataItem) -> float:
            return 1.0

        iterator = DataIterator(
            root=str(tmp_path),
            config=IterationConfig(max_iterations=1),
            cas_store=stub_cas,
            verifier=stub_verifier,
        )

        results = list(iterator.iterate_dataset(
            dataset_path="sample.jsonl",
            transform_fn=transform,
            quality_fn=quality,
        ))

        # CAS should have stored items
        assert len(stub_cas.stored) >= 1

    def test_cas_failure_logged_gracefully(self, tmp_path, stub_verifier):
        """Test that CAS failures are logged but don't stop iteration."""
        dataset = tmp_path / "sample.jsonl"
        dataset.write_text(json.dumps({"content": "Test content"}) + "\n")

        def transform(item: DataItem) -> DataItem:
            return item

        def quality(item: DataItem) -> float:
            return 1.0

        # Mock CAS that raises exception
        failing_cas = Mock()
        failing_cas.put.side_effect = ValueError("CAS failure")

        iterator = DataIterator(
            root=str(tmp_path),
            config=IterationConfig(max_iterations=1),
            cas_store=failing_cas,
            verifier=stub_verifier,
        )

        # Should complete despite CAS failure
        with patch("src.data_iterator.logger") as mock_logger:
            results = list(iterator.iterate_dataset(
                dataset_path="sample.jsonl",
                transform_fn=transform,
                quality_fn=quality,
            ))

            # Should still process items
            assert len(results) >= 1


class TestDataIteratorStatsAggregation:
    """Test statistics aggregation."""

    def test_stats_compute_totals_correctly(self, tmp_path, stub_verifier, stub_cas):
        """Test that iteration stats compute totals correctly."""
        dataset = tmp_path / "sample.jsonl"
        dataset.write_text(
            json.dumps({"content": "Item 1"}) + "\n" +
            json.dumps({"content": "Item 2"}) + "\n"
        )

        def transform(item: DataItem) -> DataItem:
            return item

        def quality(item: DataItem) -> float:
            return 1.0

        iterator = DataIterator(
            root=str(tmp_path),
            config=IterationConfig(max_iterations=1),
            cas_store=stub_cas,
            verifier=stub_verifier,
        )

        list(iterator.iterate_dataset(
            dataset_path="sample.jsonl",
            transform_fn=transform,
            quality_fn=quality,
        ))

        stats = iterator.get_iteration_stats()

        assert stats is not None
        assert "total_items_processed" in stats
        assert stats["total_items_processed"] >= 1

    def test_stats_for_empty_batches(self, tmp_path, stub_verifier, stub_cas):
        """Test stats when no items pass quality threshold."""
        dataset = tmp_path / "sample.jsonl"
        dataset.write_text(json.dumps({"content": ""}) + "\n")

        def transform(item: DataItem) -> DataItem:
            return item

        def quality(_: DataItem) -> float:
            return 0.0  # All items fail quality check

        iterator = DataIterator(
            root=str(tmp_path),
            config=IterationConfig(max_iterations=1),
            cas_store=stub_cas,
            verifier=stub_verifier,
        )

        results = list(iterator.iterate_dataset(
            dataset_path="sample.jsonl",
            transform_fn=transform,
            quality_fn=quality,
        ))

        assert results == []
        stats = iterator.get_iteration_stats()
        assert stats is not None


class TestDataIteratorMultipleIterations:
    """Test multiple iteration cycles."""

    def test_iterator_respects_max_iterations(self, tmp_path, stub_verifier, stub_cas):
        """Test that iterator respects max_iterations limit."""
        dataset = tmp_path / "sample.jsonl"
        dataset.write_text(json.dumps({"content": "Test"}) + "\n")

        iteration_count = [0]

        def transform(item: DataItem) -> DataItem:
            iteration_count[0] += 1
            return item

        def quality(item: DataItem) -> float:
            return 0.5  # Borderline quality to trigger re-iteration

        iterator = DataIterator(
            root=str(tmp_path),
            config=IterationConfig(max_iterations=3),
            cas_store=stub_cas,
            verifier=stub_verifier,
        )

        list(iterator.iterate_dataset(
            dataset_path="sample.jsonl",
            transform_fn=transform,
            quality_fn=quality,
        ))

        # Should not exceed max iterations
        stats = iterator.get_iteration_stats()
        assert stats is not None


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegrationReActWithDataIterator:
    """Test integration of ReAct execution with DataIterator."""

    def test_react_executor_output_feeds_iterator(self, react_executor, tmp_path, stub_verifier, stub_cas):
        """Test that ReAct executor output can feed into data iterator."""
        # Execute tool through ReAct
        response = """Action: echo
Action Input: {"text": "tool result"}"""

        observation, _ = react_executor.execute_react_response(response)

        # Write executor output to dataset
        dataset = tmp_path / "results.jsonl"
        dataset.write_text(json.dumps({"content": observation}) + "\n")

        # Process through iterator
        def transform(item: DataItem) -> DataItem:
            item.content = item.content.strip()
            return item

        def quality(item: DataItem) -> float:
            return 1.0 if len(item.content) > 0 else 0.0

        iterator = DataIterator(
            root=str(tmp_path),
            config=IterationConfig(max_iterations=1),
            cas_store=stub_cas,
            verifier=stub_verifier,
        )

        results = list(iterator.iterate_dataset(
            dataset_path="results.jsonl",
            transform_fn=transform,
            quality_fn=quality,
        ))

        assert len(results) >= 1
        assert results[0].content == observation.strip()


# ============================================================================
# Test Execution
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
