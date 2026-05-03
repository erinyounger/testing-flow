---
name: tflow-standard
description: 使用内置 Claude Agent 执行通用任务（Plan → Execute → Verify）
argument-hint: "<任务描述> [--full] [--discuss]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Agent
  - Task
  - AskUserQuestion
---

<purpose>
使用标准工作流（Plan → Execute → Verify）执行通用任务。采用路径 A（Skill Tool → 内置 Agent），调用 agent-planner、agent-executor、agent-verifier 三个内置 Agent。适用于中小型任务，支持断点续做和原子提交。
</purpose>

<required_reading>
@.tflow/workflows/workflow-standard.md
</required_reading>

<context>
$ARGUMENTS

解析参数：
- `--full` 标志 — 启用计划检查（最多2次迭代）和执行后验证
- `--discuss` 标志 — 规划前的轻量级决策提取，识别灰区进行交互式讨论
- 其余文本作为任务描述
</context>

<execution>
完全按照 '.tflow/workflows/workflow-standard.md' 执行。

步骤 3 执行路径：
```
Spawn agent-planner agent（路径 A）
    ↓
agent-planner 输出：plan.json + TASK-*.json
    ↓
Spawn agent-executor agent（路径 A）
    ↓
agent-executor 输出：summaries/*.md + git commit
    ↓
（可选）Spawn agent-verifier agent（路径 A）
    ↓
verification.json
```

**完成后的下一步路由：**
- 任务完成，--full 验证通过 → /manage-status
- 任务完成，验证发现差距 → /quality-debug {issue}
- 任务完成，需要同步文档 → /quality-sync
- 需要完整阶段工作流 → /maestro-plan {phase}
</execution>

<error_codes>
| 代码 | 严重性 | 条件 | 恢复方式 |
|------|--------|------|----------|
| E001 | error | 任务描述为空 | 检查参数格式，重新运行并提供正确输入 |
| E002 | error | Scratch 目录创建失败 | 检查磁盘空间和 .workflow/ 权限 |
| E003 | error | 工作流模板缺失 | 检查 .tflow/workflows/workflow-standard.md 是否存在 |
| W001 | warning | 验证发现轻微问题 | 审查问题并判断是否需要修复 |
</error_codes>

<success_criteria>
- [ ] Scratch 任务目录创建于 .workflow/scratch/
- [ ] plan.json 包含任务定义和波次分组
- [ ] 所有任务执行并写入摘要
- [ ] 每个任务原子 git 提交
- [ ] state.json 更新 scratch 任务条目
- [ ] （--full）verification.json 包含三层验证结果
</success_criteria>
