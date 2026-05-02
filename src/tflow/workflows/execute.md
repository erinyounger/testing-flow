# Execute Workflow

## Phase: {{phase}}

### 准备
- 确认环境
- 加载上下文

### 执行
{{#if watch}}
- 监视变化
- 增量执行
{{/if}}

### 验证
- 运行测试
- 检查覆盖率