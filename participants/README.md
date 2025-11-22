# 参赛者Agent目录

## 目录结构

每个参赛者应该在此目录下创建自己的子目录，例如：

```
participants/
├── player1/              # 参赛者1的目录
│   └── agent.py         # 参赛者1的Agent实现
├── player2/              # 参赛者2的目录
│   └── agent.py         # 参赛者2的Agent实现
└── ...
```

## 如何创建自己的Agent

### 步骤1：创建你的目录

在 `participants/` 目录下创建以你的名字或ID命名的目录，例如：
- `participants/zhangsan/`
- `participants/team_alpha/`
- `participants/player_001/`

### 步骤2：创建agent.py文件

在你的目录下创建 `agent.py` 文件，实现你的Agent类。

#### 代码Agent示例

```python
from agents.code_agent import CodeAgent
from game.agent import Observation

class MyAgent(CodeAgent):
    """我的Agent - 描述你的策略"""
    
    def step(self, observation: Observation) -> str:
        """
        实现你的策略逻辑
        
        Args:
            observation: 当前游戏状态观察对象
            
        Returns:
            行动指令字符串
        """
        # 你的策略代码
        if observation.enemies_in_view:
            # 有敌人时攻击
            closest = min(observation.enemies_in_view, key=lambda e: e['distance'])
            if self._is_aiming_at_from_obs(observation, tuple(closest['position'])):
                return "shoot"
            return "turn_right"
        return "move_up"
```

#### Prompt Agent示例

```python
import os
from agents.prompt_agent import PromptAgent

class MyPromptAgent(PromptAgent):
    """我的Prompt Agent"""
    
    def __init__(self, name: str, api_key: str = None):
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        super().__init__(name, api_key=api_key)
        
        # 自定义你的Prompt模板
        self.set_prompt_template("""
        你的自定义Prompt...
        """)
```

### 步骤3：导出你的Agent类

确保你的 `agent.py` 文件中有一个主要的Agent类，类名建议使用 `Agent` 或 `MyAgent`。

### 步骤4：测试你的Agent

你可以创建一个测试文件来测试你的Agent：

```python
from participants.player1.agent import MyAgent
from game.engine import GameEngine

agent = MyAgent("我的Agent")
# 测试代码...
```

## 命名规范

- 目录名：使用小写字母、数字和下划线，例如 `zhangsan`, `team_alpha`
- Agent类名：使用大驼峰命名，例如 `MyAgent`, `SmartAgent`
- 文件名：使用小写字母和下划线，例如 `agent.py`, `my_agent.py`

## 注意事项

1. **不要修改框架代码**：只在你自己的目录下创建文件
2. **不要导入其他参赛者的代码**：保持代码独立性
3. **Agent类名要唯一**：避免与其他参赛者冲突
4. **遵循接口规范**：确保你的Agent继承自 `CodeAgent` 或 `PromptAgent`，并实现 `step` 方法

