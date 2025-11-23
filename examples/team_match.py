"""
示例：多人组队对战
"""
import sys
from pathlib import Path

# 允许作为脚本运行
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.code_agent import AggressiveAgent, DefensiveAgent, SmartAgent, RandomAgent
from game.engine import GameEngine
from visualizer.web_visualizer import WebVisualizer


def main():
    # 创建四个Agent，分两队
    a1 = AggressiveAgent("TeamA_Agg")
    a2 = SmartAgent("TeamA_Smart")
    b1 = DefensiveAgent("TeamB_Def")
    b2 = RandomAgent("TeamB_Rand")

    # 设置队伍：A 队为 1，B 队为 2
    a1.team_id = 1
    a2.team_id = 1
    b1.team_id = 2
    b2.team_id = 2

    agents = [a1, a2, b1, b2]

    engine = GameEngine(agents, map_width=100, map_height=100)
    visualizer = WebVisualizer(100, 100)

    # 运行并记录回放
    frame_interval = 2
    max_turns = 1500
    # 固定跑满 max_turns，再按评分判定队伍胜负
    while engine.state.turn < max_turns:
        state = engine.step()
        if engine.state.turn % frame_interval == 0:
            visualizer.record_frame(state)

    # 按队伍评分：存活人数 > 总击杀数 > 总血量
    winning_team = None
    alive = engine.state.get_alive_agents()
    team_scores = {}
    for agent in alive:
        if getattr(agent, "team_id", None) is None:
            continue
        tid = agent.team_id
        if tid not in team_scores:
            team_scores[tid] = {"alive": 0, "kills": 0, "health": 0}
        team_scores[tid]["alive"] += 1
        team_scores[tid]["kills"] += agent.kills
        team_scores[tid]["health"] += agent.health
    if team_scores:
        scored = [
            (
                tid,
                s["alive"] * 1000000 + s["kills"] * 10000 + s["health"],
            )
            for tid, s in team_scores.items()
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        if len(scored) == 1 or scored[0][1] > scored[1][1]:
            winning_team = scored[0][0]

    # 输出结果（游戏结束后，允许按评分判定）
    winner_agent = engine.state.get_winner(allow_score_judge=True)
    if winner_agent:
        print(f"胜者（个体）: {winner_agent.name} (击杀: {winner_agent.kills}, 血量: {winner_agent.health})")
    if winning_team:
        print(f"胜利队伍: 队伍 {winning_team}")
        alive = engine.state.get_alive_agents()
        team_members = [a.name for a in alive if getattr(a, 'team_id', None) == winning_team]
        print(f"队伍成员: {', '.join(team_members)}")
    else:
        print("完全平局，无队伍获胜")

    # 生成回放
    out = project_root / "replays" / "team_match.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    visualizer.generate_html(str(out), auto_play=True, fps=15)
    print("回放文件:", out)


if __name__ == "__main__":
    main()


