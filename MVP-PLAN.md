# Testing-Flow MVP 学习版计划 (v4)

> 基于 maestro-flow 架构的 Python 简化实现
>
> **版本**: v4 (基于 maestro-quick 兼容性分析修订)
> **创建日期**: 2026-05-02
> **评审状态**: 已修复 6 个阻断性问题

---

## 评审反馈摘要 (v3 → v4)

| 问题类型 | 具体问题 | 修复措施 |
|---------|---------|---------|
| **HIGH** | Node 类型比较失败 (`"terminal"` vs `NodeType.TERMINAL`) | NodeType 枚举使用字符串值 |
| **HIGH** | 命令字段名错误 (`command` vs `cmd`) | `node.config.get("cmd")` |
| **HIGH** | 下一节点获取逻辑 (edges vs `config["next"]`) | 优先从 `node.config["next"]` 获取 |
| **HIGH** | 图文件路径 (`graphs/` vs `chains/singles/`) | 支持多路径搜索 |
| **MED** | 起始节点硬编码 `"start"` | 使用 `graph.entry` |
| **MED** | 枚举值与 JSON 字符串不匹配 | NodeType 枚举使用字符串值 |

| 问题类型 | 具体问题 | 修复措施 |
|---------|---------|---------|
| **链路断裂** | Command 执行缺少 CliExecutor | 新增 `CliExecutor` 类 |
| **链路断裂** | Walker ↔ Broker 缺少适配层 | 新增 `CoordinatorAdapter` |
| **链路断裂** | Broker → MCP 缺少桥接 | 新增 `ChannelRelay` |
| **链路断裂** | 结果解析缺失 | 新增 `OutputParser` |
| **链路断裂** | 并行执行缺失 | 新增 `ParallelRunner` |
| **入口错误** | CLI 用文件路径 | 改为 `coordinate <graph-id>` |
| **事件流反转** | Client poll Broker | 修正为 Agent push → poll |
| **接口不匹配** | GraphWalker 接口 | 改为 `start()` / `walk()` / `get_state()` |

---

## 1. 核心架构 (修订版)

### 1.1 完整执行链路

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户入口                                  │
│              python -m mvp.cli coordinate my-flow               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  CLI Layer (cli.py)                                              │
│  - parse: coordinate <graph-id>                                  │
│  - resolve: graph-id → file path                                  │
│  - delegate to GraphWalker                                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  CoordinatorAdapter (coordinator_adapter.py)                      │
│  - register_session() → Broker                                   │
│  - create_channel()                                              │
│  - expose: run_job(), publish_event(), poll_events()            │
└────────────────────────────┬────────────────────────────────────┘
                             │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────┐ ┌───────────────┐ ┌─────────────────┐
│  GraphLoader    │ │  GraphWalker  │ │   Broker        │
│  - load(id)     │ │  - start()    │ │   - Session     │
│  - parse graph  │ │  - walk()     │ │   - Job         │
└─────────────────┘ │  - get_state()│ │   - Events      │
                    └───────┬───────┘ └───────┬───────┘
                            │                   │
                            │                   │
                            ▼                   ▼
              ┌───────────────────────┐ ┌───────────────────────┐
              │     CliExecutor       │ │   ChannelRelay        │
              │  (cli_executor.py)    │ │ (channel_relay.py)    │
              │                       │ │                       │
              │  - execute(cmd)       │ │  - poll_events()      │
              │  - subprocess spawn   │ │  - forward to MCP     │
              │  - parse output       │ │                       │
              └───────────────────────┘ └───────────────────────┘
                            │                   │
                            ▼                   ▼
              ┌───────────────────────┐ ┌───────────────────────┐
              │   Agent (subprocess)  │ │    MCP Server         │
              │   echo / shell cmd    │ │    (stdio)             │
              └───────────────────────┘ └───────────────────────┘
```

### 1.2 模块对应关系 (完整版)

| testing-flow (Python) | maestro-flow (TypeScript) | 必要性 |
|----------------------|---------------------------|--------|
| `cli.py` | `src/cli.ts` + `src/commands/coordinate.ts` | 核心 |
| `coordinator_adapter.py` | `src/coordinator/coordinate-broker-adapter.ts` | **新增** |
| `broker.py` | `src/async/delegate-broker.ts` | 核心 |
| `channel_relay.py` | `src/mcp/delegate-channel-relay.ts` | **新增** |
| `graph/loader.py` | `src/coordinator/graph-loader.ts` | 核心 |
| `graph/walker.py` | `src/coordinator/graph-walker.ts` | 核心 |
| `graph/cli_executor.py` | `src/coordinator/cli-executor.ts` | **新增** |
| `graph/output_parser.py` | `src/coordinator/output-parser.ts` | **新增** |
| `graph/parallel_runner.py` | `src/agents/parallel-cli-runner.ts` | **新增** |
| `graph/evaluator.py` | `src/coordinator/expr-evaluator.ts` | 核心 |
| `mcp/server.py` | `src/mcp/server.ts` | 核心 |
| `tools/registry.py` | `src/core/tool-registry.ts` | 核心 |

---

## 2. 数据模型

### 2.1 Session / Job / Event

```python
# session.py
@dataclass
class Session:
    id: str                    # sess_{timestamp}_{random}
    task_type: str             # "coordinate"
    status: SessionStatus       # ACTIVE / COMPLETED / FAILED / CANCELLED
    created_at: float
    last_heartbeat: float
    context: dict               # 跨 Job 共享上下文

# job.py
@dataclass
class Job:
    id: str                    # job_{timestamp}_{random}
    session_id: str            # 所属 Session
    agent_type: str            # "echo" | "shell"
    prompt: str                # 执行指令
    status: JobStatus          # QUEUED / RUNNING / COMPLETED / FAILED / CANCELLED / INPUT_REQUIRED
    created_at: float
    started_at: Optional[float]
    completed_at: Optional[float]
    output: Optional[str]
    error: Optional[str]

# event.py
@dataclass
class JobEvent:
    id: str
    job_id: str
    session_id: str
    event_type: str            # "queued" | "started" | "completed" | "failed"
    timestamp: float
    data: dict
    acked: bool = False
```

### 2.2 Graph 结构

```python
# graph/types.py
@dataclass
class Graph:
    id: str
    name: str
    version: str
    nodes: dict[str, Node]
    edges: list[Edge]
    entry: Optional[str] = None  # 起始节点 ID，与 maestro-flow 一致

@dataclass
class Node:
    id: str
    type: NodeType             # COMMAND / DECISION / FORK / JOIN / GATE / EVAL / TERMINAL
    config: dict

@dataclass
class Edge:
    from_: str                 # 源节点 ID
    to: str                    # 目标节点 ID
    condition: Optional[dict]  # {"expr": "choice == 'A'"} 或 None

# 节点类型枚举 (使用字符串值，与 JSON 图文件一致)
class NodeType(str, Enum):
    COMMAND = "command"
    DECISION = "decision"
    FORK = "fork"
    JOIN = "join"
    GATE = "gate"
    EVAL = "eval"
    TERMINAL = "terminal"

# 注意: NodeType 继承 str + Enum，确保与 JSON 字符串直接比较
# 例如: node.type == "terminal" 和 node.type == NodeType.TERMINAL 都成立
```

---

### GraphLoader (多路径支持)

```python
# graph/loader.py
class GraphLoader:
    """
    图加载器

    支持多种文件路径格式：
    - chains/singles/{id}.json  (maestro-flow 默认格式)
    - graphs/{id}.json
    - {id}.json

    对应 maestro-flow: src/coordinator/graph-loader.ts
    """

    def load(self, graph_id: str) -> Graph:
        """
        加载图文件

        Args:
            graph_id: 图 ID (如 "quick", "singles/quick")

        Returns:
            Graph: 解析后的图结构
        """
        # 尝试多个路径
        paths = [
            f"chains/singles/{graph_id}.json",
            f"chains/singles/{graph_id}.json",
            f"graphs/{graph_id}.json",
            f"{graph_id}.json",
        ]

        for path in paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                return self._parse(data)

        raise FileNotFoundError(f"Graph not found: {graph_id}")

    def _parse(self, data: dict) -> Graph:
        """解析图数据"""
        nodes = {}
        for node_id, node_data in data.get("nodes", {}).items():
            nodes[node_id] = Node(
                id=node_id,
                type=node_data.get("type", "command"),
                config=node_data.get("config", {}) or node_data  # 兼容不同格式
            )

        edges = []
        for edge in data.get("edges", []):
            edges.append(Edge(
                from_=edge.get("from"),
                to=edge.get("to"),
                condition=edge.get("condition")
            ))

        return Graph(
            id=data.get("id", ""),
            name=data.get("name", ""),
            version=data.get("version", "1.0"),
            nodes=nodes,
            edges=edges,
            entry=data.get("entry")  # 起始节点
        )
```

---

## 3. 核心模块详解

### Phase 1: Broker (Day 1)

#### 3.1 Broker 接口

```python
# broker.py
class Broker(ABC):
    """异步任务生命周期管理器"""

    # Session 管理
    def create_session(self, task_type: str, context: dict = None) -> Session: ...
    def get_session(self, session_id: str) -> Optional[Session]: ...
    def session_heartbeat(self, session_id: str) -> Session: ...

    # Job 管理
    def create_job(self, session_id: str, agent_type: str, prompt: str) -> Job: ...
    def get_job(self, job_id: str) -> Optional[Job]: ...
    def job_heartbeat(self, job_id: str) -> Job: ...
    def update_job(self, job_id: str, **updates) -> Job: ...
    def request_cancel(self, job_id: str) -> Job: ...

    # 事件系统 (核心！)
    def publish_event(self, job_id: str, event_type: str, data: dict = None) -> JobEvent: ...
    def poll_events(self, session_id: str, since: float = 0) -> list[JobEvent]: ...
    def ack_events(self, event_ids: list[str]) -> int: ...

    # 消息队列
    def queue_message(self, job_id: str, content: str, delivery: str = "inject") -> QueuedMessage: ...
    def get_pending_messages(self, job_id: str) -> list[QueuedMessage]: ...

    # 超时管理
    def check_timeouts(self, max_idle: float = 300) -> list[Job]: ...
    def purge_expired_events(self, max_age: float = 86400) -> int: ...
```

#### 3.2 事件流 (修正版)

```
Agent (CliExecutor)                          Client (ChannelRelay)
      │                                            │
      │  1. job_heartbeat()                        │
      │────────────────────────────────────────────▶│
      │                                            │
      │  2. publish_event("started", {...})        │
      │────────────────────────────────────────────▶│ 事件写入 broker
      │                                            │
      │  3. ... 执行中 ...                          │
      │                                            │
      │  4. publish_event("completed", {output})   │
      │────────────────────────────────────────────▶│
      │                                            │
      │                       5. poll_events(since)
      │◀────────────────────────────────────────────│
      │                       6. [events...]
      │────────────────────────────────────────────▶│
      │                       7. ack([event_ids])  │
      │◀────────────────────────────────────────────│
```

**关键点**：
- Agent (CliExecutor) 主动调用 `publish_event()` **推送** 事件
- Client (ChannelRelay) 主动调用 `poll_events()` **拉取** 事件
- `ack()` 确保事件不重复投递

---

### Phase 2: CoordinatorAdapter (Day 2)

#### 3.3 CoordinatorAdapter (新增核心模块)

```python
# coordinator_adapter.py
class CoordinatorAdapter:
    """
    GraphWalker 与 Broker 之间的适配层

    封装了：
    1. Session 注册与管理
    2. Job 创建与状态更新
    3. 事件发布与轮询
    4. 消息队列操作

    对应 maestro-flow: src/coordinator/coordinate-broker-adapter.ts
    """

    def __init__(self, broker: Broker):
        self.broker = broker
        self.session: Optional[Session] = None
        self.job_map: dict[str, Job] = {}  # node_id → Job

    def start(self, task_type: str = "coordinate") -> Session:
        """启动协调会话"""
        self.session = self.broker.create_session(task_type)
        return self.session

    def run_command(self, node_id: str, command: str, agent_type: str = "shell") -> Job:
        """
        执行 Command 节点

        对应原系统的 CliExecutor.execute()
        """
        job = self.broker.create_job(
            session_id=self.session.id,
            agent_type=agent_type,
            prompt=command
        )
        self.job_map[node_id] = job
        return job

    def get_result(self, job_id: str) -> str:
        """获取 Job 执行结果"""
        job = self.broker.get_job(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        return job.output or job.error or ""

    def get_node_result(self, node_id: str) -> str:
        """获取节点执行结果 (通过 node_id 查找)"""
        job = self.job_map.get(node_id)
        if not job:
            return ""
        return self.get_result(job.id)

    def check_complete(self, job_id: str) -> bool:
        """检查 Job 是否完成"""
        job = self.broker.get_job(job_id)
        return job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]

    def poll_for_complete(self, job_id: str, timeout: float = 60) -> Job:
        """等待 Job 完成 (轮询)"""
        start = time.time()
        while time.time() - start < timeout:
            job = self.broker.get_job(job_id)
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                return job
            time.sleep(0.1)
        raise TimeoutError(f"Job {job_id} timed out")
```

---

### Phase 3: CliExecutor (Day 2-3)

#### 3.4 CliExecutor (新增核心模块)

```python
# graph/cli_executor.py
class CliExecutor:
    """
    Command 节点执行器

    核心职责：
    1. 接收 Command 节点配置
    2. 执行命令 (subprocess)
    3. 解析输出

    对应 maestro-flow: src/coordinator/cli-executor.ts
    """

    def __init__(self, adapter: CoordinatorAdapter):
        self.adapter = adapter

    def execute(self, node: Node, assemble_request: dict = None) -> ExecResult:
        """
        执行单个 Command 节点

        Args:
            node: Command 节点
            assemble_request: 可选的请求组装参数

        Returns:
            ExecResult: { success: bool, output: str, error: str }
        """
        # 关键：使用 "cmd" 字段获取命令 (与 maestro-flow quick.json 一致)
        command = node.config.get("cmd", "")
        agent_type = node.config.get("agent", "shell")

        # 通过 Adapter 创建 Job
        job = self.adapter.run_command(node.id, command, agent_type)

        # 等待执行完成
        try:
            completed_job = self.adapter.poll_for_complete(job.id, timeout=60)
        except TimeoutError:
            return ExecResult(success=False, output="", error="Timeout")

        # 解析输出
        output = completed_job.output or ""
        error = completed_job.error or ""

        # 解析为结构化结果 (简化版)
        parsed = self.parse_output(output, node.config)

        return ExecResult(
            success=completed_job.status == JobStatus.COMPLETED,
            output=parsed.get("output", output),
            error=error
        )

    def parse_output(self, raw_output: str, config: dict) -> dict:
        """
        解析命令输出

        对应 maestro-flow: src/coordinator/output-parser.ts
        """
        # 简化版：直接返回原始输出
        # 完整版会根据 config 的 output_schema 解析
        return {"output": raw_output}


@dataclass
class ExecResult:
    success: bool
    output: str
    error: str
```

#### 3.5 OutputParser (新增模块)

```python
# graph/output_parser.py
class OutputParser:
    """
    命令输出解析器

    将原始命令输出解析为结构化结果
    支持：JSON 输出解析、状态码检测、错误提取

    对应 maestro-flow: src/coordinator/output-parser.ts
    """

    @staticmethod
    def parse(raw_output: str, schema: dict = None) -> dict:
        """
        解析输出

        Args:
            raw_output: 原始输出
            schema: 可选的输出 schema

        Returns:
            dict: 解析后的结果
        """
        result = {"raw": raw_output, "output": raw_output}

        # 尝试 JSON 解析
        if raw_output.strip().startswith("{"):
            try:
                result = json.loads(raw_output)
            except json.JSONDecodeError:
                pass

        # 检测状态
        if "SUCCESS" in raw_output:
            result["status"] = "success"
        elif "FAILURE" in raw_output:
            result["status"] = "failure"

        return result

    @staticmethod
    def extract_error(output: str) -> Optional[str]:
        """提取错误信息"""
        # 简化版：查找 "Error:" 或 "ERROR:" 后的内容
        import re
        match = re.search(r'(?:Error|ERROR):\s*(.+?)(?:\n|$)', output)
        return match.group(1) if match else None
```

---

### Phase 4: GraphWalker (Day 3-4)

#### 3.6 GraphWalker (修正版)

```python
# graph/walker.py
class GraphWalker:
    """
    图遍历器

    状态机遍历 Graph 结构，执行各节点

    对应 maestro-flow: src/coordinator/graph-walker.ts
    """

    def __init__(self, adapter: CoordinatorAdapter, executor: CliExecutor):
        self.adapter = adapter
        self.executor = executor
        self.graph: Optional[Graph] = None
        self.context: dict = {}          # 执行上下文
        self.fork_state: dict = {}        # Fork/Join 状态
        self.current_node: Optional[str] = None

    def start(self, graph: Graph, intent: str = None, options: dict = None) -> dict:
        """
        启动图遍历

        Args:
            graph: 图结构
            intent: 用户意图 (用于 Decision 节点)
            options: 启动选项 { step_mode: bool, ... }

        Returns:
            dict: 最终上下文
        """
        self.graph = graph
        self.context = {"intent": intent, "results": {}}

        # 创建 Session
        self.adapter.start("coordinate")

        # 使用 graph.entry 作为起始节点，而非硬编码 "start"
        # 与 maestro-flow 一致: quick.json 的 entry 是 "quick"
        entry_node = getattr(graph, 'entry', None) or "start"
        self.walk(entry_node)

        return self.context

    def walk(self, start_node_id: str = "start"):
        """遍历图 (状态机)"""
        current = start_node_id

        while current and current != "terminal":
            self.current_node = current
            node = self.graph.nodes.get(current)

            if not node:
                raise ValueError(f"Node not found: {current}")

            # 状态机分发
            if node.type == NodeType.COMMAND:
                self._handle_command(node)
                current = self._get_next(current)

            elif node.type == NodeType.DECISION:
                current = self._handle_decision(node)

            elif node.type == NodeType.FORK:
                self._handle_fork(node)
                current = self._get_next(current)

            elif node.type == NodeType.JOIN:
                self._handle_join(node)
                current = self._get_next(current)

            elif node.type == NodeType.EVAL:
                self._handle_eval(node)
                current = self._get_next(current)

            elif node.type == NodeType.GATE:
                current = self._handle_gate(node)

            elif node.type == NodeType.TERMINAL:
                break

    def _handle_command(self, node: Node):
        """执行 Command 节点"""
        result = self.executor.execute(node)
        self.context["results"][node.id] = result

        # 发布事件
        job = self.adapter.job_map.get(node.id)
        if job:
            event_type = "completed" if result.success else "failed"
            self.adapter.broker.publish_event(job.id, event_type, {"output": result.output})

    def _handle_decision(self, node: Node) -> str:
        """执行 Decision 节点，返回下一节点 ID"""
        prompt = node.config.get("prompt", "")
        strategy = node.config.get("strategy", "expr")  # "expr" | "llm"

        if strategy == "expr":
            # 表达式策略：从 context 中获取决策变量
            choice = self.context.get(prompt.strip(), "A")
        else:
            # LLM 策略 (简化版用随机)
            choice = "A"

        self.context["last_decision"] = choice

        # 根据决策选择下一节点
        return self._get_next_with_condition(node.id, choice)

    def _handle_fork(self, node: Node):
        """执行 Fork 节点 - 并行执行分支"""
        branches = node.config.get("branches", [])
        strategy = node.config.get("strategy", "all")

        self.fork_state[node.id] = {
            "branches": {b: None for b in branches},
            "strategy": strategy,
            "pending": len(branches)
        }

        # 简化版：顺序执行分支
        # 完整版会并行执行
        for branch_id in branches:
            self.walk(branch_id)
            self.fork_state[node.id]["branches"][branch_id] = "done"

    def _handle_join(self, node: Node):
        """执行 Join 节点 - 等待分支完成"""
        wait_for = node.config.get("wait_for", [])
        strategy = node.config.get("strategy", "all")

        # 检查所有分支是否完成
        for branch_id in wait_for:
            if self.fork_state.get(branch_id) != "done":
                # 简化版：假设已经完成
                pass

    def _handle_gate(self, node: Node) -> str:
        """执行 Gate 节点 - 条件判断"""
        condition = node.config.get("when")  # e.g., "result.success"

        # 简化版：直接通过
        return self._get_next(node.id)

    def _handle_eval(self, node: Node):
        """执行 Eval 节点 - 表达式求值"""
        expr = node.config.get("expr", "")
        # 简化版：直接存储表达式
        self.context[node.id] = expr

    def _get_next(self, node_id: str) -> Optional[str]:
        """
        获取下一节点 (无条件)

        优先级：
        1. 优先从 node.config["next"] 获取 (与 maestro-flow quick.json 一致)
        2. 回退到 edges 列表查找
        """
        # 优先从 node.config["next"] 获取 (quick.json 使用这种方式)
        node = self.graph.nodes.get(node_id)
        if node and "next" in node.config:
            return node.config["next"]

        # 回退到 edges 列表
        for edge in self.graph.edges:
            if edge.from_ == node_id and edge.condition is None:
                return edge.to
        return None

    def _get_next_with_condition(self, node_id: str, choice: str) -> Optional[str]:
        """获取下一节点 (有条件)"""
        for edge in self.graph.edges:
            if edge.from_ == node_id and edge.condition:
                # 检查条件
                cond_expr = edge.condition.get("expr", "")
                if self._evaluate_condition(cond_expr, choice):
                    return edge.to
        return None

    def _evaluate_condition(self, expr: str, choice: str) -> bool:
        """评估条件表达式"""
        # 简化版：直接匹配
        if "choice == 'A'" in expr or 'choice == "A"' in expr:
            return choice == "A"
        if "choice == 'B'" in expr or 'choice == "B"' in expr:
            return choice == "B"
        return False

    def get_state(self) -> dict:
        """获取当前状态 (用于恢复)"""
        return {
            "current_node": self.current_node,
            "context": self.context,
            "fork_state": self.fork_state
        }

    def resume(self, state: dict):
        """从状态恢复"""
        self.current_node = state["current_node"]
        self.context = state["context"]
        self.fork_state = state["fork_state"]
```

---

### Phase 5: ParallelRunner (Day 4)

#### 3.7 ParallelRunner (新增模块)

```python
# graph/parallel_runner.py
class ParallelRunner:
    """
    并行执行器

    对应 maestro-flow: src/agents/parallel-cli-runner.ts
    """

    def __init__(self, adapter: CoordinatorAdapter):
        self.adapter = adapter

    def run_all(self, tasks: list[dict], strategy: str = "all") -> list[ExecResult]:
        """
        并行执行多个任务

        Args:
            tasks: [{"node_id": str, "command": str}, ...]
            strategy: "all" | "any" | "majority"

        Returns:
            list[ExecResult]: 所有任务的执行结果
        """
        import concurrent.futures

        results = []

        def run_single(task):
            job = self.adapter.run_command(task["node_id"], task["command"])
            completed = self.adapter.poll_for_complete(job.id, timeout=60)
            return ExecResult(
                success=completed.status == JobStatus.COMPLETED,
                output=completed.output or "",
                error=completed.error or ""
            )

        # 并行执行
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(tasks)) as executor:
            futures = {executor.submit(run_single, task): task for task in tasks}

            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

        return results

    def run_fork_node(self, node: Node) -> dict:
        """
        执行 Fork 节点

        对应原系统的 ParallelCliRunner + DefaultParallelExecutor
        """
        branches = node.config.get("branches", [])
        strategy = node.config.get("strategy", "all")

        # 构建任务列表
        tasks = []
        for branch_id in branches:
            branch_node = self.adapter.graph.nodes.get(branch_id)
            if branch_node and branch_node.type == NodeType.COMMAND:
                tasks.append({
                    "node_id": branch_id,
                    "command": branch_node.config.get("command", "")
                })

        # 并行执行
        results = self.run_all(tasks, strategy)

        return {
            "strategy": strategy,
            "results": {t["node_id"]: r for t, r in zip(tasks, results)}
        }
```

---

### Phase 6: ChannelRelay (Day 5)

#### 3.8 ChannelRelay (新增核心模块)

```python
# channel_relay.py
class ChannelRelay:
    """
    事件中继器

    职责：
    1. 轮询 Broker 的事件
    2. 转发给 MCP Server
    3. 发送 notifications/claude/channel 通知

    对应 maestro-flow: src/mcp/delegate-channel-relay.ts
    """

    def __init__(self, broker: Broker, mcp_server: 'MCPServer'):
        self.broker = broker
        self.mcp_server = mcp_server
        self.last_poll_time: float = 0
        self.running: bool = False

    def start(self, session_id: str):
        """启动中继"""
        self.running = True
        self.last_poll_time = time.time()

        while self.running:
            events = self.broker.poll_events(session_id, since=self.last_poll_time)

            for event in events:
                self._forward_event(event)

            if events:
                self.broker.ack_events([e.id for e in events])

            self.last_poll_time = time.time()
            time.sleep(0.5)  # 轮询间隔

    def stop(self):
        """停止中继"""
        self.running = False

    def _forward_event(self, event: JobEvent):
        """转发事件到 MCP"""
        # 发送 MCP notification
        notification = {
            "method": "notifications/claude/channel",
            "params": {
                "source": "maestro",
                "exec_id": event.job_id,
                "event_type": event.event_type,
                "status": event.data.get("status", ""),
                "timestamp": event.timestamp
            }
        }
        self.mcp_server.send_notification(notification)
```

---

### Phase 7: MCPServer (Day 5)

#### 3.9 MCPServer

```python
# mcp/server.py
class MCPServer:
    """
    MCP Server

    实现 JSON-RPC 2.0 协议
    提供 tools/list 和 tools/call 接口

    对应 maestro-flow: src/mcp/server.ts
    """

    def __init__(self, broker: Broker, registry: ToolRegistry):
        self.broker = broker
        self.registry = registry
        self.notification_handler = None
        self.channel_relay: Optional[ChannelRelay] = None

    def set_channel_relay(self, relay: ChannelRelay):
        """设置 ChannelRelay"""
        self.channel_relay = relay

    def send_notification(self, notification: dict):
        """发送通知 (到 stdout)"""
        print(json.dumps(notification), flush=True)

    def handle_request(self, request: dict) -> dict:
        """处理 JSON-RPC 请求"""
        method = request.get("method")
        req_id = request.get("id")
        params = request.get("params", {})

        try:
            if method == "tools/list":
                tools = self.registry.list_tools()
                return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools}}

            elif method == "tools/call":
                result = self.registry.call(params["name"], params.get("arguments", {}))
                return {"jsonrpc": "2.0", "id": req_id, "result": result}

            elif method == "ping":
                return {"jsonrpc": "2.0", "id": req_id, "result": {"pong": True}}

            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32603, "message": str(e)}
            }

    def run(self):
        """stdio 主循环"""
        while True:
            line = sys.stdin.readline()
            if not line:
                break

            request = json.loads(line.strip())
            response = self.handle_request(request)

            if response:  # notifications 没有 id
                print(json.dumps(response), flush=True)
```

---

### Phase 8: CLI (Day 6)

#### 3.10 CLI 入口

```python
# cli.py
import click

@click.group()
def cli():
    """Testing-Flow - 简单工作流编排系统"""
    pass

@cli.command()
@click.argument("graph_id")
@click.option("--intent", default=None, help="用户意图")
def coordinate(graph_id: str, intent: str):
    """
    协调执行工作流图

    GRAPH_ID: 图 ID (对应 graphs/<id>.json)
    """
    # 1. 解析 graph_id → 加载图
    graph = GraphLoader.load(graph_id)

    # 2. 创建适配器
    broker = JsonBroker()
    adapter = CoordinatorAdapter(broker)
    executor = CliExecutor(adapter)
    walker = GraphWalker(adapter, executor)

    # 3. 执行
    result = walker.start(graph, intent=intent)

    # 4. 输出结果
    click.echo(json.dumps(result, indent=2))

@cli.command()
@click.argument("prompt")
@click.option("--to", default="echo", help="Agent 类型")
@click.option("--mode", default="analysis", type=click.Choice(["analysis", "write"]))
def delegate(prompt: str, to: str, mode: str):
    """委托任务给 Agent"""
    broker = JsonBroker()
    adapter = CoordinatorAdapter(broker)

    session = adapter.start("delegate")
    job = broker.create_job(session.id, to, prompt)

    # 等待完成
    result = adapter.poll_for_complete(job.id)

    click.echo(result.output or result.error)

@cli.command()
def serve():
    """启动 MCP Server"""
    broker = JsonBroker()
    registry = ToolRegistry()
    registry.register_builtin_tools()
    server = MCPServer(broker, registry)

    # 可选：启动 ChannelRelay
    relay = ChannelRelay(broker, server)
    server.set_channel_relay(relay)

    click.echo("MCP Server started")
    server.run()

if __name__ == "__main__":
    cli()
```

---

## 4. 执行计划 (8天)

| Day | 任务 | 核心模块 |
|-----|------|---------|
| Day 1 | Broker 核心 | `broker.py` (Session/Job/Event + JSON 实现) |
| Day 2 | 适配层 + Executor | `coordinator_adapter.py` + `cli_executor.py` |
| Day 3 | GraphWalker 基础 | `graph/walker.py` (Command/Decision/Terminal) |
| Day 4 | Fork/Join/Parallel | `graph/fork_join.py` + `parallel_runner.py` |
| Day 5 | ChannelRelay + MCP | `channel_relay.py` + `mcp/server.py` |
| Day 6 | CLI + 集成 | `cli.py` + 端到端测试 |
| Day 7 | 完善 | `output_parser.py` + `evaluator.py` |
| Day 8 | 测试 + 文档 | 完整测试 + README |

---

## 5. 完整项目结构

```
testing-flow/
├── mvp/
│   ├── __init__.py
│   │
│   ├── broker.py                  # Day 1
│   │   ├── Session, Job, JobEvent 数据类
│   │   ├── Broker 抽象接口
│   │   └── JsonBroker 实现
│   │
│   ├── coordinator_adapter.py     # Day 2
│   │   └── CoordinatorAdapter
│   │
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── types.py               # Graph, Node, Edge, NodeType
│   │   ├── loader.py              # Day 3: GraphLoader
│   │   ├── walker.py             # Day 3: GraphWalker
│   │   ├── cli_executor.py       # Day 2: CliExecutor
│   │   ├── output_parser.py     # Day 7: OutputParser
│   │   ├── evaluator.py          # Day 7: ExprEvaluator
│   │   ├── fork_join.py          # Day 4: Fork/Join 处理
│   │   └── parallel_runner.py    # Day 4: ParallelRunner
│   │
│   ├── mcp/
│   │   ├── __init__.py
│   │   └── server.py             # Day 5: MCPServer
│   │
│   ├── channel_relay.py          # Day 5: ChannelRelay
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   └── registry.py           # ToolRegistry
│   │
│   └── cli.py                    # Day 6: CLI 入口
│
├── graphs/                        # 图定义文件
│   ├── simple.json               # 简单线性流程
│   ├── decision.json             # 条件分支
│   └── fork_join.json           # 并行分支
│
├── tests/
│   ├── test_broker.py
│   ├── test_graph_walker.py
│   ├── test_mcp_server.py
│   └── test_integration.py
│
└── README.md
```

---

## 6. 端到端测试场景

### 场景：执行 `python -m mvp.cli coordinate simple`

**完整流程**：

```
1. CLI 解析命令
   └─ coordinate("simple") → GraphLoader.load("simple")

2. 加载图 graphs/simple.json
   └─ Graph(id="simple", nodes={...}, edges=[...])

3. 创建 Session
   └─ adapter.start() → broker.create_session()

4. GraphWalker.start(graph)
   └─ adapter.start("coordinate")

5. 遍历图 start
   └─ walk("start")

6. 遇到 Command 节点 (start)
   └─ walker._handle_command(node)
       └─ executor.execute(node)
           └─ adapter.run_command(node.id, command)
               └─ broker.create_job(session.id, agent, prompt)
           └─ adapter.poll_for_complete(job.id)
               └─ (执行 subprocess echo)
           └─ 返回 ExecResult

7. 遇到 Decision 节点 (decide)
   └─ walker._handle_decision(node)
       └─ 选择路径 → "_get_next_with_condition()"

8. 遇到 Fork 节点 (fork_step)
   └─ walker._handle_fork(node)
       └─ parallel_runner.run_fork_node(node)
           └─ 并行执行 branch_1, branch_2

9. 遇到 Join 节点 (join)
   └─ walker._handle_join(node)
       └─ 等待所有分支完成

10. 遇到 Terminal 节点 (end)
    └─ walk() 结束

11. 返回 context
    └─ { intent: ..., results: {...} }
```

---

## 7. 验收标准

### 7.1 模块验收

| 模块 | 验收条件 |
|------|---------|
| `broker.py` | Session/Job/Event CRUD + 事件发布/轮询/确认 |
| `coordinator_adapter.py` | start() → run_command() → poll_for_complete() |
| `cli_executor.py` | execute(node) → ExecResult |
| `graph/walker.py` | start(graph) → walk() → context |
| `parallel_runner.py` | run_all(tasks) → list[ExecResult] |
| `channel_relay.py` | start() → poll_events() → forward |
| `mcp/server.py` | tools/list + tools/call |

### 7.2 端到端验收

```bash
# 1. 简单图
python -m mvp.cli coordinate simple
# 预期：输出 context 结果

# 2. 条件分支图
python -m mvp.cli coordinate decision --intent "选择 A"
# 预期：根据 intent 选择路径

# 3. 并行分支图
python -m mvp.cli coordinate fork_join
# 预期：并行执行分支，join 等待完成

# 4. MCP Server
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python -m mvp.cli serve &
# 预期：返回工具列表
```

---

## 8. 评审问题修复确认 (v3 → v4)

| 评审问题 | 修复措施 | 状态 |
|---------|---------|------|
| **v3 遗留问题** | | |
| [HIGH-1] CLI 入口路径错误 | 改为 `coordinate <graph-id>` | ✅ 已修复 |
| [HIGH-2] 缺少 CliExecutor | 新增 `graph/cli_executor.py` | ✅ 已修复 |
| [HIGH-3] 事件流方向反转 | 修正为 Agent push → poll | ✅ 已修复 |
| **v4 新发现问题** | | |
| Node 类型比较失败 | `NodeType(str, Enum)` 使用字符串值 | ✅ 已修复 |
| 命令字段名错误 | `node.config.get("cmd")` | ✅ 已修复 |
| 下一节点获取逻辑 | 优先 `config["next"]`，回退 edges | ✅ 已修复 |
| 图文件路径不匹配 | GraphLoader 多路径搜索 | ✅ 已修复 |
| 起始节点硬编码 | 使用 `graph.entry` | ✅ 已修复 |
| **待完善功能** | | |
| Terminal delegate_graph | 增加 `delegate_graph` 支持 | ⏳ 可选 |
| Hooks 数量 | 简化为 4 个核心钩子 | ⏳ 可选 |

---

## 9. maestro-quick 执行验证

### quick.json 结构

```json
{
  "id": "singles/quick",
  "entry": "quick",
  "nodes": {
    "quick": { "type": "command", "cmd": "maestro-quick", "next": "done" },
    "done": { "type": "terminal", "status": "success" }
  }
}
```

### MVP 执行链路验证

| 步骤 | MVP 实现 | quick.json 字段 | 状态 |
|------|---------|-----------------|------|
| GraphLoader.load("quick") | 多路径搜索 chains/singles/ | - | ✅ |
| graph.entry | Graph.entry = "quick" | entry: "quick" | ✅ |
| Node.type 比较 | `NodeType(str, Enum)` | type: "command" | ✅ |
| 获取命令 | `node.config.get("cmd")` | cmd: "maestro-quick" | ✅ |
| 获取下一节点 | `node.config["next"]` | next: "done" | ✅ |
| Terminal 退出 | `node.type == "terminal"` | type: "terminal" | ✅ |

---

*计划版本: v4*
*修订日期: 2026-05-02*
*基于: maestro-quick 兼容性分析*
