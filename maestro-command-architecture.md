# Maestro Command Architecture

本文档描述 Maestro 如何将用户命令通过分层工作流路由，最终产生已提交、可验证的代码产物。

---

## 快速参考

### Command 入口点

| Command | 用途 | 对应 Workflow |
|---------|------|---------------|
| `/maestro-quick "task"` | 带工作流保障的小型临时任务 | `quick.md` |
| `/maestro-plan [phase]` | 为某个 phase 生成任务计划 | `plan.md` |
| `/maestro-execute [phase]` | 波次执行pending计划 | `execute.md` |
| `maestro delegate "prompt"` | 调用外部 CLI agent（gemini/qwen/codex） | 直连 |

### 三种 Agent Spawn 路径

| 路径 | 机制 | 典型用途 |
|------|------|---------|
| **A** | Claude Code Skill Tool → 内置 Agent | workflow-planner, workflow-executor, workflow-verifier |
| **B** | Bash → `maestro delegate` → CliAgentRunner | 外部 CLI agent 探索性分析 |
| **C** | `maestro coordinate` → `maestro cli` → CliAgentRunner | 旧版 chain 机制（已废弃） |

### 状态层次

```
Command → Workflow → Agent → Artifact → State → Commit
```

- **Command**（`.claude/commands/*.md`）：入口点，参数解析
- **Workflow**（`~/.maestro/workflows/*.md`）：可复用流程模板
- **Agent**：执行任务 — Claude Code 内置或外部 CLI
- **Artifact**：plan.json, TASK-*.json, summaries, verification.json
- **State**：`.workflow/state.json`（项目级），`index.json`（计划级），`TASK-*.json`（任务级）

---

## 一、概念概述

Maestro 解决的核心问题是：**将用户模糊的意图转化为已提交、可验证的代码变更**，通过分层管道实现。

**核心矛盾：**用户思考的是目标（"实现登录"），Claude Code agent 思考的是文件和编辑。Maestro 通过以下方式弥合这一鸿沟：

1. 将目标分解为带**收敛条件**的 task（grep 可验证的条件）
2. 将 task 路由到合适的**执行器**（Claude Code agent 或外部 CLI）
3. 强制**波次执行**（波次内并行，波次间串行）
4. 每个 task 后**原子提交**——不留半成品状态
5. 在**状态产物**中跟踪一切，支持断点续做

**读者定位：**
- 运行 `/maestro-quick` 或 `/maestro-execute` 的实践者——需要理解命令如何流转
- 基于 Maestro 构建的集成者——需要 spawn 路径机制
- 追踪失败的调试者——需要完整调用链

---

## 二、架构：五层管道

Maestro 的 Command 系统是**五层职责分离的管道**，每层只做一件事：

```
┌──────────────────────────────────────────────────────────────┐
│  LAYER 1: Command Definition  (.claude/commands/*.md)        │
│  "做什么" — 声明式状态机：步骤 + 路由                         │
└────────────────────────────┬─────────────────────────────────┘
                             │ Skill Tool 调用
                             ▼
┌──────────────────────────────────────────────────────────────┐
│  LAYER 2: Workflow Engine  (~/.maestro/workflows/*.md)     │
│  "怎么做" — 可复用流程模板                                   │
└────────────────────────────┬─────────────────────────────────┘
                             │ Agent 调度（Bash 或 Agent Tool）
                             ▼
┌──────────────────────────────────────────────────────────────┐
│  LAYER 3: Claude Code Agent / CLI Agent                     │
│  "谁来做" — workflow-planner/executor/verifier 或            │
│              gemini/codex/qwen                               │
└────────────────────────────┬─────────────────────────────────┘
                             │ 文件读写 + git commit
                             ▼
┌──────────────────────────────────────────────────────────────┐
│  LAYER 4: Data Artifacts  (.workflow/scratch/)              │
│  "产出什么" — plan.json, TASK-*.json, summaries              │
└────────────────────────────┬─────────────────────────────────┘
                             │ 状态读写
                             ▼
┌──────────────────────────────────────────────────────────────┐
│  LAYER 5: State & Persistence  (.workflow/state.json)        │
│  "记得什么" — 项目状态，artifact 注册                        │
└──────────────────────────────────────────────────────────────┘
```

**Command → Workflow 绑定：** Command 通过 `<required_reading>@~/.maestro/workflows/{workflow}.md</required_reading>` 声明依赖，使用 `follow 'path'` 加载并执行 Workflow 模板。一个 Command 引用一个 Workflow。

| Command | Workflow |
|---------|----------|
| `maestro-quick.md` | `quick.md` |
| `maestro-plan.md` | `plan.md` |
| `maestro-execute.md` | `execute.md` |

---

## 三、Command 定义格式

每个 `.claude/commands/*.md` 遵循 **YAML frontmatter + 执行契约** 格式：

```markdown
---
name: {command-name}
description: {一句话描述}
argument-hint: "[phase] [--flag]"
allowed-tools:
  - Read | Write | Edit | Bash | Glob | Grep | Agent | AskUserQuestion
---

<purpose>
命令的高层目的
</purpose>

<required_reading>
@~/.maestro/workflows/{workflow}.md
</required_reading>

<context>
$ARGUMENTS — {参数解析规则}
</context>

<execution>
### Step 1: {步骤名}
{执行逻辑}

### Step 2: {条件步骤}
Skip entirely if NOT $FLAG_MODE.
</execution>

<error_codes>
| Code | Severity | Condition | Recovery |
|------|----------|-----------|----------|
| E001 | error    | ...       | ...      |
</error_codes>

<success_criteria>
- [ ] {检查项}
</success_criteria>
```

`allowed-tools` 字段控制 spawned agent 的能力边界。`<execution>` 段描述 Skill Tool 解析并顺序执行的步骤。

---

## 四、三种 Agent Spawn 路径

这是系统的核心机制。Maestro 有**三条完全不同的 agent 调用路径**。

### 路径 A：Skill Tool → Claude Code Agent

适用场景：`workflow-planner`、`workflow-executor`、`workflow-verifier`、`workflow-plan-checker`

```
Workflow MD 步骤: "Spawn workflow-planner agent"
          │
          ▼
┌────────────────────────────────────────────────────┐
│  Claude Code Skill Tool                            │
│  1. 解析 .claude/commands/maestro-*.md           │
│  2. 执行 <execution> 步骤                         │
│  3. 调用内置 Agent Tool                            │
│  4. 加载 .claude/agents/workflow-planner.md       │
│  5. 以 6-field prompt 结构执行                     │
│  Agent 通过 Read/Write/Bash 工具自主执行            │
└────────────────────────────────────────────────────┘
```

这是 **Claude Code 的内置机制**，不是 Maestro 代码。`allowed-tools` 字段约束 agent 的操作范围。

### 路径 B：Bash → `maestro delegate` → CliAgentRunner

适用场景：使用 gemini/qwen/codex 进行探索性分析，`--method cli` 执行

```
Workflow MD 步骤:
  Bash({
    command: "maestro delegate \"<prompt>\" --to gemini --mode write",
    run_in_background: true
  })
          │
          ▼
┌────────────────────────────────────────────────────┐
│  bin/maestro.js → 命令路由                         │
│  src/commands/delegate.ts → CliAgentRunner.run()  │
└────────────────────────────┬─────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────┐
│  CliAgentRunner.run()                              │
│  1. assemblePrompt() — 组装 protocol + prompt + rule│
│  2. createAdapter() — DashboardBridge 或           │
│     TerminalAdapter（tmux/wezterm）                │
│  3. adapter.spawn() — 启动 CLI 进程               │
│  4. 订阅 adapter.onEntry() 事件                   │
│  5. broker.publishEvent() — 事件持久化             │
└────────────────────────────┬─────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │  backend: 'direct'（默认）   │  backend: 'terminal'
              ▼                             ▼
    DashboardBridge (WS)          TerminalAdapter
    → gemini/qwen/codex           → tmux 或 wezterm
                                    每 2s 轮询
                                    stale 超时：120s
```

**Delegate Prompt Builder**（Path B 用于 `execute.md` 波次执行）：

```
buildDelegatePrompt(task_def, phase_context, specs_content, prior_summaries)
// 返回：
// PURPOSE: Implement task ${task_def.id}: ${task_def.title}
// TASK: ${task_def.action} | Read existing code | Verify convergence
// MODE: write
// CONTEXT: @${task_def.scope}/**/* | Phase: ${phase_context.goal}
// EXPECTED: Working code, verified convergence criteria, summary
// CONSTRAINTS: Scope limited to task files | Follow project specs
```

### 路径 C：`maestro coordinate` → `maestro cli`（旧版）

适用场景：旧版 chain graph 系统（已废弃）

```
GraphWalker 执行 command node
    │
    ▼
createSpawnFn()  // src/commands/coordinate.ts:64
    │
    └─→ execFileAsync(process.execPath, [
          entryScript, 'cli', '-p', config.prompt,
          '--tool', tool, '--mode', mode, '--cd', config.workDir
        ])
            │
            ▼
    src/commands/cli.ts → CliAgentRunner.run()
```

路径 C 是**历史遗留机制**。`coordinate.ts` 的 `createSpawnFn()` 在新版 skill 系统中不再使用。

### Spawn 路径决策逻辑

```
1. 任务是否需要 workflow 纪律（task 分解 + 收敛条件 + 原子提交）？
   → YES → 路径 A（workflow-planner/executor/verifier）

2. 任务是否需要多 agent 协作（Team 模式）？
   → YES → 路径 A 变体（team-worker / team-supervisor agent types）

3. 任务是否需要 Gemini/Qwen/Codex 的特定探索能力？
   → YES → 路径 B（maestro delegate --to {gemini|qwen|codex}）

4. 是否是旧版 chain/coordinate 机制？
   → YES → 路径 C（历史遗留，新场景不应使用）
```

### 路径 A 变体：Team Agent Types

对于 `team-lifecycle-v4`，`team-worker` 和 `team-supervisor` 是**专门的 agent types**（非标准 workflow agent）：

```
Agent({
  subagent_type: "team-worker",   // 或 "team-supervisor"
  run_in_background: true,
  prompt: `## Role Assignment
role: <role>
role_spec: <skill_root>/roles/<role>/role.md
...`
})
```

**team-worker vs workflow-executor：**

| 维度 | workflow-executor | team-worker |
|------|-----------------|-------------|
| 生命周期 | 单次 task 执行 | task 发现 → 执行 → 报告 循环 |
| 任务来源 | 读取 plan.json TASK-* | TaskList() API 动态发现 |
| 协作模式 | 独立执行 | 通过 team_msg 与 coordinator 通信 |
| 权限边界 | scope/focus_paths | role-prefix 过滤的任务 |
| 后台运行 | 由 executor 主控 | 独立 background agent |
| 适用场景 | quick/plan/execute 管道 | team-lifecycle-v4 多角色协作 |

---

## 五、Skill Context Hook

`src/hooks/skill-context.ts` 在 `UserPromptSubmit` 时向 Skill agent 注入工作流状态上下文。

```
用户输入 /maestro-execute 2
    │
    ▼
parseSkillInvocation("/maestro-execute 2")
    └── { skill: 'maestro-execute', phaseNum: 2 }

evaluateSkillContext({ user_prompt, cwd, session_id })
    │
    ├── 读取 .workflow/state.json
    ├── 读取 artifact registry
    │
    ├── buildStateSection()    → Milestone / Phase / Status / Key decisions
    ├── buildArtifactTree()    → .task/ 状态列表 / .summaries/ 数量
    └── buildOutcomesSection() → Deferred items / Verification gaps / Learnings
    │
    ▼
HookOutput.additionalContext 注入到 Skill agent prompt
```

这让 Skill agent 能看到当前项目状态（哪些 task 已完成、处于哪个 phase 等），无需手动读取文件。

---

## 六、执行流程：Command 详解

### `/maestro-quick` 流程

```
用户: /maestro-quick "implement login" --full --discuss
          │
          ▼
Step 1: 参数解析
  $DESCRIPTION = "implement login"
  $FULL_MODE = true, $DISCUSS_MODE = true
          │
          ▼
Step 2: 验证项目
  检查 .workflow/state.json 存在
          │
          ▼
Step 3: 创建 Scratch 目录
  .workflow/scratch/quick-{slug}-{date}/
          │
          ├─── $DISCUSS_MODE = true ──────────────┐
          ▼                                      ▼
Step 4: 讨论阶段                          Step 4.5: 加载 Specs
  识别灰区                                  maestro spec load --category coding
  AskUserQuestion（locked/free/deferred）
  → context.md
          │                                      │
          ▼                                      ▼
Step 5: 调度 Planner                          │
  "Spawn workflow-planner agent"               │
  （Claude Code Agent Tool，路径 A）─────────────┘
          │
          ▼
  workflow-planner 读取：context.md, specs, state.json
  输出：plan.json + .task/TASK-*.json
          │
          ├─── $FULL_MODE = true ──────────────┐
          ▼                                      │
Step 6: Plan Checker Loop                      │
  Spawn workflow-plan-checker（最多2次迭代）     │
  问题 → 修订 → 重新检查                        │
          │                                      │
          └──────────────┬──────────────────────┘
                         ▼
Step 7: 调度 Executor
  "Spawn workflow-executor agent"
  （Claude Code Agent Tool，路径 A）
          │
          ▼
  workflow-executor 读取：plan.json, TASK-*.json, specs
  输出：.summaries/TASK-*-summary.md, 更新 TASK-*.json status
          │
          ├─── $FULL_MODE = true ──────────────┐
          ▼                                      │
Step 8: Verification                          │
  Spawn workflow-verifier                      │
  输出：verification.json                       │
          │                                      │
          └──────────────┬──────────────────────┘
                         ▼
Step 9: 更新状态
  将 quick task 追加到 state.json quick_tasks 数组
          │
          ▼
Step 10: Git 提交并完成
  git add scratch/ state.json
  git commit -m "quick({slug}): {description}"
```

### `/maestro-execute` 流程

```
用户: /maestro-execute 2
          │
          ▼
E0.5: 执行选项确认
  AskUserQuestion：executor 方法 + 代码审查工具
  如有 -y 标志或 executionContext 已确认则跳过
          │
          ▼
E1: 加载计划
  读取 ${PLAN_DIR}/plan.json
  检测已完成的 task（断点续做）
  构建波次执行队列
          │
          ▼
E1.5: 加载项目 Specs
  maestro spec load --category coding
          │
          ▼
E2: 波次并行执行
  For each wave（顺序）：
    For each task in wave（并行）：
      解析 executor（agent/codex/gemini 按 domain 路由）
      路径 A: Spawn workflow-executor（Claude Code Agent）
      路径 B: maestro delegate --to ${executor} --mode write
      task 完成时：原子提交（如 auto-commit）
      写入 .summaries/${task_id}-summary.md
    等待波次内所有 task
    如有 blocked：提示继续或停止
          │
          ▼
E2.5: 波次后验证
  检查 summary 存在性、task status 一致性、
  技术栈约束合规性
          │
          ▼
E2.6: 代码审查（可选）
  maestro delegate --to ${codeReviewTool} --mode analysis
          │
          ▼
E3: 自动同步
  如 config.auto_sync_after_execute：运行 /workflow:sync 逻辑
          │
          ▼
E4: 反思（可选）
  将策略观察记录到 reflection-log.md
          │
          ▼
E5: 注册 Artifact & 提取学习
  在 state.json 创建 EXC artifact
  从 summaries 提取 learnings → specs/learnings.md
```

### Executor 解析（E2 内）

```
executionMethod 来自 E0.5 或 --method 标志

单 executor 模式（agent/codex/gemini/cli）：所有 task 使用该 executor

自动模式（"auto"）：
  For each task，从 task 定义确定 domain：
    frontend  → .tsx/.jsx/.vue/.css/.html，scope 包含 ui/frontend/component/
    backend   → .go/.rs/.java/.py/.sql/.proto，scope 包含 api/backend/server/
    general   → 混合，.ts/.js 仅限，config, tests 或不明确

  查找 domainRouting[domain]，回退到 domainRouting.default

  记录路由决策：
    TASK-001 [frontend] → gemini
    TASK-002 [backend]  → codex
    TASK-003 [general]  → agent
```

### 偏差规则

```
每个 task 最多 3 次自动修复尝试：
  Agent 路径：workflow-executor 内部处理
  CLI 路径：  1) --resume ${fixedId} → 2) 简化 prompt → 3) 回退到 agent

如 3 次都失败：标记 "blocked"，在 .task/${task_id}.json.meta.checkpoint 记录
  { attempt: 3, last_error, partial_files, executor, delegate_id: fixedId }
继续波次（其他 task 不受影响）
```

---

## 七、状态管理架构

### 三层状态层次

```
┌──────────────────────────────────────────────────────────────┐
│  .workflow/state.json  （项目级）                            │
│  version, status, artifacts[], accumulated_context           │
└────────────────────────────┬─────────────────────────────────┘
                             │ Artifact 注册联动
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  PLN artifact   │  │  EXC artifact   │  │  VRF artifact   │
│  （计划产物）    │  │  （执行产物）    │  │  （验证产物）    │
└─────────────────┘  └─────────────────┘  └─────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  .workflow/scratch/{slug}/index.json  （计划级）              │
│  status, plan{task_ids[], task_count}, execution{}           │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  .workflow/scratch/{slug}/.task/TASK-001.json  （任务级）    │
│  status, convergence.criteria[], files[], implementation[]   │
└──────────────────────────────────────────────────────────────┘
```

### 状态流转

**任务级：**
```
pending → active → completed
                  ↘ completed_with_deviations
                  ↘ blocked
```

**计划级（index.json）：**
```
active → planning → completed | blocked
```

**项目级（state.json）：**
```
idle | planning | executing | verifying
```

### 断点续做

execute 工作流完全支持续做：

```
状态跟踪在 index.json.execution：
  tasks_completed, current_wave, commits, method,
  delegate_ids: { task_id: fixedId, ... }

续做行为（重新运行 /maestro-execute）：
  1. 扫描每个 .task/TASK-*.json status + delegate status 获取进行中 CLI task
  2. CLI task：获取已完成输出或用 --resume ${fixedId} 重试
  3. 构建剩余 task 队列
  4. 从下一个 pending 波次继续
  5. 不重复执行已完成的 task
```

### accumulated_context

```
"accumulated_context": {
  "key_decisions": [],   // 跨 task 的重要决策
  "blockers": [],       // 阻碍项
  "deferred": []        // 推迟事项
}
```

---

## 八、Agent 角色与数据契约

| Agent | 职责 | 关键约束 |
|-------|------|---------|
| `workflow-planner` | 将目标分解为 task 列表 → plan.json + TASK-*.json | 1 feature = 1 task；收敛条件必须 grep 可验证 |
| `workflow-executor` | 原子执行单个 task，验证收敛，提交 | 每个 task 一次 git commit；不超出范围 |
| `workflow-verifier` | 三层验证（存在/实质/连接） | 只读；从不修改文件 |
| `workflow-plan-checker` | 验证计划质量 | 只读；提供修订建议 |

### 数据流：Planner → Executor → Verifier

```
workflow-planner
  输入: context.md, specs, explorationContext
  输出: plan.json + .task/TASK-{NNN}.json
  约束: 1 feature = 1 task；criteria grep 可验证
          │
          ▼
workflow-executor
  输入: TASK-*.json, specs, prior summaries
  输出: .summaries/TASK-{NNN}-summary.md
        更新 TASK-*.json status → completed/blocked
  约束: 原子提交，不超出范围，每 task 一次 git commit
          │
          ▼
workflow-verifier（full 模式）
  输入: plan.json, TASK-*.json, summaries, 产物文件
  输出: verification.json
  三层: existence / substance / connection
  约束: 只读；每条检查必须有证据
```

---

## 九、数据 Schema

### Schema 参考表

| Schema | 文件位置 | 用途 | 关键字段 |
|--------|---------|------|---------|
| `state.json` | `.workflow/state.json` | 项目级状态 | version, status, artifacts[], accumulated_context |
| `plan.json` | `.workflow/scratch/{slug}/plan.json` | 计划概览 | task_ids[], waves[], complexity, approach |
| `task.json` | `.workflow/scratch/{slug}/.task/TASK-*.json` | 单 task 定义 | status, convergence.criteria[], files[], implementation[] |
| `scratch-index.json` | `.workflow/scratch/{slug}/index.json` | Quick 任务入口 | flags, plan, execution |
| `verification.json` | `.workflow/scratch/{slug}/verification.json` | 验证结果 | layers{}, convergence_check{}, gaps[] |
| `config.json` | `.workflow/config.json` | 项目配置 | workflow, execution, git, gates, specs 设置 |
| `ExecutionMeta` | `~/.maestro/cli-history/{execId}.meta.json` | CLI 执行元数据 | execId, tool, mode, prompt, startedAt |
| `EntryLike` | `~/.maestro/cli-history/{execId}.jsonl` | JSONL 历史条目 | type, [type-specific fields] |
| `DelegateJobRecord` | `~/.maestro/data/async/delegate-broker.{json\|sqlite}` | Broker job 记录 | jobId, status, lastEventId |
| `DelegateJobEvent` | `~/.maestro/data/async/delegate-broker.{json\|sqlite}` | Broker 事件 | eventId, sequence, jobId, type |
| `DelegateQueuedMessage` | `~/.maestro/data/async/delegate-broker.{json\|sqlite}` | 排队消息 | messageId, delivery, status |
| `DelegateExecutionRequest` | 内存中（delegate.ts） | Delegate 请求 | prompt, tool, mode, workDir, execId |
| `ExecutionSnapshot` | 内存中 + broker | Broker 快照 | execId, status, outputPreview |
| `doc-index.json` | `.workflow/codebase/doc-index.json` | 代码库文档索引 | features[], components[], requirements[] |

### artifact 类型枚举

`plan` | `execute` | `verify` | `quick`

### cliHistoryDir

`~/.maestro/cli-history/`

### Broker State

`~/.maestro/data/async/delegate-broker.json`（文件锁，跨进程）或 `delegate-broker.sqlite`（WAL 模式，高并发）。

---

## 十、设计哲学

| 原则 | 实现方式 |
|------|---------|
| **单向数据流** | Command → Workflow → Agent → Artifact → State → Commit |
| **状态驱动** | 所有状态变更持久化到 state.json |
| **原子性** | 每个 executor task 一次 git commit |
| **断点续做** | 重新运行时跳过已完成的 task |
| **可验证性** | convergence.criteria 必须 grep/命令可验证 |
| **知识积累** | accumulated_context 跨 task 记录关键决策 |
| **三层验证** | existence → substance → connection |
| **最小干预** | Command 只修改必须修改的文件 |
| **渐进复杂度** | quick（无 flags）→ +discuss → +full |
| **质量门控** | `--discuss` 和 `--full` 作为可选质量门控 |

---

## 附录：文件位置

### 资源位置

| 资源 | 路径 |
|------|------|
| Command 定义 | `.claude/commands/*.md` |
| Workflow 模板 | `~/.maestro/workflows/*.md` |
| Agent 定义 | `.claude/agents/workflow-*.md` |
| Data Schema | `~/.maestro/templates/*.json` |
| 项目状态 | `.workflow/state.json` |
| Scratch 产物 | `.workflow/scratch/{plan\|quick}-{slug}/` |
| 学习产物 | `.workflow/learning/investigate-{slug}/` |
| Specs 目录 | `.workflow/specs/` |
| Issues 目录 | `.workflow/issues/` |

### 核心源码文件

| 文件 | 职责 |
|------|------|
| `src/commands/delegate.ts` | `maestro delegate` 命令：解析参数，调用 CliAgentRunner |
| `src/commands/cli.ts` | `maestro cli` 命令（coordinate 内部使用） |
| `src/agents/cli-agent-runner.ts` | **统一 CLI agent 执行器**：组装 prompt、启动进程、管理事件 |
| `src/agents/terminal-adapter.ts` | tmux/wezterm 后端：每 2s 轮询，120s stale 超时 |
| `src/agents/dashboard-bridge.ts` | Dashboard WebSocket 桥接器 |
| `src/async/delegate-broker.ts` | Event broker：文件或 SQLite 持久化，pub/sub job 状态 |
| `src/agents/cli-history-store.ts` | JSONL 历史存储（`{execId}.jsonl` + `.meta.json`） |
| `src/commands/coordinate.ts` | `maestro coordinate` 命令；`createSpawnFn()` 调用 `maestro cli` |
| `src/hooks/skill-context.ts` | `UserPromptSubmit` hook：向 Skill agent 注入工作流状态上下文 |
| `src/tools/team-agents.ts` | Team agents MCP 工具：`spawn_agent`/`shutdown_agent` |
| `src/agents/parallel-cli-runner.ts` | 并行 CLI runner，支持波次并行执行 |

### Tool-to-Agent 映射

```javascript
// src/agents/cli-agent-runner.ts
const TOOL_TO_AGENT_TYPE = {
  gemini:         'gemini',
  'gemini-a2a':   'gemini-a2a',
  qwen:           'qwen',
  codex:          'codex',
  'codex-server': 'codex-server',
  claude:         'claude-code',
  opencode:       'opencode',
};

const AGENT_TYPE_TO_TERMINAL_CMD = {
  'gemini':       'gemini',
  'gemini-a2a':   'gemini',
  'qwen':         'qwen',
  'codex':        'codex',
  'codex-server': 'codex',
  'claude-code':  'claude',
  'opencode':     'opencode',
};

const TOOL_PREFIX = {
  gemini:         'gem',
  'gemini-a2a':   'gma',
  qwen:           'qwn',
  codex:          'cdx',
  'codex-server': 'cxs',
  claude:         'cld',
  opencode:       'opc',
};
```

### Broker 事件类型

```
queued → running → completed
                 → failed
                 → cancelled
              ↗
         input_required
```

两种 Broker 实现：
- **FileDelegateBroker**：`delegate-broker.json`（文件锁，跨进程）
- **SqliteDelegateBroker**：`delegate-broker.sqlite`（WAL 模式，高并发）

### Terminal Adapter 轮询机制

```typescript
// src/agents/terminal-adapter.ts
async pollOutput(processId, paneId) {
  let staleCount = 0;
  while (this.panes.get(processId)?.polling) {
    await sleep(2000);              // 每 2s 轮询
    alive = await this.backend.isAlive(paneId);
    content = await this.backend.getText(paneId);

    if (content !== lastContent) {
      emit({ type: 'assistant_message', content: newContent, partial: true });
      lastContent = content;
      staleCount = 0;
    } else {
      staleCount++;
      if (staleCount >= 60) {      // 60 × 2s = 120s
        emit({ type: 'status_change', status: 'stopped', reason: 'stale timeout' });
        break;
      }
    }
  }
}
```
