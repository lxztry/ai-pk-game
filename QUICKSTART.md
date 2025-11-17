# 快速开始指南

## 1. 安装依赖

```bash
pip install -r requirements.txt
```

## 2. 运行简单对战

### 方式1：网页版可视化（推荐）✨

生成精美的网页版游戏回放，在浏览器中查看：

```bash
python examples/web_match.py
```

这将生成一个 `game_replay.html` 文件，在浏览器中打开即可看到：
- 🎨 精美的图形界面
- 🎯 实时显示Agent位置、方向、血量
- 💥 子弹轨迹和碰撞效果
- 📊 实时统计信息面板
- ⏯️ 播放控制（播放/暂停/加速/减速）

### 方式2：命令行实时显示

运行一场4个Agent的对战，在命令行实时显示：

```bash
python examples/simple_match.py
```

这将显示实时游戏画面（命令行文本可视化）。

## 3. 运行比赛系统

运行完整的比赛（循环赛或淘汰赛）：

```bash
python run_tournament.py
```

然后选择：
- `1` - 循环赛（每个Agent与其他所有Agent对战）
- `2` - 淘汰赛（单败淘汰制）

## 4. 使用Prompt Agent（可选）

如果你有OpenAI API Key，可以尝试Prompt Agent：

```bash
# Windows
set OPENAI_API_KEY=your-api-key-here
python examples/prompt_agent_example.py

# Linux/Mac
export OPENAI_API_KEY=your-api-key-here
python examples/prompt_agent_example.py
```

## 5. 创建自己的Agent

### 代码Agent示例

创建 `my_agent.py`:

```python
from agents.code_agent import CodeAgent
from game.agent import Observation

class MyAgent(CodeAgent):
    def step(self, observation: Observation) -> str:
        # 你的策略逻辑
        if observation.enemies_in_view:
            return "shoot"
        return "move_up"
```

然后在 `run_tournament.py` 中导入并使用。

### Prompt Agent示例

```python
from agents.prompt_agent import PromptAgent

agent = PromptAgent("我的Prompt Agent", api_key="your-key")
agent.set_prompt_template("你的自定义Prompt...")
```

## 6. 测试

运行基础功能测试：

```bash
python test_basic.py
```

## 常见问题

**Q: 游戏运行很慢？**  
A: 可以在 `GameEngine.run()` 中设置 `verbose=False` 来减少输出。

**Q: 如何调整游戏参数？**  
A: 在创建 `GameEngine` 时可以设置 `map_width` 和 `map_height`。

**Q: Prompt Agent不工作？**  
A: 确保已设置 `OPENAI_API_KEY` 环境变量，并且已安装 `openai` 库。

