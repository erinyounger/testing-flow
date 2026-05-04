/**
 * 贪吃蛇游戏单元测试
 * 运行方式: 在浏览器控制台执行 或 Node.js环境
 */

const GRID_SIZE = 20;
const CELL_SIZE = 20;
const GAME_SPEED = 100;

class SnakeGame {
    constructor() {
        this.init();
    }

    init() {
        this.snake = [
            { x: 10, y: 10 },
            { x: 9, y: 10 },
            { x: 8, y: 10 }
        ];
        this.direction = { x: 1, y: 0 };
        this.nextDirection = { x: 1, y: 0 };
        this.food = this.generateFood();
        this.score = 0;
        this.gameState = 'idle';
    }

    handleKeyDown(key) {
        const keyMap = {
            'ArrowUp': { x: 0, y: -1 },
            'ArrowDown': { x: 0, y: 1 },
            'ArrowLeft': { x: -1, y: 0 },
            'ArrowRight': { x: 1, y: 0 },
            'w': { x: 0, y: -1 },
            'W': { x: 0, y: -1 },
            's': { x: 0, y: 1 },
            'S': { x: 0, y: 1 },
            'a': { x: -1, y: 0 },
            'A': { x: -1, y: 0 },
            'd': { x: 1, y: 0 },
            'D': { x: 1, y: 0 }
        };

        const newDir = keyMap[key];
        if (newDir) {
            if (this.isOppositeDirection(newDir, this.direction)) {
                return;
            }
            this.nextDirection = newDir;
        }
    }

    isOppositeDirection(dir1, dir2) {
        return dir1.x === -dir2.x && dir1.y === -dir2.y;
    }

    moveSnake() {
        const head = {
            x: this.snake[0].x + this.direction.x,
            y: this.snake[0].y + this.direction.y
        };

        this.snake.unshift(head);
        this.snake.pop();
    }

    checkCollision() {
        const head = this.snake[0];

        if (head.x < 0 || head.x >= GRID_SIZE || head.y < 0 || head.y >= GRID_SIZE) {
            return true;
        }

        for (let i = 1; i < this.snake.length; i++) {
            if (head.x === this.snake[i].x && head.y === this.snake[i].y) {
                return true;
            }
        }

        return false;
    }

    checkFoodCollision() {
        const head = this.snake[0];
        return head.x === this.food.x && head.y === this.food.y;
    }

    eatFood() {
        const tail = this.snake[this.snake.length - 1];
        this.snake.push({ ...tail });

        this.score += 10;
        this.food = this.generateFood();
    }

    generateFood() {
        let newFood;
        do {
            newFood = {
                x: Math.floor(Math.random() * GRID_SIZE),
                y: Math.floor(Math.random() * GRID_SIZE)
            };
        } while (this.isOnSnake(newFood));

        return newFood;
    }

    isOnSnake(pos) {
        return this.snake.some(segment => segment.x === pos.x && segment.y === pos.y);
    }
}

function runTests() {
    const results = [];
    let passCount = 0;
    let failCount = 0;

    function test(name, fn) {
        try {
            fn();
            results.push({ name, passed: true });
            passCount++;
            console.log(`✓ ${name}`);
        } catch (e) {
            results.push({ name, passed: false, error: e.message });
            failCount++;
            console.log(`✗ ${name}: ${e.message}`);
        }
    }

    function assertEqual(actual, expected, message) {
        if (actual !== expected) {
            throw new Error(`${message || 'Assertion failed'}: expected ${expected}, got ${actual}`);
        }
    }

    function assertTrue(value, message) {
        if (!value) {
            throw new Error(message || 'Expected true, got ' + value);
        }
    }

    function assertFalse(value, message) {
        if (value) {
            throw new Error(message || 'Expected false, got ' + value);
        }
    }

    console.log('=== 贪吃蛇游戏单元测试 ===\n');

    test('SnakeGame初始化 - 蛇长度为3', () => {
        const game = new SnakeGame();
        assertEqual(game.snake.length, 3, '初始蛇长度应为3');
    });

    test('SnakeGame初始化 - 初始分数为0', () => {
        const game = new SnakeGame();
        assertEqual(game.score, 0, '初始分数应为0');
    });

    test('SnakeGame初始化 - 初始方向向右', () => {
        const game = new SnakeGame();
        assertEqual(game.direction.x, 1, '水平方向应为1');
        assertEqual(game.direction.y, 0, '垂直方向应为0');
    });

    test('SnakeGame初始化 - 食物不在蛇身上', () => {
        const game = new SnakeGame();
        assertFalse(game.isOnSnake(game.food), '食物不应在蛇身上');
    });

    test('方向键控制 - ArrowUp设置向上方向', () => {
        const game = new SnakeGame();
        game.handleKeyDown('ArrowUp');
        assertEqual(game.nextDirection.x, 0, '水平方向应为0');
        assertEqual(game.nextDirection.y, -1, '垂直方向应为-1');
    });

    test('方向键控制 - ArrowDown设置向下方向', () => {
        const game = new SnakeGame();
        game.handleKeyDown('ArrowDown');
        assertEqual(game.nextDirection.x, 0, '水平方向应为0');
        assertEqual(game.nextDirection.y, 1, '垂直方向应为1');
    });

    test('方向键控制 - ArrowLeft设置向左方向', () => {
        const game = new SnakeGame();
        game.direction = { x: 0, y: 1 };
        game.handleKeyDown('ArrowLeft');
        assertEqual(game.nextDirection.x, -1, '水平方向应为-1');
        assertEqual(game.nextDirection.y, 0, '垂直方向应为0');
    });

    test('方向键控制 - ArrowRight设置向右方向', () => {
        const game = new SnakeGame();
        game.handleKeyDown('ArrowRight');
        assertEqual(game.nextDirection.x, 1, '水平方向应为1');
        assertEqual(game.nextDirection.y, 0, '垂直方向应为0');
    });

    test('方向键控制 - WASD w键设置向上方向', () => {
        const game = new SnakeGame();
        game.handleKeyDown('w');
        assertEqual(game.nextDirection.y, -1, '垂直方向应为-1');
    });

    test('方向键控制 - WASD s键设置向下方向', () => {
        const game = new SnakeGame();
        game.handleKeyDown('s');
        assertEqual(game.nextDirection.y, 1, '垂直方向应为1');
    });

    test('方向键控制 - WASD a键设置向左方向', () => {
        const game = new SnakeGame();
        game.direction = { x: 0, y: 1 };
        game.handleKeyDown('a');
        assertEqual(game.nextDirection.x, -1, '水平方向应为-1');
    });

    test('方向键控制 - WASD d键设置向右方向', () => {
        const game = new SnakeGame();
        game.handleKeyDown('d');
        assertEqual(game.nextDirection.x, 1, '水平方向应为1');
    });

    test('防止掉头 - 向右不能直接改成向左', () => {
        const game = new SnakeGame();
        game.direction = { x: 1, y: 0 };
        game.handleKeyDown('ArrowLeft');
        assertEqual(game.nextDirection.x, 1, '水平方向保持为1（不能掉头）');
    });

    test('防止掉头 - 向左不能直接改成向右', () => {
        const game = new SnakeGame();
        game.direction = { x: -1, y: 0 };
        game.nextDirection = { x: -1, y: 0 };
        game.handleKeyDown('ArrowRight');
        assertEqual(game.nextDirection.x, -1, '水平方向保持为-1（不能掉头）');
    });

    test('防止掉头 - 向上不能直接改成向下', () => {
        const game = new SnakeGame();
        game.direction = { x: 0, y: -1 };
        game.nextDirection = { x: 0, y: -1 };
        game.handleKeyDown('ArrowDown');
        assertEqual(game.nextDirection.y, -1, '垂直方向保持为-1（不能掉头）');
    });

    test('防止掉头 - 向下不能直接改成向上', () => {
        const game = new SnakeGame();
        game.direction = { x: 0, y: 1 };
        game.nextDirection = { x: 0, y: 1 };
        game.handleKeyDown('ArrowUp');
        assertEqual(game.nextDirection.y, 1, '垂直方向保持为1（不能掉头）');
    });

    test('碰撞检测 - 撞墙（上边界）', () => {
        const game = new SnakeGame();
        game.snake[0] = { x: 10, y: -1 };
        assertTrue(game.checkCollision(), '蛇头在边界外应检测为碰撞');
    });

    test('碰撞检测 - 撞墙（下边界）', () => {
        const game = new SnakeGame();
        game.snake[0] = { x: 10, y: GRID_SIZE };
        assertTrue(game.checkCollision(), '蛇头在边界外应检测为碰撞');
    });

    test('碰撞检测 - 撞墙（左边界）', () => {
        const game = new SnakeGame();
        game.snake[0] = { x: -1, y: 10 };
        assertTrue(game.checkCollision(), '蛇头在边界外应检测为碰撞');
    });

    test('碰撞检测 - 撞墙（右边界）', () => {
        const game = new SnakeGame();
        game.snake[0] = { x: GRID_SIZE, y: 10 };
        assertTrue(game.checkCollision(), '蛇头在边界外应检测为碰撞');
    });

    test('碰撞检测 - 撞自己身体', () => {
        const game = new SnakeGame();
        game.snake[0] = { x: 9, y: 10 };
        assertTrue(game.checkCollision(), '蛇头在自己身上应检测为碰撞');
    });

    test('碰撞检测 - 无碰撞时返回false', () => {
        const game = new SnakeGame();
        assertFalse(game.checkCollision(), '正常位置应检测为无碰撞');
    });

    test('食物碰撞检测 - 吃到食物', () => {
        const game = new SnakeGame();
        game.food = { x: 10, y: 10 };
        assertTrue(game.checkFoodCollision(), '蛇头在食物位置应检测为吃到食物');
    });

    test('食物碰撞检测 - 未吃到食物', () => {
        const game = new SnakeGame();
        game.food = { x: 15, y: 15 };
        assertFalse(game.checkFoodCollision(), '蛇头不在食物位置应检测为未吃到食物');
    });

    test('吃食物 - 蛇增长', () => {
        const game = new SnakeGame();
        const initialLength = game.snake.length;
        game.food = { x: game.snake[0].x, y: game.snake[0].y };
        if (game.checkFoodCollision()) {
            game.eatFood();
        }
        assertEqual(game.snake.length, initialLength + 1, '吃食物后蛇长度应增加1');
    });

    test('吃食物 - 分数增加', () => {
        const game = new SnakeGame();
        const initialScore = game.score;
        game.food = { x: game.snake[0].x, y: game.snake[0].y };
        if (game.checkFoodCollision()) {
            game.eatFood();
        }
        assertEqual(game.score, initialScore + 10, '吃食物后分数应增加10');
    });

    test('吃食物 - 食物重新生成', () => {
        const game = new SnakeGame();
        game.food = { x: game.snake[0].x, y: game.snake[0].y };
        if (game.checkFoodCollision()) {
            const oldFood = { ...game.food };
            game.eatFood();
            assertFalse(
                game.food.x === oldFood.x && game.food.y === oldFood.y,
                '吃食物后食物应重新生成'
            );
        }
    });

    test('移动蛇 - 位置正确更新', () => {
        const game = new SnakeGame();
        const oldHead = { ...game.snake[0] };
        game.direction = { x: 1, y: 0 };
        game.nextDirection = { x: 1, y: 0 };
        game.moveSnake();
        assertEqual(game.snake[0].x, oldHead.x + 1, '蛇头x应增加1');
        assertEqual(game.snake[0].y, oldHead.y, '蛇头y应保持不变');
    });

    test('isOnSnake - 检测点在蛇身上', () => {
        const game = new SnakeGame();
        assertTrue(game.isOnSnake(game.snake[0]), '蛇头应在蛇身上');
    });

    test('isOnSnake - 检测点不在蛇身上', () => {
        const game = new SnakeGame();
        assertFalse(game.isOnSnake({ x: 0, y: 0 }), '(0,0)不在蛇身上');
    });

    console.log(`\n=== 测试结果: ${passCount} 通过, ${failCount} 失败 ===`);

    return { passCount, failCount, results };
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SnakeGame, runTests };
}

runTests();
