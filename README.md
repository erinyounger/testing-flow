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
- **TDD Support** - Built-in testing patterns with 80+ unit tests

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

## Quick Start

```bash
# Run a workflow
tflow run --goal "Test login functionality" --scope tests/login/

# Delegate a task to Claude
tflow delegate "Analyze code quality" --to claude --mode analysis

# Check workflow status
tflow status

# List sessions
tflow session list

# Show session details
tflow session show wf-20230504-abc123
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `tflow run [workflow]` | Execute a workflow |
| `tflow delegate [prompt]` | Delegate to an agent |
| `tflow status [session]` | View status |
| `tflow stop [session]` | Stop execution |
| `tflow session list` | List sessions |
| `tflow session show <id>` | Show session details |

### Options

```bash
# Workflow options
--config, -c     # Config file path
--type, -t        # standard | full
--goal, -g        # Goal description
--scope, -s       # Scope paths

# Delegate options
--to, -t          # claude | gemini | qwen | codex | opencode
--mode, -m        # analysis | write
--backend, -b      # direct | terminal
--async           # Run asynchronously
```

## Development

### Project Structure

```
src/tflow/
├── core/              # AgentExecutor, JobManager
├── agents/            # AgentRegistry, backends
├── workflow/          # WorkflowEngine, state
├── broker/            # Events, persistence
├── storage/           # SQLite, JSONL stores
├── delegate/          # Task delegation
├── spec/              # Spec loader
└── realtime/          # WebSocket bridge
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src/tflow --cov-report=html

# Run specific module
pytest tests/test_workflow_engine.py -v
```

## Design Principles

1. **Simplicity First** - Linear state machine, not complex graph walker
2. **Event-Driven** - Pub/sub architecture for decoupling
3. **Async-First** - asyncio for I/O-bound operations
4. **TDD** - 80+ unit tests with >85% coverage target

## License

MIT License - see [LICENSE](LICENSE)

## References

- [Maestro-Flow](https://github.com/your-org/maestro-flow) - Architecture inspiration
- [Claude Code](https://docs.anthropic.com/claude-code) - Primary agent
- [MCP Protocol](https://modelcontextprotocol.io) - Extensibility layer
