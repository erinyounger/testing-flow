# Standard Task Workflow

使用结构化管道执行标准任务，提供工作流保障（原子提交、状态跟踪）。Standard 模式生成 agent-planner + agent-executor(s) + agent-verifier，在 `.workflow/scratch/` 中跟踪任务，并更新 state.json。

`--discuss`：规划前的轻量级决策提取。识别灰区，进行交互式讨论，将决策分类为 Locked/Free/Deferred 写入 context.md，使 planner 将 Locked 决策视为约束，Free 决策留给实现者判断。

`--full`：启用计划检查（最多 2 次迭代）和执行后验证。

标志可组合：`--discuss --full` = 讨论 + 计划检查 + 验证。

---

## 前置条件

- `.workflow/state.json` 必须存在（项目已初始化）
- Standard 任务可在任意阶段运行 — 验证仅检查项目存在，不检查阶段状态

---

### Step 1: 解析参数

**解析 $ARGUMENTS 中的标志和描述：**

提取：
- `--full` 标志 -> 存储为 `$FULL_MODE` (true/false)
- `--discuss` 标志 -> 存储为 `$DISCUSS_MODE` (true/false)
- 其余文本 -> 用作 `$DESCRIPTION`

如果解析后 `$DESCRIPTION` 为空：
```
AskUserQuestion(
  header: "Task",
  question: "What do you want to do?",
  followUp: null
)
```

将响应存储为 `$DESCRIPTION`。
如果仍为空，重新提示："Please provide a task description."

显示横幅：`WORKFLOW > STANDARD TASK`，根据标志显示不同后缀：

| 标志 | 横幅后缀 | 副标题 |
|-------|--------------|----------|
| --discuss + --full | `(DISCUSS + FULL)` | 讨论 + 计划检查 + 验证已启用 |
| --discuss only | `(DISCUSS)` | 讨论阶段已启用 — 规划前识别灰区 |
| --full only | `(FULL MODE)` | 计划检查 + 验证已启用 |
| none | _(无后缀)_ | _(无副标题)_ |

---

### Step 2: 验证项目

**验证项目状态：**

检查 .workflow/ 存在且有 state.json：
```bash
test -f .workflow/state.json && echo "exists" || echo "missing"
```

如果缺失：错误 — "Standard 模式需要已初始化的项目。先运行 /workflow:init。"

Standard 任务可在任意阶段运行 — 验证仅检查项目存在，不检查阶段状态。

---

### Step 3: 创建 Scratch 目录

**创建 scratch 目录：**

从 $DESCRIPTION 生成 slug（小写、连字符、最大 40 字符）。
日期设为当前日期（YYYY-MM-DD）。

```bash
STANDARD_DIR=".workflow/scratch/standard-${slug}-${date}"
mkdir -p "$STANDARD_DIR/.task"
mkdir -p "$STANDARD_DIR/.summaries"
```

写入 index.json：
```json
{
  "id": "standard-{slug}-{date}",
  "type": "standard",
  "title": "{DESCRIPTION}",
  "status": "active",
  "created_at": "{ISO timestamp}",
  "updated_at": "{ISO timestamp}",
  "flags": {
    "discuss": {DISCUSS_MODE},
    "full": {FULL_MODE}
  },
  "plan": {
    "task_ids": [],
    "task_count": 0
  },
  "execution": {
    "method": "agent",
    "tasks_completed": 0,
    "tasks_total": 0
  }
}
```

报告："Creating standard task: {DESCRIPTION}\nDirectory: {STANDARD_DIR}"

---

### Step 4: 讨论阶段（仅当 $DISCUSS_MODE）

**轻量级讨论：**

如果 NOT $DISCUSS_MODE 则完全跳过。

```
------------------------------------------------------------
  WORKFLOW > DISCUSSING STANDARD TASK
------------------------------------------------------------
Surfacing gray areas for: {DESCRIPTION}
```

**4a. 识别灰区：**

分析 $DESCRIPTION 识别 2-4 个灰区 — 会改变结果的实现决策。使用领域感知启发式：

- 用户**看到**的东西 -> 布局、密度、交互、状态
- 用户**调用**的东西 -> 响应、错误、认证、版本控制
- 用户**运行**的东西 -> 输出格式、标志、模式、错误处理
- 用户**读取**的东西 -> 结构、语气、深度、流程
- 被**组织**的东西 -> 标准、分组、命名、异常

**4b. 展示灰区：**

```
AskUserQuestion(
  header: "Gray Areas",
  question: "Which areas need clarification before planning?",
  options: [
    { label: "{area_1}", description: "{why_it_matters}" },
    { label: "{area_2}", description: "{why_it_matters}" },
    { label: "{area_3}", description: "{why_it_matters}" },
    { label: "All clear", description: "Skip discussion -- I know what I want" }
  ],
  multiSelect: true
)
```

如果用户选择 "All clear" -> 跳到 Step 5（不写 context.md）。

**4c. 讨论选定区域：**

对于每个选定区域，问 1-2 个聚焦问题：
```
AskUserQuestion(
  header: "{area_name}",
  question: "{specific question}",
  options: [
    { label: "{choice_1}", description: "{what this means}" },
    { label: "{choice_2}", description: "{what this means}" },
    { label: "You decide", description: "Implementer's discretion" }
  ]
)
```

每个区域最多 2 个问题。收集所有决策。

**4d. 分类决策：**

- **Locked**：firm decisions that cannot be changed during implementation
- **Free**：open for implementation discretion
- **Deferred**：postponed (captured but not acted on in this task)

**4e. 写入 context.md：**

```markdown
# Standard Task: {DESCRIPTION} - Context

**Gathered:** {date}
**Status:** Ready for planning

## Task Boundary

{DESCRIPTION}

## Constraints

### Locked
{decisions that are final and must be followed}

### Free
{decisions left to implementer discretion, including "You decide" areas}

### Deferred
{ideas captured but out of scope for this task}
```

写入 `${STANDARD_DIR}/context.md`。
报告："Context captured: ${STANDARD_DIR}/context.md"

---

### Step 4.5: 加载项目 Specs

```
specs_content = cat .workflow/specs/*.md 2>/dev/null || echo ""
```

传递给 Step 5 的 planner agent。

---

### Step 5: Spawn Planner

**Spawn workflow-planner：**

Spawn `agent-planner` agent：

- **Context**: mode (`standard` 或 `standard-full`), directory, description, state.json, CLAUDE.md, specs, context.md (如果 discuss 模式)
- **Constraints**: 单个计划 1-3 个原子任务，无研究阶段。Full 模式：~40% context 使用量 + 每个 task 需要 files/action/convergence.criteria/implementation。默认：~30% context 使用量。
- **Output**: `${STANDARD_DIR}/plan.json`, `${STANDARD_DIR}/.task/TASK-{NNN}.json`. 返回 `## PLANNING COMPLETE` 和计划路径。

Planner 返回后：
1. 验证 plan.json 存在于 `${STANDARD_DIR}/plan.json`
2. 更新 index.json plan 字段
3. 报告："Plan created: ${STANDARD_DIR}/plan.json"

如果计划未找到："Planner failed to create plan.json"

---

### Step 6: 计划检查（仅当 $FULL_MODE）

**计划检查循环：**

如果 NOT $FULL_MODE 则完全跳过。

```
------------------------------------------------------------
  WORKFLOW > CHECKING PLAN
------------------------------------------------------------
Spawning plan checker...
```

生成 `agent-plan-checker` agent 验证 plan.json 和 TASK-*.json：

- **Check dimensions**: 需求覆盖、任务完整性（files/action/convergence.criteria/implementation）、范围合理性（1-3 个任务）、上下文合规性（如果 discuss 模式）
- **Return**: `## VERIFICATION PASSED` 或 `## ISSUES FOUND` + 结构化问题列表

**处理检查器返回：**

- **VERIFICATION PASSED:** 继续 Step 7
- **ISSUES FOUND:** 进入修订循环

**修订循环（最多 2 次迭代）：**

如果 iteration_count < 2：
- 显示："Sending back to planner for revision... (iteration {N}/2)"
- 生成带有修订上下文 + 检查器问题的 planner
- 用检查器重新检查
- 递增 iteration_count

如果 iteration_count >= 2：
- 显示："Max iterations reached. {N} issues remain."
- 提供选项：1) 强制继续，2) 中止

---

### Step 7: Spawn Executor

**Spawn workflow-executor：**

Spawn `agent-executor` agent：

- **Read**: plan.json, TASK-*.json, state.json, CLAUDE.md
- **Constraints**: 执行所有任务，每个任务原子提交，写入摘要到 `${STANDARD_DIR}/.summaries/TASK-{NNN}-summary.md`

Executor 返回后：
1. 验证摘要存在
2. 更新 index.json execution 字段
3. 报告完成状态

---

### Step 8: 验证（仅当 $FULL_MODE）

**执行后验证：**

如果 NOT $FULL_MODE 则完全跳过。

```
------------------------------------------------------------
  WORKFLOW > VERIFYING RESULTS
------------------------------------------------------------
Spawning verifier...
```

生成 `agent-verifier` agent：使用 plan.json 和摘要检查计划目标与实际代码库的对比。将结果写入 `${STANDARD_DIR}/verification.json`。

读取验证结果：
| 状态 | 动作 |
|------|------|
| passed | 存储 "Verified"，继续 |
| gaps_found | 显示差距，提供：1) 重新运行 executor，2) 接受现状 |

---

### Step 9: 更新状态

**更新 state.json：**

读取 state.json。将 standard 任务添加到 accumulated_context 或 standard_tasks 数组。

记录：
```json
{
  "id": "standard-{slug}-{date}",
  "description": "{DESCRIPTION}",
  "completed_at": "{ISO timestamp}",
  "directory": "{STANDARD_DIR}",
  "verified": {FULL_MODE ? verification_status : "skipped"}
}
```

更新 last_updated 时间戳。

---

### Step 10: 提交并完成

**最终提交和完成：**

更新 index.json 状态为 "completed"。

提交 standard 任务产物：
```bash
git add "${STANDARD_DIR}/" .workflow/state.json
git commit -m "standard({slug}): {DESCRIPTION}"
```

显示完成：

显示完成横幅 `WORKFLOW > STANDARD TASK COMPLETE`（如果适用则带有 `(FULL MODE)` 后缀）：
- 显示：Standard Task 名称、摘要路径（`${STANDARD_DIR}/.summaries/`）、目录路径
- Full 模式还显示：验证路径 + 状态（`${STANDARD_DIR}/verification.json`）
- 页脚：`Ready for next task: /tflow-standard`
