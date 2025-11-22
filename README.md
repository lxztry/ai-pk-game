# AI竞技平台 🏟️

一个游戏化的AI竞技平台，通过统一框架让参与者通过Prompt工程或代码编写来优化AI Agent，进行自动对战。

## 核心概念

在一个统一的游戏项目框架下（策略射击游戏），每位参与者扮演一个"AI驯兽师"。他们通过以下两种方式之一来控制和优化自己的游戏角色（AI Agent）：

1. **Prompt派**：只通过编写和优化自然语言Prompt，来引导大语言模型（如GPT-4）实时生成角色的行动决策。
2. **代码派**：直接编写Python代码，实现更复杂、精准的策略逻辑。

所有AI Agent在同一个竞技场中自动对抗，最终决出最强"驯兽师"。

## 游戏规则

### 游戏模式：策略射击游戏

- **场地**：一个二维网格（默认100x100）
- **角色**：每个玩家控制一个特工
- **目标**：击败所有其他特工，成为最后存活者
- **核心动作**：
  - **移动**：上下左右移动
  - **转向**：改变面向方向
  - **射击**：向面向方向发射子弹，有冷却时间
  - **观察**：获取周围环境信息（视野内的敌人位置、距离、自己的血量等）

## 安装

```bash
# 克隆或下载项目
cd pk

# 安装依赖
pip install -r requirements.txt
```

## 快速开始

### 1. 网页版可视化对战（推荐）✨

生成精美的网页版游戏回放，在浏览器中查看：

```bash
python examples/web_match.py
```

这将生成一个 `game_replay.html` 文件，在浏览器中打开即可看到：
- 🎨 精美的图形界面和动画效果
- 🎯 实时显示Agent位置、方向、血量条
- 💥 子弹轨迹和碰撞效果
- 📊 实时统计信息面板
- ⏯️ 播放控制（播放/暂停/加速/减速）

### 2. 命令行实时对战

运行一场简单的多Agent对战，在命令行实时显示：

```bash
python examples/simple_match.py
```

### 3. 比赛系统示例

运行循环赛或淘汰赛：

```bash
python examples/tournament_example.py
```

### 4. Prompt Agent示例

使用LLM驱动的Agent（需要OpenAI API Key）：

```bash
# 设置API Key
export OPENAI_API_KEY='your-api-key'

# 运行示例
python examples/prompt_agent_example.py
```

## 项目结构

```
pk/
├── game/                  # 游戏核心
│   ├── __init__.py
│   ├── agent.py          # Agent基类
│   └── engine.py         # 游戏引擎
├── agents/               # Agent实现
│   ├── __init__.py
│   ├── prompt_agent.py   # Prompt派Agent
│   └── code_agent.py     # 代码派Agent示例
├── participants/         # 参赛者Agent目录（多人参赛时使用）
│   ├── README.md         # 参赛者指南
│   ├── example_player/   # 示例参赛者
│   │   └── agent.py
│   └── ...               # 其他参赛者的目录
├── tournament/           # 比赛系统
│   ├── __init__.py
│   └── tournament.py     # 循环赛、淘汰赛
├── utils/                # 工具模块
│   ├── __init__.py
│   └── agent_loader.py   # Agent自动加载器
├── visualizer/           # 可视化工具
│   ├── __init__.py
│   ├── console_visualizer.py  # 命令行可视化
│   └── web_visualizer.py      # 网页版可视化
├── examples/             # 示例代码
│   ├── simple_match.py      # 命令行实时对战
│   ├── web_match.py         # 网页版对战（推荐）
│   ├── tournament_example.py
│   └── prompt_agent_example.py
├── run_tournament.py              # 主程序（使用默认Agent）
├── run_tournament_with_participants.py  # 主程序（自动加载参赛者）
├── requirements.txt
├── README.md
└── PARTICIPANTS_GUIDE.md  # 参赛者详细指南
```

## 如何参与

### 方式1：在participants目录下创建你的Agent（推荐）⭐

这是多人参赛的标准方式：

1. **创建你的目录**：
   ```bash
   mkdir participants/your_name
   ```

2. **创建agent.py文件**：
   ```python
   # participants/your_name/agent.py
   from agents.code_agent import CodeAgent
   from game.agent import Observation
   
   class Agent(CodeAgent):
       def step(self, observation: Observation) -> str:
           # 你的策略代码
           if observation.enemies_in_view:
               return "shoot"
           return "move_up"
   ```

3. **运行比赛**：
   ```bash
   python run_tournament_with_participants.py
   ```
   
   程序会自动发现并加载所有参赛者的Agent！

详细说明请查看 [PARTICIPANTS_GUIDE.md](PARTICIPANTS_GUIDE.md)

### 方式2：创建Prompt Agent

继承 `PromptAgent` 类并自定义Prompt模板：

```python
from agents.prompt_agent import PromptAgent

class MyPromptAgent(PromptAgent):
    def __init__(self, name, api_key):
        super().__init__(name, api_key)
        # 自定义Prompt模板
        self.set_prompt_template("""
        你的自定义Prompt...
        """)
```

### 方式3：创建代码Agent（直接使用）

继承 `CodeAgent` 类并实现 `step` 方法：

```python
from agents.code_agent import CodeAgent
from game.agent import Observation

class MyCodeAgent(CodeAgent):
    def step(self, observation: Observation) -> str:
        # 实现你的策略逻辑
        enemies = observation.enemies_in_view
        if enemies:
            # 攻击最近的敌人
            closest = min(enemies, key=lambda e: e['distance'])
            # ... 实现攻击逻辑
            return "shoot"
        return "move_up"
```

### 方式4：使用现有Agent

项目已包含多个示例Agent：

- `RandomAgent`: 完全随机行动
- `AggressiveAgent`: 激进型，主动攻击
- `DefensiveAgent`: 防御型，优先躲避
- `SmartAgent`: 综合策略

## Agent API

### Observation对象

Agent的 `step` 方法接收一个 `Observation` 对象，包含：

- `my_health`: 当前血量
- `my_position`: 当前位置 (x, y)
- `my_direction`: 当前方向向量 (dx, dy)
- `enemies_in_view`: 视野内的敌人列表
- `bullets_in_view`: 视野内的子弹列表
- `map_boundary`: 地图边界 [width, height]
- `shoot_cooldown`: 射击冷却时间

### 可用动作

- `"move_up"`: 向上移动
- `"move_down"`: 向下移动
- `"move_left"`: 向左移动
- `"move_right"`: 向右移动
- `"turn_left"`: 向左转向
- `"turn_right"`: 向右转向
- `"shoot"`: 射击（需要冷却时间为0）
- `"idle"`: 不执行任何动作

## 比赛系统

### 循环赛

每个Agent与其他所有Agent对战，根据胜场和击杀数排名：

```python
from tournament.tournament import RoundRobinTournament

tournament = RoundRobinTournament(agents, save_replay=True, replay_dir="replays")
rankings = tournament.run(verbose=True)
```

### 淘汰赛

单败淘汰制，直到决出冠军：

```python
from tournament.tournament import EliminationTournament

tournament = EliminationTournament(agents, save_replay=True, replay_dir="replays")
champion = tournament.run(verbose=True)
```

### 分组比赛

适合大规模参赛者（200+人）：

```python
from tournament.group_tournament import GroupTournament

tournament = GroupTournament(
    agents=agents,
    group_size=4,        # 每组4人
    advance_per_group=2, # 每组前2名出线
    save_replay=True,
    replay_dir="replays"
)
result = tournament.run(verbose=True)
```

## 可视化

项目提供两种可视化方式：

### 网页版可视化（推荐）

生成精美的HTML回放文件，在浏览器中查看：

```python
from visualizer.web_visualizer import WebVisualizer

visualizer = WebVisualizer(map_width=100, map_height=100)
# 记录游戏过程
visualizer.record_frame(state_info)
# 生成HTML文件
visualizer.render_replay(output_file="game_replay.html")
```

### 命令行可视化

实时在命令行显示游戏状态：

```python
from visualizer.console_visualizer import ConsoleVisualizer

visualizer = ConsoleVisualizer(map_width=100, map_height=100)
visualizer.render(state_info)
```

## 扩展建议

1. **添加新游戏元素**：障碍物、补给包、特殊武器等
2. **改进可视化**：使用pygame或其他图形库创建图形界面
3. **添加更多统计**：胜率、平均存活时间等
4. **支持团队战**：多人组队对战模式
5. **录制回放**：保存比赛录像供后续分析

## 贡献

欢迎提交Pull Request或Issue！

## 许可证

MIT License

