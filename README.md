# LangChain Chaos Middleware

A middleware for LangChain agents that intentionally injects failures (exceptions) into tool and model calls to test agent resilience.

## Features

- **Failure Injection**: Randomly raises exceptions based on a configurable failure rate.
- **Targeted Chaos**: Include or exclude specific tools from chaos.
- **Safety Mechanism**: Requires an environment variable (`ENABLE_CHAOS=true`) to be active, preventing accidental production issues.
- **Customizable Exceptions**: Choose which exceptions to raise (e.g., network errors, rate limits).

## Installation

```bash
pip install langchain-chaos-middleware
```

## Usage

### Basic Example

```python
import os
from langchain.agents import create_agent
from chaos_middleware import ChaosMiddleware, NETWORK_ERRORS

# 1. Enable Chaos (Safety Check)
os.environ["ENABLE_CHAOS"] = "true"

# 2. Configure Middleware
chaos_config = {
    "failure_rate": 0.2,  # 20% chance of failure
    "exception_types": NETWORK_ERRORS,
    "exclude_tools": ["save_memory"], # Don't break critical tools
}
chaos = ChaosMiddleware(chaos_config)

# 3. Inject into Agent
agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[chaos]
)

# 4. Run Agent
# The agent will now experience random network errors!
```

## Configuration

The `ChaosMiddleware` is initialized with a `ChaosConfig` dictionary:

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `failure_rate` | `float` | `0.1` | Probability of failure (0.0 to 1.0). |
| `exception_types` | `List[Exception]` | `[]` | List of exceptions to randomly choose from. |
| `include_tools` | `List[str]` | `None` | If set, only these tools will be targeted. |
| `exclude_tools` | `List[str]` | `[]` | These tools will NEVER fail. |
| `seed` | `int` | `None` | Random seed for reproducible chaos. |
| `safety_key` | `str` | `"ENABLE_CHAOS"` | Env var name required to enable the middleware. |

## Default Exception Profiles

The library provides pre-built lists of exceptions for common scenarios:

- `NETWORK_ERRORS`: `[TimeoutError, ConnectionError]`
- `LLM_ERRORS`: `[RateLimitError, ServiceUnavailableError]`
- `CRITICAL_ERRORS`: `[ValueError, KeyError]`

## Custom Exception Profiles

You can define your own lists of exceptions to simulate specific scenarios (e.g., database failures, custom API errors). Just create a list of exception classes and pass it to the `exception_types` configuration:

```python
class DatabaseError(Exception):
    pass

MY_DB_ERRORS = [DatabaseError]

config = {
    "exception_types": MY_DB_ERRORS,
    # ...
}
```

## Safety

To prevent accidental chaos in production, the middleware checks for an environment variable (default: `ENABLE_CHAOS`). If this variable is not set to `"true"`, the middleware acts as a pass-through and does nothing.
