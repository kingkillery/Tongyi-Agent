"""
Tests for Tongyi-powered orchestrator with tool calling.
"""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.tongyi_orchestrator import TongyiOrchestrator
from src.tool_registry import ToolCall, ToolResult


class TestTongyiOrchestrator:
    """Test suite for TongyiOrchestrator."""
    
    @pytest.fixture
    def mock_client(self):
        """Mock OpenRouter client."""
        client = Mock()
        return client
    
    @pytest.fixture
    def orchestrator(self, mock_client):
        """Create orchestrator with mocked client."""
        with patch('src.tongyi_orchestrator.load_openrouter_client', return_value=mock_client):
            return TongyiOrchestrator(root="/test")
    
    def test_init_requires_api_key(self):
        """Test that config validation happens at import time via Pydantic validation."""
        # The API key validation happens when DEFAULT_TONGYI_CONFIG is created
        # at module import time through Pydantic validation + field_validator
        with patch('config.os.getenv', return_value=None):
            # This should cause ValidationError when config module is imported
            with pytest.raises(Exception):  # Catch ValidationError or SystemExit
                import importlib
                import config
                importlib.reload(config)
    
    def test_init_handles_client_failure(self):
        """Test that orchestrator handles client initialization failure."""
        with patch('src.tongyi_orchestrator.load_openrouter_client') as mock_load:
            mock_load.return_value = None
            with pytest.raises(RuntimeError, match="Failed to initialize OpenRouter client"):
                TongyiOrchestrator()
    
    def test_simple_question_no_tools(self, orchestrator, mock_client):
        """Test handling of simple question without tool calls."""
        mock_client.chat.return_value = "This is a simple answer."
        
        result = orchestrator.run("What is 2+2?")
        
        assert result == "This is a simple answer."
        mock_client.chat.assert_called_once()
    
    def test_tool_call_execution(self, orchestrator, mock_client):
        """Test proper tool call execution."""
        # Create properly structured mock for tool call
        mock_function = Mock()
        mock_function.name = "search_code"  # Set as attribute, not parameter
        mock_function.arguments = json.dumps({"query": "test", "max_results": 5})
        
        mock_tool_call = Mock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function = mock_function
        
        # Mock tool call response
        tool_response = Mock()
        tool_response.tool_calls = [mock_tool_call]
        
        # Mock final response after tool execution
        final_response = Mock()
        final_response.tool_calls = None
        
        # Set up side_effect for two calls: first with tool, second with final answer
        mock_client.chat.side_effect = [tool_response, final_response]
        
        with patch.object(orchestrator.tools, 'execute_tool') as mock_execute:
            mock_execute.return_value = ToolResult(
                name="search_code",
                result=["file1.py", "file2.py", "file3.py"]
            )
            
            result = orchestrator.run("Find test functions")
            
            # Verify tool was executed
            assert mock_execute.call_count == 1, "execute_tool should be called once"
            call_args = mock_execute.call_args[0][0]
            assert call_args.name == "search_code"
            assert call_args.parameters == {"query": "test", "max_results": 5}
    
    def test_budget_enforcement(self, orchestrator, mock_client):
        """Test that tool budgets are enforced."""
        # Mock budget exceeded
        with patch.object(orchestrator.policy, 'allow', return_value=False):
            tool_response = Mock()
            tool_response.tool_calls = [
                Mock(
                    id="call_123",
                    function=Mock(
                        name="search_papers",
                        arguments=json.dumps({"query": "test"})
                    )
                )
            ]
            mock_client.chat.return_value = tool_response
            
            result = orchestrator.run("Search for papers")
            
            # Should include budget error in response
            assert "budget exceeded" in result or "Error" in result
    
    def test_malformed_tool_call(self, orchestrator, mock_client):
        """Test handling of malformed tool call JSON."""
        tool_response = Mock()
        tool_response.tool_calls = [
            Mock(
                id="call_123",
                function=Mock(
                    name="search_code",
                    arguments="invalid json {"
                )
            )
        ]
        mock_client.chat.return_value = tool_response
        
        # Should continue without executing the malformed tool
        result = orchestrator.run("Test malformed call")
        
        # Should not crash and should eventually return a response
        assert result is not None
    
    def test_fallback_json_tool_call(self, orchestrator, mock_client):
        """Test fallback JSON tool call format."""
        # First response is JSON tool call
        mock_client.chat.side_effect = [
            json.dumps({"tool": "read_file", "parameters": {"path": "test.py"}}),
            "File content here"
        ]
        
        with patch.object(orchestrator.tools, 'execute_tool') as mock_execute:
            mock_execute.return_value = ToolResult(
                name="read_file",
                result="print('hello')"
            )
            
            result = orchestrator.run("Read test.py")
            
            assert "File content here" in result
            mock_execute.assert_called_once()
    
    def test_max_iterations_protection(self, orchestrator, mock_client):
        """Test protection against infinite tool calling loops."""
        # Always return a tool call to trigger max iterations
        tool_response = Mock()
        tool_response.tool_calls = [
            Mock(
                id="call_123",
                function=Mock(
                    name="search_code",
                    arguments=json.dumps({"query": "loop"})
                )
            )
        ]
        mock_client.chat.return_value = tool_response
        
        with patch.object(orchestrator.tools, 'execute_tool') as mock_execute:
            mock_execute.return_value = ToolResult(
                name="search_code",
                result=[]
            )
            
            result = orchestrator.run("Test loop protection")
            
            assert "maximum iterations" in result.lower()
    
    def test_local_first_behavior(self, orchestrator, mock_client):
        """Test that system prompt enforces local-first behavior."""
        prompt = orchestrator.system_prompt
        
        assert "local-first" in prompt.lower()
        assert "search_code" in prompt
        assert "read_file" in prompt
        assert "search_papers" in prompt
        assert "only if local" in prompt.lower() or "insufficient" in prompt
    
    def test_logging_of_tool_calls(self, orchestrator, mock_client):
        """Test that tool calls are properly logged."""
        with patch('src.tongyi_orchestrator.logger') as mock_logger:
            tool_response = Mock()
            tool_response.tool_calls = [
                Mock(
                    id="call_123",
                    function=Mock(
                        name="run_sandbox",
                        arguments=json.dumps({"code": "print(1)"})
                    )
                )
            ]
            mock_client.chat.return_value = tool_response
            # Set up the second call to return final response
            second_response = Mock()
            second_response.tool_calls = None
            mock_client.chat.side_effect = [tool_response, second_response]
            
            with patch.object(orchestrator.tools, 'execute_tool') as mock_execute:
                mock_execute.return_value = ToolResult(
                    name="run_sandbox",
                    result={"stdout": "1\n", "returncode": 0}
                )
                
                orchestrator.run("Run code")
                
                # Verify logging calls - check that info was called
                assert mock_logger.info.called, "Logger.info should be called for tool execution"
                log_messages = [call.args[0] for call in mock_logger.info.call_args_list]
                # Look for any tool-related logging
                tool_logs = [msg for msg in log_messages if "tool" in msg.lower()]
                assert len(tool_logs) > 0, f"Should have tool-related logs. Found: {log_messages}"
    
    def test_error_handling_in_tool_execution(self, orchestrator, mock_client):
        """Test error handling when tool execution fails."""
        tool_response = Mock()
        tool_response.tool_calls = [
            Mock(
                id="call_123",
                function=Mock(
                    name="read_file",
                    arguments=json.dumps({"path": "nonexistent.py"})
                )
            )
        ]
        mock_client.chat.return_value = tool_response
        mock_client.chat.return_value = "Final response."
        
        with patch.object(orchestrator.tools, 'execute_tool') as mock_execute:
            mock_execute.return_value = ToolResult(
                name="read_file",
                result=None,
                error="File not found"
            )
            
            result = orchestrator.run("Read missing file")
            
            # Should handle error gracefully and continue
            assert result is not None
    
    def test_verification_gate_integration(self, orchestrator, mock_client):
        """Test that final answers pass through verification."""
        mock_client.chat.return_value = "Answer with citation [source: file.py]"
        
        with patch.object(orchestrator, '_verify_response') as mock_verify:
            mock_verify.return_value = "Verified answer with citation"
            
            result = orchestrator.run("Test verification")
            
            assert result == "Verified answer with citation"
            mock_verify.assert_called_once()
    
    def test_get_tool_usage_summary(self, orchestrator):
        """Test tool usage summary method."""
        summary = orchestrator.get_tool_usage_summary()
        registered_tools = orchestrator.tools.get_tools()
        expected_names = [tool.name for tool in registered_tools]
        
        assert "total_tools" in summary
        assert "tool_names" in summary
        assert "root_directory" in summary
        assert "model" in summary
        assert summary["total_tools"] == len(expected_names)
        assert set(summary["tool_names"]) == set(expected_names)
        assert "search_code" in summary["tool_names"]
        assert "alibaba/tongyi-deepresearch-30b-a3b" in summary["model"]
