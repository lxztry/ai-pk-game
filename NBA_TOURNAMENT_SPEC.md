# NBA式赛事运营系统设计规范

## 项目概述

目标：将 AI竞技平台 打造成一个持续运营的赛事生态系统，类似 NBA 模式：
- **每日比赛**：所有注册选手进行 PK
- **每日结果**：公布当天比赛结果
- **每周排名**：积分榜定期更新
- **选手分类**：区分 AI选手 和 人类选手

---

## 一、选手体系设计

### 1.1 选手分类

| 类型 | 标识 | 说明 |
|------|------|------|
| 🤖 AI选手 | `[AI]` | 使用 Agent/模型 开发的参赛者 |
| 👤 人类选手 | `[Human]` | 人工编写策略的参赛者 |

### 1.2 选手元数据 (participant_metadata.json)

```json
{
  "participants": [
    {
      "id": "smart_agent",
      "name": "SmartAgent",
      "display_name": "🤖 SmartAgent",
      "type": "ai",  // "ai" | "human"
      "developer": "AI Model",
      "model_info": "code-based",
      "created_at": "2026-03-10",
      "参赛次数": 0,
      "总积分": 0
    }
  ]
}
```

### 1.3 Agent 基类扩展

在 `game/agent.py` 中添加：
- `agent_type`: "ai" | "human"
- `developer_info`: str
- `model_info`: str (用于AI选手，标注使用的模型)

---

## 二、赛事日程系统

### 2.1 每日赛程 (Daily Schedule)

```
每天自动执行：
1. 08:00 - 加载所有注册选手
2. 09:00 - 生成当日赛程（循环赛/随机匹配）
3. 09:00-22:00 - 分批次运行比赛
4. 22:00 - 汇总当日结果，生成排行榜
5. 22:30 - 发布每日报告
```

### 2.2 比赛模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `daily_pk` | 随机抽签对战 | 日常比赛 |
| `round_robin` | 循环赛 | 每周杯赛 |
| `tournament` | 淘汰赛 | 决赛/杯赛 |

### 2.3 每日比赛数量

- 每个选手每天至少 PK **3场**
- 最多 **10场**（避免资源占用）
- 优先匹配：同积分段选手

---

## 三、积分系统

### 3.1 胜场积分

| 结果 | 积分 |
|------|------|
| 🥇 胜利 | +3 分 |
| 🥈 平局 | +1 分 |
| ❌ 失败 | +0 分 |

### 3.2 额外积分

| 成就 | 积分 |
|------|------|
| 击杀数 > 3 | +1 分 |
| 存活到最后3名 | +1 分 |
| 零死亡获胜 | +2 分 |

### 3.3 排行榜类型

1. **总积分榜** - 累计最高
2. **AI选手榜** - 仅AI选手
3. **人类选手榜** - 仅人类选手
4. **周榜** - 本周积分
5. **月榜** - 本月积分

---

## 四、数据存储设计

### 4.1 目录结构

```
data/
├── participants/           # 选手数据
│   └── participants.json    # 选手注册信息
├── daily/
│   ├── 2026-03-30/
│   │   ├── schedule.json   # 当日赛程
│   │   ├── results.json    # 当日比赛结果
│   │   └── report.md       # 当日比赛报告
│   └── ...
├── rankings/               # 排行榜
│   ├── overall.json        # 总榜
│   ├── ai_only.json        # AI榜
│   ├── human_only.json     # 人类榜
│   └── weekly/
│       └── 2026-W13.json   # 第13周排行
├── matches/                # 比赛记录
│   └── 2026-03-30/
│       ├── match_001.html  # 回放文件
│       └── ...
└── leaderboard.json        # 最新排行榜快照
```

### 4.2 数据库表设计 (SQLite)

```sql
-- 选手表
CREATE TABLE participants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    display_name TEXT,
    type TEXT CHECK(type IN ('ai', 'human')),
    developer_info TEXT,
    model_info TEXT,
    total_points INTEGER DEFAULT 0,
    total_matches INTEGER DEFAULT 0,
    total_wins INTEGER DEFAULT 0,
    total_kills INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 每日比赛表
CREATE TABLE daily_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    match_index INTEGER,
    agent1_id TEXT,
    agent2_id TEXT,
    agent3_id TEXT,
    agent4_id TEXT,
    winner_id TEXT,
    scores TEXT,  -- JSON格式
    replay_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 积分变动表
CREATE TABLE point_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_id TEXT,
    date TEXT,
    points_earned INTEGER,
    match_id INTEGER,
    reason TEXT,
    FOREIGN KEY (participant_id) REFERENCES participants(id)
);

-- 周榜表
CREATE TABLE weekly_rankings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week TEXT,  -- 2026-W13
    participant_id TEXT,
    rank INTEGER,
    points INTEGER,
    matches INTEGER,
    wins INTEGER,
    FOREIGN KEY (participant_id) REFERENCES participants(id)
);
```

---

## 五、自动赛事脚本

### 5.1 每日赛事脚本 (run_daily_tournament.py)

```python
"""
每日赛事运行脚本
- 自动加载所有选手
- 生成赛程
- 运行比赛
- 更新积分
- 生成报告
"""
import schedule
import time
from datetime import datetime

def daily_tournament():
    """每日赛事主流程"""
    print(f"[{datetime.now()}] 开始每日赛事...")
    
    # 1. 加载选手
    # 2. 生成赛程
    # 3. 运行比赛
    # 4. 更新积分
    # 5. 生成报告
    # 6. 发布结果
    
    print(f"[{datetime.now()}] 每日赛事完成")

# 定时任务
schedule.every().day.at("09:00").do(daily_tournament)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 5.2 赛程生成器 (scheduler.py)

```python
class MatchScheduler:
    """赛程生成器"""
    
    def __init__(self, participants, matches_per_day=5):
        self.participants = participants
        self.matches_per_day = matches_per_day
        
    def generate_daily_schedule(self, date):
        """
        生成每日赛程
        - 每个选手每天固定场次
        - 优先同积分段匹配
        - 4人一场比赛
        """
        schedule = []
        # 实现匹配逻辑
        return schedule
```

---

## 六、报告生成系统

### 6.1 每日报告 (daily_report.md)

```markdown
# 📅 2026年3月30日 每日赛事报告

## 今日赛果

| 场次 | 对阵 | 胜者 |
|------|------|------|
| #001 | SmartAgent vs AggressiveAgent vs ... | SmartAgent |
| #002 | ... | ... |

## 今日积分榜 TOP 10

| 排名 | 选手 | 类型 | 积分 | 胜/负 |
|------|------|------|------|-------|
| 1 | 🤖 SmartAgent | AI | 45 | 15/2 |
| 2 | 👤 Player1 | Human | 38 | 12/5 |

## 选手风采

### 🤖 MVP: SmartAgent
- 今日战绩：15胜2负
- 击杀数：42
- 场均积分：4.5

### 👤 MVP: Player1  
- 今日战绩：12胜5负
- 击杀数：28
- 场均积分：3.8

## 明日预告
- 杯赛资格赛
- 排名后50%选手参与
```

### 6.2 周报 (weekly_report.md)

```markdown
# 📊 第13周 (2026-03-24 ~ 2026-03-30) 周报

## 本周总积分榜

| 排名 | 选手 | 类型 | 周积分 | 胜/负 | 击杀 |
|------|------|------|--------|-------|------|
| 1 | 🤖 SmartAgent | AI | 156 | 52/8 | 186 |
| 2 | 👤 Player1 | Human | 142 | 47/13 | 154 |

## AI vs Human 对决统计
- 总比赛场次：312
- AI选手获胜：178 (57%)
- 人类选手获胜：134 (43%)

## 进步最快
- 🏆 Player3: +15名，跃升到第8位
```

---

## 七、网页展示界面

### 7.1 首页 (index.html)

- 今日比赛直播/回放入口
- 实时积分榜
- 选手列表（筛选AI/人类）
- 赛事日历

### 7.2 选手页面 (player.html?id=xxx)

- 选手基本信息（类型、开发者、模型）
- 历史战绩
- 积分曲线图
- 最近比赛回放

### 7.3 赛事页面 (tournament.html)

- 当前/历史赛事列表
- 赛程表
- 比赛结果
- 颁奖台

### 7.4 排行榜页面 (rankings.html)

- 总榜
- AI专属榜
- 人类专属榜
- 周榜/月榜
- 历史排行

---

## 八、自动化部署

### 8.1 Cron 任务

```bash
# 每天 09:00 运行每日赛事
0 9 * * * cd /path/to/ai-pk-game && python run_daily_tournament.py

# 每周一 08:00 生成周报
0 8 * * 1 cd /path/to/ai-pk-game && python generate_weekly_report.py

# 每晚 23:00 清理旧回放（保留30天）
0 23 * * * cd /path/to/ai-pk-game && python cleanup_replays.py --keep-days 30
```

### 8.2 通知系统

- 每日报告自动推送到飞书群
- 周榜自动发布
- 里程碑成就通知

---

## 九、实现优先级

### Phase 1: 基础框架 (1-2天)
1. ✅ 选手元数据系统
2. ✅ 赛程生成器
3. ✅ 数据库表创建
4. ✅ 每日赛事脚本

### Phase 2: 积分系统 (1天)
1. ✅ 积分计算逻辑
2. ✅ 排行榜生成
3. ✅ 数据持久化

### Phase 3: 报告系统 (1天)
1. ✅ 每日报告生成
2. ✅ 周报生成
3. ✅ 页面展示

### Phase 4: 自动化 (1天)
1. ✅ Cron 定时任务
2. ✅ 通知推送
3. ✅ 数据清理

---

## 十、文件清单

```
ai-pk-game/
├── game/
│   └── agent.py              # 添加 agent_type, developer_info
├── tournament/
│   ├── daily_tournament.py   # 新增：每日赛事主脚本
│   ├── scheduler.py          # 新增：赛程生成器
│   └── ranking.py            # 新增：排行榜生成器
├── data/                     # 新增：数据目录
│   ├── participants.json
│   ├── daily/
│   ├── rankings/
│   └── matches/
├── reports/                  # 新增：报告目录
│   ├── templates/
│   └── generated/
├── web/
│   ├── leaderboard.html      # 新增：排行榜页面
│   ├── player.html           # 新增：选手页面
│   └── tournament.html       # 新增：赛事页面
├── utils/
│   ├── database.py           # 新增：数据库管理
│   └── participant_manager.py # 新增：选手管理
├── run_daily_tournament.py   # 新增：每日赛事入口
├── generate_weekly_report.py  # 新增：周报生成
└── cleanup_replays.py        # 新增：回放清理
```

---

## 十一、后续扩展想法

1. **直播功能**：实时展示比赛
2. **投注系统**：虚拟币投注
3. **皮肤系统**：选手自定义外观
4. **社区功能**：评论、分享
5. **联赛系统**：甲级/乙级联赛升降级
