## 1. 实现

- [x] 1.1 修改前端界面 (`online/templates/index.html`)
  - [x] 在 `match-controls` 区域添加回合数配置输入框
  - [x] 添加标签和输入框（number类型，默认值500，最小值50，最大值2000）
  - [x] 更新 `startMatch()` 函数，将回合数包含在请求中

- [x] 1.2 修改后端API (`online/server.py`)
  - [x] 修改 `/api/match/start` 路由，接收 `max_turns` 参数（可选，默认500）
  - [x] 修改 `run_match()` 函数签名，添加 `max_turns` 参数（默认500）
  - [x] 将 `max_turns` 参数传递给游戏循环（使用传入的参数而不是硬编码的500）

- [ ] 1.3 测试
  - [ ] 测试默认值（不提供max_turns时使用500）
  - [ ] 测试自定义值（提供不同的max_turns值）
  - [ ] 测试边界值（最小值50，最大值2000）
  - [ ] 测试界面交互（输入框显示和值传递）

