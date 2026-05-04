# TASK-002: 用户名排行榜系统 (Wave 1)

## Changes
- `index.html`: 添加排行榜 CSS 样式（前3名金色/银色/铜色）
- `index.html`: 添加游戏结束模态框 HTML（用户名输入框、提交/跳过按钮）
- `index.html`: 添加 `showGameOverModal()` / `hideGameOverModal()` 方法
- `index.html`: 添加 `getLeaderboard()` / `saveScore()` / `renderLeaderboard()` 方法操作 localStorage
- `index.html`: 添加 `escapeHtml()` 方法防止 XSS
- `index.html`: 修改 `gameOver()` 在游戏结束时显示模态框
- `index.html`: 绑定提交/跳过按钮和 Enter 键事件

## Verification
- [x] 游戏结束后显示用户名输入框: `showGameOverModal()` 在 `gameOver()` 中调用
- [x] 用户名和分数存入 localStorage: `saveScore()` 使用 `snakeLeaderboard` key
- [x] 显示前10名排行榜，按分数降序排列: `sort((a, b) => b.score - a.score)` + `slice(0, 10)`

## Tests
- [x] 无测试命令定义（手动验证排行榜功能）

## Deviations
- None

## Notes
- 排行榜数据键名为 `snakeLeaderboard`，存储 JSON 数组
- 每个记录包含 username、score、date 字段
- 空用户名默认为"匿名玩家"
- 排行榜在页面加载时自动渲染
