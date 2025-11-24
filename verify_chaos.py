import os
import unittest
from chaos_middleware import ChaosMiddleware, NETWORK_ERRORS

class TestChaosMiddleware(unittest.TestCase):
    def setUp(self):
        self.handler = lambda x: "success"
        self.tool_call = {"name": "test_tool", "args": {}}
        self.model_call = {"messages": []}

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
        result = middleware.wrap_tool_call(self.tool_call, self.handler)
        self.assertEqual(result, "success")

    def test_failure_injection(self):
        os.environ["ENABLE_CHAOS"] = "true"
        config = {
            "failure_rate": 1.0, # Always fail
            "exception_types": [ValueError],
            "include_tools": None,
            "exclude_tools": [],
            "seed": 42,
            "safety_key": "ENABLE_CHAOS"
        }
        middleware = ChaosMiddleware(config)
        
        with self.assertRaises(ValueError):
            middleware.wrap_tool_call(self.tool_call, self.handler)

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
        safe_call = {"name": "safe_tool", "args": {}}
        result = middleware.wrap_tool_call(safe_call, self.handler)
        self.assertEqual(result, "success")
        
        # Other tool should fail
        with self.assertRaises(ValueError):
            middleware.wrap_tool_call(self.tool_call, self.handler)

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
        result = middleware.wrap_tool_call(self.tool_call, self.handler)
        self.assertEqual(result, "success")
        
        # Included tool should fail
        risky_call = {"name": "risky_tool", "args": {}}
        with self.assertRaises(ValueError):
            middleware.wrap_tool_call(risky_call, self.handler)

    def test_model_call(self):
        os.environ["ENABLE_CHAOS"] = "true"
        config = {
            "failure_rate": 1.0,
            "exception_types": [ValueError],
            "include_tools": ["some_tool"], # Should be ignored for model calls
            "exclude_tools": [],
            "seed": 42,
            "safety_key": "ENABLE_CHAOS"
        }
        middleware = ChaosMiddleware(config)
        
        with self.assertRaises(ValueError):
            middleware.wrap_model_call(self.model_call, self.handler)

if __name__ == "__main__":
    unittest.main()
