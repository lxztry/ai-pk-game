# Project Context

## Purpose

AI竞技平台（AI PK Game）是一个游戏化的AI竞技平台，通过统一框架让参与者通过Prompt工程或代码编写来优化AI Agent，进行自动对战。

**核心目标**：
- 提供一个统一的策略射击游戏框架
- 支持两种开发方式：Prompt派（通过LLM生成决策）和代码派（直接编写Python策略）
- 实现完整的比赛系统（循环赛、淘汰赛、分组比赛、在线对战）
- 提供精美的可视化回放系统

**游戏模式**：二维网格策略射击游戏，Agent在包含障碍物的地图上对战，通过移动、转向、射击等动作击败对手。

## Tech Stack

### 核心语言和运行时
- **Python 3.x** - 主要编程语言
- 使用类型提示（typing模块）增强代码可读性和类型安全

### 主要依赖库
- **numpy** (>=1.24.0) - 数值计算
- **openai** (>=1.0.0) - OpenAI API客户端（用于Prompt Agent，可选）
- **flask** (>=2.3.0) - Web框架（用于在线对战服务器）
- **flask-cors** (>=4.0.0) - 跨域资源共享支持
- **colorama** (>=0.4.6) - 命令行颜色输出

### 开发工具
- **OpenSpec** - 规范驱动的开发流程管理

## Project Conventions

### Code Style

**命名约定**：
- 使用 `snake_case` 命名变量、函数和方法
- 使用 `PascalCase` 命名类
- 私有方法/属性使用单下划线前缀（如 `_angle_to_from_obs`）
- 常量使用 `UPPER_SNAKE_CASE`

**代码格式**：
- 使用4个空格缩进（不使用Tab）
- 行长度建议不超过100字符
- 类和方法必须包含文档字符串（docstring）
- 使用类型提示标注函数参数和返回值

**文档字符串格式**：
```python
"""
模块或类的简要描述
"""
```

**导入顺序**：
1. 标准库导入
2. 第三方库导入
3. 本地模块导入

### Architecture Patterns

**核心架构模式**：

1. **游戏引擎模式** (`game/engine.py`)
   - `GameEngine` 类负责游戏循环、状态管理、物理计算
   - `GameState` 类管理游戏状态（Agent、子弹、障碍物、补给等）
   - 回合制游戏循环

2. **Agent模式** (`game/agent.py`, `agents/`)
   - `Agent` 抽象基类定义接口
   - `CodeAgent` 和 `PromptAgent` 提供不同实现方式
   - 所有Agent通过 `step(observation: Observation) -> str` 方法返回动作

3. **观察者模式**
   - `Observation` 对象封装Agent可感知的游戏状态
   - Agent只能通过Observation获取信息，不能直接访问游戏状态

4. **模块化设计**
   - `game/` - 游戏核心逻辑
   - `agents/` - Agent实现
   - `tournament/` - 比赛系统
   - `visualizer/` - 可视化工具
   - `online/` - Web服务器
   - `participants/` - 参赛者Agent目录

**设计原则**：
- 单一职责：每个模块专注于特定功能
- 开放封闭：通过继承扩展Agent行为
- 依赖倒置：Agent依赖抽象Observation接口

### Testing Strategy

**测试文件**：
- `test_basic.py` - 基础功能测试
- `test_participants.py` - 参赛者Agent测试

**测试方法**：
- 使用简单的功能测试验证游戏基本流程
- 测试Agent行为是否符合预期
- 验证游戏引擎的正确性

**测试运行**：
```bash
python test_basic.py
python test_participants.py
```

### Git Workflow

**分支策略**：
- 主分支：`main` 或 `master`（稳定版本）
- 功能分支：`feature/功能名称`
- 修复分支：`fix/问题描述`

**提交约定**：
- 使用清晰的中文或英文提交信息
- 提交信息应描述做了什么改动
- 建议格式：`类型: 简短描述`（如 `feat: 添加新武器类型`）

**忽略文件**：
- `__pycache__/` - Python缓存目录
- `*.pyc` - 编译的Python文件
- `replays/*.html` - 生成的回放文件（可能很大）
- `online/rankings.db` - SQLite数据库文件

## Domain Context

### 游戏核心概念

**游戏世界**：
- 二维网格地图（默认100x100）
- 包含随机生成的矩形障碍物（AABB碰撞检测）
- 支持多种补给物品和武器

**Agent动作**：
- `move_up/down/left/right` - 移动
- `turn_left/right` - 转向
- `shoot` - 射击（有冷却时间）
- `idle` - 不执行动作

**武器系统**：
- 普通武器：伤害10，冷却20回合
- 霰弹枪：三发散射，每发伤害8，冷却25回合，需要弹药
- 狙击枪：高伤害25，高速子弹，冷却35回合，需要弹药
- 火箭筒：伤害20，溅射效果，冷却40回合，需要弹药

**获胜条件**：
1. 直接获胜：成为唯一存活的Agent
2. 超时判定：达到最大回合数（默认500）后，按评分判定
   - 评分 = 击杀数 × 10000 + 剩余血量
   - 评分最高者获胜

**团队模式**：
- Agent可以设置 `team_id`
- 同队Agent不会互相伤害
- 当只剩一个队伍存活时，该队伍获胜

### Agent开发方式

**代码派（CodeAgent）**：
- 继承 `CodeAgent` 类
- 实现 `step(observation: Observation) -> str` 方法
- 直接编写Python逻辑实现策略

**Prompt派（PromptAgent）**：
- 继承 `PromptAgent` 类
- 通过自然语言Prompt引导LLM生成决策
- 需要OpenAI API Key

### Observation对象结构

Agent通过 `Observation` 对象获取游戏状态：
- `my_health` - 当前血量
- `my_position` - 当前位置 (x, y)
- `my_direction` - 当前方向向量 (dx, dy)
- `my_weapon` - 当前武器类型
- `my_ammo` - 当前武器弹药数
- `enemies_in_view` - 视野内的敌人列表
- `bullets_in_view` - 视野内的子弹列表
- `obstacles_in_view` - 视野内的障碍物列表
- `supplies_in_view` - 视野内的补给列表
- `map_boundary` - 地图边界 [width, height]
- `shoot_cooldown` - 射击冷却时间

## Important Constraints

**技术约束**：
- Python 3.7+ 要求（使用类型提示和现代语法）
- 游戏引擎是单线程的，不支持并发游戏循环
- Agent的 `step` 方法必须快速返回，不能阻塞（Prompt Agent需要异步处理）

**游戏规则约束**：
- 最大回合数限制（默认500回合）
- 射击冷却时间限制
- 地图边界限制
- 障碍物碰撞检测

**性能约束**：
- 游戏循环需要高效运行，避免性能瓶颈
- 可视化系统需要优化，避免生成过大的HTML文件

**安全约束**：
- Agent代码在沙箱环境中运行（当前实现中，Agent可以访问所有Python功能，未来可能需要限制）
- Prompt Agent需要API Key，不应硬编码在代码中

## External Dependencies

### OpenAI API（可选）
- **用途**：Prompt Agent使用OpenAI API生成决策
- **配置**：通过环境变量 `OPENAI_API_KEY` 或构造函数参数提供
- **模型**：默认使用 `gpt-4o-mini`，可配置
- **要求**：需要有效的OpenAI API Key和网络连接

### Web服务器依赖
- **Flask**：用于在线对战系统的Web服务器
- **Flask-CORS**：支持跨域请求
- **SQLite**：用于存储对战记录和排名（通过Python标准库sqlite3）

### 其他依赖
- **NumPy**：数值计算（虽然当前代码中可能未直接使用，但在依赖列表中）
- **Colorama**：命令行颜色输出（用于console_visualizer）

### 环境要求
- Python 3.7+
- pip包管理器
- 网络连接（仅在使用Prompt Agent或在线对战功能时需要）
