# TASK-001: 实现贪吃蛇游戏核心逻辑 (Wave 1)

## Changes
- `/home/eeric/code/testing-flow/index.html`: 修复损坏的HTML文件，创建包含贪吃蛇游戏完整HTML/CSS/JS的单文件实现

## Verification
- [x] 20x20网格Canvas: GRID_SIZE=20, CELL_SIZE=20, Canvas 400x400
- [x] 方向键和WASD控制: handleKeyDown支持ArrowUp/Down/Left/Right和w/a/s/d
- [x] 食物随机生成: generateFood在20x20网格内随机生成且不在蛇身上
- [x] 蛇撞墙或撞自己时游戏结束: checkCollision检测边界和自撞
- [x] tick speed = 100ms: GAME_SPEED = 100

## Tests
- [x] node tests/snake.test.js: 30 通过, 0 失败

## Deviations
- None

## Notes
- 文件之前被损坏（测试代码拼接在HTML之前），已完全重写
- 游戏使用requestAnimationFrame实现平滑的游戏循环
- 碰撞检测包含边界检测和自撞检测
