"""
Test security fixes for Agent Lightning integration
"""
import unittest
import tempfile
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from optimized_tongyi_agent import OptimizedTongyiAgent
from optimized_claude_agent import OptimizedClaudeAgent


class TestSecurityFixes(unittest.TestCase):
    """Test security fixes for Agent Lightning integration"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.agent_tongyi = OptimizedTongyiAgent(
            root=self.temp_dir,
            enable_training=False
        )
        self.agent_claude = OptimizedClaudeAgent(
            root=self.temp_dir,
            enable_training=False
        )

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_export_filepath_validation(self):
        """Test that export validates filepaths properly"""
        # Test with invalid types
        with self.assertRaises(TypeError):
            self.agent_tongyi.export_training_data(123)

        with self.assertRaises(TypeError):
            self.agent_claude.export_training_data(None)

    def test_export_path_traversal_protection(self):
        """Test that export prevents path traversal attacks"""
        # Test relative path traversal
        dangerous_relative_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config"
        ]

        for dangerous_path in dangerous_relative_paths:
            with self.assertRaises((ValueError, TypeError)):
                self.agent_tongyi.export_training_data(dangerous_path)

        # Test absolute paths outside safe directory
        dangerous_absolute_paths = [
            "/etc/shadow",
            "C:\\Windows\\System32\\drivers\\etc\\hosts",
            "C:\\Windows\\System32\\config",
            "/etc/passwd",
            "C:\\Users\\Public\\Documents\\..\\..\\Windows\\System32"
        ]

        for dangerous_path in dangerous_absolute_paths:
            with self.assertRaises((ValueError, TypeError)):
                self.agent_tongyi.export_training_data(dangerous_path)

        # Test dangerous path patterns
        dangerous_pattern_paths = [
            "path_with_../../../etc/passwd",
            "C:\\Users\\temp\\..\\..\\Windows\\System32\\file",
            "some_path/../../../../../etc/shadow"
        ]

        for dangerous_path in dangerous_pattern_paths:
            with self.assertRaises((ValueError, TypeError)):
                self.agent_tongyi.export_training_data(dangerous_path)

    def test_export_sanitizes_data(self):
        """Test that export sanitizes sensitive data"""
        import json

        # Add some test interactions with sensitive data
        self.agent_tongyi.interaction_history.append({
            "timestamp": 1234567890,
            "query": "My password is secret123 and my API key is sk-1234567890",
            "response": "Here's your secret password and API key back",
            "response_time": 1.5,
            "tools_used": ["search"]
        })

        # Export to temporary file
        export_file = os.path.join(self.temp_dir, "test_export.json")
        self.agent_tongyi.export_training_data(export_file)

        # Verify export was created
        self.assertTrue(os.path.exists(export_file))

        # Load and verify sanitization
        with open(export_file, 'r') as f:
            data = json.load(f)

        # Check that sensitive data is not in export
        export_str = json.dumps(data)
        self.assertNotIn("secret123", export_str)
        self.assertNotIn("sk-1234567890", export_str)
        self.assertNotIn("My password", export_str)

        # Verify that metadata is preserved
        self.assertIn("interactions", data)
        self.assertIn("metrics", data)
        self.assertIn("export_timestamp", data)
        self.assertIn("version", data)

    def test_safe_filepath_resolution(self):
        """Test that relative paths are resolved safely"""
        # Test safe relative path
        safe_path = "training_data.json"
        export_file = os.path.join(self.temp_dir, safe_path)

        # Should not raise an exception
        self.agent_tongyi.export_training_data(safe_path)

        # Verify file was created in safe directory
        expected_path = os.path.join(
            self.agent_tongyi.training_data_path,
            "training_data.json"
        )
        self.assertTrue(os.path.exists(expected_path))

    def test_claude_agent_export_security(self):
        """Test Claude agent export security"""
        # Add test data with sensitive information
        self.agent_claude.interaction_history.append({
            "timestamp": 1234567890,
            "query": "Access database with admin:admin and password:secret",
            "response": "Database credentials: admin:admin, password:secret",
            "claude_success": True,
            "response_time": 2.1,
            "tools_used": ["Read", "Write"]
        })

        export_file = os.path.join(self.temp_dir, "claude_export.json")
        self.agent_claude.export_training_data(export_file)

        # Verify export was created and sanitized
        self.assertTrue(os.path.exists(export_file))

        import json
        with open(export_file, 'r') as f:
            data = json.load(f)

        export_str = json.dumps(data)
        self.assertNotIn("admin:admin", export_str)
        self.assertNotIn("password:secret", export_str)
        self.assertEqual(data["agent_type"], "claude_sdk")

    def test_export_version_metadata(self):
        """Test that exports include version metadata"""
        export_file = os.path.join(self.temp_dir, "version_test.json")
        self.agent_tongyi.export_training_data(export_file)

        import json
        with open(export_file, 'r') as f:
            data = json.load(f)

        # Check version metadata
        self.assertIn("version", data)
        self.assertIn("export_timestamp", data)
        self.assertEqual(data["version"], "1.0")
        self.assertIsInstance(data["export_timestamp"], (int, float))


class TestErrorHandling(unittest.TestCase):
    """Test improved error handling"""

    def test_agent_lightning_unavailable_handling(self):
        """Test graceful handling when Agent Lightning is unavailable"""
        # This should work without raising exceptions
        try:
            agent = OptimizedTongyiAgent(enable_training=True)
            # Should gracefully fall back to standard orchestrator
            self.assertFalse(agent.enable_training)
            self.assertIsNotNone(agent.base_orchestrator)
        except Exception as e:
            self.fail(f"Agent Lightning fallback failed: {e}")

    def test_export_with_safe_defaults(self):
        """Test export works with safe default configurations"""
        temp_dir = tempfile.mkdtemp()
        try:
            agent = OptimizedTongyiAgent(root=temp_dir, enable_training=False)

            # Should work without any setup
            export_file = os.path.join(temp_dir, "safe_export.json")
            agent.export_training_data(export_file)

            # Verify file was created
            self.assertTrue(os.path.exists(export_file))

            # Verify it's valid JSON
            import json
            with open(export_file, 'r') as f:
                data = json.load(f)
            self.assertIsInstance(data, dict)

        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()