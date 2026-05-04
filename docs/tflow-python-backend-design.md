# tflow Python 后端核心模块设计方案

> 基于 Maestro-Flow 架构分析 | 2026-05-04

---

## 一、项目背景

### Maestro-Flow 核心借鉴

| 组件 | 职责 | tflow 对应设计 |
|------|------|---------------|
| `CliAgentRunner` | 统一执行器：Prompt组装、进程管理、事件订阅 | `AgentExecutor` |
| `DelegateBroker` | Job状态管理 + 事件pub/sub | `JobManager` |
| `CliHistoryStore` | JSONL历史存储 + Session恢复 | `ExecutionStore` |
| `TerminalAdapter` | tmux/wezterm后端集成 | `TerminalBackend` |
| `DashboardBridge` | WebSocket实时事件转发 | `RealtimeBridge` |
| `GraphWalker` | 图遍历状态机 | `GraphWalker` |

### tflow MVP 需求

- **领域**: 通用软件测试流程管理
- **流程**: 规划 → 执行 → 验证
- **任务类型**: Standard (标准测试) / Full (完整测试)
- **产物**: 计划、任务摘要、验证报告

---

## 二、现状问题分析

### 2.1 目录结构

```
src/tflow/
├── broker/                   # 消息代理模块 (部分实现)
│   ├── event.py             # ✅ JobEvent 事件定义
│   ├── job.py               # ✅ Job 状态管理
│   ├── message.py           # ✅ QueuedMessage 消息队列
│   └── __init__.py          # ❌ 引用不存在的 persistence/json_broker
├── agents/                   # ❌ 空目录
├── commands/                 # ❌ 空目录
└── utils/                    # ❌ 空目录
```

### 2.2 问题清单

| 问题 | 严重性 | 说明 |
|------|--------|------|
| broker 模块不完整 | **高** | 缺少 `persistence.py`、`json_broker.py` |
| agents/ 命令/工具目录为空 | **高** | 只有 Markdown 定义，无 Python 实现 |
| 无 CLI 入口 | **高** | 无法直接执行 tflow 命令 |
| 无 MCP Server | 中 | 缺少 MCP 协议实现 |

---

## 三、核心模块架构

### 3.1 模块划分

```
src/tflow/
├── __init__.py
├── __main__.py               # CLI 入口
│
├── core/                     # 核心业务逻辑
│   ├── __init__.py
│   ├── executor.py          # AgentExecutor - 统一执行器
│   ├── job_manager.py       # JobManager - 状态机 + Broker
│   ├── session.py           # Session 管理
│   └── events.py            # 事件定义
│
├── agents/                   # Agent 抽象层
│   ├── __init__.py
│   ├── base.py             # BaseAgent 抽象基类
│   ├── registry.py         # AgentRegistry 注册表
│   └── backends/
│       ├── __init__.py
│       ├── direct.py        # DirectBackend 直连模式
│       └── terminal.py      # TerminalBackend 终端模式
│
├── workflow/                 # 工作流引擎 (简单状态机)
│   ├── __init__.py
│   ├── engine.py           # WorkflowEngine - 简单状态机
│   ├── state.py            # 工作流状态定义
│   └── persistence.py      # 会话持久化
│
├── broker/                   # 消息代理 (已有框架，需补全)
│   ├── __init__.py         # 修复导入错误
│   ├── job.py              # ✅ 已有
│   ├── event.py            # ✅ 已有
│   ├── message.py          # ✅ 已有
│   ├── persistence.py      # ❌ 需创建
│   └── json_broker.py      # ❌ 需创建
│
├── delegate/                 # 委派系统
│   ├── __init__.py
│   ├── broker.py           # DelegateBroker
│   └── session.py          # 会话管理
│
├── spec/                    # 规范系统
│   ├── __init__.py
│   └── loader.py           # SpecLoader
│
├── storage/                  # 存储层
│   ├── __init__.py
│   ├── jsonl_store.py      # JSONL 存储
│   └── sqlite_store.py     # SQLite 存储
│
├── api/                      # API 层 (可选，后续扩展)
│   ├── __init__.py
│   └── routes/
│
├── realtime/                 # 实时通信
│   ├── __init__.py
│   └── bridge.py           # RealtimeBridge
│
└── config/                   # 配置管理
    ├── __init__.py
    └── settings.py         # Pydantic Settings
```

### 3.2 模块交互关系

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI / API                               │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AgentExecutor                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  Adapter    │  │  Process    │  │  Event Emitter          │ │
│  │  Registry  │  │  Manager    │  │                         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  WorkflowEngine │  │  JobManager     │  │  SpecLoader     │
│                 │  │                 │  │                 │
│  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │
│  │ Workflow  │  │  │  │ Job       │  │  │  │ Specs     │  │
│  │ State     │  │  │  └───────────┘  │  │  └───────────┘  │
│  └───────────┘  │  │                 │  │                 │
│                 │  │  ┌───────────┐  │  │                 │
│  线性状态机:    │  │  │ Events    │  │  │                 │
│  Parsing→      │  │  └───────────┘  │  │                 │
│  Validating→   │  │                 │  │                 │
│  Planning→     │  │                 │  │                 │
│  Executing→    │  │                 │  │                 │
│  Verifying→    │  │                 │  │                 │
│  Completing    │  │                 │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ExecutionStore                               │
│                   (JSONL + SQLite Persistence)                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 四、核心模块详细设计

### 4.0 模板与状态映射

#### 4.0.1 状态值统一映射

**两种状态类型的职责划分：**

```python
"""
JobStatus (JobManager): 用于底层 Job 队列管理
  - QUEUED, RUNNING, INPUT_REQUIRED, COMPLETED, FAILED, CANCELLED

WorkflowStatus (WorkflowEngine): 用于高层工作流状态机
  - IDLE, PARSING, VALIDATING, PLANNING, EXECUTING, VERIFYING, COMPLETING, COMPLETED, FAILED, PAUSED
"""
```

**WorkflowStatus 完整状态表：**

| `state.json` (文件) | `WorkflowStatus` (代码) | 阶段 | 说明 |
|---------------------|------------------------|------|------|
| `idle` | `IDLE = "idle"` | - | 初始状态 |
| `parsing` | `PARSING = "parsing"` | 解析阶段 | 解析参数和目标 |
| `validating` | `VALIDATING = "validating"` | 验证阶段 | 验证项目结构 |
| `planning` | `PLANNING = "planning"` | 规划阶段 | 调用 Planner Agent |
| `executing` | `EXECUTING = "executing"` | 执行阶段 | 波次并行执行任务 |
| `verifying` | `VERIFYING = "verifying"` | 验证阶段 | 调用 Verifier Agent |
| `completing` | `COMPLETING = "completing"` | 完成阶段 | 生成总结 |
| `completed` | `COMPLETED = "completed"` | - | 终止状态（成功） |
| `failed` | `FAILED = "failed"` | - | 终止状态（失败） |
| `paused` | `PAUSED = "paused"` | - | 可恢复状态 |

**JobStatus 完整状态表：**

| `JobStatus` (代码) | 说明 |
|---------------------|------|
| `QUEUED = "queued"` | 任务排队中 |
| `RUNNING = "running"` | 任务执行中 |
| `INPUT_REQUIRED = "input_required"` | 等待输入/暂停 |
| `COMPLETED = "completed"` | 任务完成 |
| `FAILED = "failed"` | 任务失败 |
| `CANCELLED = "cancelled"` | 任务取消 |

**状态转换关系：**

```
WorkflowEngine 状态机:
IDLE → PARSING → VALIDATING → PLANNING → EXECUTING → VERIFYING → COMPLETING → COMPLETED
                  ↓             ↓            ↓            ↓              ↓
                FAILED       FAILED      FAILED       FAILED        FAILED

PAUSED 可从任意状态进入，通过 resume() 恢复

JobManager 与 WorkflowEngine 同步:
WorkflowStatus.RUNNING (任意阶段) → JobStatus.RUNNING
WorkflowStatus.COMPLETED → JobStatus.COMPLETED
WorkflowStatus.FAILED → JobStatus.FAILED
WorkflowStatus.PAUSED → JobStatus.INPUT_REQUIRED
```

#### 4.0.2 模板与 Context 映射

```
模板文件                    →  WorkflowState.context     →  说明
──────────────────────────────────────────────────────────────────────────────
state.json                 →  (独立持久化)              →  项目级状态
scratch-index.json         →  context["scratch"]        →  Scratch 索引
plan.json                 →  context["plan"]          →  计划信息 (含 waves)
task.json                 →  context["tasks"]         →  任务列表
verification.json          →  result["verification"]    →  验证结果
```

**详细映射：**

```python
# Scratch Index 映射
scratch_index = {
    "id": "{{TYPE}}-{{SLUG}}-{{DATE}}",
    "type": context["workflow_type"],  # "standard" | "full"
    "title": context["goal"],
    "status": serialize_status(state.status),
    "flags": context.get("flags", {}),
    "plan": {
        "task_ids": context.get("plan", {}).get("task_ids", []),
        "task_count": context.get("plan", {}).get("task_count", 0),
    },
    "execution": {
        "method": "agent",
        "tasks_completed": context.get("tasks_completed", 0),
        "tasks_total": context.get("tasks_total", 0),
    },
}

# Plan 映射 (包含 waves)
plan = {
    "id": context["plan"].get("id"),
    "type": context["workflow_type"],
    "title": context["goal"],
    "status": serialize_status(state.status),
    "waves": context.get("waves", [[]]),  # 支持 waves 分批执行
    "task_ids": context.get("plan", {}).get("task_ids", []),
    "task_count": len(context.get("tasks", [])),
}

# Task 映射
tasks = [
    {
        "id": task["id"],
        "title": task["title"],
        "status": task.get("status", "pending"),
        "scope": task.get("scope", ""),
        "convergence": task.get("convergence", {}),
        "wave": task.get("wave", 1),
    }
    for task in context.get("tasks", [])
]

# Verification 映射
verification = {
    "phase": context.get("phase"),
    "status": serialize_status(state.status),
    "layers": result.get("verification", {}).get("layers", {}),
    "convergence_check": result.get("verification", {}).get("checks", {}),
    "gaps": result.get("verification", {}).get("gaps", []),
}
```

### 4.1 AgentExecutor (`core/executor.py`)

**职责**: 统一执行器，协调适配器选择、进程启动、输出渲染、退出处理

```python
"""Agent 统一执行器 - 对应 Maestro 的 CliAgentRunner"""

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Awaitable
import asyncio
import subprocess
from pathlib import Path
import uuid

class AgentType(Enum):
    CLAUDE_CODE = "claude-code"
    GEMINI = "gemini"
    QWEN = "qwen"
    CODEX = "codex"
    OPENCODE = "opencode"

class ExecutionMode(Enum):
    ANALYSIS = "analysis"
    WRITE = "write"

class BackendType(Enum):
    DIRECT = "direct"
    TERMINAL = "terminal"

@dataclass
class RunOptions:
    prompt: str
    tool: AgentType
    mode: ExecutionMode
    work_dir: Path
    model: str | None = None
    rule: str | None = None
    exec_id: str | None = None
    backend: BackendType = BackendType.DIRECT
    settings_file: str | None = None
    session_id: str | None = None

@dataclass
class ExecutionResult:
    exec_id: str
    exit_code: int | None
    output: str
    success: bool
    duration_ms: int
    entries: list[dict] = None  # NormalizedEntry 列表

class AgentExecutor:
    """统一 Agent 执行器"""

    TOOL_MAP = {
        "gemini": AgentType.GEMINI,
        "qwen": AgentType.QWEN,
        "codex": AgentType.CODEX,
        "claude": AgentType.CLAUDE_CODE,
        "opencode": AgentType.OPENCODE,
    }

    def __init__(
        self,
        broker_client=None,  # JobManager/DelegateBroker client
        session_store=None,   # ExecutionStore
        realtime_bridge=None, # RealtimeBridge
    ):
        self.broker = broker_client
        self.store = session_store
        self.bridge = realtime_bridge
        self._entry_handlers: list[Callable] = []

    async def run(self, options: RunOptions) -> ExecutionResult:
        """执行 Agent 并返回结果"""
        import time
        start = time.time()

        # 1. 确定 Agent 类型
        agent_type = self.TOOL_MAP.get(options.tool.value, options.tool)

        # 2. 组装 Prompt
        full_prompt = self._assemble_prompt(options)

        # 3. 启动进程
        process = await self._spawn_process(agent_type, full_prompt, options)

        # 4. 收集输出和事件
        entries = []
        if self.store:
            self.store.append_entry(process.exec_id, {"type": "spawn", "process": process})

        # 5. 等待完成
        exit_code = await process.wait()
        output = process.get_output()

        # 6. 保存历史
        if self.store:
            self.store.append_entry(process.exec_id, {
                "type": "completion",
                "exit_code": exit_code,
                "output": output,
            })

        return ExecutionResult(
            exec_id=process.exec_id,
            exit_code=exit_code,
            output=output,
            success=exit_code == 0,
            duration_ms=int((time.time() - start) * 1000),
            entries=entries,
        )

    async def run_async(
        self,
        options: RunOptions,
        on_entry: Callable[[dict], Awaitable[None]] | None = None,
    ) -> str:
        """异步执行，返回 exec_id"""
        exec_id = options.exec_id or f"run-{uuid.uuid4().hex[:8]}"
        options.exec_id = exec_id

        async def _run():
            result = await self.run(options)
            if on_entry:
                await on_entry({
                    "type": "completion",
                    "exec_id": exec_id,
                    "result": result,
                })

        asyncio.create_task(_run())
        return exec_id

    async def _spawn_process(
        self,
        agent_type: AgentType,
        prompt: str,
        options: RunOptions,
    ) -> "AgentProcess":
        """启动 Agent 进程"""
        cmd = self._build_command(agent_type, prompt, options)

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=options.work_dir,
            text=True,
        )

        return AgentProcess(
            process=process,
            exec_id=options.exec_id or str(process.pid),
            agent_type=agent_type,
        )

    def _build_command(
        self,
        agent_type: AgentType,
        prompt: str,
        options: RunOptions,
    ) -> list[str]:
        """构建 agent 特定命令行

        支持的 agent 类型及调用方式:
        - CLAUDE_CODE: claude -p <prompt> [--model <model>] [--no-input]
        - GEMINI: gemini -p <prompt> [--model <model>] [--api-key <key>]
        - QWEN: qwen chat -p <prompt> [--model <model>]
        - CODEX: codex '<prompt>' [--language <lang>]
        - OPENCODE: opencode -p <prompt> [--provider <provider>]
        """
        cmd: list[str] = []

        if agent_type == AgentType.CLAUDE_CODE:
            cmd = ["claude", "-p", prompt, "--no-input"]
            if options.model:
                cmd.extend(["--model", options.model])
            if options.settings_file:
                cmd.extend(["--settings", options.settings_file])

        elif agent_type == AgentType.GEMINI:
            cmd = ["gemini", "-p", prompt]
            if options.model:
                cmd.extend(["--model", options.model])

        elif agent_type == AgentType.QWEN:
            cmd = ["qwen", "chat", "-p", prompt]
            if options.model:
                cmd.extend(["--model", options.model])

        elif agent_type == AgentType.CODEX:
            cmd = ["codex", f"'{prompt}'"]
            if options.model:
                cmd.extend(["--language", options.model])

        elif agent_type == AgentType.OPENCODE:
            cmd = ["opencode", "-p", prompt]
            if options.model:
                cmd.extend(["--model", options.model])

        else:
            raise ValueError(f"Unsupported agent type: {agent_type}")

        return cmd

    def _assemble_prompt(
        self,
        options: RunOptions,
        context: dict | None = None,
    ) -> str:
        """组装 agent 特定 Prompt

        不同 agent 有不同的 prompt 格式偏好，这里做差异化处理。
        """
        parts = []

        # 1. Agent 特定的 system prompt
        system_prompts = {
            AgentType.CLAUDE_CODE: "You are a helpful coding assistant. Follow the user's instructions precisely.",
            AgentType.GEMINI: "You are Gemini, a helpful AI assistant.",
            AgentType.QWEN: "你是阿里云通义千问助手，请根据用户的问题提供准确的回答。",
            AgentType.CODEX: "You are Claude Code, an AI coding assistant.",
            AgentType.OPENCODE: "You are an AI assistant powered by OpenCode.",
        }
        if options.tool in system_prompts:
            parts.append(f"# System\n{system_prompts[options.tool]}")

        # 2. Mode 相关的指令
        if options.mode == ExecutionMode.WRITE:
            parts.append("# Mode\nYou are in write mode. Write clean, well-documented code.")
        else:
            parts.append("# Mode\nYou are in analysis mode. Provide clear analysis and reasoning.")

        # 3. Workflow Context (如果提供)
        if context:
            if "goal" in context:
                parts.append(f"# Goal\n{context['goal']}")
            if "scope" in context:
                parts.append(f"# Scope\n{', '.join(context['scope'])}")
            if "plan" in context:
                parts.append(f"# Plan\n{context['plan']}")

        # 4. Rule (如果提供)
        if options.rule:
            parts.append(f"# Rules\n{options.rule}")

        # 5. User prompt
        parts.append(f"# Task\n{options.prompt}")

        return "\n\n".join(parts)


class AgentProcess:
    """Agent 进程封装"""

    def __init__(self, process: subprocess.Popen, exec_id: str, agent_type: AgentType):
        self.process = process
        self.exec_id = exec_id
        self.agent_type = agent_type
        self._output = ""

    async def wait(self) -> int:
        """等待进程完成"""
        self._output, _ = self.process.communicate()
        return self.process.returncode

    def get_output(self) -> str:
        """获取输出"""
        return self._output

    def stop(self) -> None:
        """停止进程"""
        self.process.terminate()
```

---

### 4.2 JobManager (`core/job_manager.py`)

**职责**: Job 状态管理 + 事件 Broker，对应 Maestro 的 DelegateBroker

```python
"""Job 状态管理 + 事件 Broker"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable
import asyncio
import json
import sqlite3
from pathlib import Path
import uuid

class JobStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    INPUT_REQUIRED = "input_required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class MessageDelivery(Enum):
    INJECT = "inject"
    AFTER_COMPLETE = "after_complete"

@dataclass
class Job:
    job_id: str
    status: JobStatus
    created_at: str
    updated_at: str
    last_event_id: int = 0
    last_event_type: str = ""
    latest_snapshot: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class JobEvent:
    event_id: int
    sequence: int
    job_id: str
    type: str
    created_at: str
    status: JobStatus | None = None
    payload: dict[str, Any] = field(default_factory=dict)

class JobManager:
    """Job 状态管理和事件 Broker"""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._subscribers: list[Callable[[JobEvent], None]] = []

    def _init_db(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_event_id INTEGER DEFAULT 0,
                    last_event_type TEXT DEFAULT '',
                    latest_snapshot TEXT,
                    metadata TEXT
                );

                CREATE TABLE IF NOT EXISTS events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sequence INTEGER NOT NULL,
                    job_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT,
                    payload TEXT,
                    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
                );

                CREATE INDEX IF NOT EXISTS idx_events_job ON events(job_id);
            """)

    async def create_job(
        self,
        job_type: str,
        payload: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job:
        """创建新 Job"""
        now = datetime.now().isoformat()
        job = Job(
            job_id=f"job-{uuid.uuid4().hex[:12]}",
            status=JobStatus.QUEUED,
            created_at=now,
            updated_at=now,
            metadata=metadata or {"type": job_type},
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO jobs (job_id, status, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (job.job_id, job.status.value, job.created_at, job.updated_at, json.dumps(job.metadata)))

        await self._publish_event(job.job_id, "job_created", {"job_id": job.job_id})

        return job

    async def update_status(
        self,
        job_id: str,
        status: JobStatus,
        event_type: str,
        payload: dict[str, Any] | None = None,
    ) -> JobEvent:
        """更新 Job 状态"""
        now = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            # 获取序列号
            row = conn.execute(
                "SELECT COALESCE(MAX(sequence), 0) FROM events WHERE job_id = ?",
                (job_id,)
            ).fetchone()
            sequence = (row[0] or 0) + 1

            # 插入事件
            cursor = conn.execute("""
                INSERT INTO events (sequence, job_id, type, created_at, status, payload)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sequence, job_id, event_type, now, status.value, json.dumps(payload or {})))
            event_id = cursor.lastrowid

            # 更新 Job
            conn.execute("""
                UPDATE jobs SET updated_at = ?, status = ?, last_event_id = ?, last_event_type = ?
                WHERE job_id = ?
            """, (now, status.value, event_id, event_type, job_id))

        event = JobEvent(
            event_id=event_id,
            sequence=sequence,
            job_id=job_id,
            type=event_type,
            created_at=now,
            status=status,
            payload=payload or {},
        )

        # 通知订阅者
        for subscriber in self._subscribers:
            await subscriber(event)

        # 检查是否需要触发后续消息
        if status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            await self._dispatch_queued_messages(job_id, status)

        return event

    async def poll_events(
        self,
        session_id: str,
        job_id: str | None = None,
        after_event_id: int = 0,
        limit: int = 100,
    ) -> list[JobEvent]:
        """轮询事件"""
        with sqlite3.connect(self.db_path) as conn:
            if job_id:
                rows = conn.execute("""
                    SELECT event_id, sequence, job_id, type, created_at, status, payload
                    FROM events
                    WHERE job_id = ? AND event_id > ?
                    ORDER BY event_id
                    LIMIT ?
                """, (job_id, after_event_id, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT event_id, sequence, job_id, type, created_at, status, payload
                    FROM events
                    WHERE event_id > ?
                    ORDER BY event_id
                    LIMIT ?
                """, (after_event_id, limit)).fetchall()

        return [
            JobEvent(
                event_id=row[0],
                sequence=row[1],
                job_id=row[2],
                type=row[3],
                created_at=row[4],
                status=JobStatus(row[5]) if row[5] else None,
                payload=json.loads(row[6]) if row[6] else {},
            )
            for row in rows
        ]

    async def subscribe(
        self,
        callback: Callable[[JobEvent], None],
    ) -> Callable[[], None]:
        """订阅事件"""
        self._subscribers.append(callback)
        return lambda: self._subscribers.remove(callback)

    async def _publish_event(self, job_id: str, event_type: str, payload: dict) -> JobEvent:
        """发布事件"""
        now = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO events (sequence, job_id, type, created_at, payload)
                VALUES (
                    COALESCE((SELECT MAX(sequence) FROM events WHERE job_id = ?), 0) + 1,
                    ?, ?, ?, ?
                )
            """, (job_id, job_id, event_type, now, json.dumps(payload)))
            event_id = cursor.lastrowid

            conn.execute("""
                UPDATE jobs
                SET updated_at = ?, last_event_id = ?, last_event_type = ?
                WHERE job_id = ?
            """, (now, event_id, event_type, job_id))

        return JobEvent(
            event_id=event_id,
            sequence=0,
            job_id=job_id,
            type=event_type,
            created_at=now,
            payload=payload,
        )

    async def _dispatch_queued_messages(self, job_id: str, final_status: JobStatus) -> None:
        """分发排队的消息"""
        # 从数据库获取该 job 的排队消息
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT message_id, delivery, payload
                FROM message_queue
                WHERE job_id = ? AND status = 'pending'
            """, (job_id,)).fetchall()

        for row in rows:
            message_id, delivery, payload = row
            # 只分发 AFTER_COMPLETE 类型的消息
            if delivery == MessageDelivery.AFTER_COMPLETE.value:
                # 实际实现时会调用相应的处理器
                # 这里只是标记消息已被处理
                pass

            # 更新消息状态
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE message_queue
                    SET status = 'dispatched', dispatched_at = ?
                    WHERE message_id = ?
                """, (datetime.now().isoformat(), message_id))
```

### 4.2.1 BrokerPersistence (`broker/persistence.py`)

```python
"""Broker 持久化基类"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .job_manager import Job, JobEvent

class BrokerPersistence(ABC):
    """Broker 持久化抽象基类"""

    @abstractmethod
    async def save_job(self, job: "Job") -> None:
        """保存 Job 状态"""
        pass

    @abstractmethod
    async def get_job(self, job_id: str) -> "Job | None":
        """获取 Job"""
        pass

    @abstractmethod
    async def save_event(self, event: "JobEvent") -> None:
        """保存事件"""
        pass

    @abstractmethod
    async def get_events(
        self,
        job_id: str | None = None,
        after_event_id: int = 0,
        limit: int = 100,
    ) -> list["JobEvent"]:
        """获取事件"""
        pass

    @abstractmethod
    async def list_jobs(self, status: str | None = None) -> list["Job"]:
        """列出 Jobs"""
        pass
```

### 4.2.2 JsonBroker (`broker/json_broker.py`)

```python
"""JSON Broker 实现 - 基于 JSONL 的事件持久化"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
import asyncio
import json
import os
from .persistence import BrokerPersistence
from .job_manager import Job, JobEvent, JobStatus

@dataclass
class JsonBrokerConfig:
    """JSON Broker 配置"""
    data_dir: Path = Path(".tflow/data")
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    flush_interval: int = 5  # 秒

class JsonBroker(BrokerPersistence):
    """JSON Broker - JSONL 存储实现"""

    def __init__(self, config: JsonBrokerConfig | None = None):
        self.config = config or JsonBrokerConfig()
        self._jobs_file = self.config.data_dir / "jobs.jsonl"
        self._events_dir = self.config.data_dir / "events"
        self._jobs: dict[str, Job] = {}
        self._lock = asyncio.Lock()
        self._init_storage()

    def _init_storage(self) -> None:
        """初始化存储目录"""
        self.config.data_dir.mkdir(parents=True, exist_ok=True)
        self._events_dir.mkdir(parents=True, exist_ok=True)
        if self._jobs_file.exists():
            self._load_jobs()

    def _load_jobs(self) -> None:
        """加载 jobs"""
        with open(self._jobs_file, "r") as f:
            for line in f:
                if line.strip():
                    job_dict = json.loads(line)
                    job = Job(**job_dict)
                    self._jobs[job.job_id] = job

    async def save_job(self, job: Job) -> None:
        """保存 Job"""
        async with self._lock:
            self._jobs[job.job_id] = job
            with open(self._jobs_file, "a") as f:
                f.write(json.dumps(job.__dict__, default=str) + "\n")

    async def get_job(self, job_id: str) -> Job | None:
        """获取 Job"""
        return self._jobs.get(job_id)

    async def save_event(self, event: JobEvent) -> None:
        """保存事件到 JSONL 文件"""
        async with self._lock:
            events_file = self._events_dir / f"{event.job_id}.jsonl"
            with open(events_file, "a") as f:
                f.write(json.dumps(event.__dict__, default=str) + "\n")

            # 检查文件大小，必要时轮转
            if events_file.stat().st_size > self.config.max_file_size:
                await self._rotate_events_file(event.job_id)

    async def _rotate_events_file(self, job_id: str) -> None:
        """轮转事件文件"""
        events_file = self._events_dir / f"{job_id}.jsonl"
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        rotated = self._events_dir / f"{job_id}_{timestamp}.jsonl"
        events_file.rename(rotated)

    async def get_events(
        self,
        job_id: str | None = None,
        after_event_id: int = 0,
        limit: int = 100,
    ) -> list[JobEvent]:
        """获取事件"""
        if job_id:
            return await self._get_job_events(job_id, after_event_id, limit)
        else:
            # 获取所有 jobs 的最新事件
            all_events = []
            for jid in self._jobs:
                all_events.extend(await self._get_job_events(jid, after_event_id, limit))
            return sorted(all_events, key=lambda e: e.event_id)[:limit]

    async def _get_job_events(
        self,
        job_id: str,
        after_event_id: int,
        limit: int,
    ) -> list[JobEvent]:
        """获取指定 job 的事件"""
        events_file = self._events_dir / f"{job_id}.jsonl"
        if not events_file.exists():
            return []

        events = []
        with open(events_file, "r") as f:
            for line in f:
                if line.strip():
                    event_dict = json.loads(line)
                    if event_dict["event_id"] > after_event_id:
                        events.append(JobEvent(**event_dict))
                    if len(events) >= limit:
                        break
        return events

    async def list_jobs(self, status: str | None = None) -> list[Job]:
        """列出 Jobs"""
        if status:
            return [j for j in self._jobs.values() if j.status.value == status]
        return list(self._jobs.values())

    # 与 JobManager 的集成方法
    async def handle_job_event(self, event: JobEvent) -> None:
        """处理 Job 事件"""
        await self.save_event(event)
        if event.status:
            job = await self.get_job(event.job_id)
            if job:
                job.status = event.status
                job.last_event_id = event.event_id
                job.last_event_type = event.type
                await self.save_job(job)
```

### 4.2.3 broker/__init__.py 修复

```python
"""Broker 模块 - 修复导入错误"""

from .job_manager import JobManager, Job, JobEvent, JobStatus, MessageDelivery
from .persistence import BrokerPersistence
from .json_broker import JsonBroker, JsonBrokerConfig

__all__ = [
    "JobManager",
    "Job",
    "JobEvent",
    "JobStatus",
    "MessageDelivery",
    "BrokerPersistence",
    "JsonBroker",
    "JsonBrokerConfig",
]
```

---

### 4.3 WorkflowEngine (`workflow/engine.py`)

**职责**: 简单状态机，按线性阶段顺序执行工作流

```python
"""WorkflowEngine - 简单状态机工作流引擎"""

from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
import uuid

from tflow.workflow.state import (
    WorkflowState,
    WorkflowStatus,
    WorkflowType,
    TRANSITIONS,
)
from tflow.workflow.persistence import WorkflowPersistence

# Phase handler type
PhaseHandler = Callable[["WorkflowEngine", WorkflowState], bool]

class WorkflowEngine:
    """简单状态机工作流引擎

    线性流程：IDLE → PARSING → VALIDATING → PLANNING → EXECUTING → VERIFYING → COMPLETING → COMPLETED

    特点：
    - 简单线性状态机，适合固定顺序的流程
    - 易于理解和维护
    - 支持暂停/恢复
    - 事件驱动便于扩展
    """

    def __init__(
        self,
        job_manager=None,
        agent_executor=None,
        workflow_id: Optional[str] = None,
        workflow_type: WorkflowType = WorkflowType.STANDARD,
        persistence: Optional[WorkflowPersistence] = None,
    ):
        """初始化工作流引擎"""
        self.job_manager = job_manager
        self.agent_executor = agent_executor
        self.workflow_id = workflow_id or str(uuid.uuid4())
        self.workflow_type = workflow_type
        self._persistence = persistence or WorkflowPersistence()
        self._state: Optional[WorkflowState] = None
        self._handlers: Dict[WorkflowStatus, List[PhaseHandler]] = {}
        self._load_or_create_state()

    def _load_or_create_state(self) -> None:
        """加载或创建状态"""
        existing = self._persistence.load(self.workflow_id)
        if existing:
            self._state = existing
        else:
            self._state = WorkflowState(
                workflow_type=self.workflow_type,
                session_id=f"session-{self.workflow_id[:8]}",
                status=WorkflowStatus.IDLE,
                current_phase="idle",
                workflow_id=self.workflow_id,
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
            )
            self._persistence.save(self._state)

    @property
    def state(self) -> WorkflowState:
        return self._state

    @property
    def status(self) -> WorkflowStatus:
        return self._state.status

    def register_handler(self, status: WorkflowStatus, handler: PhaseHandler) -> None:
        """注册阶段处理器"""
        if status not in self._handlers:
            self._handlers[status] = []
        self._handlers[status].append(handler)

    def _execute_handlers(self, status: WorkflowStatus) -> bool:
        """执行所有处理器"""
        handlers = self._handlers.get(status, [])
        for handler in handlers:
            try:
                result = handler(self, self._state)
                if not result:
                    return False
            except Exception as e:
                print(f"Handler error for {status.value}: {e}")
                self._state.error = str(e)
                return False
        return True

    def transition_to(self, new_status: WorkflowStatus) -> bool:
        """转换到新状态"""
        if not self._state.can_transition_to(new_status):
            print(f"Invalid transition: {self._state.status.value} -> {new_status.value}")
            return False

        old_status = self._state.status
        self._state.status = new_status
        self._state.updated_at = datetime.utcnow().isoformat()

        if not self._execute_handlers(new_status):
            self._state.status = old_status
            return False

        self._persistence.save(self._state)
        return True

    def start(self) -> bool:
        """启动工作流 (IDLE → PARSING)"""
        return self.transition_to(WorkflowStatus.PARSING)

    def parse(self) -> bool:
        """解析阶段 (PARSING → VALIDATING)"""
        return self.transition_to(WorkflowStatus.VALIDATING)

    def validate(self) -> bool:
        """验证阶段 (VALIDATING → PLANNING)"""
        return self.transition_to(WorkflowStatus.PLANNING)

    def plan(self) -> bool:
        """规划阶段 (PLANNING → EXECUTING)"""
        return self.transition_to(WorkflowStatus.EXECUTING)

    def execute(self) -> bool:
        """执行阶段 (EXECUTING → VERIFYING)"""
        return self.transition_to(WorkflowStatus.VERIFYING)

    def verify(self) -> bool:
        """验证阶段 (VERIFYING → COMPLETING)"""
        return self.transition_to(WorkflowStatus.COMPLETING)

    def complete(self) -> bool:
        """完成阶段 (COMPLETING → COMPLETED)"""
        return self.transition_to(WorkflowStatus.COMPLETED)

    def fail(self, error: Optional[str] = None) -> bool:
        """标记工作流失败"""
        if error:
            self._state.error = error
        return self.transition_to(WorkflowStatus.FAILED)

    def pause(self) -> bool:
        """暂停工作流（仅从 EXECUTING）"""
        if self._state.status == WorkflowStatus.EXECUTING:
            self._state.status = WorkflowStatus.PAUSED
            self._state.updated_at = datetime.utcnow().isoformat()
            self._persistence.save(self._state)
            return True
        return False

    def resume(self) -> bool:
        """恢复工作流（PAUSED → EXECUTING）"""
        if self._state.status == WorkflowStatus.PAUSED:
            self._state.status = WorkflowStatus.EXECUTING
            self._state.updated_at = datetime.utcnow().isoformat()
            self._persistence.save(self._state)
            return True
        return False

    def cancel(self) -> bool:
        """取消工作流（任意 → FAILED）"""
        if self._state.status in [
            WorkflowStatus.PAUSED,
            WorkflowStatus.EXECUTING,
            WorkflowStatus.PARSING,
            WorkflowStatus.VALIDATING,
            WorkflowStatus.PLANNING,
        ]:
            self._state.status = WorkflowStatus.FAILED
            self._state.error = "Cancelled by user"
            self._state.updated_at = datetime.utcnow().isoformat()
            self._persistence.save(self._state)
            return True
        return False

    def reset(self) -> bool:
        """重置工作流到 IDLE 状态"""
        self._state.status = WorkflowStatus.IDLE
        self._state.error = None
        self._state.updated_at = datetime.utcnow().isoformat()
        self._persistence.save(self._state)
        return True

    def set_context(self, key: str, value: Any) -> None:
        """设置上下文值"""
        self._state.context[key] = value
        self._state.updated_at = datetime.utcnow().isoformat()
        self._persistence.save(self._state)

    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文值"""
        return self._state.context.get(key, default)
```

---

### 4.4 WorkflowState (`workflow/state.py`)

```python
"""工作流状态定义"""

from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any

class WorkflowType(Enum):
    """工作流类型"""
    STANDARD = "standard"
    FULL = "full"
    INIT = "init"

class WorkflowStatus(Enum):
    """工作流状态"""
    IDLE = "idle"
    PARSING = "parsing"
    VALIDATING = "validating"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

# 有效状态转换
TRANSITIONS: Dict[WorkflowStatus, list[WorkflowStatus]] = {
    WorkflowStatus.IDLE: [WorkflowStatus.PARSING],
    WorkflowStatus.PARSING: [WorkflowStatus.VALIDATING, WorkflowStatus.FAILED],
    WorkflowStatus.VALIDATING: [WorkflowStatus.PLANNING, WorkflowStatus.FAILED],
    WorkflowStatus.PLANNING: [WorkflowStatus.EXECUTING, WorkflowStatus.FAILED],
    WorkflowStatus.EXECUTING: [WorkflowStatus.VERIFYING, WorkflowStatus.FAILED],
    WorkflowStatus.VERIFYING: [WorkflowStatus.COMPLETING, WorkflowStatus.FAILED],
    WorkflowStatus.COMPLETING: [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED],
    WorkflowStatus.COMPLETED: [],
    WorkflowStatus.FAILED: [WorkflowStatus.IDLE],
    WorkflowStatus.PAUSED: [WorkflowStatus.EXECUTING, WorkflowStatus.FAILED],
}

@dataclass
class WorkflowState:
    """工作流状态"""
    workflow_type: WorkflowType
    session_id: str
    status: WorkflowStatus
    current_phase: str
    workflow_id: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    result: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_type": self.workflow_type.value,
            "session_id": self.session_id,
            "status": self.status.value,
            "current_phase": self.current_phase,
            "workflow_id": self.workflow_id,
            "context": self.context,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowState":
        return cls(
            workflow_type=WorkflowType(data.get("workflow_type", "standard")),
            session_id=data["session_id"],
            status=WorkflowStatus(data.get("status", "idle")),
            current_phase=data.get("current_phase", ""),
            workflow_id=data.get("workflow_id", ""),
            context=data.get("context", {}),
            result=data.get("result", {}),
            error=data.get("error"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )

    def can_transition_to(self, new_status: WorkflowStatus) -> bool:
        """检查是否可转换到新状态"""
        allowed = TRANSITIONS.get(self.status, [])
        return new_status in allowed

    def transition_to(self, new_status: WorkflowStatus) -> bool:
        """转换到新状态"""
        if self.can_transition_to(new_status):
            self.status = new_status
            self.updated_at = None  # 由持久化层设置
            return True
        return False

    def set_context(self, key: str, value: Any) -> None:
        """设置上下文值"""
        self.context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文值"""
        return self.context.get(key, default)
```

---

### 4.5 Agent Registry (`agents/registry.py`)

```python
"""Agent 注册表 - 包含具体 Agent 实现"""

from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
import subprocess
import signal
import os

class AgentType(Enum):
    """Agent 类型"""
    CLAUDE_CODE = "claude-code"
    GEMINI = "gemini"
    QWEN = "qwen"
    CODEX = "codex"
    OPENCODE = "opencode"

class ExecutionMode(Enum):
    """Agent 执行模式"""
    DIRECT = "direct"
    TERMINAL = "terminal"
    MCP = "mcp"

@dataclass
class AgentConfig:
    """Agent 配置"""
    agent_type: AgentType
    name: str
    description: str
    execution_mode: ExecutionMode = ExecutionMode.DIRECT
    command: Optional[str] = None
    env: Dict[str, str] = field(default_factory=dict)
    working_dir: Optional[str] = None
    timeout: int = 300
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.command:
            self.command = self._default_command()

    def _default_command(self) -> Optional[str]:
        commands = {
            AgentType.CLAUDE_CODE: "claude",
            AgentType.GEMINI: "gemini",
            AgentType.QWEN: "qwen",
            AgentType.CODEX: "codex",
            AgentType.OPENCODE: "opencode",
        }
        return commands.get(self.agent_type)

@dataclass
class AgentProcess:
    """Agent 进程封装"""
    pid: int
    process: subprocess.Popen
    command: List[str]
    started_at: Optional[str] = None

    def is_alive(self) -> bool:
        if self.process is None:
            return False
        return self.process.poll() is None

    def stop(self, timeout: int = 5) -> bool:
        """停止进程"""
        if self.process is None:
            return True
        try:
            self.process.terminate()
            self.process.wait(timeout=timeout)
            return True
        except subprocess.TimeoutExpired:
            self.process.kill()
            return False
        except Exception:
            return False

    def send_input(self, data: str) -> bool:
        """发送输入到进程"""
        if self.process and self.process.stdin:
            try:
                self.process.stdin.write(data + "\n")
                self.process.stdin.flush()
                return True
            except Exception:
                return False
        return False

class BaseAgent(ABC):
    """Agent 抽象基类"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self._process: Optional[AgentProcess] = None

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def agent_type(self) -> AgentType:
        return self.config.agent_type

    @abstractmethod
    def spawn(self, task: Dict[str, Any]) -> AgentProcess:
        """启动 Agent 进程"""
        pass

    @abstractmethod
    def on_entry(self, task: Dict[str, Any]) -> None:
        """当 Agent 被分配任务时调用"""
        pass

    def stop(self) -> bool:
        """停止 Agent 进程"""
        if self._process:
            return self._process.stop()
        return True

    def get_process(self) -> Optional[AgentProcess]:
        """获取当前进程"""
        return self._process

# 具体 Agent 实现

class ClaudeAgent(BaseAgent):
    def spawn(self, task: Dict[str, Any]) -> AgentProcess:
        cmd = [self.config.command or "claude"]
        if task.get("prompt"):
            cmd.extend(["--prompt", task["prompt"]])
        env = os.environ.copy()
        env.update(self.config.env)
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            env=env,
            cwd=self.config.working_dir,
        )
        self._process = AgentProcess(pid=process.pid, process=process, command=cmd)
        return self._process

    def on_entry(self, task: Dict[str, Any]) -> None:
        pass

class GeminiAgent(BaseAgent):
    def spawn(self, task: Dict[str, Any]) -> AgentProcess:
        cmd = [self.config.command or "gemini"]
        if task.get("prompt"):
            cmd.extend(["--prompt", task["prompt"]])
        env = os.environ.copy()
        env.update(self.config.env)
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            env=env,
            cwd=self.config.working_dir,
        )
        self._process = AgentProcess(pid=process.pid, process=process, command=cmd)
        return self._process

    def on_entry(self, task: Dict[str, Any]) -> None:
        pass

# ... 其他 Agent 类似实现

class AgentRegistry:
    """Agent 注册表 - 单例模式"""

    _instance: Optional["AgentRegistry"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._agents: Dict[str, BaseAgent] = {}
            cls._instance._configs: Dict[str, AgentConfig] = {}
        return cls._instance

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.name] = agent
        self._configs[agent.name] = agent.config

    def get(self, name: str) -> Optional[BaseAgent]:
        return self._agents.get(name)

    def get_config(self, name: str) -> Optional[AgentConfig]:
        return self._configs.get(name)

    def list_agents(self) -> List[str]:
        return list(self._agents.keys())

    def create_agent(self, config: AgentConfig) -> BaseAgent:
        agent_classes = {
            AgentType.CLAUDE_CODE: ClaudeAgent,
            AgentType.GEMINI: GeminiAgent,
            AgentType.QWEN: QwenAgent,
            AgentType.CODEX: CodexAgent,
            AgentType.OPENCODE: OpencodeAgent,
        }
        agent_class = agent_classes.get(config.agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {config.agent_type}")
        agent = agent_class(config)
        self.register(agent)
        return agent

agent_registry = AgentRegistry()
```

### 4.5.1 DirectBackend (`agents/backends/direct.py`)

```python
"""直连模式 - 直接 spawn 子进程"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List, AsyncIterator
import subprocess
import os
import asyncio

@dataclass
class DirectBackendConfig:
    """直连后端配置"""
    command: List[str]
    env: Optional[Dict[str, str]] = None
    cwd: Optional[str] = None
    timeout: int = 300
    shell: bool = False

class DirectBackend:
    """直连模式 - 直接 spawn 子进程执行 agent"""

    def __init__(self, config: Optional[DirectBackendConfig] = None):
        self.config = config
        self._process: Optional[asyncio.subprocess.Process] = None

    async def execute(
        self,
        command: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """执行命令并yield输出"""
        if command is None and self.config:
            command = self.config.command
        if env is None and self.config:
            env = self.config.env
        if cwd is None and self.config:
            cwd = self.config.cwd
        if timeout is None and self.config:
            timeout = self.config.timeout

        if not command:
            raise ValueError("No command provided")

        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)

        try:
            self._process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=exec_env,
                cwd=cwd,
                shell=self.config.shell if self.config else False,
            )

            try:
                # 读取 stdout
                while True:
                    try:
                        chunk = await asyncio.wait_for(
                            self._process.stdout.read(1024),
                            timeout=0.1,
                        )
                        if chunk:
                            yield chunk.decode(errors="replace")
                        else:
                            break
                    except asyncio.TimeoutError:
                        if self._process.returncode is not None:
                            break
                        continue

                # 读取 stderr
                stderr_bytes = await self._process.stderr.read()
                if stderr_bytes:
                    yield f"\n[stderr] {stderr_bytes.decode(errors='replace')}"

                # 等待进程结束
                await self._process.wait()
                yield f"\n[exit code: {self._process.returncode}]"

            except asyncio.TimeoutError:
                if self._process:
                    self._process.kill()
                    await self._process.wait()
                yield f"\n[timeout: command timed out after {timeout}s]"
        except Exception as e:
            yield f"\n[error: {str(e)}]"
        finally:
            self._process = None

    def kill(self) -> bool:
        """强制终止进程"""
        if self._process and self._process.poll() is None:
            try:
                self._process.kill()
                return True
            except Exception:
                return False
        return False

    def is_running(self) -> bool:
        """检查进程是否在运行"""
        if self._process:
            return self._process.poll() is None
        return False

    def execute_sync(
        self,
        command: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """同步执行命令"""
        # 实现同步版本...
```

### 4.5.2 TerminalBackend (`agents/backends/terminal.py`)

```python
"""终端模式 - 通过 tmux/wezterm 运行 agent"""

import asyncio
import re
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, AsyncIterator

@dataclass
class TerminalBackendConfig:
    """终端后端配置"""
    session_name: str = "tflow-agent"
    socket_name: Optional[str] = None
    window_name: str = "agent"
    keep_session: bool = True
    timeout: int = 3600

class TerminalBackend:
    """终端模式 - 通过 tmux/wezterm 运行 agent"""

    def __init__(self, config: Optional[TerminalBackendConfig] = None):
        self.config = config or TerminalBackendConfig()
        self._session_id: Optional[str] = None
        self._process: Optional[asyncio.subprocess.Process] = None

    async def execute(
        self,
        command: List[str],
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """通过 tmux session 执行命令"""
        session = self.config.session_name

        # 构建 tmux 命令
        escaped_cmd = " ".join(f"'{c}'" for c in command)
        tmux_cmd = [
            "tmux", "new-session", "-d", "-s", session,
            "bash", "-c", escaped_cmd
        ]

        # 启动 tmux session
        proc = await asyncio.create_subprocess_exec(
            *tmux_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.wait()

        self._session_id = session

        # 捕获输出
        capture_cmd = ["tmux", "capture-pane", "-t", session, "-p"]
        last_output = ""
        timeout_count = 0
        max_timeout = self.config.timeout // 5

        try:
            while timeout_count < max_timeout:
                await asyncio.sleep(5)

                # 检查 session 是否存在
                check = await asyncio.create_subprocess_exec(
                    "tmux", "has-session", "-t", session,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await check.wait()
                if check.returncode != 0:
                    if not self.config.keep_session:
                        break

                # 获取输出
                capture_proc = await asyncio.create_subprocess_exec(
                    *capture_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await capture_proc.communicate()
                current = stdout.decode(errors="replace")

                if current != last_output:
                    new_content = current[len(last_output):]
                    last_output = current
                    yield new_content
                    timeout_count = 0

                    if re.search(r"(?:\$|#)\s*$", new_content):
                        break
                else:
                    timeout_count += 1

        except asyncio.TimeoutError:
            yield "\n[Session timeout]\n"

    async def _cleanup_session(self, session: str) -> None:
        """清理 tmux session"""
        cleanup = await asyncio.create_subprocess_exec(
            "tmux", "kill-session", "-t", session,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await cleanup.wait()

    async def send_input(self, session: str, text: str) -> None:
        """向 session 发送输入"""
        cmd = ["tmux", "send-keys", "-t", session, text, "Enter"]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()

    async def kill_session(self, session: Optional[str] = None) -> None:
        """终止 session"""
        target = session or self._session_id
        if target:
            proc = await asyncio.create_subprocess_exec(
                "tmux", "kill-session", "-t", target,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
            if self._session_id == target:
                self._session_id = None
```

---

### 4.6 SpecLoader (`spec/loader.py`)

```python
"""规范加载器"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

class SpecCategory(Enum):
    CODING = "coding"
    ARCH = "arch"
    QUALITY = "quality"
    DEBUG = "debug"
    TEST = "test"
    REVIEW = "review"
    LEARNING = "learning"

class SpecScope(Enum):
    PROJECT = "project"
    GLOBAL = "global"
    TEAM = "team"
    PERSONAL = "personal"

CATEGORY_MAP = {
    "coding-conventions.md": SpecCategory.CODING,
    "architecture-constraints.md": SpecCategory.ARCH,
    "quality-rules.md": SpecCategory.QUALITY,
    "debug-notes.md": SpecCategory.DEBUG,
    "test-conventions.md": SpecCategory.TEST,
    "review-standards.md": SpecCategory.REVIEW,
    "learnings.md": SpecCategory.LEARNING,
}

@dataclass
class SpecLoadResult:
    content: str
    matched_specs: list[str]
    total_loaded: int

class SpecLoader:
    """规范加载器"""

    def __init__(self, project_path: str | Path = "."):
        self.project_path = Path(project_path)

    def resolve_spec_dir(self, scope: SpecScope, uid: str | None = None) -> Path:
        """解析规范目录"""
        if scope == SpecScope.GLOBAL:
            return Path.home() / ".config" / "maestro" / "specs"
        elif scope == SpecScope.TEAM:
            return self.project_path / ".workflow" / "collab" / "specs"
        elif scope == SpecScope.PERSONAL:
            if not uid:
                raise ValueError("personal scope requires uid")
            return self.project_path / ".workflow" / "collab" / "specs" / uid
        else:  # PROJECT
            return self.project_path / ".workflow" / "specs"

    def load_by_category(
        self,
        category: SpecCategory,
        scope: SpecScope = SpecScope.PROJECT,
    ) -> SpecLoadResult:
        """按类别加载规范"""
        spec_dir = self.resolve_spec_dir(scope)
        matched = []
        content_parts = []

        for filename, cat in CATEGORY_MAP.items():
            if cat == category:
                filepath = spec_dir / filename
                if filepath.exists():
                    matched.append(str(filepath))
                    content_parts.append(f"# {filename}\n{filepath.read_text()}")

        return SpecLoadResult(
            content="\n\n".join(content_parts),
            matched_specs=matched,
            total_loaded=len(matched),
        )

    def load_all(self, scope: SpecScope = SpecScope.PROJECT) -> SpecLoadResult:
        """加载所有规范"""
        spec_dir = self.resolve_spec_dir(scope)
        matched = []
        content_parts = []

        for filename in spec_dir.glob("*.md"):
            matched.append(str(filename))
            content_parts.append(f"# {filename.name}\n{filename.read_text()}")

        return SpecLoadResult(
            content="\n\n".join(content_parts),
            matched_specs=matched,
            total_loaded=len(matched),
        )
```

### 4.7 ExecutionStore (`storage/jsonl_store.py`)

```python
"""执行历史存储 - JSONL 实现"""

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List, Dict, Any, AsyncIterator
import json
import asyncio
from datetime import datetime

@dataclass
class ExecutionRecord:
    """执行记录"""
    execution_id: str
    workflow_id: str
    task_id: str
    agent_id: str
    status: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if not self.started_at:
            self.started_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionRecord":
        return cls(**data)

class ExecutionStore:
    """JSONL 执行历史存储"""

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent
            base_dir = project_root / ".workflow" / "executions"
        else:
            base_dir = Path(base_dir)
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    def _get_file_path(self, workflow_id: str) -> Path:
        return self.base_dir / f"{workflow_id}.jsonl"

    async def append(self, record: ExecutionRecord) -> bool:
        """追加执行记录"""
        try:
            path = self._get_file_path(record.workflow_id)
            async with self._lock:
                with open(path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
            return True
        except Exception as e:
            print(f"Failed to append record: {e}")
            return False

    async def get(self, workflow_id: str) -> List[ExecutionRecord]:
        """获取工作流的所有执行记录"""
        records = []
        path = self._get_file_path(workflow_id)
        if not path.exists():
            return records
        try:
            async with self._lock:
                with open(path, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            data = json.loads(line)
                            records.append(ExecutionRecord.from_dict(data))
        except Exception as e:
            print(f"Failed to read records: {e}")
        return records

    async def get_latest(self, workflow_id: str) -> Optional[ExecutionRecord]:
        """获取最新的执行记录"""
        records = await self.get(workflow_id)
        return records[-1] if records else None

    async def get_by_task(self, workflow_id: str, task_id: str) -> List[ExecutionRecord]:
        """获取特定任务的执行记录"""
        records = await self.get(workflow_id)
        return [r for r in records if r.task_id == task_id]

    async def list_workflows(self) -> List[str]:
        """列出所有工作流 ID"""
        try:
            return [p.stem for p in self.base_dir.glob("*.jsonl")]
        except Exception as e:
            print(f"Failed to list workflows: {e}")
            return []

    async def iter_sessions(self) -> AsyncIterator[str]:
        """迭代所有会话 ID"""
        for p in self.base_dir.glob("*.jsonl"):
            yield p.stem
```

### 4.8 SQLiteStore (`storage/sqlite_store.py`)

```python
"""结构化数据存储 - SQLite 实现"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any
import sqlite3
import json
import asyncio

@dataclass
class SQLiteStoreConfig:
    """SQLite 配置"""
    db_path: Optional[str] = None
    timeout: int = 5
    wal_mode: bool = True  # Write-Ahead Logging

class SQLiteStore:
    """SQLite 存储 - 用于结构化数据"""

    def __init__(self, config: Optional[SQLiteStoreConfig] = None):
        if config is None:
            config = SQLiteStoreConfig()
        self.config = config
        if config.db_path is None:
            project_root = Path(__file__).parent.parent.parent.parent
            db_path = project_root / ".workflow" / "tflow.db"
        else:
            db_path = Path(config.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._lock = asyncio.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=self.config.timeout)
        conn.row_factory = sqlite3.Row
        if self.config.wal_mode:
            conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    context TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL,
                    input_data TEXT,
                    output_data TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)
            conn.commit()
        finally:
            conn.close()

    async def save_session(self, session_data: Dict[str, Any]) -> bool:
        """保存会话"""
        async with self._lock:
            return await asyncio.to_thread(self._save_session_sync, session_data)

    def _save_session_sync(self, session_data: Dict[str, Any]) -> bool:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            context_json = json.dumps(session_data.get("context", {}))
            metadata_json = json.dumps(session_data.get("metadata", {}))
            cursor.execute("""
                INSERT OR REPLACE INTO sessions
                (session_id, name, context, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_data["session_id"],
                session_data["name"],
                context_json,
                session_data["created_at"],
                session_data["updated_at"],
                metadata_json,
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Failed to save session: {e}")
            return False
        finally:
            conn.close()

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话"""
        async with self._lock:
            return await asyncio.to_thread(self._get_session_sync, session_id)

    def _get_session_sync(self, session_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_session(row)
            return None
        finally:
            conn.close()

    def _row_to_session(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "session_id": row["session_id"],
            "name": row["name"],
            "context": json.loads(row["context"] or "{}"),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "metadata": json.loads(row["metadata"] or "{}"),
        }

    async def list_sessions(self, status: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """列出所有会话"""
        async with self._lock:
            return await asyncio.to_thread(self._list_sessions_sync, status, limit)

    async def save_task(self, task_data: Dict[str, Any]) -> bool:
        """保存任务"""
        async with self._lock:
            return await asyncio.to_thread(self._save_task_sync, task_data)

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务"""
        async with self._lock:
            return await asyncio.to_thread(self._get_task_sync, task_id)

    async def get_tasks(self, session_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取任务列表"""
        async with self._lock:
            return await asyncio.to_thread(self._get_tasks_sync, session_id, status)

    async def close(self) -> None:
        """关闭连接"""
        pass
```

### 4.9 RealtimeBridge (`realtime/bridge.py`)

```python
"""实时事件桥接 - SSE 实现"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List, Callable, AsyncIterator
from datetime import datetime
import asyncio

class EventDelivery(Enum):
    """事件投递方式"""
    SYNC = "sync"
    ASYNC = "async"
    FIRE_AND_FORGET = "fire_and_forget"

@dataclass
class BridgeEvent:
    """桥接事件"""
    type: str
    session_id: str
    data: Dict[str, Any]
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

@dataclass
class RealtimeBridgeConfig:
    """实时桥接配置"""
    name: str = "default"
    buffer_size: int = 1000
    heartbeat_interval: int = 30
    max_queue_size: int = 100
    delivery: EventDelivery = EventDelivery.ASYNC

class RealtimeBridge:
    """实时事件桥接器"""

    def __init__(self, config: Optional[RealtimeBridgeConfig] = None):
        if config is None:
            config = RealtimeBridgeConfig()
        self.config = config
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._event_buffer: List[BridgeEvent] = []
        self._running = False
        self._lock = asyncio.Lock()

    async def subscribe(self, session_id: str) -> AsyncIterator[BridgeEvent]:
        """订阅会话事件"""
        queue: asyncio.Queue[BridgeEvent] = asyncio.Queue(maxsize=self.config.max_queue_size)
        async with self._lock:
            if session_id not in self._subscribers:
                self._subscribers[session_id] = []
            self._subscribers[session_id].append(queue)

        try:
            while self._running:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield event
                except asyncio.TimeoutError:
                    continue
        finally:
            async with self._lock:
                if session_id in self._subscribers and queue in self._subscribers[session_id]:
                    self._subscribers[session_id].remove(queue)

    async def publish(self, session_id: str, event_type: str, data: Dict[str, Any]) -> None:
        """发布事件"""
        event = BridgeEvent(
            type=event_type,
            session_id=session_id,
            timestamp=datetime.utcnow().isoformat(),
            data=data,
        )

        # 添加到缓冲区
        self._event_buffer.append(event)
        if len(self._event_buffer) > self.config.buffer_size:
            self._event_buffer = self._event_buffer[-self.config.buffer_size:]

        # 投递到订阅者
        async with self._lock:
            queues = self._subscribers.get(session_id, [])

        for queue in queues:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass

    async def broadcast(self, event_type: str, data: Dict[str, Any]) -> None:
        """广播事件到所有订阅者"""
        event = BridgeEvent(
            type=event_type,
            session_id="*",
            timestamp=datetime.utcnow().isoformat(),
            data=data,
        )

        self._event_buffer.append(event)
        if len(self._event_buffer) > self.config.buffer_size:
            self._event_buffer = self._event_buffer[-self.config.buffer_size:]

        async with self._lock:
            all_queues = [q for queues in self._subscribers.values() for q in queues]

        for queue in all_queues:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass

    async def attach_to_job_manager(self, job_manager: Any) -> None:
        """附加到 JobManager"""
        async def on_job_event(event: Any) -> None:
            await self.publish(
                event.job_id,
                event.type,
                {
                    "status": event.status.value if event.status else None,
                    "payload": event.payload,
                }
            )
        await job_manager.subscribe(on_job_event)

    def get_events(self, event_type: Optional[str] = None, limit: int = 100) -> List[BridgeEvent]:
        """获取缓冲的事件"""
        events = self._event_buffer
        if event_type:
            events = [e for e in events if e.type == event_type]
        return events[-limit:]

    def clear_events(self) -> None:
        """清空事件缓冲区"""
        self._event_buffer.clear()

    async def start_heartbeat(self) -> None:
        """启动心跳"""
        self._running = True
        while self._running:
            try:
                await asyncio.sleep(self.config.heartbeat_interval)
                if self._running:
                    await self.broadcast("heartbeat", {"timestamp": datetime.utcnow().isoformat()})
            except asyncio.CancelledError:
                break

    def stop_heartbeat(self) -> None:
        """停止心跳"""
        self._running = False

    def get_subscriber_count(self) -> int:
        """获取订阅者数量"""
        return sum(len(qs) for qs in self._subscribers.values())

    def format_sse(self, event: BridgeEvent) -> str:
        """格式化为 SSE 格式"""
        return f"id: {event.session_id}\nevent: {event.type}\ndata: {event.data}\n\n"
```

### 4.10 DelegateBroker (`delegate/broker.py`)

```python
"""DelegateBroker - 委派系统 Broker"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Awaitable
import asyncio
import json
from pathlib import Path

class DelegateStatus(Enum):
    """委派状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class DelegateTask:
    """委派任务"""
    task_id: str
    agent_type: str
    prompt: str
    context: dict[str, Any] = field(default_factory=dict)
    status: DelegateStatus = DelegateStatus.PENDING
    result: dict[str, Any] | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    error: str | None = None

class DelegateBroker:
    """DelegateBroker - 管理 agent 委派任务的生命周期"""

    def __init__(self, data_dir: Path = Path(".tflow/data/delegates")):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._tasks: dict[str, DelegateTask] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._subscribers: list[Callable[[str, DelegateTask], Awaitable[None]]] = []
        self._lock = asyncio.Lock()

    def _get_task_lock(self, task_id: str) -> asyncio.Lock:
        """获取任务的锁"""
        if task_id not in self._locks:
            self._locks[task_id] = asyncio.Lock()
        return self._locks[task_id]

    async def create_task(
        self,
        task_id: str,
        agent_type: str,
        prompt: str,
        context: dict[str, Any] | None = None,
    ) -> DelegateTask:
        """创建委派任务"""
        task = DelegateTask(
            task_id=task_id,
            agent_type=agent_type,
            prompt=prompt,
            context=context or {},
        )
        async with self._lock:
            self._tasks[task_id] = task
        await self._save_task(task)
        await self._notify("created", task)
        return task

    async def update_status(
        self,
        task_id: str,
        status: DelegateStatus,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> DelegateTask:
        """更新任务状态"""
        async with self._get_task_lock(task_id):
            if task_id not in self._tasks:
                raise ValueError(f"Task not found: {task_id}")
            task = self._tasks[task_id]
            task.status = status
            task.updated_at = datetime.now().isoformat()
            if result is not None:
                task.result = result
            if error is not None:
                task.error = error
            await self._save_task(task)
        await self._notify("updated", task)
        return task

    async def get_task(self, task_id: str) -> DelegateTask | None:
        """获取任务"""
        return self._tasks.get(task_id)

    async def list_tasks(
        self,
        status: DelegateStatus | None = None,
        agent_type: str | None = None,
    ) -> list[DelegateTask]:
        """列出任务"""
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        if agent_type:
            tasks = [t for t in tasks if t.agent_type == agent_type]
        return tasks

    async def subscribe(
        self,
        callback: Callable[[str, DelegateTask], Awaitable[None]],
    ) -> Callable[[], None]:
        """订阅任务变化"""
        self._subscribers.append(callback)
        return lambda: self._subscribers.remove(callback)

    async def _notify(self, event_type: str, task: DelegateTask) -> None:
        """通知订阅者"""
        for subscriber in self._subscribers:
            try:
                await subscriber(event_type, task)
            except Exception:
                pass  # 不影响其他订阅者

    async def _save_task(self, task: DelegateTask) -> None:
        """保存任务到文件"""
        file_path = self.data_dir / f"{task.task_id}.json"
        with open(file_path, "w") as f:
            json.dump(task.__dict__, f, default=str, indent=2)

    async def _load_tasks(self) -> None:
        """加载所有任务"""
        for file_path in self.data_dir.glob("*.json"):
            with open(file_path, "r") as f:
                task_dict = json.load(f)
                task = DelegateTask(**task_dict)
                self._tasks[task.task_id] = task

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = await self.get_task(task_id)
        if not task or task.status in (DelegateStatus.COMPLETED, DelegateStatus.FAILED, DelegateStatus.CANCELLED):
            return False
        await self.update_status(task_id, DelegateStatus.CANCELLED)
        return True
```

---

## 五、扩展性设计

### 5.1 Agent 类型扩展

新增 Agent 只需：

1. 在 `agents/protocols/` 添加协议实现类
2. 在 `agents/backends/` 添加后端适配（如需要）
3. 注册到 `AgentRegistry`

```python
# 示例：新增 CustomAgent
class CustomAgent(BaseAgent):
    async def spawn(self, config: AgentConfig) -> AgentProcess:
        ...
    async def stop(self, process_id: str) -> None:
        ...
    def on_entry(self, process_id: str, callback) -> Callable:
        ...

# 注册
agent_registry.register(AgentType.CUSTOM, CustomAgent)
```

### 5.2 Storage 后端扩展

```python
class PostgresStore(StorageBackend):
    """PostgreSQL 后端 - 未来可扩展"""
    async def save_job(self, job: Job) -> None: ...
    async def get_job(self, job_id: str) -> Job | None: ...
    async def publish_event(self, event: JobEvent) -> JobEvent: ...

# 切换后端只需修改配置
# config.yaml: storage.backend: "postgresql"
```

### 5.3 Workflow 模板扩展

```python
# 用户可自定义工作流模板
class CustomWorkflow(BaseWorkflow):
    async def plan(self, context: dict) -> Plan: ...
    async def execute_phase(self, phase: Phase) -> PhaseResult: ...
    async def verify(self, result: ExecutionResult) -> VerificationReport: ...

# 注册模板
workflow_engine.register_template("custom_test", CustomWorkflow())
```

---

## 六、关键设计决策记录 (ADR)

### ADR-001: 简单状态机而非复杂图遍历

**决策**: 采用简单线性状态机，而非 Graph Walker 图遍历

**理由**:
- tflow 当前流程是线性的：Parsing → Validating → Planning → Executing → Verifying → Completing
- 简单状态机易于理解和维护
- YAGNI原则：先用简单的，等真正需要分支/并行时再升级

**未来升级路径**:
- 当需要条件分支时：可添加 `DecisionNode` 支持
- 当需要并行执行时：可添加 `Fork/Join` 支持
- 当需要嵌套子图时：可引入 `GraphWalker`

### ADR-002: 使用 asyncio 作为并发模型

**决策**: 采用 asyncio 而非多线程/多进程作为核心并发模型

**理由**:
- I/O 密集型任务（Agent 执行、文件 IO、网络）适合 asyncio
- 与 Python 生态良好集成
- 避免 GIL 限制

**替代方案**:
- 线程池: 适合 CPU 密集型，但增加复杂度
- 多进程: 更好的隔离性，但通信开销大

### ADR-003: 采用 Event-Driven Architecture

**决策**: Job 管理采用 pub/sub 事件驱动架构

**理由**:
- Decoupling: Producer/Consumer 通过事件交互
- 可恢复性: 事件持久化支持断点续做
- 实时性: 事件驱动天然支持实时通知

**替代方案**:
- 请求/响应: 简单但紧耦合
- RPC: 适合同步调用，但事件场景不如 pub/sub 自然

### ADR-004: JSONL + SQLite 双存储

**决策**: Execution 历史用 JSONL，Job/Broker 用 SQLite

**理由**:
- JSONL: Append-only，适合大量写入的执行记录
- SQLite: 结构化查询、事务支持、WAL 模式高并发

**替代方案**:
- 纯 PostgreSQL: 功能更强但部署复杂
- 纯 JSON 文件: 查询能力弱

---

## 七、CLI 命令设计

### 7.1 命令概览

```
tflow run [workflow]              # 运行工作流
tflow delegate [prompt]            # 委派任务给 Agent
tflow status [session_id]         # 查看状态
tflow stop [session_id]           # 停止执行
tflow session list                 # 列出会话
tflow session show <id>           # 会话详情
```

### 7.2 命令详细设计

#### `tflow run` - 运行工作流

```bash
tflow run [workflow] [options]

# 选项
--config, -c <path>    # 工作流配置文件路径
--type, -t <type>     # 工作流类型: standard | full (默认: standard)
--goal, -g <goal>     # 目标描述
--scope, -s <paths>   # 范围路径 (逗号分隔)
--dry-run             # 预览模式，不实际执行

# 示例
tflow run                    # 运行默认工作流
tflow run tests/smoke        # 运行指定工作流
tflow run -t full -g "完整测试" -s "src/,tests/"
tflow run --dry-run          # 预览执行计划
```

**实现要求**:
- 调用 `WorkflowEngine.execute(workflow_type, goal, scope, options)`
- 创建 Session 并返回 `session_id`
- 支持从 `.tflow/config.yaml` 读取默认配置

---

#### `tflow delegate` - 委派任务 (核心命令)

```bash
tflow delegate [prompt] [options]

# 位置参数
prompt                 # 要执行的 prompt (必填)

# 选项
--to, -t <tool>       # Agent 工具: claude | gemini | qwen | codex | opencode (默认: claude)
--mode, -m <mode>     # 执行模式: analysis | write (默认: analysis)
--backend, -b <type>  # 后端类型: direct | terminal (默认: direct)
--cd <dir>            # 工作目录 (默认: 当前目录)
--rule, -r <template> # 规则模板名称
--id <exec_id>        # 执行 ID (自动生成)
--resume [id]         # 恢复之前的会话
--async               # 异步执行，不阻塞

# 示例
tflow delegate "分析这个函数的性能" --to claude
tflow delegate "重构这段代码" --to codex --mode write
tflow delegate "审查 PR" --to gemini --backend terminal
tflow delegate "写测试用例" --to claude --rule testing
```

**实现要求**:
- 调用 `AgentExecutor.run(RunOptions(...))`
- 通过 `DelegateBroker.create_task()` 创建委派任务
- 支持同步/异步两种模式
- 使用 `ExecutionStore` 记录执行历史

---

#### `tflow status` - 查看状态

```bash
tflow status [session_id]

# 选项
--watch, -w           # 实时监控模式
--json                # JSON 格式输出

# 示例
tflow status                      # 查看当前会话状态
tflow status wf-20230504-abc123   # 查看指定会话
tflow status --watch              # 实时监控
tflow status --json               # JSON 输出
```

**实现要求**:
- 调用 `WorkflowEngine.get_status(session_id)` 或 `JobManager`
- 支持 `--watch` 时通过 `RealtimeBridge` 订阅事件
- 无 `session_id` 时从 `.tflow/current` 读取当前会话

---

#### `tflow stop` - 停止执行

```bash
tflow stop [session_id]

# 选项
--force, -f          # 强制终止

# 示例
tflow stop                    # 停止当前会话
tflow stop wf-20230504-abc123
tflow stop --force           # 强制终止
```

**实现要求**:
- 调用 `WorkflowEngine.cancel(session_id)` 或 `JobManager.update_status(..., JobStatus.CANCELLED)`
- 通知 `AgentExecutor` 杀死子进程

---

#### `tflow session list` - 列出会话

```bash
tflow session list

# 选项
--limit, -n <num>    # 限制数量 (默认: 20)
--status <status>    # 按状态筛选

# 示例
tflow session list
tflow session list --limit 50
tflow session list --status running
```

**实现要求**:
- 调用 `SQLiteStore.get_session_list()` 或直接查询 `sessions` 表
- 解析 `state.json` 获取会话状态

---

#### `tflow session show` - 会话详情

```bash
tflow session show <session_id>

# 选项
--verbose, -v        # 详细信息
--tasks             # 显示任务列表

# 示例
tflow session show wf-20230504-abc123
tflow session show wf-20230504-abc123 --tasks
```

**实现要求**:
- 调用 `WorkflowEngine.get_status(session_id)` 获取完整状态
- 调用 `SQLiteStore.get_tasks(session_id)` 获取任务列表
- 展示 `waves` 分批执行情况

### 7.3 CLI 入口实现

```python
# __main__.py
"""tflow CLI 入口"""

import asyncio
from pathlib import Path
from typing import Optional
import sys

import click
from dotenv import load_dotenv

from .core.job_manager import JobManager
from .core.executor import AgentExecutor
from .workflow.engine import WorkflowEngine
from .workflow.state import WorkflowType
from .storage.sqlite_store import SQLiteStore
from .storage.jsonl_store import ExecutionStore
from .delegate.broker import DelegateBroker

load_dotenv()


@click.group()
@click.version_option()
def cli():
    """tflow - 测试流程编排 CLI"""
    pass


@cli.command()
@click.argument("workflow", required=False)
@click.option("--config", "-c", type=click.Path())
@click.option("--type", "-t", "workflow_type", default="standard",
              type=click.Choice(["standard", "full"]))
@click.option("--goal", "-g")
@click.option("--scope", "-s")
@click.option("--dry-run", is_flag=True)
def run(workflow, config, workflow_type, goal, scope, dry_run):
    """运行工作流"""
    wf_type = WorkflowType.FULL if workflow_type == "full" else WorkflowType.STANDARD

    # 初始化组件
    job_mgr = JobManager(Path(".tflow/data/jobs.db"))
    executor = AgentExecutor()
    engine = WorkflowEngine(job_mgr, executor)

    if dry_run:
        click.echo("[DRY-RUN] 预览执行计划")
        # TODO: 实现预览模式
        return

    # 执行工作流
    session_id = asyncio.run(engine.execute(wf_type, goal, scope.split(",") if scope else None))
    click.echo(f"Session: {session_id}")


@cli.command()
@click.argument("prompt")
@click.option("--to", "-t", "tool", default="claude",
              type=click.Choice(["claude", "gemini", "qwen", "codex", "opencode"]))
@click.option("--mode", "-m", default="analysis",
              type=click.Choice(["analysis", "write"]))
@click.option("--backend", "-b", "backend_type", default="direct",
              type=click.Choice(["direct", "terminal"]))
@click.option("--cd")
@click.option("--rule", "-r")
@click.option("--async", "is_async", is_flag=True)
def delegate(prompt, tool, mode, backend_type, cd, rule, is_async):
    """委派任务给 Agent"""
    executor = AgentExecutor()
    options = RunOptions(
        tool=AgentType[tool.upper()],
        mode=ExecutionMode[mode.upper()],
        prompt=prompt,
        work_dir=Path(cd or "."),
        rule=rule,
    )

    if is_async:
        # 异步模式：启动后台任务
        exec_id = asyncio.run(_run_delegate_async(executor, options))
        click.echo(f"[{exec_id}] Started async delegate")
    else:
        # 同步模式：等待结果
        result = asyncio.run(executor.run(options))
        click.echo(result.output)


async def _run_delegate_async(executor, options):
    broker = DelegateBroker()
    exec_id = f"delegate-{uuid.uuid4().hex[:12]}"
    # 创建任务并异步执行
    # ...
    return exec_id


@cli.command()
@click.argument("session_id", required=False)
@click.option("--watch", "-w", is_flag=True)
@click.option("--json", "as_json", is_flag=True)
def status(session_id, watch, as_json):
    """查看状态"""
    if not session_id:
        # 读取当前会话
        current_file = Path(".tflow/current")
        if current_file.exists():
            session_id = current_file.read_text().strip()

    if not session_id:
        click.echo("No active session")
        return

    engine = WorkflowEngine()
    state = engine.get_status(session_id)

    if as_json:
        click.echo(json.dumps(state.to_dict()))
    else:
        click.echo(f"Session: {state.session_id}")
        click.echo(f"Status: {state.status.value}")
        click.echo(f"Phase: {state.current_phase}")


@cli.command()
@click.argument("session_id", required=False)
@click.option("--force", "-f", is_flag=True)
def stop(session_id, force):
    """停止执行"""
    if not session_id:
        current_file = Path(".tflow/current")
        if current_file.exists():
            session_id = current_file.read_text().strip()

    if not session_id:
        click.echo("No active session to stop")
        return

    engine = WorkflowEngine()
    engine.cancel(session_id, force=force)
    click.echo(f"Stopped: {session_id}")


@cli.group()
def session():
    """会话管理"""
    pass


@session.command("list")
@click.option("--limit", "-n", default=20)
@click.option("--status")
def session_list(limit, status):
    """列出会话"""
    store = SQLiteStore()
    sessions = asyncio.run(store.list_sessions(status=status, limit=limit))
    for s in sessions:
        click.echo(f"{s['session_id']}  {s['status']}  {s['created_at']}")


@session.command("show")
@click.argument("session_id")
@click.option("--tasks", is_flag=True)
def session_show(session_id, tasks):
    """会话详情"""
    engine = WorkflowEngine()
    state = engine.get_status(session_id)

    click.echo(f"Session: {state.session_id}")
    click.echo(f"Type: {state.workflow_type.value}")
    click.echo(f"Status: {state.status.value}")
    click.echo(f"Phase: {state.current_phase}")

    if tasks:
        store = SQLiteStore()
        task_list = asyncio.run(store.get_tasks(state.session_id))
        for t in task_list:
            click.echo(f"  [{t['status']}] {t['task_id']} - {t['title']}")


if __name__ == "__main__":
    cli()
```

### 7.4 命令与模块映射

| 命令 | 调用的模块 | 方法 |
|------|-----------|------|
| `run` | WorkflowEngine | `execute()` |
| `delegate` | AgentExecutor | `run()` |
| `status` | WorkflowEngine | `get_status()` |
| `stop` | WorkflowEngine | `cancel()` |
| `session list` | SQLiteStore | `list_sessions()` |
| `session show` | WorkflowEngine + SQLiteStore | `get_status()` + `get_tasks()` |

---

## 十、TDD 单元测试方案

### 10.1 测试策略

**测试金字塔:**
```
        ╱ E2E Tests ╲       ← 少量端到端测试
      ╱────────────────╲
    ╱  Integration Tests  ╲  ← 核心流程集成测试
  ╱────────────────────────╲
╱      Unit Tests           ╲ ← 每个模块充分单元测试
```

**测试框架:**
- `pytest` - 主测试框架
- `pytest-asyncio` - 异步测试支持
- `pytest-mock` - Mock/Patch
- `pytest-cov` - 覆盖率报告

**测试数据:**
- 使用 `tmp_path` fixture 管理临时测试文件
- 使用 `faker` 生成模拟数据

### 10.2 模块测试设计

#### 10.2.1 AgentExecutor 测试 (`test_executor.py`)

```python
"""AgentExecutor 单元测试"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from tflow.core.executor import (
    AgentExecutor,
    AgentType,
    ExecutionMode,
    RunOptions,
    ExecutionResult,
)

# ===== Fixtures =====

@pytest.fixture
def executor():
    """创建 AgentExecutor 实例"""
    return AgentExecutor()

@pytest.fixture
def run_options():
    """创建 RunOptions"""
    return RunOptions(
        prompt="分析这段代码",
        tool=AgentType.CLAUDE_CODE,
        mode=ExecutionMode.ANALYSIS,
        work_dir=Path("/tmp"),
    )

# ===== 同步测试 =====

class TestAgentExecutorBuildCommand:
    """测试 _build_command 方法"""

    def test_build_command_claude(self, executor):
        """测试 Claude 命令构建"""
        options = RunOptions(
            prompt="test prompt",
            tool=AgentType.CLAUDE_CODE,
            mode=ExecutionMode.ANALYSIS,
            work_dir=Path("/tmp"),
        )
        cmd = executor._build_command(AgentType.CLAUDE_CODE, "test prompt", options)
        assert cmd[0] == "claude"
        assert "-p" in cmd
        assert "test prompt" in cmd

    def test_build_command_gemini(self, executor):
        """测试 Gemini 命令构建"""
        options = RunOptions(
            prompt="test prompt",
            tool=AgentType.GEMINI,
            mode=ExecutionMode.ANALYSIS,
            work_dir=Path("/tmp"),
        )
        cmd = executor._build_command(AgentType.GEMINI, "test prompt", options)
        assert cmd[0] == "gemini"
        assert "-p" in cmd

    def test_build_command_with_model(self, executor):
        """测试带模型参数的命令构建"""
        options = RunOptions(
            prompt="test",
            tool=AgentType.CLAUDE_CODE,
            mode=ExecutionMode.ANALYSIS,
            work_dir=Path("/tmp"),
            model="claude-3-opus",
        )
        cmd = executor._build_command(AgentType.CLAUDE_CODE, "test", options)
        assert "--model" in cmd
        assert "claude-3-opus" in cmd

    def test_build_command_unsupported(self, executor):
        """测试不支持的 Agent 类型"""
        options = RunOptions(
            prompt="test",
            tool=AgentType.CLAUDE_CODE,
            mode=ExecutionMode.ANALYSIS,
            work_dir=Path("/tmp"),
        )
        with pytest.raises(ValueError, match="Unsupported agent type"):
            executor._build_command(AgentType.CODEX, "test", options)

class TestAgentExecutorAssemblePrompt:
    """测试 _assemble_prompt 方法"""

    def test_assemble_prompt_basic(self, executor, run_options):
        """测试基础 prompt 组装"""
        prompt = executor._assemble_prompt(run_options)
        assert "# Task" in prompt
        assert "分析这段代码" in prompt

    def test_assemble_prompt_with_context(self, executor, run_options):
        """测试带上下文的 prompt 组装"""
        context = {
            "goal": "重构代码",
            "scope": ["src/main.py", "src/utils.py"],
            "plan": "1. 分析 2. 重构",
        }
        prompt = executor._assemble_prompt(run_options, context)
        assert "重构代码" in prompt
        assert "src/main.py" in prompt

    def test_assemble_prompt_write_mode(self, executor):
        """测试 Write 模式的 prompt"""
        options = RunOptions(
            prompt="写一个函数",
            tool=AgentType.CLAUDE_CODE,
            mode=ExecutionMode.WRITE,
            work_dir=Path("/tmp"),
        )
        prompt = executor._assemble_prompt(options)
        assert "write mode" in prompt.lower()

# ===== 异步测试 =====

class TestAgentExecutorRun:
    """测试 run 方法"""

    @pytest.mark.asyncio
    async def test_run_success(self, executor, run_options):
        """测试成功执行"""
        # Mock subprocess.Popen
        mock_process = MagicMock()
        mock_process.communicate = AsyncMock(return_value=("test output", ""))
        mock_process.pid = 12345
        mock_process.returncode = 0

        with patch("subprocess.Popen", return_value=mock_process):
            result = await executor.run(run_options)

        assert isinstance(result, ExecutionResult)
        assert result.success is True
        assert result.exit_code == 0
        assert "test output" in result.output

    @pytest.mark.asyncio
    async def test_run_failure(self, executor, run_options):
        """测试执行失败"""
        mock_process = MagicMock()
        mock_process.communicate = AsyncMock(return_value=("", "error"))
        mock_process.pid = 12345
        mock_process.returncode = 1

        with patch("subprocess.Popen", return_value=mock_process):
            result = await executor.run(run_options)

        assert result.success is False
        assert result.exit_code == 1

    @pytest.mark.asyncio
    async def test_run_with_store(self, executor, run_options):
        """测试带存储的执行"""
        mock_store = MagicMock()
        mock_store.append_entry = MagicMock()

        executor.store = mock_store
        mock_process = MagicMock()
        mock_process.communicate = AsyncMock(return_value=("output", ""))
        mock_process.pid = 12345
        mock_process.returncode = 0

        with patch("subprocess.Popen", return_value=mock_process):
            await executor.run(run_options)

        assert mock_store.append_entry.called
```

#### 10.2.2 JobManager 测试 (`test_job_manager.py`)

```python
"""JobManager 单元测试"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch
from tflow.core.job_manager import (
    JobManager,
    Job,
    JobEvent,
    JobStatus,
)

@pytest.fixture
def job_manager(tmp_path):
    """创建 JobManager 实例"""
    return JobManager(db_path=tmp_path / "test.db")

@pytest.fixture
def sample_job():
    """创建示例 Job"""
    return Job(
        job_id="job-test-001",
        status=JobStatus.QUEUED,
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
    )

# ===== 创建 Job 测试 =====

class TestJobManagerCreate:
    """测试 create_job 方法"""

    @pytest.mark.asyncio
    async def test_create_job_success(self, job_manager):
        """测试成功创建 Job"""
        job = await job_manager.create_job(
            job_type="test",
            payload={"key": "value"},
        )

        assert job.job_id.startswith("job-")
        assert job.status == JobStatus.QUEUED
        assert job.metadata["type"] == "test"

    @pytest.mark.asyncio
    async def test_create_job_with_metadata(self, job_manager):
        """测试带元数据的创建"""
        metadata = {"source": "test", "priority": "high"}
        job = await job_manager.create_job(
            job_type="test",
            metadata=metadata,
        )

        assert job.metadata["source"] == "test"
        assert job.metadata["priority"] == "high"

# ===== 状态更新测试 =====

class TestJobManagerUpdate:
    """测试 update_status 方法"""

    @pytest.mark.asyncio
    async def test_update_status_to_running(self, job_manager):
        """测试状态更新为 RUNNING"""
        job = await job_manager.create_job(job_type="test")

        event = await job_manager.update_status(
            job_id=job.job_id,
            status=JobStatus.RUNNING,
            event_type="started",
        )

        assert event.job_id == job.job_id
        assert event.status == JobStatus.RUNNING
        assert event.type == "started"

    @pytest.mark.asyncio
    async def test_update_status_to_completed(self, job_manager):
        """测试状态更新为 COMPLETED"""
        job = await job_manager.create_job(job_type="test")

        event = await job_manager.update_status(
            job_id=job.job_id,
            status=JobStatus.COMPLETED,
            event_type="completed",
            payload={"result": "success"},
        )

        assert event.status == JobStatus.COMPLETED
        assert event.payload["result"] == "success"

# ===== 事件轮询测试 =====

class TestJobManagerPollEvents:
    """测试 poll_events 方法"""

    @pytest.mark.asyncio
    async def test_poll_events_empty(self, job_manager):
        """测试无事件时轮询返回空列表"""
        events = await job_manager.poll_events(session_id="nonexistent")
        assert events == []

    @pytest.mark.asyncio
    async def test_poll_events_after_id(self, job_manager):
        """测试指定起始 ID 的轮询"""
        job = await job_manager.create_job(job_type="test")
        await job_manager.update_status(job.job_id, JobStatus.RUNNING, "start")

        events = await job_manager.poll_events(
            job_id=job.job_id,
            after_event_id=0,
            limit=10,
        )

        assert len(events) >= 1
        assert events[0].event_id > 0

# ===== 订阅测试 =====

class TestJobManagerSubscribe:
    """测试订阅功能"""

    @pytest.mark.asyncio
    async def test_subscribe_callback(self, job_manager):
        """测试订阅回调"""
        received = []

        async def callback(event):
            received.append(event)

        unsubscribe = await job_manager.subscribe(callback)

        job = await job_manager.create_job(job_type="test")
        await job_manager.update_status(job.job_id, JobStatus.RUNNING, "start")

        # 等待事件处理
        await asyncio.sleep(0.1)

        assert len(received) >= 1
        assert received[0].job_id == job.job_id

        # 测试取消订阅
        unsubscribe()
```

#### 10.2.3 WorkflowEngine 测试 (`test_workflow_engine.py`)

```python
"""WorkflowEngine 单元测试"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from tflow.workflow.engine import (
    WorkflowEngine,
    WorkflowStatus,
    WorkflowState,
    PhaseResult,
)
from tflow.workflow.state import WorkflowType

@pytest.fixture
def mock_job_manager():
    """创建 Mock JobManager"""
    manager = MagicMock()
    manager.create_job = AsyncMock()
    manager.update_status = AsyncMock()
    return manager

@pytest.fixture
def mock_executor():
    """创建 Mock AgentExecutor"""
    executor = MagicMock()
    executor.run = AsyncMock()
    return executor

@pytest.fixture
def engine(mock_job_manager, mock_executor):
    """创建 WorkflowEngine 实例"""
    return WorkflowEngine(
        job_manager=mock_job_manager,
        agent_executor=mock_executor,
        persistence=None,
    )

# ===== 状态转换测试 =====

class TestWorkflowEngineTransitions:
    """测试状态转换"""

    def test_initial_status_is_parsing(self, engine):
        """测试初始状态为 PARSING"""
        assert WorkflowEngine.TRANSITIONS[WorkflowStatus.IDLE] == WorkflowStatus.PARSING

    def test_parsing_transitions_to_validating(self, engine):
        """测试 PARSING -> VALIDATING"""
        assert WorkflowEngine.TRANSITIONS[WorkflowStatus.PARSING] == WorkflowStatus.VALIDATING

    def test_all_phases_transition_forward(self, engine):
        """测试所有阶段正确前向转换"""
        expected = {
            WorkflowStatus.VALIDATING: WorkflowStatus.PLANNING,
            WorkflowStatus.PLANNING: WorkflowStatus.EXECUTING,
            WorkflowStatus.EXECUTING: WorkflowStatus.VERIFYING,
            WorkflowStatus.VERIFYING: WorkflowStatus.COMPLETING,
            WorkflowStatus.COMPLETING: WorkflowStatus.COMPLETED,
        }
        assert WorkflowEngine.TRANSITIONS == expected

# ===== execute 方法测试 =====

class TestWorkflowEngineExecute:
    """测试 execute 方法"""

    @pytest.mark.asyncio
    async def test_execute_creates_session(self, engine, mock_job_manager):
        """测试执行创建会话"""
        mock_job_manager.create_job.return_value = MagicMock(
            job_id="job-123",
            status="queued",
        )

        # Mock 阶段处理器
        engine._handlers[WorkflowStatus.PARSING] = AsyncMock(
            return_value=PhaseResult(phase="parsing", success=True)
        )

        state = await engine.execute(
            workflow_type=WorkflowType.STANDARD,
            goal="测试目标",
            scope=["src/"],
        )

        assert state.session_id.startswith("wf-")
        assert state.status == WorkflowStatus.PARSING
        assert state.context["goal"] == "测试目标"

    @pytest.mark.asyncio
    async def test_execute_with_mock_handlers(self, engine, mock_job_manager, mock_executor):
        """测试完整执行流程（Mock 所有阶段）"""
        # Mock Job
        mock_job = MagicMock()
        mock_job.job_id = "job-123"
        mock_job_manager.create_job.return_value = mock_job

        # Mock 所有阶段处理器
        async def mock_handler(state):
            state.context["parsed_goal"] = state.context.get("goal", "")
            return PhaseResult(phase=state.status.value, success=True)

        for status in [
            WorkflowStatus.PARSING,
            WorkflowStatus.VALIDATING,
            WorkflowStatus.PLANNING,
            WorkflowStatus.EXECUTING,
            WorkflowStatus.VERIFYING,
            WorkflowStatus.COMPLETING,
        ]:
            engine._handlers[status] = mock_handler

        mock_executor.run.return_value = MagicMock(
            success=True,
            output="plan output",
            exit_code=0,
        )

        state = await engine.execute(
            workflow_type=WorkflowType.STANDARD,
            goal="测试",
            scope=["src/"],
        )

        # 所有阶段成功，最终状态应为 COMPLETED
        assert state.status == WorkflowStatus.COMPLETED

# ===== cancel 方法测试 =====

class TestWorkflowEngineCancel:
    """测试 cancel 方法"""

    @pytest.mark.asyncio
    async def test_cancel_session_not_found(self, engine):
        """测试取消不存在的会话"""
        with pytest.raises(ValueError, match="Session not found"):
            await engine.cancel("nonexistent-session")

# ===== get_status 方法测试 =====

class TestWorkflowEngineGetStatus:
    """测试 get_status 方法"""

    def test_get_status_no_persistence(self, engine):
        """测试无持久化时返回 None"""
        result = engine.get_status("any-session")
        assert result is None
```

#### 10.2.4 WorkflowState 测试 (`test_workflow_state.py`)

```python
"""WorkflowState 单元测试"""

import pytest
from tflow.workflow.state import (
    WorkflowState,
    WorkflowStatus,
    WorkflowType,
    WorkflowPersistence,
)

@pytest.fixture
def sample_state():
    """创建示例 WorkflowState"""
    return WorkflowState(
        workflow_type=WorkflowType.STANDARD,
        session_id="wf-test-001",
        status=WorkflowStatus.PARSING,
        current_phase="parsing",
        workflow_id="wf-123",
        context={"goal": "测试"},
        result={},
    )

# ===== 序列化测试 =====

class TestWorkflowStateSerialization:
    """测试状态序列化"""

    def test_to_dict(self, sample_state):
        """测试 to_dict 方法"""
        data = sample_state.to_dict()

        assert data["workflow_type"] == "standard"
        assert data["session_id"] == "wf-test-001"
        assert data["status"] == "parsing"
        assert data["context"]["goal"] == "测试"

    def test_from_dict(self, sample_state):
        """测试 from_dict 方法"""
        data = sample_state.to_dict()
        restored = WorkflowState.from_dict(data)

        assert restored.workflow_type == sample_state.workflow_type
        assert restored.session_id == sample_state.session_id
        assert restored.status == sample_state.status

    def test_from_dict_partial_data(self):
        """测试从部分数据恢复"""
        data = {
            "workflow_type": "full",
            "session_id": "wf-456",
            "status": "completed",
            "current_phase": "completing",
        }
        state = WorkflowState.from_dict(data)

        assert state.workflow_type == WorkflowType.FULL
        assert state.context == {}  # 默认空字典
        assert state.result == {}   # 默认空字典

# ===== 持久化测试 =====

class TestWorkflowPersistence:
    """测试 WorkflowPersistence"""

    def test_save_and_load_state(self, sample_state, tmp_path):
        """测试保存和加载状态"""
        persistence = WorkflowPersistence(storage_dir=tmp_path)

        persistence.save_state(sample_state)
        loaded = persistence.load_state(sample_state.session_id)

        assert loaded is not None
        assert loaded.session_id == sample_state.session_id
        assert loaded.status == sample_state.status

    def test_load_nonexistent(self, tmp_path):
        """测试加载不存在的状态"""
        persistence = WorkflowPersistence(storage_dir=tmp_path)
        result = persistence.load_state("nonexistent")

        assert result is None
```

#### 10.2.5 SQLiteStore 测试 (`test_sqlite_store.py`)

```python
"""SQLiteStore 单元测试"""

import pytest
import asyncio
from pathlib import Path
from tflow.storage.sqlite_store import SQLiteStore

@pytest.fixture
def store(tmp_path):
    """创建 SQLiteStore 实例"""
    return SQLiteStore(config={"db_path": tmp_path / "test.db"})

# ===== 会话测试 =====

class TestSQLiteStoreSession:
    """测试会话管理"""

    @pytest.mark.asyncio
    async def test_save_and_get_session(self, store):
        """测试保存和获取会话"""
        await store.save_session(
            session_id="wf-test-001",
            status="running",
            context={"goal": "测试"},
            result={"output": "done"},
        )

        session = await store.get_session("wf-test-001")

        assert session is not None
        assert session["session_id"] == "wf-test-001"
        assert session["status"] == "running"
        assert session["context"]["goal"] == "测试"

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, store):
        """测试获取不存在的会话"""
        result = await store.get_session("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_sessions(self, store):
        """测试列出会话"""
        await store.save_session("wf-1", "running", {})
        await store.save_session("wf-2", "completed", {})
        await store.save_session("wf-3", "running", {})

        sessions = await store.list_sessions(limit=10)

        assert len(sessions) == 3
        # 默认按 updated_at DESC 排序
        assert sessions[0]["session_id"] == "wf-3"

    @pytest.mark.asyncio
    async def test_list_sessions_by_status(self, store):
        """测试按状态筛选会话"""
        await store.save_session("wf-1", "running", {})
        await store.save_session("wf-2", "completed", {})

        running = await store.list_sessions(status="running")
        completed = await store.list_sessions(status="completed")

        assert len(running) == 1
        assert running[0]["status"] == "running"
        assert len(completed) == 1
```

### 10.3 测试覆盖目标

| 模块 | 覆盖率目标 | 关键测试点 |
|------|-----------|-----------|
| AgentExecutor | ≥90% | 命令构建、Prompt 组装、执行流程 |
| JobManager | ≥90% | CRUD、状态转换、事件订阅 |
| WorkflowEngine | ≥85% | 状态转换、暂停/恢复、取消 |
| WorkflowState | ≥95% | 序列化/反序列化、持久化 |
| SQLiteStore | ≥90% | CRUD、查询、事务 |
| DelegateBroker | ≥85% | 任务创建、状态更新、订阅 |
| DirectBackend | ≥85% | 进程启动、输出捕获、超时处理 |
| TerminalBackend | ≥80% | tmux session 管理、输入发送 |
| JsonBroker | ≥85% | 事件持久化、文件轮转 |
| RealtimeBridge | ≥80% | 订阅发布、广播、心跳 |

### 10.4 Mock 策略

```python
# 1. subprocess - 永远 mock (正确的 patch 路径)
@pytest.fixture
def mock_subprocess():
    with patch("subprocess.Popen") as mock_popen:
        process = MagicMock()
        process.communicate = AsyncMock(return_value=("output", ""))
        process.pid = 12345
        process.returncode = 0
        process.terminate = MagicMock()
        mock_popen.return_value = process
        yield mock_popen

# 2. Async 方法必须用 AsyncMock
mock_store.append_entry = AsyncMock()

# 3. 文件系统 - 使用 tmp_path fixture
@pytest.fixture
def temp_storage(tmp_path):
    return tmp_path / "data"

# 4. 事件循环
@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
```

### 10.5 测试数据工厂

```python
# tests/factories.py
import uuid
from datetime import datetime

class WorkflowStateFactory:
    """WorkflowState 测试工厂"""
    @staticmethod
    def create(**kwargs):
        defaults = {
            "workflow_type": WorkflowType.STANDARD,
            "session_id": f"wf-{uuid.uuid4().hex[:12]}",
            "status": WorkflowStatus.IDLE,
            "current_phase": "idle",
        }
        defaults.update(kwargs)
        return WorkflowState(**defaults)

class JobFactory:
    """Job 测试工厂"""
    @staticmethod
    def create(**kwargs):
        defaults = {
            "job_id": f"job-{uuid.uuid4().hex[:12]}",
            "status": JobStatus.QUEUED,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        defaults.update(kwargs)
        return Job(**defaults)

class DelegateTaskFactory:
    """DelegateTask 测试工厂"""
    @staticmethod
    def create(**kwargs):
        defaults = {
            "task_id": f"task-{uuid.uuid4().hex[:12]}",
            "agent_type": "claude",
            "prompt": "test prompt",
            "context": {},
            "status": DelegateStatus.PENDING,
        }
        defaults.update(kwargs)
        return DelegateTask(**defaults)
```

### 10.6 补充测试：WorkflowEngine 暂停/恢复

```python
# ===== 暂停/恢复测试 =====

class TestWorkflowEnginePauseResume:
    """测试 pause/resume 方法"""

    @pytest.mark.asyncio
    async def test_pause_success(self, engine, mock_persistence, sample_state):
        """测试成功暂停"""
        mock_persistence.load_state.return_value = sample_state
        engine.persistence = mock_persistence

        await engine.pause(sample_state.session_id)

        assert sample_state.status == WorkflowStatus.PAUSED
        mock_persistence.save_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_pause_session_not_found(self, engine):
        """测试暂停不存在的会话"""
        engine.persistence = MagicMock()
        engine.persistence.load_state.return_value = None

        with pytest.raises(ValueError, match="Session not found"):
            await engine.pause("nonexistent")

    @pytest.mark.asyncio
    async def test_resume_success(self, engine, mock_persistence, sample_state):
        """测试成功恢复"""
        sample_state.status = WorkflowStatus.PAUSED
        mock_persistence.load_state.return_value = sample_state
        engine.persistence = mock_persistence

        # Mock 阶段处理器以避免实际执行
        engine._handlers[WorkflowStatus.PLANNING] = AsyncMock(
            return_value=PhaseResult(phase="planning", success=True)
        )

        result = await engine.resume(sample_state.session_id)

        assert sample_state.status == WorkflowStatus.PLANNING

    @pytest.mark.asyncio
    async def test_resume_session_not_found(self, engine):
        """测试恢复不存在的会话"""
        engine.persistence = MagicMock()
        engine.persistence.load_state.return_value = None

        with pytest.raises(ValueError, match="Session not found"):
            await engine.resume("nonexistent")

class TestWorkflowEngineStatusMapping:
    """测试 _to_job_status 方法"""

    def test_parsing_maps_to_running(self, engine):
        """测试 PARSING -> RUNNING"""
        result = engine._to_job_status(WorkflowStatus.PARSING)
        assert result == JobStatus.RUNNING

    def test_completed_maps_to_completed(self, engine):
        """测试 COMPLETED -> COMPLETED"""
        result = engine._to_job_status(WorkflowStatus.COMPLETED)
        assert result == JobStatus.COMPLETED

    def test_failed_maps_to_failed(self, engine):
        """测试 FAILED -> FAILED"""
        result = engine._to_job_status(WorkflowStatus.FAILED)
        assert result == JobStatus.FAILED

    def test_paused_maps_to_input_required(self, engine):
        """测试 PAUSED -> INPUT_REQUIRED"""
        result = engine._to_job_status(WorkflowStatus.PAUSED)
        assert result == JobStatus.INPUT_REQUIRED

    def test_all_statuses_mapped(self, engine):
        """测试所有状态都有映射"""
        for status in WorkflowStatus:
            result = engine._to_job_status(status)
            assert result is not None, f"No mapping for {status}"

class TestWorkflowEngineException:
    """测试异常处理"""

    @pytest.mark.asyncio
    async def test_execute_catches_exception(self, engine, mock_job_manager):
        """测试 execute 捕获异常"""
        mock_job_manager.create_job.return_value = MagicMock(job_id="job-123")

        # Mock 一个会抛出异常的处理器
        engine._handlers[WorkflowStatus.PARSING] = AsyncMock(
            side_effect=RuntimeError("Test error")
        )

        state = await engine.execute(
            workflow_type=WorkflowType.STANDARD,
            goal="Test",
            scope=[],
        )

        assert state.status == WorkflowStatus.FAILED
        assert "Test error" in state.result.get("error", "")
```

### 10.7 补充测试：JobManager 错误处理

```python
# ===== 错误处理测试 =====

class TestJobManagerErrorHandling:
    """测试错误处理"""

    @pytest.mark.asyncio
    async def test_update_status_invalid_job(self, job_manager):
        """测试更新不存在的 job"""
        with pytest.raises(Exception):  # SQLite 会抛出异常
            await job_manager.update_status(
                job_id="nonexistent-job",
                status=JobStatus.RUNNING,
                event_type="start",
            )

    @pytest.mark.asyncio
    async def test_dispatch_queued_messages(self, job_manager):
        """测试 _dispatch_queued_messages 方法"""
        job = await job_manager.create_job(job_type="test")
        await job_manager.update_status(
            job.job_id,
            JobStatus.COMPLETED,
            "completed",
        )
        # 验证方法被调用（不抛异常）
        # 实际实现会查询 message_queue 表
```

### 10.8 补充测试：SQLiteStore Task CRUD

```python
# ===== Task CRUD 测试 =====

class TestSQLiteStoreTask:
    """测试任务管理"""

    @pytest.mark.asyncio
    async def test_save_and_get_task(self, store):
        """测试保存和获取任务"""
        await store.save_task(
            task_id="task-001",
            session_id="wf-test",
            title="Test Task",
            status="pending",
            wave=1,
        )

        tasks = await store.get_tasks("wf-test")
        assert len(tasks) == 1
        assert tasks[0]["task_id"] == "task-001"
        assert tasks[0]["title"] == "Test Task"

    @pytest.mark.asyncio
    async def test_get_tasks_by_status(self, store):
        """测试按状态筛选任务"""
        await store.save_task("task-1", "wf-1", "Task 1", "pending", 1)
        await store.save_task("task-2", "wf-1", "Task 2", "running", 1)
        await store.save_task("task-3", "wf-1", "Task 3", "completed", 1)

        pending = await store.get_tasks("wf-1", status="pending")
        running = await store.get_tasks("wf-1", status="running")
        completed = await store.get_tasks("wf-1", status="completed")

        assert len(pending) == 1
        assert len(running) == 1
        assert len(completed) == 1

    @pytest.mark.asyncio
    async def test_get_tasks_by_wave(self, store):
        """测试按 wave 筛选任务"""
        await store.save_task("task-1", "wf-1", "Task 1", "pending", 1)
        await store.save_task("task-2", "wf-1", "Task 2", "pending", 2)
        await store.save_task("task-3", "wf-1", "Task 3", "pending", 2)

        tasks = await store.get_tasks("wf-1")
        wave1 = [t for t in tasks if t["wave"] == 1]
        wave2 = [t for t in tasks if t["wave"] == 2]

        assert len(wave1) == 1
        assert len(wave2) == 2

    @pytest.mark.asyncio
    async def test_close(self, store):
        """测试关闭连接"""
        await store.close()
        # 验证可以再次操作而不报错
        result = await store.get_session("nonexistent")
        assert result is None
```

### 10.9 补充测试：DirectBackend

```python
# ===== DirectBackend 测试 =====

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tflow.agents.backends.direct import DirectBackend, DirectBackendConfig

@pytest.fixture
def backend():
    return DirectBackend(config=DirectBackendConfig(timeout=5))

class TestDirectBackend:
    """DirectBackend 单元测试"""

    @pytest.mark.asyncio
    async def test_execute_success(self, backend):
        """测试成功执行"""
        cmd = ["echo", "hello"]

        output_lines = []
        async for line in backend.execute(cmd):
            output_lines.append(line)

        assert len(output_lines) >= 1
        assert "hello" in output_lines[0]

    @pytest.mark.asyncio
    async def test_execute_with_stdin(self, backend):
        """测试带 stdin 的执行"""
        cmd = ["cat"]
        stdin_data = "test input"

        output_lines = []
        async for line in backend.execute(cmd, stdin_data=stdin_data):
            output_lines.append(line)

        assert any("test input" in line for line in output_lines)

    @pytest.mark.asyncio
    async def test_execute_timeout(self, backend):
        """测试超时处理"""
        backend.config.timeout = 1
        cmd = ["sleep", "10"]

        output_lines = []
        async for line in backend.execute(cmd):
            output_lines.append(line)

        assert any("timeout" in line.lower() for line in output_lines)

    def test_is_running_false_when_no_process(self, backend):
        """测试无进程时返回 False"""
        assert backend.is_running() is False

    @pytest.mark.asyncio
    async def test_kill(self, backend):
        """测试杀死进程"""
        cmd = ["sleep", "100"]
        # 启动一个长时间运行的进程
        task = asyncio.create_task(backend.execute(cmd))
        await asyncio.sleep(0.1)  # 让进程启动

        assert backend.is_running()
        await backend.kill()
        assert backend.is_running() is False
```

### 10.9.1 补充测试：TerminalBackend

```python
# ===== TerminalBackend 测试 =====

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tflow.agents.backends.terminal import TerminalBackend, TerminalBackendConfig

@pytest.fixture
def terminal_backend():
    return TerminalBackend(config=TerminalBackendConfig(
        session_name="tflow-test",
        keep_session=False,
        timeout=10,
    ))

class TestTerminalBackend:
    """TerminalBackend 单元测试"""

    def test_build_tmux_command(self, terminal_backend):
        """测试 tmux 命令构建"""
        cmd = ["echo", "hello"]
        tmux_cmd = terminal_backend._build_tmux_command(cmd)

        assert tmux_cmd[0] == "tmux"
        assert "new-session" in tmux_cmd
        assert "-d" in tmux_cmd
        assert "-s" in tmux_cmd
        assert "tflow-test" in tmux_cmd

    def test_build_tmux_command_with_socket(self, terminal_backend):
        """测试带 socket name 的 tmux 命令"""
        terminal_backend.config.socket_name = "test-socket"
        cmd = ["echo", "hello"]
        tmux_cmd = terminal_backend._build_tmux_command(cmd)

        assert "-L" in tmux_cmd
        assert "test-socket" in tmux_cmd

    @pytest.mark.asyncio
    async def test_send_input(self, terminal_backend):
        """测试发送输入到 session"""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value.wait = AsyncMock(return_value=0)

            await terminal_backend.send_input("tflow-test", "echo hello")

            assert mock_exec.called
            # 验证 send-keys 命令被调用
            call_args = mock_exec.call_args[0]
            assert "send-keys" in call_args

    @pytest.mark.asyncio
    async def test_kill_session(self, terminal_backend):
        """测试终止 session"""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value.wait = AsyncMock(return_value=0)

            await terminal_backend.kill_session("tflow-test")

            assert mock_exec.called
            call_args = mock_exec.call_args[0]
            assert "kill-session" in call_args
            assert "-t" in call_args

    @pytest.mark.asyncio
    async def test_cleanup_session(self, terminal_backend):
        """测试清理 session"""
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value.wait = AsyncMock(return_value=0)

            await terminal_backend._cleanup_session("tflow-test")

            assert mock_exec.called

    def test_session_id_tracking(self, terminal_backend):
        """测试 session ID 追踪"""
        assert terminal_backend._session_id is None
        terminal_backend._session_id = "tflow-test-123"
        assert terminal_backend._session_id == "tflow-test-123"
```
```

### 10.10 补充测试：JsonBroker

```python
# ===== JsonBroker 测试 =====

import pytest
from pathlib import Path
from tflow.broker.json_broker import JsonBroker, JsonBrokerConfig

@pytest.fixture
def json_broker(tmp_path):
    return JsonBroker(config=JsonBrokerConfig(data_dir=tmp_path))

class TestJsonBroker:
    """JsonBroker 单元测试"""

    @pytest.mark.asyncio
    async def test_save_and_get_job(self, json_broker, sample_job):
        """测试保存和获取 Job"""
        await json_broker.save_job(sample_job)
        result = await json_broker.get_job(sample_job.job_id)

        assert result is not None
        assert result.job_id == sample_job.job_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_job(self, json_broker):
        """测试获取不存在的 Job"""
        result = await json_broker.get_job("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_save_and_get_event(self, json_broker, sample_event):
        """测试保存和获取事件"""
        await json_broker.save_event(sample_event)

        events = await json_broker.get_events(job_id=sample_event.job_id)
        assert len(events) >= 1
        assert events[0].event_id == sample_event.event_id

    @pytest.mark.asyncio
    async def test_list_jobs_by_status(self, json_broker, sample_job):
        """测试按状态列出 Jobs"""
        await json_broker.save_job(sample_job)

        all_jobs = await json_broker.list_jobs()
        queued_jobs = await json_broker.list_jobs(status="queued")

        assert len(all_jobs) >= 1
        assert len(queued_jobs) >= 1

    @pytest.mark.asyncio
    async def test_file_rotation(self, json_broker, sample_event):
        """测试文件轮转"""
        json_broker.config.max_file_size = 100  # 小文件大小触发轮转

        # 写入多个事件
        for i in range(10):
            event = JobEvent(
                event_id=i,
                sequence=i,
                job_id=f"job-{i}",
                type="test",
                created_at="2024-01-01T00:00:00",
            )
            await json_broker.save_event(event)

        # 验证文件被轮转
        events_dir = json_broker.config.data_dir / "events"
        rotated_files = list(events_dir.glob("job-0_*.jsonl"))
        assert len(rotated_files) >= 1
```

### 10.11 补充测试：RealtimeBridge

```python
# ===== RealtimeBridge 测试 =====

import pytest
import asyncio
from tflow.realtime.bridge import RealtimeBridge, RealtimeBridgeConfig, EventDelivery

@pytest.fixture
def bridge():
    return RealtimeBridge(config=RealtimeBridgeConfig(
        delivery=EventDelivery.SSE,
        heartbeat_interval=60,
    ))

class TestRealtimeBridge:
    """RealtimeBridge 单元测试"""

    @pytest.mark.asyncio
    async def test_publish_and_subscribe(self, bridge):
        """测试发布和订阅"""
        received = []

        async def collector(event):
            received.append(event)

        # 订阅
        async def subscribe():
            async for event in bridge.subscribe("session-1"):
                await collector(event)

        sub_task = asyncio.create_task(subscribe())

        # 发布事件
        await bridge.publish("session-1", "test_event", {"data": "value"})

        # 等待事件处理
        await asyncio.sleep(0.1)

        assert len(received) >= 1
        assert received[0].type == "test_event"

        # 清理
        sub_task.cancel()
        try:
            await sub_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_broadcast(self, bridge):
        """测试广播"""
        received_count = 0

        async def counter1(event):
            nonlocal received_count
            received_count += 1

        async def counter2(event):
            nonlocal received_count
            received_count += 1

        # 创建两个订阅
        bridge._subscribers["session-1"] = []
        bridge._subscribers["session-2"] = []

        q1 = asyncio.Queue()
        q2 = asyncio.Queue()
        bridge._subscribers["session-1"].append(q1)
        bridge._subscribers["session-2"].append(q2)

        # 广播
        await bridge.broadcast("global_event", {"info": "test"})

        # 等待广播
        await asyncio.sleep(0.1)

        # 验证两个订阅者都收到
        assert not q1.empty() or not q2.empty()

    @pytest.mark.asyncio
    async def test_heartbeat(self, bridge):
        """测试心跳"""
        bridge.config.heartbeat_interval = 1
        await bridge.start()

        heartbeat_received = []

        async def collect_heartbeat():
            async for event in bridge.subscribe("heartbeat-test"):
                heartbeat_received.append(event)

        task = asyncio.create_task(collect_heartbeat())
        await asyncio.sleep(2.5)  # 等待至少2个心跳

        await bridge.stop()
        task.cancel()

        # 验证收到心跳
        assert len(heartbeat_received) >= 2
```

### 10.12 补充测试：DelegateBroker

```python
# ===== DelegateBroker 测试 =====

import pytest
from pathlib import Path
from tflow.delegate.broker import DelegateBroker, DelegateStatus, DelegateTask

@pytest.fixture
def broker(tmp_path):
    return DelegateBroker(data_dir=tmp_path / "delegates")

class TestDelegateBroker:
    """DelegateBroker 单元测试"""

    @pytest.mark.asyncio
    async def test_create_task(self, broker):
        """测试创建任务"""
        task = await broker.create_task(
            task_id="task-001",
            agent_type="claude",
            prompt="Analyze this code",
        )

        assert task.task_id == "task-001"
        assert task.agent_type == "claude"
        assert task.status == DelegateStatus.PENDING

    @pytest.mark.asyncio
    async def test_update_status(self, broker):
        """测试更新任务状态"""
        task = await broker.create_task(
            task_id="task-001",
            agent_type="claude",
            prompt="test",
        )

        updated = await broker.update_status(
            task_id="task-001",
            status=DelegateStatus.IN_PROGRESS,
            result={"output": "done"},
        )

        assert updated.status == DelegateStatus.IN_PROGRESS
        assert updated.result["output"] == "done"

    @pytest.mark.asyncio
    async def test_get_task(self, broker):
        """测试获取任务"""
        await broker.create_task(
            task_id="task-001",
            agent_type="claude",
            prompt="test",
        )

        task = await broker.get_task("task-001")
        assert task is not None
        assert task.task_id == "task-001"

    @pytest.mark.asyncio
    async def test_list_tasks_by_status(self, broker):
        """测试按状态列出任务"""
        await broker.create_task("task-1", "claude", "test 1")
        await broker.create_task("task-2", "gemini", "test 2")

        await broker.update_status("task-1", DelegateStatus.IN_PROGRESS)

        pending = await broker.list_tasks(status=DelegateStatus.PENDING)
        in_progress = await broker.list_tasks(status=DelegateStatus.IN_PROGRESS)

        assert len(pending) == 1
        assert len(in_progress) == 1

    @pytest.mark.asyncio
    async def test_cancel_task(self, broker):
        """测试取消任务"""
        await broker.create_task(
            task_id="task-001",
            agent_type="claude",
            prompt="test",
        )

        result = await broker.cancel_task("task-001")
        assert result is True

        task = await broker.get_task("task-001")
        assert task.status == DelegateStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_completed_fails(self, broker):
        """测试取消已完成任务失败"""
        await broker.create_task(
            task_id="task-001",
            agent_type="claude",
            prompt="test",
        )
        await broker.update_status("task-001", DelegateStatus.COMPLETED)

        result = await broker.cancel_task("task-001")
        assert result is False

    @pytest.mark.asyncio
    async def test_subscribe_callback(self, broker):
        """测试订阅回调"""
        received = []

        async def callback(event_type, task):
            received.append((event_type, task))

        await broker.subscribe(callback)

        task = await broker.create_task(
            task_id="task-001",
            agent_type="claude",
            prompt="test",
        )

        await asyncio.sleep(0.1)
        assert len(received) >= 1
```

### 10.13 Edge Cases 测试设计

```python
# ===== 通用 Edge Cases 测试 =====

class TestEdgeCases:
    """边界条件和异常情况测试"""

    # None/空值测试
    @pytest.mark.asyncio
    async def test_null_handling(self, executor, run_options):
        """测试 None 值处理"""
        run_options.prompt = None  # 边界情况
        # 验证代码正确处理或抛出明确错误

    def test_empty_command_list(self, executor):
        """测试空命令列表"""
        options = RunOptions(
            prompt="test",
            tool=AgentType.CLAUDE_CODE,
            mode=ExecutionMode.ANALYSIS,
            work_dir=Path("/tmp"),
        )
        # 空列表应抛出明确错误
        with pytest.raises(ValueError):
            executor._build_command(AgentType.CLAUDE_CODE, "", options)

    # 无效类型测试
    @pytest.mark.asyncio
    async def test_invalid_status_update(self, job_manager):
        """测试无效状态更新"""
        job = await job_manager.create_job(job_type="test")
        # 无效状态值应抛出错误
        with pytest.raises((ValueError, TypeError)):
            await job_manager.update_status(
                job.job_id,
                status="invalid_status",  # 必须是 JobStatus 枚举
                event_type="test",
            )

    # 并发测试
    @pytest.mark.asyncio
    async def test_concurrent_updates(self, job_manager):
        """测试并发状态更新"""
        job = await job_manager.create_job(job_type="test")

        async def update():
            await job_manager.update_status(job.job_id, JobStatus.RUNNING, "start")

        # 并发更新应不抛异常
        await asyncio.gather(*[update() for _ in range(10)])

    # 数据库错误恢复
    @pytest.mark.asyncio
    async def test_database_error_recovery(self, job_manager, monkeypatch):
        """测试数据库错误恢复"""
        original_connect = sqlite3.connect

        def mock_connect(*args, **kwargs):
            raise sqlite3.DatabaseError("Simulated error")

        monkeypatch.setattr("sqlite3.connect", mock_connect)

        with pytest.raises(sqlite3.DatabaseError):
            await job_manager.create_job(job_type="test")
```

### 10.14 测试执行指南

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定模块测试
pytest tests/test_executor.py -v
pytest tests/test_workflow_engine.py -v

# 运行带覆盖率报告
pytest tests/ --cov=src/tflow --cov-report=html

# 运行异步测试
pytest tests/ -v --asyncio-mode=auto

# 运行特定标记的测试
pytest tests/ -v -m "not slow"

# 生成测试报告
pytest tests/ --html=report.html --self-contained-html
```

---

## 十一、实施优先级

### Phase 1: 核心框架（高优先级）

| 顺序 | 任务 | 说明 |
|------|------|------|
| 1 | 修复 broker 模块 | 创建 `persistence.py`、`json_broker.py` |
| 2 | 实现 AgentExecutor | 统一执行器 |
| 3 | 实现 JobManager | 状态机 + Broker |
| 4 | 创建 CLI 入口 | `__main__.py` |

### Phase 2: 工作流引擎（中优先级）

| 顺序 | 任务 | 说明 |
|------|------|------|
| 5 | 实现 WorkflowEngine | 简单状态机 |
| 6 | 实现 WorkflowState | 状态定义和持久化 |
| 7 | 创建内置工作流模板 | 标准测试流程 |

### Phase 3: 扩展功能（低优先级）

| 顺序 | 任务 | 说明 |
|------|------|------|
| 8 | 实现 MCP Server | MCP 协议支持 |
| 9 | 添加 RealtimeBridge | WebSocket 实时事件 |
| 10 | 实现 SpecLoader | 规范系统 |

---

## 十二、技术选型

| 层级 | 技术选型 | 理由 |
|------|---------|------|
| API 框架 | FastAPI / orjson | 高性能、自动 OpenAPI 文档 |
| 异步框架 | asyncio + trio | 结构化并发 |
| 数据库 | SQLite (dev) / PostgreSQL (prod) | 零配置 / 企业级 |
| 实时通信 | WebSocket + SSE | 浏览器友好 |
| MCP 协议 | mcp-python-sdk | 官方 SDK |
| 配置管理 | Pydantic Settings | 类型安全 |
| 日志 | structlog | 结构化日志 |
| 进程管理 | subprocess (std) / pyte (terminal) | 进程隔离 / 终端模拟 |

---

## 十三、文件创建清单

```
src/tflow/
├── __main__.py               # CLI 入口
├── core/
│   ├── executor.py           # AgentExecutor
│   ├── job_manager.py        # JobManager
│   ├── session.py            # Session 管理
│   └── events.py             # 事件定义
├── broker/
│   ├── persistence.py        # BrokerPersistence 基类
│   └── json_broker.py        # JsonBroker 实现
├── agents/
│   ├── base.py              # BaseAgent
│   ├── registry.py           # AgentRegistry
│   └── backends/
│       ├── direct.py         # DirectBackend
│       └── terminal.py       # TerminalBackend
├── workflow/                  # 简单状态机
│   ├── engine.py            # WorkflowEngine
│   ├── state.py             # WorkflowState 状态定义
│   └── persistence.py       # 会话持久化
├── delegate/
│   ├── broker.py            # DelegateBroker
│   └── session.py            # 会话管理
├── spec/
│   └── loader.py            # SpecLoader
├── storage/
│   ├── jsonl_store.py       # JSONL 存储
│   └── sqlite_store.py      # SQLite 存储
└── realtime/
    └── bridge.py             # RealtimeBridge
```

---

## 十四、参考来源

- Maestro-Flow 后端源码: `/home/eeric/code/maestro-flow/src/`
- tflow 现状分析: `/home/eeric/code/testing-flow/src/tflow/`
- DelegateBroker 实现: `/home/eeric/code/maestro-flow/src/async/delegate-broker.ts`
- CliAgentRunner 实现: `/home/eeric/code/maestro-flow/src/agents/cli-agent-runner.ts`
