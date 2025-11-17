# 大规模比赛设计文档

## 200个Agent比赛设计方案

### 方案1：分组赛 + 淘汰赛（推荐）⭐

#### 赛制设计

1. **小组赛阶段**
   - 将200个Agent分成50个小组，每组4人
   - 每组内进行循环赛（每人与其他3人对战）
   - 每组前2名出线，共100人进入淘汰赛

2. **淘汰赛阶段**
   - 100人进行单败淘汰赛
   - 共7轮淘汰赛决出冠军

#### 比赛场次统计

- 小组赛：50组 × 6场 = 300场
- 淘汰赛：100 → 50 → 25 → 13 → 7 → 4 → 2 → 1 = 99场
- **总计：约399场比赛**

#### 使用方式

```python
from tournament.group_tournament import GroupTournament
from utils.agent_loader import AgentLoader

# 加载所有Agent
loader = AgentLoader(participants_dir="participants")
agents = loader.create_agent_instances()

# 创建分组比赛
tournament = GroupTournament(
    agents=agents,
    group_size=4,        # 每组4人
    advance_per_group=2  # 每组前2名出线
)

# 运行比赛
result = tournament.run(verbose=True)
print(f"冠军: {result['champion'].name}")
```

### 方案2：多轮分组赛

#### 赛制设计

1. **第一轮分组赛**
   - 200人分成40组，每组5人
   - 每组前2名出线，共80人

2. **第二轮分组赛**
   - 80人分成16组，每组5人
   - 每组前2名出线，共32人

3. **淘汰赛阶段**
   - 32人进行单败淘汰赛
   - 共5轮决出冠军

#### 比赛场次统计

- 第一轮：40组 × 10场 = 400场
- 第二轮：16组 × 10场 = 160场
- 淘汰赛：32 → 16 → 8 → 4 → 2 → 1 = 31场
- **总计：约591场比赛**

### 方案3：直接淘汰赛（不推荐）

- 200人直接进行单败淘汰赛
- 需要199场比赛
- 但很多Agent只打一场就被淘汰，体验不佳

## 图形界面使用

### 启动图形界面

```bash
python run_gui.py
```

### 界面功能

1. **Agent管理**
   - 自动加载所有参赛者Agent
   - 显示Agent列表
   - 支持选择特定Agent参赛

2. **比赛模式选择**
   - 分组赛（适合大规模）
   - 循环赛
   - 淘汰赛
   - 循环赛（带回放）

3. **分组设置**（仅分组赛）
   - 每组人数：2-10人
   - 每组出线：1-5人

4. **实时输出**
   - 显示比赛进度
   - 显示比赛结果
   - 显示最终排名

## 性能优化建议

### 对于200个Agent的比赛

1. **并行处理**（未来优化）
   - 可以并行运行多场比赛
   - 使用多进程或多线程

2. **减少回合数**
   - 默认2000回合可能太长
   - 可以设置为1000回合加快速度

3. **批量处理**
   - 小组赛可以批量运行
   - 减少中间输出

4. **进度保存**
   - 支持保存比赛进度
   - 支持断点续赛

## 示例：运行200人分组赛

```python
from tournament.group_tournament import GroupTournament
from utils.agent_loader import AgentLoader

# 加载所有Agent（假设有200个）
loader = AgentLoader(participants_dir="participants")
agents = loader.create_agent_instances()

# 创建分组比赛
# 200人分成50组，每组4人，每组前2名出线
tournament = GroupTournament(
    agents=agents,
    group_size=4,
    advance_per_group=2
)

# 运行比赛
result = tournament.run(verbose=True)

# 查看结果
tournament.print_results()
print(f"\n冠军: {result['champion'].name}")
```

## 比赛时间估算

假设每场比赛平均需要500回合（约30秒）：

- 小组赛：300场 × 30秒 = 9000秒 ≈ 2.5小时
- 淘汰赛：99场 × 30秒 = 2970秒 ≈ 50分钟
- **总计：约3.5小时**

如果使用并行处理（10场同时进行）：
- **总计：约20-30分钟**

## 注意事项

1. **内存使用**：200个Agent同时加载可能占用较多内存
2. **文件管理**：如果生成回放，需要足够的磁盘空间
3. **时间成本**：大规模比赛需要较长时间，建议使用后台运行
4. **结果保存**：建议保存比赛结果到文件，便于后续分析

