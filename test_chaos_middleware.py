"""
LangChain Chaos Middleware Test

You will need a .env file with the following variables:

OPENAI_API_KEY

This script demonstrates using the langchain-chaos-middleware package
to inject failures and test agent resilience.
"""
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool

# Import chaos middleware
try:
    from chaos_middleware import ChaosMiddleware, ChaosConfig
    CHAOS_AVAILABLE = True
except ImportError:
    print("langchain-chaos-middleware not installed")
    CHAOS_AVAILABLE = False

# Load environment variables
load_dotenv()


# Define tools for testing
@tool
def fetch_data(source: str) -> str:
    """Fetch data from a source (mock)."""
    return f"Data fetched from {source}"


@tool
def process_data(data: str) -> str:
    """Process data (mock)."""
    return f"Processed: {data}"


def test_without_chaos():
    """Test agent without chaos middleware."""
    print("\n" + "=" * 60)
    print("Test 1: Agent WITHOUT Chaos Middleware")
    print("=" * 60)
    
    agent = create_agent(
        model="gpt-4o-mini",
        tools=[fetch_data, process_data],
    )
    
    print("\nAgent created (no chaos)")
    
    test_query = "Fetch data from API and process it"
    print(f"\nTest Query: {test_query}")
    
    try:
        response = agent.invoke({"messages": [{"role": "user", "content": test_query}]})
        print(f"\nSuccess! Response received")
    except Exception as e:
        print(f"\nError: {e}")


def test_with_chaos():
    """Test agent with chaos middleware."""
    if not CHAOS_AVAILABLE:
        print("\nSkipping chaos test - middleware not installed")
        return
    
    print("\n" + "=" * 60)
    print("Test 2: Agent WITH Chaos Middleware")
    print("=" * 60)
    
    # Configure chaos to inject failures
    # ChaosConfig expects: failure_rate, exception_types, include_tools, exclude_tools, seed, safety_key
    chaos_config: ChaosConfig = {
        "failure_rate": 0.1,  # 10% chance of tool failure (lower rate = higher success)
        "exception_types": [],  # Use default exceptions
        "include_tools": None,  # Target all tools
        "exclude_tools": [],  # Don't exclude any tools
        "seed": None,  # Random behavior
        "safety_key": "ENABLE_CHAOS"  # Environment variable to enable chaos
    }
    
    # Enable chaos via environment variable
    import os
    os.environ["ENABLE_CHAOS"] = "true"
    
    agent = create_agent(
        model="gpt-4o-mini",
        tools=[fetch_data, process_data],
        middleware=[ChaosMiddleware(config=chaos_config)]
    )
    
    print("\nAgent created with chaos middleware:")
    print(f"  - Tool failure rate: {chaos_config['failure_rate'] * 100}%")
    print(f"  - Exception types: {'default' if not chaos_config['exception_types'] else len(chaos_config['exception_types'])}")
    print(f"  - Targeting: {'all tools' if chaos_config['include_tools'] is None else chaos_config['include_tools']}")
    
    # Run multiple tests to see chaos in action
    test_query = "Fetch data from API and process it"
    print(f"\nRunning 5 iterations with chaos enabled...")
    
    successes = 0
    failures = 0
    
    for i in range(5):
        print(f"\n  Iteration {i+1}:")
        try:
            response = agent.invoke({"messages": [{"role": "user", "content": test_query}]})
            print(f"    Success")
            successes += 1
        except Exception as e:
            print(f"    Failed: {type(e).__name__}")
            failures += 1
    
    print(f"\nResults:")
    print(f"  Successes: {successes}/5")
    print(f"  Failures: {failures}/5")


def main():
    print("=" * 60)
    print("LangChain Chaos Middleware Test")
    print("=" * 60)
    
    test_without_chaos()
    test_with_chaos()
    
    print("\n" + "=" * 60)
    print("Tests Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
