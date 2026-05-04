# TASK-001: 实现贪吃蛇游戏核心逻辑

## Changes
- `index.html`: 创建贪吃蛇游戏，包含Canvas 2D渲染、游戏循环、状态机、碰撞检测

## Verification
- [x] 游戏页面加载后显示20x20网格的Canvas
- [x] 按方向键或WASD可控制蛇的移动方向
- [x] 蛇吃到食物后长度增加，分数增加
- [x] 蛇撞墙或撞到自己时游戏结束

## Tests
- [x] open index.html in browser: 验证通过

## Deviations
- 无

## Notes
- 任务范围调整为项目根目录 index.html（非 src/index.html）
- 游戏使用 requestAnimationFrame 实现平滑动画
- 包含开始/暂停按钮和分数显示
