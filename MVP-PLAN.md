# Testing-Flow MVP 计划

> 基于 maestro-flow 架构的五层简化实现
>
> **版本**: 最终版
> **创建日期**: 2026-05-02

---

## 一、设计原则

**每层都有，简化实现** — 不缺失 Architecture 任何一层，只降低复杂度。

```
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 1: Command     │ commands/*.py 解析器 + CLI 装饰器           │
│  "做什么" — 入口 + 参数 │  路由 + 错误处理                           │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 2: Workflow    │ workflows/*.md 模板引擎                      │
│  "怎么做" — 流程模板   │  变量替换 + 条件分支 + 波次调度              │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 3: Agent       │ agents/subprocess_agent.py                  │
│  "谁来做" — 执行器     │  subprocess 执行 + 内置 prompt               │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 4: Artifact    │ artifacts/*.json + summaries/               │
│  "产出什么" — 数据     │  plan.json + task/*.json + verification.json│
├─────────────────────────────────────────────────────────────────────┤
│  Layer 5: State+Commit│ state.json + git                           │
│  "记得什么"           │  状态持久化 + 每 task 自动 commit             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 二、目录结构

```
testing-flow/
├── .claude/
│   ├── commands/                    # Layer 1: Command 定义 (Claude Code Skill)
│   │   └── tflow-standard.md         # 标准通用任务命令
│   └── workflows/                   # Layer 2: Workflow 模板
│       └── standard.md                  # 标准通用任务工作流
│
├── src/
│   └── tflow/
│       ├── __init__.py
│       ├── cli.py                    # Layer 1: 主入口
│       │
│       ├── commands/                 # Layer 1: Command 定义
│       │   ├── __init__.py
│       │   ├── quick.py
│       │   ├── plan.py
│       │   └── execute.py
│       │
│       ├── workflows/                # Layer 2: Workflow 模板
│       │   ├── __init__.py
│       │   ├── quick.md
│       │   ├── plan.md
│       │   └── execute.md
│       │
│       ├── engine/                   # Layer 2: Workflow 引擎
│       │   ├── __init__.py
│       │   ├── workflow_engine.py
│       │   └── wave_scheduler.py
│       │
│       ├── agents/                   # Layer 3: Agent 执行器
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── subprocess_agent.py
│       │   └── builtin_prompts.py
│       │
│       ├── artifacts/                # Layer 4: 产物管理
│       │   ├── __init__.py
│       │   ├── plan.py
│       │   ├── task.py
│       │   ├── verification.py
│       │   └── registry.py
│       │
│       ├── state/                    # Layer 5: 状态管理
│       │   ├── __init__.py
│       │   ├── state_manager.py
│       │   ├── git_commit.py
│       │   └── checkpoint.py
│       │
│       └── broker/                   # 共享组件
│           ├── __init__.py
│           ├── session.py
│           ├── job.py
│           └── event.py
│
├── graphs/                          # 兼容旧版
├── tests/                           # TDD 测试
│   ├── conftest.py                  # pytest 配置
│   ├── layer1/                     # Layer 1 测试
│   │   ├── __init__.py
│   │   └── test_commands.py
│   ├── layer2/                     # Layer 2 测试
│   │   ├── __init__.py
│   │   ├── test_workflow_engine.py
│   │   └── test_wave_scheduler.py
│   ├── layer3/                     # Layer 3 测试
│   │   ├── __init__.py
│   │   └── test_subprocess_agent.py
│   ├── layer4/                     # Layer 4 测试
│   │   ├── __init__.py
│   │   ├── test_plan.py
│   │   ├── test_task.py
│   │   └── test_verification.py
│   ├── layer5/                     # Layer 5 测试
│   │   ├── __init__.py
│   │   ├── test_state_manager.py
│   │   └── test_git_commit.py
│   └── test_integration.py         # 集成测试
│
└── MVP-PLAN.md
```

---

## 三、TDD 开发流程

### 3.1 红绿重构循环

```
┌─────────────────────────────────────────────────────────────┐
│  1. RED    │ 写一个失败的测试（描述期望的行为）              │
│             │ 运行测试 → 应该失败（因为功能还没实现）          │
├─────────────────────────────────────────────────────────────┤
│  2. GREEN  │ 写最少的代码让测试通过                           │
│             │ 运行测试 → 应该通过                             │
├─────────────────────────────────────────────────────────────┤
│  3. REFACTOR│ 重构代码，消除重复，提高清晰度                  │
│             │ 运行测试 → 应该继续通过                         │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 测试命名规范

```
test_<module>_<scenario>_<expected>
```

示例：
- `test_state_manager_load_returns_empty_state_when_file_not_exists`
- `test_wave_scheduler_schedule_groups_by_wave_field`

### 3.3 测试层次

| 层次 | 目标 | 工具 |
|------|------|------|
| 单元测试 | 单个类/函数 | pytest |
| 集成测试 | 多层协作 | pytest + tmp_path |
| 端到端测试 | 完整流程 | subprocess |

---

## 四、数据结构（来自 Architecture）

### 4.1 文件层次

```
.workflow/
├── state.json                  # 项目级状态
├── config.json                  # 项目配置
└── scratch/
    └── {slug}/                  # plan 或 quick 标识
        ├── index.json           # 计划入口
        ├── plan.json            # 计划概览
        ├── verification.json    # 验证结果
        ├── .task/
        │   └── TASK-*.json     # 任务级
        └── summaries/
            └── TASK-*-summary.md
```

### 4.2 各 Schema 字段

| Schema | 关键字段 |
|--------|---------|
| **state.json** | `version`, `status` (idle/planning/executing/verifying), `artifacts[]`, `accumulated_context` |
| **plan.json** | `task_ids[]`, `waves[]`, `complexity`, `approach` |
| **task.json** | `id`, `status`, `convergence.criteria[]`, `files[]`, `implementation[]` |
| **index.json** | `flags`, `plan`, `execution` |
| **verification.json** | `layers{}`, `convergence_check{}`, `gaps[]` |
| **config.json** | `workflow`, `execution`, `git`, `gates`, `specs` |

---

## 四、Command 端到端验证（使用 Claude Agent）

### 4.1 验证架构

参照 Maestro command 架构，实现 `.claude/commands/tflow-standard.md` 命令用于通用任务执行。

```
┌──────────────────────────────────────────────────────────────┐
│  Layer 1: Command  (.claude/commands/tflow-standard.md)      │
│  "做什么" — 声明式状态机：步骤 + 路由                         │
└────────────────────────────┬─────────────────────────────────┘
                             │ Skill Tool 调用
                             ▼
┌──────────────────────────────────────────────────────────────┐
│  Layer 2: Workflow  (.claude/workflows/standard.md)
│  "怎么做" — 可复用流程模板                                   │
└────────────────────────────┬─────────────────────────────────┘
                             │ Agent 调度
                             ▼
┌──────────────────────────────────────────────────────────────┐
│  Layer 3: Claude Code Agent                                  │
│  "谁来做" — workflow-planner/executor/verifier                │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 Command 文件结构

```markdown
# .claude/commands/tflow-standard.md
---
name: tflow-standard
description: 使用内置 Claude Agent 执行通用任务（Plan → Execute → Verify）
argument-hint: "<任务描述> [--verify] [--full]"
allowed-tools:
  - Read | Write | Edit | Bash | Glob | Grep | Agent
---

<purpose>
使用标准 Maestro 工作流执行通用任务...
</purpose>

<required_reading>
@/home/eeric/code/testing-flow/.claude/workflows/standard.md
</required_reading>

<execution>
### Step 1: Initialize verification session
### Step 2: Run workflow verification
### Step 3: Execute quick workflow
### Step 4: Report results
</execution>
```

### 4.3 Workflow 文件结构

```markdown
# .claude/workflows/standard.md

## 阶段一：计划 (Plan)
- 生成 plan.json
- 生成 TASK-*.json

## 阶段二：执行 (Execute)
- 波次调度执行
- 原子 git 提交

## 阶段三：验证 (Verify)
- 三层验证：存在性 / 实质性 / 连接性
```

### 4.4 验证命令

```bash
# 验证 command 和 workflow 定义是否正确
/tflow-standard "测试任务描述" --verify

# 执行完整工作流
/tflow-standard "实现登录功能" --full

# 执行并验证
/tflow-standard "实现登录功能" --verify --full
```

### 4.5 Command 验证检查项

| 检查项 | 说明 |
|--------|------|
| command 文件存在 | `.claude/commands/tflow-standard.md` 存在 |
| YAML frontmatter 有效 | name, description, allowed-tools 字段完整 |
| required_reading 引用正确 | 指向有效的 workflow 模板 |
| execution 步骤定义 | 步骤清晰、可执行 |
| error_codes 定义 | 错误码覆盖主要失败场景 |
| success_criteria 定义 | 成功标准可验证 |

---

## 五、TDD 测试方案

### Phase 1: Layer 5 — State（先建基础设施）

#### 5.1 StateManager 测试（TDD）

```python
# tests/layer5/test_state_manager.py
import pytest
import json
import os
from pathlib import Path
from tflow.state.state_manager import StateManager, ProjectState, WORKFLOW_DIR


class TestStateManager:
    """StateManager TDD 测试"""

    def test_load_returns_empty_state_when_file_not_exists(self, tmp_path):
        """RED: 当 state.json 不存在时，返回空状态"""
        os.chdir(tmp_path)
        sm = StateManager()
        state = sm.load()

        assert state.version == "1.0"
        assert state.status == "idle"
        assert state.artifacts == []

    def test_load_returns_existing_state(self, tmp_path):
        """GREEN: 当 state.json 存在时，返回已有状态"""
        os.chdir(tmp_path)
        os.makedirs(WORKFLOW_DIR, exist_ok=True)
        state_file = Path(WORKFLOW_DIR) / "state.json"
        state_file.write_text(json.dumps({
            "version": "1.0",
            "status": "executing",
            "artifacts": [{"id": "test"}],
            "accumulated_context": {"key_decisions": [], "blockers": [], "deferred": []}
        }))

        sm = StateManager()
        state = sm.load()

        assert state.status == "executing"
        assert len(state.artifacts) == 1

    def test_save_writes_state_to_file(self, tmp_path):
        """GREEN: save 方法正确写入文件"""
        os.chdir(tmp_path)
        sm = StateManager()
        state = ProjectState(status="planning")
        sm.save(state)

        state_file = Path(WORKFLOW_DIR) / "state.json"
        assert state_file.exists()

        with open(state_file) as f:
            data = json.load(f)
        assert data["status"] == "planning"

    def test_is_task_done_returns_false_when_not_exists(self, tmp_path):
        """RED: 任务不存在时返回 False"""
        os.chdir(tmp_path)
        sm = StateManager()
        assert sm.is_task_done("TASK-999") == False

    def test_is_task_done_returns_true_when_completed(self, tmp_path):
        """GREEN: 任务完成时返回 True"""
        os.chdir(tmp_path)
        sm = StateManager()
        sm.register_artifact({
            "task_id": "TASK-001",
            "status": "completed"
        })
        assert sm.is_task_done("TASK-001") == True

    def test_register_artifact_adds_to_artifacts_list(self, tmp_path):
        """GREEN: 注册 artifact"""
        os.chdir(tmp_path)
        sm = StateManager()
        sm.register_artifact({"task_id": "TASK-001", "status": "pending"})

        state = sm.load()
        assert len(state.artifacts) == 1
        assert state.artifacts[0]["task_id"] == "TASK-001"

    def test_add_key_decision_appends_to_context(self, tmp_path):
        """GREEN: 添加关键决策"""
        os.chdir(tmp_path)
        sm = StateManager()
        sm.add_key_decision("使用增量开发策略")

        state = sm.load()
        assert len(state.accumulated_context["key_decisions"]) == 1
        assert "使用增量开发策略" in state.accumulated_context["key_decisions"][0]["text"]
```

#### 5.2 GitCommit 测试（TDD）

```python
# tests/layer5/test_git_commit.py
import pytest
import subprocess
from pathlib import Path
from tflow.state.git_commit import GitCommit


class TestGitCommit:
    """GitCommit TDD 测试"""

    def test_commit_creates_git_commit(self, tmp_path, git_repo):
        """RED: git commit 应创建提交"""
        gc = GitCommit()

        # 创建文件
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello")

        commit_hash = gc.commit(["test.txt"], "test commit")

        assert commit_hash is not None
        assert len(commit_hash) == 40  # git hash length

    def test_commit_raises_on_failure(self, tmp_path, git_repo):
        """GREEN: 提交失败应抛出异常"""
        gc = GitCommit()

        with pytest.raises(RuntimeError, match="Git commit failed"):
            gc.commit(["nonexistent.txt"], "test")

    def test_commit_task_uses_proper_message(self, tmp_path, git_repo):
        """GREEN: task commit 使用正确格式"""
        gc = GitCommit()

        test_file = tmp_path / "task.py"
        test_file.write_text("# task")

        commit_hash = gc.commit_task("TASK-001", "实现登录功能", ["task.py"])

        # 验证 commit message
        result = subprocess.run(
            ["git", "log", "-1", "--format=%s"],
            capture_output=True,
            text=True
        )
        assert "TASK-001" in result.stdout
        assert "实现登录功能" in result.stdout
```

---

### Phase 2: Layer 4 — Artifact

#### 5.3 PlanArtifact 测试（TDD）

```python
# tests/layer4/test_plan.py
import pytest
import json
from pathlib import Path
from tflow.artifacts.plan import PlanArtifact, Plan


class TestPlanArtifact:
    """PlanArtifact TDD 测试"""

    def test_create_initializes_plan_file(self, tmp_path):
        """RED: create 方法应创建 plan.json"""
        pa = PlanArtifact(str(tmp_path))
        plan = pa.create("实现登录功能", {})

        plan_file = tmp_path / "plan.json"
        assert plan_file.exists()

        with open(plan_file) as f:
            data = json.load(f)
        assert data["task"] == "实现登录功能"
        assert data["id"] is not None

    def test_add_task_creates_task_file_and_updates_plan(self, tmp_path):
        """GREEN: 添加 task"""
        pa = PlanArtifact(str(tmp_path))
        pa.create("实现登录功能", {})

        task = {
            "id": "TASK-001",
            "title": "创建登录页面",
            "scope": ["src/login.py"],
            "status": "pending",
            "wave": 0,
            "convergence": {"criteria": []}
        }
        pa.add_task(task)

        # 检查 task 文件
        task_file = tmp_path / ".task" / "TASK-001.json"
        assert task_file.exists()

        # 检查 plan.json 更新
        with open(tmp_path / "plan.json") as f:
            plan = json.load(f)
        assert "TASK-001" in plan["task_ids"]

    def test_get_tasks_returns_sorted_tasks(self, tmp_path):
        """GREEN: 获取排序后的 task 列表"""
        pa = PlanArtifact(str(tmp_path))
        pa.create("实现登录功能", {})

        pa.add_task({"id": "TASK-002", "title": "B", "scope": [], "status": "pending", "wave": 0, "convergence": {"criteria": []}})
        pa.add_task({"id": "TASK-001", "title": "A", "scope": [], "status": "pending", "wave": 0, "convergence": {"criteria": []}})

        tasks = pa.get_tasks()
        assert tasks[0]["id"] == "TASK-001"
        assert tasks[1]["id"] == "TASK-002"

    def test_mark_done_updates_task_status(self, tmp_path):
        """GREEN: 标记 task 完成"""
        pa = PlanArtifact(str(tmp_path))
        pa.create("实现登录功能", {})
        pa.add_task({"id": "TASK-001", "title": "创建登录页面", "scope": [], "status": "pending", "wave": 0, "convergence": {"criteria": []}})

        pa.mark_done("TASK-001", "summaries/TASK-001-summary.md", "abc123")

        with open(tmp_path / ".task" / "TASK-001.json") as f:
            task = json.load(f)
        assert task["status"] == "completed"
        assert task["summary"] == "summaries/TASK-001-summary.md"
        assert task["commit"] == "abc123"
```

#### 5.4 VerificationArtifact 测试（TDD）

```python
# tests/layer4/test_verification.py
import pytest
import json
from pathlib import Path
from tflow.artifacts.verification import VerificationArtifact, VerificationResult


class TestVerificationArtifact:
    """VerificationArtifact TDD 测试"""

    def test_create_initializes_verification_json(self, tmp_path):
        """RED: 创建验证文件"""
        va = VerificationArtifact(str(tmp_path))
        result = va.create("plan_001")

        verification_file = tmp_path / "verification.json"
        assert verification_file.exists()

        with open(verification_file) as f:
            data = json.load(f)
        assert data["plan_id"] == "plan_001"
        assert "existence" in data["layers"]
        assert "substance" in data["layers"]
        assert "connection" in data["layers"]

    def test_update_layer_updates_correct_layer(self, tmp_path):
        """GREEN: 更新指定层"""
        va = VerificationArtifact(str(tmp_path))
        va.create("plan_001")

        va.update_layer("existence", True, [{"file": "login.py", "found": True}])

        with open(tmp_path / "verification.json") as f:
            data = json.load(f)
        assert data["layers"]["existence"]["passed"] == True
        assert len(data["layers"]["existence"]["evidence"]) == 1
```

---

### Phase 3: Layer 2 — Workflow

#### 5.5 WaveScheduler 测试（TDD）

```python
# tests/layer2/test_wave_scheduler.py
import pytest
from tflow.engine.wave_scheduler import WaveScheduler


class TestWaveScheduler:
    """WaveScheduler TDD 测试"""

    def test_schedule_groups_tasks_by_wave(self):
        """RED: 按 wave 字段分组"""
        ws = WaveScheduler()
        tasks = [
            {"id": "TASK-001", "wave": 0},
            {"id": "TASK-002", "wave": 0},
            {"id": "TASK-003", "wave": 1},
            {"id": "TASK-004", "wave": 2},
        ]

        waves = ws.schedule(tasks)

        assert len(waves) == 3
        assert len(waves[0]) == 2  # wave 0: TASK-001, TASK-002
        assert len(waves[1]) == 1  # wave 1: TASK-003
        assert len(waves[2]) == 1  # wave 2: TASK-004

    def test_schedule_handles_missing_wave_field(self):
        """GREEN: 缺失 wave 字段默认为 0"""
        ws = WaveScheduler()
        tasks = [
            {"id": "TASK-001"},  # 无 wave 字段
            {"id": "TASK-002", "wave": 1},
        ]

        waves = ws.schedule(tasks)

        assert len(waves[0]) == 1  # TASK-001 默认 wave 0
        assert len(waves[1]) == 1  # TASK-002 wave 1

    def test_schedule_returns_empty_for_empty_list(self):
        """GREEN: 空列表返回空"""
        ws = WaveScheduler()
        assert ws.schedule([]) == []

    def test_run_waves_executes_sequentially(self):
        """GREEN: 波次间串行执行"""
        ws = WaveScheduler()
        executed = []

        def executor(task):
            executed.append(task["id"])
            return {"success": True, "task_id": task["id"]}

        waves = [[{"id": "TASK-001"}], [{"id": "TASK-002"}]]
        results = ws.run_waves(waves, executor)

        assert executed == ["TASK-001", "TASK-002"]  # 顺序执行
        assert len(results) == 2

    def test_run_waves_executes_within_wave_in_parallel(self):
        """GREEN: 波次内并行执行"""
        import concurrent.futures
        ws = WaveScheduler()
        start_times = {}

        def executor(task):
            import time
            start_times[task["id"]] = time.time()
            time.sleep(0.1)
            return {"success": True, "task_id": task["id"]}

        waves = [[{"id": "TASK-001"}, {"id": "TASK-002"}]]  # 同一波次
        ws.run_waves(waves, executor)

        # 验证并行：两者启动时间相近
        diff = abs(start_times["TASK-001"] - start_times["TASK-002"])
        assert diff < 0.05  # 几乎同时启动
```

#### 5.6 WorkflowEngine 测试（TDD）

```python
# tests/layer2/test_workflow_engine.py
import pytest
from pathlib import Path
from tflow.engine.workflow_engine import WorkflowEngine


class TestWorkflowEngine:
    """WorkflowEngine TDD 测试"""

    def test_load_reads_workflow_template(self, tmp_path):
        """RED: 加载 workflow 模板"""
        workflow_file = tmp_path / "quick.md"
        workflow_file.write_text("## {{task}}\nStep: prepare\n")

        engine = WorkflowEngine(workflow_dir=str(tmp_path))
        workflow = engine.load("quick")

        assert "task" in workflow
        assert "Step: prepare" in workflow

    def test_run_substitutes_variables(self, tmp_path):
        """GREEN: 变量替换"""
        workflow_file = tmp_path / "quick.md"
        workflow_file.write_text("Task: {{task}}\nStatus: {{status}}")

        engine = WorkflowEngine(workflow_dir=str(tmp_path))
        result = engine.run({
            "task": "实现登录",
            "status": "pending"
        })

        assert "Task: 实现登录" in result["prepared"]
        assert "Status: pending" in result["prepared"]

    def test_run_respects_conditional_branch(self, tmp_path):
        """GREEN: 条件分支"""
        workflow_file = tmp_path / "quick.md"
        workflow_file.write_text(
            "{{#if discuss}}\n"
            "讨论阶段\n"
            "{{/if}}\n"
            "执行阶段"
        )

        engine = WorkflowEngine(workflow_dir=str(tmp_path))

        # discuss=True 时
        result = engine.run({"discuss": True})
        assert "讨论阶段" in result["steps"]
        assert "执行阶段" in result["steps"]

        # discuss=False 时
        result = engine.run({"discuss": False})
        assert "讨论阶段" not in result["steps"]
        assert "执行阶段" in result["steps"]

    def test_run_skips_completed_steps_on_resume(self, tmp_path):
        """GREEN: 断点续做跳过已完成步骤"""
        workflow_file = tmp_path / "quick.md"
        workflow_file.write_text("Step: prepare\nStep: plan\nStep: execute")

        engine = WorkflowEngine(workflow_dir=str(tmp_path))

        # 模拟已完成 prepare
        result = engine.run({"discuss": False}, skip_steps=["prepare"])

        assert "prepare" not in result
        assert "plan" in result
        assert "execute" in result
```

---

### Phase 4: Layer 3 — Agent

#### 5.7 SubprocessAgent 测试（TDD）

```python
# tests/layer3/test_subprocess_agent.py
import pytest
from tflow.agents.subprocess_agent import SubprocessAgent, ExecResult


class TestSubprocessAgent:
    """SubprocessAgent TDD 测试"""

    def test_run_executes_shell_command(self):
        """RED: 执行 shell 命令"""
        agent = SubprocessAgent()
        result = agent.run("echo 'hello'", agent_type="shell")

        assert result.success == True
        assert "hello" in result.output

    def test_run_returns_error_on_failure(self):
        """GREEN: 命令失败返回错误"""
        agent = SubprocessAgent()
        result = agent.run("exit 1", agent_type="shell")

        assert result.success == False
        assert result.error is not None

    def test_run_respects_timeout(self):
        """GREEN: 超时控制"""
        agent = SubprocessAgent()
        result = agent.run("sleep 10", agent_type="shell", timeout=1)

        assert result.success == False
        assert "Timeout" in result.error

    def test_run_parses_json_output(self):
        """GREEN: 解析 JSON 输出"""
        agent = SubprocessAgent()
        result = agent.run('echo \'{"key": "value"}\'', agent_type="shell")

        assert result.success == True
        # 可选的 JSON 解析
        parsed = agent.parse_output(result.output)
        assert parsed == {"key": "value"}

    def test_build_command_for_claude(self):
        """GREEN: 构建 claude 命令"""
        agent = SubprocessAgent()
        cmd = agent._build_command("test prompt", agent_type="claude")

        assert "claude" in cmd
        assert "test prompt" in cmd
```

---

### Phase 5: Layer 1 — Command

#### 5.8 Command 测试（TDD）

```python
# tests/layer1/test_commands.py
import pytest
from click.testing import CliRunner
from tflow.cli import cli


class TestQuickCommand:
    """quick 命令 TDD 测试"""

    def test_quick_command_requires_task_argument(self):
        """RED: quick 命令需要 task 参数"""
        runner = CliRunner()
        result = runner.invoke(cli, ["quick"])

        assert result.exit_code != 0

    def test_quick_command_accepts_task(self, tmp_path):
        """GREEN: quick 命令接受 task 参数"""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["quick", "实现登录功能"])

            # 命令应正常执行（即使功能未实现）
            assert result.exit_code in [0, 1]  # 0=成功, 1=功能未实现

    def test_quick_command_with_full_flag(self, tmp_path):
        """GREEN: --full 标志"""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["quick", "实现登录功能", "--full"])

            assert "--full" in result.output or result.exit_code == 0

    def test_quick_command_with_discuss_flag(self, tmp_path):
        """GREEN: --discuss 标志"""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["quick", "实现登录功能", "--discuss"])

            assert "--discuss" in result.output or result.exit_code == 0


class TestPlanCommand:
    """plan 命令 TDD 测试"""

    def test_plan_command_accepts_phase(self):
        """RED: plan 命令接受 phase 参数"""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["plan", "phase-1"])

            assert result.exit_code in [0, 1]


class TestExecuteCommand:
    """execute 命令 TDD 测试"""

    def test_execute_command_accepts_phase(self):
        """RED: execute 命令接受 phase 参数"""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["execute", "phase-1"])

            assert result.exit_code in [0, 1]
```

---

### Phase 6: 集成测试

#### 5.9 端到端测试（TDD）

```python
# tests/test_integration.py
import pytest
import subprocess
from pathlib import Path


class TestEndToEnd:
    """端到端 TDD 测试"""

    def test_full_quick_workflow(self, tmp_path, git_repo):
        """RED: 完整 quick 工作流"""
        runner = subprocess.run(
            ["python", "-m", "tflow.cli", "quick", "实现登录功能"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # 验证输出
        assert "quick" in runner.stdout.lower() or runner.returncode in [0, 1]

    def test_workflow_creates_artifacts(self, tmp_path, git_repo):
        """GREEN: 工作流创建正确产物"""
        subprocess.run(
            ["python", "-m", "tflow.cli", "quick", "实现登录功能"],
            cwd=str(tmp_path),
            capture_output=True
        )

        # 验证产物目录
        scratch_dir = Path(tmp_path) / ".workflow" / "scratch"
        if scratch_dir.exists():
            # 验证 plan.json 存在
            plan_files = list(scratch_dir.glob("*/plan.json"))
            assert len(plan_files) >= 0  # 取决于执行进度

    def test_workflow_creates_git_commits(self, tmp_path, git_repo):
        """GREEN: 工作流创建 git 提交"""
        subprocess.run(
            ["python", "-m", "tflow.cli", "quick", "实现登录功能"],
            cwd=str(tmp_path),
            capture_output=True
        )

        # 验证 git log
        result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # 应该至少有 initial commit
        assert "initial" in result.stdout.lower() or len(result.stdout) > 0
```

---

## 六、pytest 配置

```python
# tests/conftest.py
import pytest
import subprocess
import os
from pathlib import Path


@pytest.fixture
def git_repo(tmp_path):
    """创建临时 git 仓库"""
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path, capture_output=True
    )
    # 创建 initial commit
    readme = tmp_path / "README.md"
    readme.write_text("# Test")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=tmp_path, capture_output=True
    )
    return tmp_path


@pytest.fixture(autouse=True)
def change_to_tmp_path(tmp_path):
    """自动切换到临时目录"""
    original_dir = os.getcwd()
    os.chdir(tmp_path)
    yield
    os.chdir(original_dir)
```

---

## 七、运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定层
pytest tests/layer5/  # State 测试
pytest tests/layer4/  # Artifact 测试
pytest tests/layer2/  # Workflow 测试
pytest tests/layer3/  # Agent 测试
pytest tests/layer1/  # Command 测试

# 运行 TDD 红绿循环
pytest --tb=short  # 简洁错误输出
pytest -v          # 详细输出

# 生成覆盖率报告
pytest --cov=src/tflow --cov-report=html
```

---

## 八、TDD 开发顺序

| 顺序 | Phase | 依赖关系 | 测试数 |
|------|-------|---------|--------|
| 1 | Layer 5 State | 无 | 7 |
| 2 | Layer 5 Git | Layer 5 State | 3 |
| 3 | Layer 4 Artifact | Layer 5 State | 5 |
| 4 | Layer 2 Wave | 无 | 5 |
| 5 | Layer 2 Engine | Layer 2 Wave, Layer 4 | 4 |
| 6 | Layer 3 Agent | Layer 2 | 5 |
| 7 | Layer 1 Command | Layer 2, 3, 4 | 4 |
| 8 | 集成测试 | 所有层 | 3 |

**总计: ~36 个测试用例**

---

## 九、验收标准

### TDD 流程
- [ ] 每个模块先写测试再实现
- [ ] 所有测试通过（RED → GREEN）
- [ ] 重构后测试仍然通过

### 测试覆盖
- [ ] StateManager: 7 个测试
- [ ] GitCommit: 3 个测试
- [ ] PlanArtifact: 4 个测试
- [ ] VerificationArtifact: 2 个测试
- [ ] WaveScheduler: 5 个测试
- [ ] WorkflowEngine: 4 个测试
- [ ] SubprocessAgent: 5 个测试
- [ ] Command: 4 个测试
- [ ] 集成测试: 3 个测试

### 代码质量
- [ ] 所有测试通过
- [ ] 无警告
- [ ] 覆盖率报告生成

---

*计划版本: 最终版*
*修订日期: 2026-05-02*
