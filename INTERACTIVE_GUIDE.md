# 交互式运行指南

## 如何交互式运行比赛

### 方法1：在终端中直接运行

打开终端（命令行），进入项目目录，然后运行：

```bash
python run_tournament_with_participants.py
```

程序会显示：

```
================================================================================
                         AI斗兽场
================================================================================

正在加载参赛者Agent...
--------------------------------------------------------------------------------
[OK] 已加载: example_player
[OK] 已加载: test_player
--------------------------------------------------------------------------------

是否添加Prompt Agent? (y/n): 
```

**此时你可以输入：**
- `y` - 添加Prompt Agent（需要设置OPENAI_API_KEY环境变量）
- `n` - 不添加Prompt Agent

然后程序会显示：

```
共加载 2 个Agent:
  1. example_player (Agent)
  2. test_player (Agent)

================================================================================
选择比赛模式:
  1. 循环赛（每个Agent与其他所有Agent对战）
  2. 淘汰赛（单败淘汰制）
  3. 退出
================================================================================

请输入选择 (1/2/3): 
```

**此时你可以输入：**
- `1` - 运行循环赛
- `2` - 运行淘汰赛
- `3` - 退出程序

### 方法2：使用自动运行版本（无需交互）

如果你不想交互式输入，可以直接运行自动版本：

```bash
python run_tournament_auto.py
```

这个版本会自动：
- 加载所有参赛者Agent
- 跳过Prompt Agent
- 自动运行循环赛

### 方法3：在Python交互式环境中运行

你也可以在Python交互式环境中手动控制：

```python
from utils.agent_loader import AgentLoader
from tournament.tournament import RoundRobinTournament, EliminationTournament

# 加载所有参赛者
loader = AgentLoader(participants_dir="participants")
agents = loader.create_agent_instances()

# 运行循环赛
tournament = RoundRobinTournament(agents)
tournament.run(verbose=True)

# 或运行淘汰赛
# tournament = EliminationTournament(agents)
# tournament.run(verbose=True)
```

## 常见问题

### Q: 为什么程序提示"用户取消操作"？

A: 这通常发生在非交互式环境中（如某些IDE的终端）。请确保在真正的命令行终端中运行。

### Q: 如何跳过交互式输入？

A: 使用 `run_tournament_auto.py`，它会自动运行循环赛，无需任何输入。

### Q: 如何在Windows PowerShell中运行？

A: 在PowerShell中直接运行：
```powershell
python run_tournament_with_participants.py
```

### Q: 如何在Linux/Mac终端中运行？

A: 在终端中运行：
```bash
python3 run_tournament_with_participants.py
```

## 提示

- 确保你在项目根目录下运行命令
- 确保已安装所有依赖：`pip install -r requirements.txt`
- 如果遇到编码问题，可以设置环境变量：`set PYTHONIOENCODING=utf-8`（Windows）或 `export PYTHONIOENCODING=utf-8`（Linux/Mac）

