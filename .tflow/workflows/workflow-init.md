# Workflow: tflow-init

测试流程工作空间初始化。通过自动状态检测创建办公流程基础设施，不涉及代码规范或开发流程配置。

---

## Step 1: 状态检测

检测当前工作空间状态，确定初始化路径。

```
state.json exists → Path C (已初始化) | .tflow/ exists → Path B (存在工作空间) | else → Path A (空工作空间)
```

### Path A: 空工作空间 (Greenfield)

1. **信息收集** -- 收集测试流程基本信息：

   打开提问："这个测试流程用于什么场景？"
   等待响应后继续：
   - 测试域（功能测试、集成测试、回归测试、预发布验证等）
   - 目标系统/服务
   - 测试范围和边界
   - 关键干系人（谁发起、谁执行、谁接收结果）
   - 成功标准

   Decision gate: 当收集到足够信息时，问"是否创建工作空间配置？"
   - "创建" → 继续
   - "继续探索" → 继续提问

   如果 `--auto` flag: 跳过交互，从 @ 引用文档提取。
   如果 `--from-template TEMPLATE-ID`:
   - 加载预设模板配置
   - 填充项目信息

2. **工作流偏好** -- 配置测试流程设置：

   Round 1 — 核心设置 (AskUserQuestion):
   - 执行模式: 顺序执行 / 并行执行 / 混合
   - 验证级别: 基础验证 / 完整验证 / 自定义
   - 通知: 邮件通知 / 内部通知 / 无

   Round 2 — 流程选项:
   - 状态跟踪: 启用 / 禁用
   - 结果归档: 自动归档 / 手动归档
   - 审批流程: 需要审批 / 自动通过

   写入 `.tflow/config.json`。

   如 `--auto`: 使用默认值（标准、顺序、基础验证、无通知）。

3. **创建项目文件:**
   - `.tflow/project.md` -- 测试域、目标、流程边界
   - `.tflow/state.json` -- 状态初始化
   - `.tflow/config.json` -- 已创建

### Path B: 已有工作空间 (有 .tflow/ 但无 state.json)

1. 创建 `.tflow/` 目录结构（如不存在）
2. 创建 `.tflow/state.json`（status: "idle"）
3. 询问是否复用现有配置或重新配置
4. 运行工作流偏好（与 Path A Step 2 相同）
5. 收集项目信息（与 Path A Step 1 相同）

### Path C: 已初始化工作空间

1. 读取 `.tflow/state.json`
2. 显示："工作空间已初始化。当前状态: {status}"
3. 路由到 `/tflow-status`

---

## Step 2: 目录结构创建

创建标准目录结构：

```
.tflow/
  project.md          ✓ (测试域和目标)
  state.json          ✓ (当前状态)
  config.json         ✓ (流程配置)
  workflows/          ✓ (工作流模板)
    workflow-standard.md  ✓ (标准任务流程)
  tasks/              ✓ (任务目录)
  artifacts/          ✓ (产物目录)
  history/            ✓ (历史记录)
```

---

## Step 3: 工作流模板初始化

确保标准工作流模板存在：

1. `.tflow/workflows/workflow-standard.md` -- 标准任务流程（tflow-standard 命令调用）

---

## Step 4: 验证并完成

1. 验证所有必要文件存在
2. 显示初始化摘要:
   - 工作空间名称和测试域
   - 配置要点（执行模式、验证级别）
3. 路由下一步:
   - "运行 `/tflow-standard <任务描述>` 创建标准测试任务"
   - "运行 `/tflow-status` 查看工作空间状态"
   - "运行 `/tflow-plan` 规划测试阶段"
