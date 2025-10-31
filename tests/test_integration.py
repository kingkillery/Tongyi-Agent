"""
Integration tests for Tongyi Agent.
"""
import pytest
from unittest.mock import Mock, patch

from src.tongyi_orchestrator import TongyiOrchestrator


class TestIntegration:
    """Integration tests for the complete Tongyi Agent system."""
    
    def test_end_to_end_simple_question(self):
        """Test end-to-end flow with a simple question."""
        mock_client = Mock()
        mock_client.chat.return_value = "The answer is 42."
        
        with patch('src.tongyi_orchestrator.load_openrouter_client', return_value=mock_client):
            orch = TongyiOrchestrator(root="/test")
            result = orch.run("What is the meaning of life?")
            
            assert "42" in result
            assert mock_client.chat.called
    
    def test_tool_call_integration(self):
        """Test tool calling in integration."""
        mock_client = Mock()
        
        # Create properly structured mock for tool call
        mock_function = Mock()
        mock_function.name = "search_code"
        mock_function.arguments = '{"query": "test", "max_results": 5}'
        
        mock_tool_call = Mock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function = mock_function
        
        # First response: tool call
        tool_response = Mock()
        tool_response.tool_calls = [mock_tool_call]
        
        # Second response: final answer (no tool calls)
        final_response = Mock()
        final_response.tool_calls = None
        
        mock_client.chat.side_effect = [tool_response, final_response]
        
        with patch('src.tongyi_orchestrator.load_openrouter_client', return_value=mock_client):
            orch = TongyiOrchestrator(root="/test")
            
            with patch.object(orch.tools, 'execute_tool') as mock_execute:
                from src.tool_registry import ToolResult
                mock_execute.return_value = ToolResult(
                    name="search_code",
                    result=["file1.py", "file2.py", "file3.py"]
                )
                
                result = orch.run("Find test functions")
                
                # Verify tool was called
                assert mock_execute.called
    
    def test_budget_enforcement_integration(self):
        """Test that budgets are enforced in integration."""
        mock_client = Mock()
        
        # Mock budget exceeded
        with patch('src.tongyi_orchestrator.load_openrouter_client', return_value=mock_client):
            orch = TongyiOrchestrator(root="/test")
            
            # Deplete budget for search_papers
            for _ in range(5):  # Exceeds the budget of 3
                orch.policy.allow("search_papers")
            
            tool_response = Mock()
            tool_response.tool_calls = [
                Mock(
                    id="call_123",
                    function=Mock(
                        name="search_papers",
                        arguments='{"query": "test"}'
                    )
                )
            ]
            mock_client.chat.return_value = tool_response
            
            result = orch.run("Search for papers")
            
            # Should handle budget exceeded gracefully
            assert result is not None
    
    def test_local_first_behavior_in_system_prompt(self):
        """Test that system prompt contains local-first instructions."""
        mock_client = Mock()
        
        with patch('src.tongyi_orchestrator.load_openrouter_client', return_value=mock_client):
            orch = TongyiOrchestrator(root="/test")
            
            prompt = orch.system_prompt
            
            # Check for local-first behavior
            assert "local" in prompt.lower()
            assert "first" in prompt.lower()
            assert "search_code" in prompt
            assert "read_file" in prompt
            assert "search_papers" in prompt
    
    def test_error_handling_integration(self):
        """Test error handling in integration."""
        mock_client = Mock()
        mock_client.chat.side_effect = Exception("API Error")
        
        with patch('src.tongyi_orchestrator.load_openrouter_client', return_value=mock_client):
            orch = TongyiOrchestrator(root="/test")
            
            # Should catch the exception and handle it gracefully
            with pytest.raises(Exception):  # The exception should propagate
                orch.run("Test error")
    
    def test_logging_integration(self):
        """Test that logging works in integration."""
        mock_client = Mock()
        mock_client.chat.return_value = "Simple answer"
        
        with patch('src.tongyi_orchestrator.load_openrouter_client', return_value=mock_client):
            with patch('src.tongyi_orchestrator.logger') as mock_logger:
                orch = TongyiOrchestrator(root="/test")
                orch.run("Test logging")
                
                # Should log the start and completion
                assert mock_logger.info.called
    
    def test_verification_integration(self):
        """Test that verification is applied to final answers."""
        mock_client = Mock()
        mock_client.chat.return_value = "Answer with sources"
        
        with patch('src.tongyi_orchestrator.load_openrouter_client', return_value=mock_client):
            orch = TongyiOrchestrator(root="/test")
            
            with patch.object(orch, '_verify_response') as mock_verify:
                mock_verify.return_value = "Verified answer"
                
                result = orch.run("Test verification")
                
                assert result == "Verified answer"
                mock_verify.assert_called_once()
