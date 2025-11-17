# 参赛者指南

## 目录结构

当有多人参赛时，每个参赛者应该在 `participants/` 目录下创建自己的子目录：

```
participants/
├── README.md                    # 参赛者说明文档
├── example_player/              # 示例参赛者（参考）
│   └── agent.py
├── player1/                     # 参赛者1的目录
│   └── agent.py                # 参赛者1的Agent实现
├── player2/                     # 参赛者2的目录
│   └── agent.py                # 参赛者2的Agent实现
└── ...
```

## 如何创建自己的Agent

### 步骤1：创建你的目录

在 `participants/` 目录下创建以你的名字或ID命名的目录：

```bash
mkdir participants/your_name
```

例如：
- `participants/zhangsan/`
- `participants/team_alpha/`
- `participants/player_001/`

### 步骤2：创建agent.py文件

在你的目录下创建 `agent.py` 文件，实现你的Agent类。

#### 代码Agent示例

```python
from agents.code_agent import CodeAgent
from game.agent import Observation
import math
import random

class Agent(CodeAgent):
    """我的Agent - 描述你的策略"""
    
    def step(self, observation: Observation) -> str:
        """
        实现你的策略逻辑
        
        Args:
            observation: 当前游戏状态观察对象
            
        Returns:
            行动指令字符串，可选值：
            - "move_up", "move_down", "move_left", "move_right"
            - "turn_left", "turn_right"
            - "shoot"
            - "idle"
        """
        # 你的策略代码
        if observation.enemies_in_view:
            # 有敌人时攻击
            closest = min(observation.enemies_in_view, key=lambda e: e['distance'])
            enemy_pos = tuple(closest['position'])
            
            if (self._is_aiming_at_from_obs(observation, enemy_pos) and 
                observation.shoot_cooldown == 0):
                return "shoot"
            
            # 转向敌人
            target_angle = self._angle_to_from_obs(observation, enemy_pos)
            current_angle = math.atan2(
                observation.my_direction[1],
                observation.my_direction[0]
            )
            angle_diff = target_angle - current_angle
            if angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            elif angle_diff < -math.pi:
                angle_diff += 2 * math.pi
            
            if abs(angle_diff) > 0.2:
                return "turn_right" if angle_diff > 0 else "turn_left"
        
        return "move_up"
```

#### Prompt Agent示例

```python
import os
from agents.prompt_agent import PromptAgent

class Agent(PromptAgent):
    """我的Prompt Agent"""
    
    def __init__(self, name: str, api_key: str = None):
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        super().__init__(name, api_key=api_key)
        
        # 自定义你的Prompt模板
        self.set_prompt_template("""
        你是一个顶级的战斗特工AI。你的目标是生存并击败所有敌人。
        
        当前游戏状态：
        - 你的生命值：{my_health}
        - 你的位置：({my_position[0]:.1f}, {my_position[1]:.1f})
        - 视野内的敌人：{enemies_info}
        
        请根据当前状态，分析最优策略，只返回一个动作字符串。
        你的决策是：
        """)
```

### 步骤3：确保类名正确

- **推荐**：使用 `Agent` 作为类名（加载器会优先查找）
- **或者**：使用其他名称，但确保类名唯一且继承自 `CodeAgent` 或 `PromptAgent`

## 如何运行比赛

### 方式1：使用自动加载器（推荐）

运行支持自动加载参赛者Agent的主程序：

```bash
python run_tournament_with_participants.py
```

这个程序会：
1. 自动扫描 `participants/` 目录下的所有子目录
2. 加载每个目录下的 `agent.py` 文件
3. 创建所有Agent实例
4. 运行比赛

### 方式2：手动导入

你也可以在代码中手动导入和使用：

```python
from participants.your_name.agent import Agent
from game.engine import GameEngine

# 创建你的Agent
my_agent = Agent("我的Agent")

# 创建游戏
agents = [my_agent, ...]  # 添加其他Agent
engine = GameEngine(agents)
engine.run()
```

## 命名规范

- **目录名**：使用小写字母、数字和下划线，例如 `zhangsan`, `team_alpha`
- **Agent类名**：推荐使用 `Agent`，或使用大驼峰命名，例如 `MyAgent`
- **文件名**：必须为 `agent.py`

## 注意事项

1. **不要修改框架代码**：只在你自己的目录下创建和修改文件
2. **不要导入其他参赛者的代码**：保持代码独立性
3. **Agent类名要唯一**：如果使用非 `Agent` 的类名，确保不与其他参赛者冲突
4. **遵循接口规范**：确保你的Agent继承自 `CodeAgent` 或 `PromptAgent`，并实现 `step` 方法
5. **测试你的Agent**：在提交前，确保你的Agent可以正常创建和运行

## 测试你的Agent

创建测试文件 `participants/your_name/test.py`：

```python
from participants.your_name.agent import Agent
from agents.code_agent import RandomAgent
from game.engine import GameEngine

# 创建你的Agent
my_agent = Agent("我的Agent")

# 创建测试对手
test_agent = RandomAgent("测试对手")

# 运行测试
engine = GameEngine([my_agent, test_agent])
winner = engine.run(max_turns=1000, verbose=True)

if winner:
    print(f"获胜者: {winner.name}")
```

## 常见问题

### Q: 如何查看我的Agent在比赛中的表现？

A: 运行 `run_tournament_with_participants.py`，比赛结束后会显示详细的统计信息，包括胜场、击杀数等。

### Q: 我可以使用外部库吗？

A: 可以，但需要确保所有依赖都在 `requirements.txt` 中，或者在你的 `agent.py` 文件中处理导入错误。

### Q: 我的Agent可以访问其他Agent的信息吗？

A: 不可以。每个Agent只能通过 `observation` 参数获取视野内的敌人信息，无法直接访问其他Agent的内部状态。

### Q: 如何调试我的Agent？

A: 可以在 `step` 方法中使用 `print` 输出调试信息，或者在测试文件中添加日志。

## 示例参考

查看 `participants/example_player/agent.py` 获取完整的示例代码。

