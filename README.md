# LangChain Chaos Middleware ( Chaos Monkey )

A middleware for LangChain agents that intentionally injects failures (exceptions) into tool and model calls to test agent resilience.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Basic Example](#basic-example)
- [Configuration](#configuration)
- [Default Exception Profiles](#default-exception-profiles)
- [Custom Exception Profiles](#custom-exception-profiles)
- [Understanding Failure Rates](#understanding-failure-rates)
- [Important Note for Production](#important-note-for-production)
- [For Developers](#for-developers)
  - [Setting Up the Development Environment](#setting-up-the-development-environment)
  - [Running Tests](#running-tests)
  - [Test Coverage](#test-coverage)
  - [Contributing](#contributing)

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

## Understanding Failure Rates

The `failure_rate` applies to **each individual tool call**, not to the entire agent task. If your agent needs to call multiple tools to complete a task, the overall success rate will be lower than you might expect.

**Example**: With a 20% failure rate per tool:
- **Single tool call**: 80% chance of success
- **Two tool calls**: 80% × 80% = **64% chance of success**
- **Three tool calls**: 80% × 80% × 80% = **51% chance of success**

This means that even with a "low" 20% failure rate, an agent that needs to call 3 tools has nearly a 50% chance of experiencing at least one failure during the task.

**Tip**: Start with a low failure rate (e.g., 10-20%) and observe how it affects your agent's overall success rate before increasing it.

## Important Note for Production

To prevent accidental chaos in production, the middleware checks for an environment variable (default: `ENABLE_CHAOS`). If this variable is not set to `"true"`, the middleware acts as a pass-through and does nothing.

## For Developers

### Setting Up the Development Environment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/iroy2000/langchain-chaos-middleware.git
   cd langchain-chaos-middleware
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   # Install the package dependencies
   .venv/bin/pip install langchain langgraph
   
   # Install test dependencies
   .venv/bin/pip install python-dotenv langchain-openai
   ```

### Running Tests

The project includes unit tests to verify the middleware functionality.

**Run all tests**:
```bash
.venv/bin/python -m unittest discover tests
```

**Run only unit tests**:
```bash
.venv/bin/python -m unittest tests.test_unit
```

**Run integration tests** (requires OpenAI API key):
```bash
# Create a .env file with your OpenAI API key
echo "OPENAI_API_KEY=your-key-here" > .env

# Run the integration test
.venv/bin/python tests/test_integration.py
```

### Test Coverage

The test suite includes:
- **Safety mechanism tests**: Verifies chaos is disabled without the safety key
- **Failure injection tests**: Confirms failures are injected at the configured rate
- **Tool filtering tests**: Validates include/exclude tool lists work correctly
- **Model call tests**: Ensures chaos applies to model calls as well

### Contributing

Contributions are welcome! Please ensure all tests pass before submitting a pull request:

```bash
.venv/bin/python -m unittest discover tests
```
