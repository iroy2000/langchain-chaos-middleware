import os
import unittest
from unittest.mock import Mock
from chaos_middleware import ChaosMiddleware, NETWORK_ERRORS


class MockTool:
    """Mock tool object for testing."""
    def __init__(self, name):
        self.name = name


class MockToolCallRequest:
    """Mock ToolCallRequest for testing."""
    def __init__(self, tool_name):
        self.tool = MockTool(tool_name)


class MockModelRequest:
    """Mock ModelRequest for testing."""
    def __init__(self):
        self.messages = []


class TestChaosMiddleware(unittest.TestCase):
    def setUp(self):
        self.handler = lambda x: "success"
        self.tool_request = MockToolCallRequest("test_tool")
        self.model_request = MockModelRequest()

    def test_safety_check(self):
        # Ensure safety key is NOT set
        if "ENABLE_CHAOS" in os.environ:
            del os.environ["ENABLE_CHAOS"]
        
        config = {
            "failure_rate": 1.0,
            "exception_types": [ValueError],
            "include_tools": None,
            "exclude_tools": [],
            "seed": 42,
            "safety_key": "ENABLE_CHAOS"
        }
        middleware = ChaosMiddleware(config)
        
        # Should pass because env var is missing
        result = middleware.wrap_tool_call(self.tool_request, self.handler)
        self.assertEqual(result, "success")

    def test_failure_injection(self):
        os.environ["ENABLE_CHAOS"] = "true"
        config = {
            "failure_rate": 1.0,  # Always fail
            "exception_types": [ValueError],
            "include_tools": None,
            "exclude_tools": [],
            "seed": 42,
            "safety_key": "ENABLE_CHAOS"
        }
        middleware = ChaosMiddleware(config)
        
        with self.assertRaises(ValueError):
            middleware.wrap_tool_call(self.tool_request, self.handler)

    def test_exclude_tools(self):
        os.environ["ENABLE_CHAOS"] = "true"
        config = {
            "failure_rate": 1.0,
            "exception_types": [ValueError],
            "include_tools": None,
            "exclude_tools": ["safe_tool"],
            "seed": 42,
            "safety_key": "ENABLE_CHAOS"
        }
        middleware = ChaosMiddleware(config)
        
        # Safe tool should pass
        safe_request = MockToolCallRequest("safe_tool")
        result = middleware.wrap_tool_call(safe_request, self.handler)
        self.assertEqual(result, "success")
        
        # Other tool should fail
        with self.assertRaises(ValueError):
            middleware.wrap_tool_call(self.tool_request, self.handler)

    def test_include_tools(self):
        os.environ["ENABLE_CHAOS"] = "true"
        config = {
            "failure_rate": 1.0,
            "exception_types": [ValueError],
            "include_tools": ["risky_tool"],
            "exclude_tools": [],
            "seed": 42,
            "safety_key": "ENABLE_CHAOS"
        }
        middleware = ChaosMiddleware(config)
        
        # Unlisted tool should pass
        result = middleware.wrap_tool_call(self.tool_request, self.handler)
        self.assertEqual(result, "success")
        
        # Included tool should fail
        risky_request = MockToolCallRequest("risky_tool")
        with self.assertRaises(ValueError):
            middleware.wrap_tool_call(risky_request, self.handler)

    def test_model_call(self):
        os.environ["ENABLE_CHAOS"] = "true"
        config = {
            "failure_rate": 1.0,
            "exception_types": [ValueError],
            "include_tools": ["some_tool"],  # Should be ignored for model calls
            "exclude_tools": [],
            "seed": 42,
            "safety_key": "ENABLE_CHAOS"
        }
        middleware = ChaosMiddleware(config)
        
        with self.assertRaises(ValueError):
            middleware.wrap_model_call(self.model_request, self.handler)


if __name__ == "__main__":
    unittest.main()
