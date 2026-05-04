# tflow - Testing Workflow Orchestration

> AI-Powered Testing Workflow Automation with MCP Support

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Status-Alpha-orange.svg" alt="Status">
</p>

---

## Overview

tflow is a **workflow orchestration CLI** designed for **automated software testing**. It leverages AI agents (Claude, Gemini, Qwen, Codex, OpenCode) to plan, execute, and verify test workflows.

Built on insights from [Maestro-Flow](https://github.com/your-org/maestro-flow), tflow provides a simple state-machine based workflow engine with extensibility through MCP (Model Context Protocol).

## Features

- **Multi-Agent Support** - Seamlessly call Claude, Gemini, Qwen, Codex, or OpenCode
- **Workflow Automation** - Linear state machine: Parsing → Validating → Planning → Executing → Verifying → Completing
- **Wave Execution** - Parallel task execution within waves, waves executed sequentially
- **Session Management** - Pause, resume, and track workflow sessions
- **Event-Driven** - Real-time progress via WebSocket/SSE
- **MCP Integration** - Extend with MCP tools and servers
- **TDD Support** - Built-in testing patterns with 85+ unit tests

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/testing-flow.git
cd testing-flow

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .\.venv\Scripts\activate  # Windows

# Install dependencies
pip install -e .
```

**Requires Python 3.11+**

## Quick Start

```bash
# Run a workflow
tflow run --goal "Test login functionality" --scope tests/login/

# Delegate a task to Claude
tflow delegate "Analyze code quality" --to claude

# Check workflow status
tflow status

# List sessions
tflow session list

# Show session details
tflow session show wf-20230504-abc123
```

---

## CLI Commands

### Global Options

| Option | Description |
|--------|-------------|
| `--version` | Show version |
| `--help` | Show help message |

---

### `tflow delegate` - Delegate Task to Agent

Delegate a task to an AI agent for execution.

```bash
tflow delegate "Your prompt here" [OPTIONS]
```

**Arguments:**
| Argument | Description |
|----------|-------------|
| `PROMPT` | The prompt/task to execute (required) |

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--to` | Agent type | `claude-code` |
| `--mode` | Execution mode: `analysis` or `write` | `analysis` |
| `--model` | Model to use (optional) | - |

**Agent Types:**
- `claude-code` - Claude Code (default)
- `gemini` - Google Gemini
- `qwen` - Alibaba Qwen
- `codex` - OpenAI Codex
- `opencode` - OpenCode

**Examples:**

```bash
# Basic delegation to Claude
tflow delegate "Write a unit test for user authentication"

# Delegate to Gemini for analysis
tflow delegate "Analyze this code for security issues" --to gemini

# Delegate with specific model
tflow delegate "Review this PR" --to claude --model sonnet

# Write mode - for code generation tasks
tflow delegate "Generate a CLI tool for file processing" --mode write

# Full example with all options
tflow delegate "Implement login with OAuth2" --to claude --mode write --model opus
```

**Output Example:**
```
Delegating to claude: Write a unit test for user authentication...
Exit code: 0
Success: True
Output:
def test_login_success():
    """Test successful login with valid credentials."""
    ...
```

---

### `tflow run` - Execute Workflow

Execute a complete workflow with goal and scope.

```bash
tflow run --goal "Your goal" [OPTIONS]
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--goal TEXT` | Workflow goal (required) | - |
| `--scope TEXT` | Scope paths (optional) | `all` |
| `--plan TEXT` | Execution plan file (optional) | - |

**Examples:**

```bash
# Basic workflow
tflow run --goal "Run all unit tests"

# With specific scope
tflow run --goal "Test authentication" --scope tests/auth/

# Multiple scopes
tflow run --goal "Full regression test" --scope "tests/unit/,tests/integration/"

# With execution plan
tflow run --goal "Execute test plan" --plan .workflow/plan.json
```

**Output Example:**
```
Running workflow: Run all unit tests
Scope: all
Exit code: 0
Success: True
Output:
...
```

---

### `tflow status` - Check Status

Check workflow or session status.

```bash
tflow status [SESSION]
```

**Arguments:**
| Argument | Description |
|----------|-------------|
| `SESSION` | Session ID (optional) |

**Examples:**

```bash
# Check overall system status
tflow status

# Check specific session
tflow status wf-20230504-abc123
```

**Output Example:**
```
tflow status: system operational
Active jobs: 0

# Or with session
Status for session: wf-20230504-abc123
```

---

### `tflow session list` - List Sessions

List all workflow sessions.

```bash
tflow session list
```

**Examples:**

```bash
tflow session list
```

**Output Example:**
```
Sessions:
  - wf-20230504-abc123: queued
  - wf-20230504-def456: completed
```

---

### `tflow session show` - Show Session Details

Show details of a specific session.

```bash
tflow session show SESSION_ID
```

**Arguments:**
| Argument | Description |
|----------|-------------|
| `SESSION_ID` | Session ID to show (required) |

**Examples:**

```bash
tflow session show wf-20230504-abc123
```

**Output Example:**
```
Session: wf-20230504-abc123
  Status: running
  Created: 2024-05-04T12:00:00

# Or if not found
Session: wf-20230504-xyz999
  Not found
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TFLOW_ENV` | Environment mode | `development` |
| `DEBUG` | Enable debug mode | `false` |

**Example:**
```bash
export TFLOW_ENV=production
export DEBUG=false
tflow delegate "Run tests" --to claude
```

---

## Architecture

```
CLI / API
    ↓
AgentExecutor ─── AgentRegistry (5 agents)
    ↓
┌───────────────┬───────────────┬──────────────┐
│WorkflowEngine │  JobManager  │  SpecLoader  │
│  (state)     │  (events)    │  (specs)    │
└───────────────┴───────────────┴──────────────┘
    ↓
ExecutionStore (JSONL + SQLite)
```

### Core Modules

| Module | Purpose |
|--------|---------|
| `AgentExecutor` | Unified agent execution coordinator |
| `JobManager` | Job state management + event broker |
| `WorkflowEngine` | Simple state machine engine |
| `WorkflowState` | State definitions + persistence |
| `AgentRegistry` | Multi-agent registration |
| `DirectBackend` | Direct subprocess execution |
| `TerminalBackend` | tmux/wezterm session execution |
| `SQLiteStore` | Structured data persistence |
| `JsonBroker` | JSONL event persistence |
| `RealtimeBridge` | WebSocket/SSE event bridge |

---

## Development

### Project Structure

```
src/tflow/
├── __main__.py          # CLI entry point
├── core/                # AgentExecutor, JobManager
├── agents/             # AgentRegistry, backends
│   └── backends/       # DirectBackend, TerminalBackend
├── workflow/            # WorkflowEngine, state
├── broker/              # Events, persistence
├── storage/             # SQLite, JSONL stores
├── delegate/            # Task delegation
├── spec/                # Spec loader
├── config/              # Settings
└── realtime/            # WebSocket bridge
```

### Running Tests

```bash
# Run all tests
PYTHONPATH=src python -m pytest tests/ -v

# With coverage
PYTHONPATH=src python -m pytest tests/ --cov=src/tflow --cov-report=html

# Run specific module
PYTHONPATH=src python -m pytest tests/test_workflow_engine.py -v

# Run with verbose output
PYTHONPATH=src python -m pytest tests/ -vv
```

### Test Categories

| Test File | Coverage |
|-----------|----------|
| `test_agent_registry.py` | Agent registry and agent types |
| `test_config.py` | Settings and configuration |
| `test_delegate_broker.py` | Task delegation |
| `test_realtime.py` | Real-time event bridge |
| `test_spec_loader.py` | Specification loading |
| `test_storage.py` | Storage backends |
| `test_workflow_engine.py` | Workflow engine |

---

## Design Principles

1. **Simplicity First** - Linear state machine, not complex graph walker
2. **Event-Driven** - Pub/sub architecture for decoupling
3. **Async-First** - asyncio for I/O-bound operations
4. **TDD** - 85+ unit tests with >85% coverage target

---

## License

MIT License - see [LICENSE](LICENSE)

## References

- [Maestro-Flow](https://github.com/your-org/maestro-flow) - Architecture inspiration
- [Claude Code](https://docs.anthropic.com/claude-code) - Primary agent
- [MCP Protocol](https://modelcontextprotocol.io) - Extensibility layer
