# AI竞技平台 🏟️

一个游戏化的AI竞技平台，通过统一框架让参与者通过Prompt工程或代码编写来优化AI Agent，进行自动对战。

## ✨ 主要特性

- 🎮 **完整的游戏系统**：障碍物、补给、多种武器、团队对战
- 🤖 **灵活的AI开发**：支持Prompt派和代码派两种开发方式
- 🏆 **完善的比赛系统**：循环赛、淘汰赛、分组比赛、在线对战
- 📊 **精美的可视化**：网页版回放、命令行实时显示
- ⚖️ **智能获胜判定**：防止过早结束，超时后按评分判定
- 🔄 **自动回放生成**：所有比赛自动生成HTML回放文件

## 核心概念

在一个统一的游戏项目框架下（策略射击游戏），每位参与者扮演一个"AI驯兽师"。他们通过以下两种方式之一来控制和优化自己的游戏角色（AI Agent）：

1. **Prompt派**：只通过编写和优化自然语言Prompt，来引导大语言模型（如GPT-4）实时生成角色的行动决策。
2. **代码派**：直接编写Python代码，实现更复杂、精准的策略逻辑。

所有AI Agent在同一个竞技场中自动对抗，最终决出最强"驯兽师"。

## 游戏规则

### 游戏模式：策略射击游戏

- **场地**：一个二维网格（默认100x100），包含随机生成的障碍物（矩形墙体）
- **角色**：每个玩家控制一个特工
- **目标**：击败所有其他特工，成为最后存活者
- **核心动作**：
  - **移动**：上下左右移动（会被障碍物阻挡）
  - **转向**：改变面向方向
  - **射击**：向面向方向发射子弹，有冷却时间
  - **观察**：获取周围环境信息（视野内的敌人、子弹、障碍物、补给等）

### 游戏元素

- **障碍物**：地图上随机生成的矩形墙体，可以阻挡移动和子弹
- **补给系统**：
  - **血量包**：恢复25点血量
  - **弹药**：为特殊武器补充弹药
  - **武器**：拾取特殊武器（霰弹枪、狙击枪、火箭筒）
- **武器系统**：
  - **普通武器**：基础伤害10，冷却20回合
  - **霰弹枪**：三发散射，每发伤害8，冷却25回合
  - **狙击枪**：高伤害25，高速子弹，冷却35回合
  - **火箭筒**：伤害20，带溅射效果，冷却40回合

### 获胜条件

1. **直接获胜**：成为唯一存活的Agent
2. **超时判定**：达到最大回合数（默认500回合）后，按评分判定获胜者
   - 评分规则：击杀数 × 10000 + 剩余血量
   - 评分最高者获胜
3. **团队模式**：在团队对战中，当只剩一个队伍存活时，该队伍获胜

## 安装

```bash
# 克隆或下载项目
cd ai-pk-game

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

### 4. 团队对战示例

运行多人组队对战：

```bash
python examples/team_match.py
```

### 5. 在线对战系统（新功能）✨

启动Web服务器，在线选择对手进行对战，查看积分排名：

```bash
# 启动服务器
python run_online_server.py

# 在浏览器中访问 http://localhost:5000
```

**功能特性**：
- 🎮 在线选择对手进行对战
- 🏆 实时积分排名系统
- 📊 对战历史记录
- 🎬 自动生成回放文件
- ⚡ 异步对战，不阻塞界面

详细说明请查看 [ONLINE_GUIDE.md](ONLINE_GUIDE.md)

### 6. Prompt Agent示例

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
│   ├── tournament.py     # 循环赛、淘汰赛
│   ├── tournament_with_replay.py  # 支持回放的比赛系统
│   └── group_tournament.py  # 分组比赛系统（适合大规模参赛）
├── online/               # 在线对战系统
│   ├── __init__.py
│   ├── database.py       # 数据库管理（SQLite）
│   ├── server.py         # Flask Web服务器
│   ├── templates/        # Web界面模板
│   │   └── index.html
│   └── static/           # 静态文件
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
│   ├── quick_web_match.py   # 快速网页版对战
│   ├── tournament_example.py  # 比赛系统示例
│   ├── team_match.py        # 团队对战示例
│   └── prompt_agent_example.py  # Prompt Agent示例
├── run_tournament.py              # 主程序（使用默认Agent）
├── run_tournament_with_participants.py  # 主程序（自动加载参赛者）
├── run_online_server.py           # 启动在线对战服务器
├── requirements.txt
├── README.md
├── PARTICIPANTS_GUIDE.md          # 参赛者详细指南
└── ONLINE_GUIDE.md                # 在线对战系统使用指南
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
        
        # 检查是否有补给
        if observation.supplies_in_view:
            closest_supply = min(observation.supplies_in_view, key=lambda s: s['distance'])
            # 移动到补给位置...
        
        # 检查障碍物
        if observation.obstacles_in_view:
            # 避开障碍物...
        
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

- `my_health`: 当前血量（0-100）
- `my_position`: 当前位置 (x, y)
- `my_direction`: 当前方向向量 (dx, dy)，已标准化
- `my_team`: 队伍ID（团队模式使用）
- `my_weapon`: 当前武器类型（'normal' | 'shotgun' | 'sniper' | 'rocket'）
- `my_ammo`: 当前武器的弹药数（特殊武器需要弹药，普通武器为None）
- `enemies_in_view`: 视野内的敌人列表，每个敌人包含：
  - `name`: 敌人名称
  - `position`: 位置 [x, y]
  - `health`: 血量
  - `direction`: 方向向量
  - `distance`: 距离
  - `team_id`: 队伍ID
- `bullets_in_view`: 视野内的子弹列表，每个子弹包含：
  - `position`: 位置 [x, y]
  - `direction`: 方向向量
  - `distance`: 距离
- `obstacles_in_view`: 视野内的障碍物列表，每个障碍物包含：
  - `rect`: 矩形区域 [x, y, width, height]
  - `nearest_point`: 最近点 [x, y]
  - `distance`: 距离
- `supplies_in_view`: 视野内的补给列表，每个补给包含：
  - `position`: 位置 [x, y]
  - `type`: 类型（'health' | 'ammo_shotgun' | 'ammo_sniper' | 'ammo_rocket' | 'weapon_shotgun' | 'weapon_sniper' | 'weapon_rocket'）
  - `distance`: 距离
- `map_boundary`: 地图边界 [width, height]
- `shoot_cooldown`: 射击冷却时间（0表示可以射击）

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

### 团队对战

支持多人组队对战模式：

```python
from agents.code_agent import AggressiveAgent, DefensiveAgent
from game.engine import GameEngine

# 创建Agent并设置队伍
agent1 = AggressiveAgent("TeamA_Player1")
agent2 = DefensiveAgent("TeamA_Player2")
agent3 = AggressiveAgent("TeamB_Player1")
agent4 = DefensiveAgent("TeamB_Player2")

# 设置队伍ID（同队不互相伤害）
agent1.team_id = 1
agent2.team_id = 1
agent3.team_id = 2
agent4.team_id = 2

# 运行团队对战
engine = GameEngine([agent1, agent2, agent3, agent4])
winner = engine.run(max_turns=500)
```

## 回放系统

所有比赛系统都支持自动生成HTML回放文件：

- **自动保存**：每场比赛结束后自动生成回放文件
- **完整记录**：记录游戏过程中的所有状态（Agent位置、血量、击杀数等）
- **获胜者显示**：正确显示通过击杀或超时评分判定的获胜者
- **播放控制**：支持播放/暂停、加速/减速、时间轴拖拽
- **统计信息**：实时显示回合数、存活人数、获胜者等信息

回放文件保存在 `replays/` 目录下，可以直接在浏览器中打开查看。

## 可视化

项目提供两种可视化方式：

### 网页版可视化（推荐）✨

生成精美的HTML回放文件，在浏览器中查看：

```python
from visualizer.web_visualizer import WebVisualizer

visualizer = WebVisualizer(map_width=100, map_height=100)
# 记录游戏过程
visualizer.record_frame(state_info)
# 生成HTML文件
html_file = visualizer.generate_html(output_file="game_replay.html", auto_play=True, fps=15)
```

**功能特性**：
- 🎨 精美的图形界面和动画效果
- 🎯 实时显示Agent位置、方向、血量条
- 💥 子弹轨迹和碰撞效果
- 🏗️ 障碍物可视化
- 📦 补给物品显示
- 📊 实时统计信息面板（回合数、存活人数、获胜者等）
- ⏯️ 播放控制（播放/暂停/加速/减速/时间轴拖拽）
- ⌨️ 键盘快捷键支持（空格播放/暂停，左右箭头逐帧）

### 命令行可视化

实时在命令行显示游戏状态：

```python
from visualizer.console_visualizer import ConsoleVisualizer

visualizer = ConsoleVisualizer(map_width=100, map_height=100)
visualizer.render(state_info)
```

## 主要特性

✅ **完整的游戏系统**
- 障碍物系统（矩形墙体，阻挡移动和子弹）
- 补给系统（血量包、弹药、武器）
- 多种武器（普通、霰弹枪、狙击枪、火箭筒）
- 团队对战支持

✅ **智能获胜判定**
- 直接获胜：唯一存活者
- 超时判定：按评分判定（击杀数 > 剩余血量）
- 防止过早结束：游戏进行中不会因评分差异而提前结束

✅ **完善的比赛系统**
- 循环赛：每个Agent与其他所有Agent对战
- 淘汰赛：单败淘汰制
- 分组比赛：适合大规模参赛者（200+人）
- 在线对战：Web界面选择对手，实时积分排名
- 自动回放生成：所有比赛自动生成HTML回放文件

✅ **精美的可视化**
- 网页版回放：支持播放控制、时间轴、统计信息
- 命令行实时显示：适合调试和快速测试

✅ **灵活的开发方式**
- Prompt派：通过自然语言Prompt控制Agent
- 代码派：直接编写Python代码实现策略
- 自动加载：支持从participants目录自动加载所有参赛者

## 扩展建议

1. **添加新游戏元素**：更多武器类型、特殊技能、地图机制等
2. **改进AI策略**：使用强化学习训练Agent
3. **添加更多统计**：胜率、平均存活时间、伤害统计等
4. **网络对战**：支持在线多人对战
5. **AI分析工具**：分析Agent策略、生成策略报告

## 贡献

欢迎提交Pull Request或Issue！

## 许可证

MIT License

