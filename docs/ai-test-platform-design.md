# ADT (AI Drive Testing) - 服务器 AI 测试编排平台

**版本:** 4.0
**日期:** 2026-05-03
**状态:** 设计中

---

## 1. 核心定位

### 1.1 平台角色

ADT 是一个**服务器 AI 测试编排平台**，融合 Maestro 工作流思想与服务器测试领域特性，将测试设计、用例、自动化框架通过分层工作流编排串联，实现测试活动的自动化调度和协同。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ADT 架构分层                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Layer 1: Command（命令入口）                                              │
│   /adt-design | /adt-execute | /adt-report — 参数解析 + 路由               │
│                                                                              │
│   Layer 2: Workflow（可复用流程模板）                                        │
│   test-design.md | test-execution.md | test-report.md                      │
│                                                                              │
│   Layer 3: Agent（执行器）                                                  │
│   planner | executor | verifier — Claude Code / 外部 CLI                   │
│                                                                              │
│   Layer 4: Artifact（数据产物）                                             │
│   plan.json | TASK-*.json | verification.json                              │
│                                                                              │
│   Layer 5: State（持久化状态）                                              │
│   .adt/state.json — 项目状态 + artifact 注册                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 与 Maestro 架构对比

| 维度 | Maestro | ADT |
|------|----------|-----|
| **目标** | 软件开发全生命周期 | 服务器测试编排 |
| **核心实体** | Artifact、Milestone | TestPlan、TestCase、Defect |
| **执行单元** | Task（原子任务） | Step（步骤）+ Task（任务） |
| **验证方式** | existence/substance/connection | 覆盖率/缺陷率/风险矩阵 |
| **触发方式** | 手动 | Webhook/定时/事件/告警 |

---

## 2. 五层管道架构

### 2.1 架构层次

```
┌──────────────────────────────────────────────────────────────┐
│  LAYER 1: Command  (.adt/commands/*.md)                   │
│  "做什么" — 参数解析 + 路由到 Workflow                      │
└────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│  LAYER 2: Workflow  (.adt/workflows/*.md)                  │
│  "怎么做" — 可复用流程模板（plan → execute → verify）     │
└────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│  LAYER 3: Agent  (planner / executor / verifier)           │
│  "谁来做" — Claude Code Agent 或外部 CLI                   │
└────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│  LAYER 4: Artifact  (.adt/scratch/{task}/)               │
│  "产出什么" — plan.json, TASK-*.json, summaries           │
└────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│  LAYER 5: State  (.adt/state.json)                       │
│  "记得什么" — 项目状态 + artifact 注册                     │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 命令格式

```markdown
---
name: adt-design
description: 测试设计工作流
argument-hint: "[spec_file] [--ai] [--full]"
allowed-tools:
  - Read | Write | Edit | Bash | Glob | Grep | Agent | AskUserQuestion
---

<purpose>
执行测试设计工作流：需求分析 → 测试点提取 → 用例生成 → 评审定稿
</purpose>

<context>
$ARGUMENTS — 规格文件路径、AI 辅助模式、完整模式
</context>

<execution>
### Step 1: 解析参数
### Step 2: 加载规格
### Step 3: Spawn Planner Agent
### Step 4: Spawn Executor Agent
### Step 5: 更新状态并提交
</execution>
```

---

## 3. 工作流模型

### 3.1 工作流形式

**工作流采用 YAML 格式**，支持 Markdown 工作流模板。

```
adt/
├── workflows/                 # 工作流模板
│   ├── test-design.md
│   ├── test-execution.md
│   └── test-report.md
├── commands/                 # 命令定义
│   ├── adt-design.md
│   ├── adt-execute.md
│   └── adt-report.md
├── scratch/                  # 任务产物
│   └── {task-name}/
│       ├── plan.json
│       ├── TASK-*.json
│       └── verification.json
└── state.json               # 项目状态
```

### 3.2 步骤类型

| 类型 | 说明 | 用途 |
|------|------|------|
| `step` | 普通步骤 | 执行单个动作 |
| `parallel` | 并行步骤 | 多个步骤同时执行 |
| `decision` | 条件分支 | 根据条件选择路径 |
| `loop` | 循环步骤 | 重复执行直到满足条件 |
| `sub-workflow` | 子工作流 | 引用其他工作流 |
| `approval` | 审批步骤 | 人工确认/审核 |
| `compensate` | 补偿步骤 | 失败时回滚/清理 |

### 3.3 错误处理

```yaml
steps:
  - id: execute
    type: step
    action:
      type: script
      handler: /path/to/test-runner.sh
    on_error:
      retry: 3
      delay: 5s
      backoff: exponential
      when: [timeout, network]
      fallback: cleanup_step
```

### 3.4 触发器

```yaml
triggers:
  - type: manual              # 手动触发
  - type: schedule             # 定时触发
    cron: "0 2 * * *"
  - type: webhook             # Webhook 触发
    endpoint: /api/hooks/test
  - type: alert               # 告警触发
    source: prometheus
```

---

## 4. Agent 角色

### 4.1 三种 Agent

| Agent | 职责 | 输入 | 输出 |
|-------|------|------|------|
| **planner** | 分解任务 → plan.json + TASK-*.json | 需求规格、上下文 | 任务计划 |
| **executor** | 原子执行任务 → summaries | TASK-*.json、plan.json | 执行结果 |
| **verifier** | 三层验证 | plan.json、summaries | verification.json |

### 4.2 Agent 状态机

```
┌─────────────────────────────────────────────────────────────────────┐
│                       Agent 状态流转                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  状态列表:                                                          │
│    pending → running → completed → passed                         │
│                  ↓                                                  │
│               blocked → failed → needs_retry                       │
│                                     ↓                              │
│                                  (retry loop, max 2)               │
│                                                                     │
│  规则：                                                             │
│  1. Planner 完成后自动触发 Executor                                  │
│  2. Executor 失败时，根据 on_error 重试（≤2次）或标记 blocked       │
│  3. Executor 全部完成后自动触发 Verifier                             │
│  4. Verifier 失败时反馈给 Planner 重新规划（最多 2 轮）             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.3 Agent 协作契约

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Agent 协作流程                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Planner          Executor           Verifier                       │
│    │                │                  │                           │
│    │── plan.json ──▶│                  │                           │
│    │   + TASK-*.json                   │                           │
│    │                │                  │                           │
│    │    summaries ──────────────────────▶│                           │
│    │                  │                  │                           │
│    │              verification.json ◀────┘                           │
│    │                │                  │                           │
│    │◀── gaps ───────┘ (if failed)    │                           │
│    │                                                   │           │
└─────────────────────────────────────────────────────────────────────┘

# 契约定义
Planner → Executor: { plan_id, tasks[], execution_mode, start_trigger }
Executor → Verifier: { plan_id, execution_id, summaries[], status }
Verifier → Planner: { verification_id, status, gaps[], recommendation }

# summaries[] 元素结构
{
  "task_id": "TASK-001",
  "summary_path": ".adt/scratch/{task}/summaries/TASK-001-summary.md",
  "status": "passed" | "failed" | "blocked",
  "convergence_result": { "criteria_met": true, "details": "..." }
}
```

### 4.4 convergence 验证机制

```yaml
# 支持多种验证类型
convergence:
  criteria:
    # Shell 命令
    - type: shell
      command: "grep -c 'pass' results.json | test 10 -gt 0"

    # JSON Path 断言
    - type: jsonpath
      path: "$.results[?(@.status=='pass')]"
      count_gte: 10

    # 性能阈值
    - type: threshold
      metric: "latency_p99"
      operator: "lte"
      value: "100ms"

    # 组合条件
    - type: composite
      operator: "and"
      conditions:
        - type: jsonpath
          path: "$.pass_rate"
          gte: 0.95
        - type: jsonpath
          path: "$.defects"
          equals: 0

on_validation_fail:
  strategy: "replan"  # replan | reexecute | accept
  max_retries: 2
```

### 4.5 Verifier 三层验证

```
三层验证：串行执行，Layer N 失败则停止后续验证

Layer 1: Existence（存在性）
  - 文件存在、产物完整
  - 示例：requirements.md 存在、test_cases.yaml 非空

Layer 2: Substance（实质性）
  - 内容符合预期、字段有值
  - 示例：test_cases ≥ 10、defects 有描述

Layer 3: Connection（连接性）
  - 产物关联正确、追溯链完整
  - 示例：
    - 每个 test_case → requirement_id
    - 每个 defect → test_case_id
    - 报告可追溯执行记录
```

### 4.6 Artifact 消费关系

```
Artifact 层消费关系：
  .adt/scratch/{task}/
  ├── plan.json        ← Planner 产出 → Executor 消费
  ├── TASK-*.json      ← Planner 产出 → Executor 消费
  ├── summaries/       ← Executor 产出 → Verifier 消费
  │   └── TASK-*-summary.md
  └── verification.json ← Verifier 产出 → 归档

State 状态管理：
  .adt/state.json      ← 各层写入 → 全局状态
  accumulated_context  ← 跨任务记录关键决策
```

---

## 5. 数据模型

### 5.1 工作流定义

```yaml
workflow:
  id: wf-2026-001
  name: BMC 测试完整流程
  version: "1.0"

  steps:
    - id: design
      type: sub-workflow
      workflow: test-design
      inputs:
        spec_file: "{{input.spec}}"

    - id: execute
      type: step
      name: 执行 BMC 测试
      action:
        type: script
        handler: /path/to/bmc-test-framework/run.sh
      inputs:
        cases: "{{steps.design.outputs.approved_cases}}"

    - id: report
      type: sub-workflow
      workflow: test-report
```

### 5.2 任务定义 (TASK-*.json)

```json
{
  "id": "TASK-001",
  "title": "BMC Redfish API 测试",
  "status": "pending",
  "convergence": {
    "criteria": [
      "grep -c 'pass' results.json | bc | test 10 -gt 0"
    ]
  },
  "implementation": [
    "src/adapters/bmc/test_redfish.py"
  ],
  "assigned_to": "executor"
}
```

### 5.3 验证结果 (verification.json)

```json
{
  "status": "passed",
  "layers": {
    "existence": { "passed": true, "checks": 5 },
    "substance": { "passed": true, "checks": 3 },
    "connection": { "passed": true, "checks": 2 }
  },
  "coverage": {
    "requirements": "15/15",
    "test_cases": "45/50"
  }
}
```

### 5.4 项目状态 (state.json)

```json
{
  "version": "1.0",
  "project": "server-bmc-test",
  "status": "executing",
  "current_phase": 2,
  "artifacts": [
    { "id": "plan-001", "type": "plan", "path": ".adt/scratch/design/plan.json" },
    { "id": "exec-001", "type": "execute", "path": ".adt/scratch/execute/" }
  ],
  "accumulated_context": {
    "decisions": ["BMC IP: 192.168.1.100"],
    "blockers": []
  }
}
```

---

## 6. 模板市场

### 6.1 预置模板

```yaml
templates:
  - id: test-design
    name: 测试设计流程
    description: 需求→策略→用例→评审
    workflow: test-design.md

  - id: test-execution
    name: 测试执行流程
    description: 解析计划→分配资源→分层执行→结果收集
    workflow: test-execution.md

  - id: test-regression
    name: 回归测试
    description: 代码变更后快速验证核心功能
    triggers:
      - type: webhook
      - type: schedule
        cron: "0 3 * * *"
    workflow: test-regression.md

  - id: test-smoke
    name: 冒烟测试
    description: 快速验证核心功能可用性
    workflow: test-smoke.md

  - id: test-report
    name: 测试报告
    description: 结果汇总→AI分析→风险评估→报告
    workflow: test-report.md
```

### 6.2 模板定义示例

```yaml
# test-design.md
workflow:
  name: 测试设计流程
  version: "1.0"

steps:
  - id: requirement
    type: step
    name: 需求分析
    action:
      type: input
      handler: ./actions/load-requirements.js

  - id: ai_analysis
    type: step
    name: AI 需求分析
    action:
      type: ai-analysis
      model: claude
    inputs:
      requirements: "{{steps.requirement.outputs.spec}}"

  - id: case_gen
    type: step
    name: 用例生成
    action:
      type: script
      handler: ./actions/generate-cases.py

  - id: review
    type: approval
    name: 人工评审
```

---

## 7. 技术选型

### 7.1 后端 (Python)

| 层次 | 技术 | 说明 |
|------|------|------|
| CLI | Typer + Rich | 现代化命令行 |
| Web | FastAPI | 高性能 API |
| ORM | SQLAlchemy | 数据库抽象 |
| 任务队列 | Celery + Redis | 异步执行 |
| AI | Claude SDK / OpenAI SDK | AI 能力 |
| 验证 | Pydantic | 类型校验 |

### 7.2 前端 (React Best Practice)

| 层次 | 技术 |
|------|------|
| 框架 | React 18 + TypeScript |
| 状态 | Zustand |
| UI | shadcn/ui + Tailwind CSS |
| 路由 | React Router v6 |
| 构建 | Vite |
| 数据 | TanStack Query |
| 实时 | Socket.io |

### 7.3 部署架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Web UI    │────▶│   Nginx     │────▶│   FastAPI   │
│   (React)   │     │             │     │   Backend   │
└─────────────┘     └─────────────┘     └──────┬──────┘
       │                                      │
       │ WebSocket                            ▼
       │                              ┌─────────────┐
       │                              │  Celery     │
       │                              │  Worker     │
       │                              └──────┬──────┘
       │                                     │
       ▼                                     ▼
┌─────────────┐                       ┌─────────────┐
│  PostgreSQL │◀──────────────────────│    Redis    │
│  + Storage  │                       │   Cache     │
└─────────────┘                       └─────────────┘
```

---

## 8. 项目结构

```
adt/
├── backend/                    # Python 后端
│   ├── adt/
│   │   ├── cli/              # Typer CLI
│   │   ├── api/              # FastAPI
│   │   ├── engine/           # 工作流引擎
│   │   ├── actions/          # 内置动作
│   │   ├── models/           # SQLAlchemy
│   │   └── plugins/          # 插件系统
│   └── tests/
│
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── stores/
│   │   └── services/
│   └── package.json
│
├── .adt/                      # 工作流状态（项目内）
│   ├── commands/             # 命令定义
│   │   ├── adt-design.md
│   │   ├── adt-execute.md
│   │   └── adt-report.md
│   ├── workflows/            # 工作流模板
│   │   ├── test-design.md
│   │   ├── test-execution.md
│   │   └── test-report.md
│   ├── agents/              # Agent 定义
│   │   ├── agent-planner.md
│   │   ├── agent-executor.md
│   │   └── agent-verifier.md
│   ├── scratch/             # 任务产物
│   │   └── {task-name}/
│   │       ├── plan.json
│   │       ├── TASK-*.json
│   │       └── verification.json
│   └── state.json           # 项目状态
│
├── templates/                 # 模板市场
├── docs/
└── docker-compose.yml
```

---

## 9. 核心差异化

| 维度 | 描述 |
|------|------|
| **五层管道** | Command → Workflow → Agent → Artifact → State |
| **测试专有** | 测试设计/执行/报告全流程，冒烟/回归/分层模板 |
| **AI 驱动** | AI 辅助需求分析、用例生成、缺陷分析、报告摘要 |
| **错误恢复** | 重试/退避/补偿机制，保证执行可靠性 |
| **多触发器** | Webhook/定时/事件/告警，适配 CI/CD |
| **Dry-run** | 执行前预览步骤，提前发现问题 |
| **三层验证** | existence → substance → connection |

---

## 10. 实施路线图

### Phase 1: 核心框架 (3 周)
- [ ] 项目脚手架
- [ ] 工作流引擎
- [ ] 五层管道实现
- [ ] 持久化存储

### Phase 2: Agent 系统 (2 周)
- [ ] Planner Agent
- [ ] Executor Agent
- [ ] Verifier Agent
- [ ] 状态管理

### Phase 3: 模板与触发器 (2 周)
- [ ] 预置工作流模板
- [ ] 触发器系统
- [ ] CLI 完善

### Phase 4: 前端与集成 (3 周)
- [ ] React 仪表盘
- [ ] AI 能力集成
- [ ] Docker 部署
