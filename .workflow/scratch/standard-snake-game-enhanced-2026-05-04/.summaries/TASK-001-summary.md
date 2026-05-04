# TASK-001: 穿墙功能 + 速度调节 (Wave 1)

## Changes
- `index.html`: 添加速度选择器下拉框 CSS 和 HTML（慢150ms/中100ms/快60ms）
- `index.html`: 修改 `moveSnake()` 使用取模运算实现穿墙功能 `(x + direction.x + GRID_SIZE) % GRID_SIZE`
- `index.html`: 修改 `checkCollision()` 移除墙壁碰撞检测（穿墙模式下不撞墙死亡）
- `index.html`: 修改 `update()` 使用动态 `this.gameSpeed` 替代常量 `GAME_SPEED`
- `index.html`: 速度选择器 `change` 事件监听器实时更新游戏速度

## Verification
- [x] 蛇从任意墙壁穿过后从对侧进入（取模运算）: `moveSnake()` 第433-434行使用 `+ GRID_SIZE) % GRID_SIZE`
- [x] 速度选择器显示：慢(150ms)/中(100ms)/快(60ms): HTML 第245-249行
- [x] 速度设置在游戏开始前可调整: `speedSelect` change 事件在游戏开始前即可触发

## Tests
- [x] 无测试命令定义（手动验证游戏功能）

## Deviations
- None

## Notes
- 穿墙功能通过取模运算实现，蛇头坐标始终在 [0, GRID_SIZE) 范围内
- 速度调节使用 `this.gameSpeed` 动态属性，支持游戏中途切换速度
- 原 GAME_SPEED 常量已改为 SPEED_SLOW/MEDIUM/FAST 三个常量
