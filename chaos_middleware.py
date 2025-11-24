import os
import random
from typing import List, Optional, Any, Type, Callable
try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict

# Import LangChain v1 middleware types
try:
    from langchain.agents.middleware import (
        AgentMiddleware,
        ModelRequest,
        ModelResponse,
    )
    # ToolCallRequest might be in a different location or named differently
    # We'll handle this gracefully
    try:
        from langchain.agents.middleware import ToolCallRequest
    except ImportError:
        # If ToolCallRequest doesn't exist, we'll use the request object directly
        ToolCallRequest = Any
except ImportError:
    # Fallback for development/testing without LangChain installed
    class AgentMiddleware:
        pass
    ModelRequest = Any
    ModelResponse = Any
    ToolCallRequest = Any

class ChaosConfig(TypedDict):
    """Configuration for the Chaos Monkey Middleware.
    
    Attributes:
        failure_rate: Probability of failure (0.0 to 1.0). Default is 0.1.
        exception_types: List of exception classes to choose from when failing.
        include_tools: List of tool names to target. If None, all tools are targeted.
        exclude_tools: List of tool names to exclude from chaos.
        seed: Random seed for reproducibility.
        safety_key: Environment variable name that must be "true" to enable chaos. Default: "ENABLE_CHAOS".
    """
    failure_rate: float
    exception_types: List[Type[Exception]]
    include_tools: Optional[List[str]]
    exclude_tools: List[str]
    seed: Optional[int]
    safety_key: str

class ChaosMiddleware(AgentMiddleware):
    """Middleware that injects random failures into tool and model calls.
    
    This middleware is designed to test the resilience of an agent by simulating
    network errors, service outages, or other unexpected exceptions.
    
    !!!Important!!!
        The middleware will ONLY be active if the environment variable specified
        by `safety_key` (default: "ENABLE_CHAOS") is set to "true".
    """
    def __init__(self, config: ChaosConfig):
        self.config = config
        self.failure_rate = config.get("failure_rate", 0.1)
        self.exception_types = config.get("exception_types", [])
        self.include_tools = config.get("include_tools", None)
        self.exclude_tools = config.get("exclude_tools", [])
        self.seed = config.get("seed", None)
        self.safety_key = config.get("safety_key", "ENABLE_CHAOS")
        
        if self.seed is not None:
            random.seed(self.seed)

    def wrap_tool_call(
        self, 
        request: ToolCallRequest, 
        handler: Callable[[ToolCallRequest], Any]
    ) -> Any:
        """Intercepts tool calls and potentially raises an exception.
        
        Args:
            request: The ToolCallRequest object containing tool information.
            handler: The next handler in the chain.
            
        Returns:
            The result of the handler if no exception is raised.
            
        Raises:
            Exception: A random exception from `exception_types` if chaos is triggered.
        """
        # Safety Check
        if os.environ.get(self.safety_key, "").lower() != "true":
            return handler(request)

        # Extract tool name from request
        # The request object should have a 'tool' attribute with the BaseTool instance
        tool_name = getattr(request, 'tool', None)
        if tool_name is not None:
            tool_name = getattr(tool_name, 'name', str(tool_name))
        
        # Target Check
        if tool_name and tool_name in self.exclude_tools:
            return handler(request)
        
        if self.include_tools is not None and (not tool_name or tool_name not in self.include_tools):
            return handler(request)

        # Roll Dice
        if random.random() <= self.failure_rate:
            if self.exception_types:
                # Instantiate the exception class
                raise random.choice(self.exception_types)()
            else:
                raise Exception("Chaos Monkey triggered!")

        return handler(request)

    def wrap_model_call(
        self, 
        request: ModelRequest, 
        handler: Callable[[ModelRequest], ModelResponse]
    ) -> ModelResponse:
        """Intercepts model calls and potentially raises an exception.
        
        Args:
            request: The ModelRequest object.
            handler: The next handler in the chain.
            
        Returns:
            The ModelResponse if no exception is raised.
            
        Raises:
            Exception: A random exception from `exception_types` if chaos is triggered.
        """
        # Safety Check
        if os.environ.get(self.safety_key, "").lower() != "true":
            return handler(request)

        # Roll Dice
        if random.random() <= self.failure_rate:
            if self.exception_types:
                # Instantiate the exception class
                raise random.choice(self.exception_types)()
            else:
                raise Exception("Chaos Monkey triggered on model call!")

        return handler(request)

# Custom Exceptions for Chaos
class RateLimitError(Exception):
    """Simulated Rate Limit Error"""
    pass

class ServiceUnavailableError(Exception):
    """Simulated Service Unavailable Error"""
    pass

# Default Exception Profiles
NETWORK_ERRORS = [TimeoutError, ConnectionError]
LLM_ERRORS = [RateLimitError, ServiceUnavailableError]
CRITICAL_ERRORS = [ValueError, KeyError]
