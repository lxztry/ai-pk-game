# 在线对战系统使用指南

## 功能特性

- 🎮 **在线选择对手**：从玩家列表中选择你的Agent和对手
- 🏆 **积分排名系统**：实时查看所有玩家的积分排名
- 📊 **对战历史**：查看所有对战记录
- 🎬 **自动回放**：每场对战自动生成HTML回放文件
- ⚡ **异步对战**：对战在后台运行，不阻塞界面

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务器

```bash
python run_online_server.py
```

服务器将在 `http://localhost:5000` 启动。

### 3. 访问Web界面

在浏览器中打开 `http://localhost:5000`，你将看到：

- **选择对手**：选择你的Agent和对手，开始对战
- **积分排名**：查看所有玩家的积分排名
- **对战历史**：查看历史对战记录

## 使用流程

1. **选择你的Agent**：在"选择对手"标签页中，点击你的Agent卡片
2. **选择对手**：选择你想要对战的对手
3. **开始对战**：点击"开始对战"按钮
4. **等待结果**：对战在后台运行，界面会显示对战状态
5. **查看结果**：对战完成后，可以查看结果和回放

## 积分规则

- **胜利**：+3 积分
- **失败**：+0 积分
- **平局**：+0 积分（超时后按评分判定）

排名按以下顺序：
1. 积分（降序）
2. 胜场数（降序）
3. 击杀数 - 死亡数（降序）

## API接口

### 获取玩家列表
```
GET /api/players
```

### 获取排名
```
GET /api/rankings?limit=100
```

### 获取玩家信息
```
GET /api/player/<name>
```

### 开始对战
```
POST /api/match/start
Content-Type: application/json

{
    "player1": "player1_name",
    "player2": "player2_name"
}
```

### 获取对战结果
```
GET /api/match/<match_id>
```

### 获取对战历史
```
GET /api/matches?player=<name>&limit=50
```

### 获取回放文件
```
GET /api/replay/<match_id>
```

## 数据库

系统使用SQLite数据库存储数据，数据库文件位于 `online/rankings.db`。

### 表结构

**players表**：
- id: 主键
- name: 玩家名称（唯一）
- agent_path: Agent路径
- points: 积分
- wins: 胜场数
- losses: 负场数
- kills: 总击杀数
- deaths: 总死亡数
- created_at: 创建时间
- updated_at: 更新时间

**matches表**：
- id: 主键
- player1_name: 玩家1名称
- player2_name: 玩家2名称
- winner_name: 获胜者名称
- player1_kills: 玩家1击杀数
- player2_kills: 玩家2击杀数
- player1_health: 玩家1剩余血量
- player2_health: 玩家2剩余血量
- replay_file: 回放文件路径
- match_date: 对战时间

## 注意事项

1. **玩家注册**：系统会自动从 `participants/` 目录加载所有Agent作为玩家
2. **对战队列**：对战在后台线程中运行，可以同时进行多场对战
3. **回放文件**：回放文件保存在 `online/replays/` 目录
4. **数据持久化**：所有数据保存在SQLite数据库中，服务器重启后数据不会丢失

## 扩展功能

可以进一步扩展的功能：

1. **用户认证**：添加用户登录系统
2. **实时通知**：使用WebSocket推送对战结果
3. **匹配系统**：根据积分自动匹配对手
4. **赛季系统**：定期重置积分，开始新赛季
5. **排行榜奖励**：为排名靠前的玩家提供奖励

