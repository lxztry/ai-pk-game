"""
Prompt 对决（Prompt Duel）

两个玩家各自提交一段自然语言 prompt + 性格说明，让同一个 LLM 控制同一个 agent，
看谁调教得好。这是 AI 竞技平台的"新玩法"。

工作流：
1. 玩家 A 提交: (prompt_text, persona)
2. 玩家 B 提交: (prompt_text, persona)
3. 双方使用同一个 LLM 客户端（保证对比公平）
4. 跑一场 1v1 比赛
5. 输出版本对比 + 胜者

使用示例：
    from tournament.prompt_duel import PromptDuel, run_prompt_duel
    result = run_prompt_duel(
        player1_prompt="你是...策略...",
        player2_prompt="你是...策略...",
        max_turns=200,
        mock=True,  # 用 mock LLM（不要真 API）
    )
"""
import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
from game.engine import GameEngine
from agents.prompt_agent import PromptAgent, MockLLMClient, LLMClient


@dataclass
class DuelPlayer:
    name: str
    prompt: str
    persona: str = "balanced"
    description: str = ""


@dataclass
class DuelResult:
    winner_name: Optional[str]
    player1_name: str
    player2_name: str
    player1_health: int
    player2_health: int
    player1_kills: int
    player2_kills: int
    player1_decisions: int  # LLM 调用次数
    player2_decisions: int
    turns: int
    replay_html: Optional[str] = None


def _equip_shotgun(agent):
    """预设霰弹枪 + 满弹药（让对决有更多击杀）"""
    agent.weapon = "shotgun"
    agent.ammo = {"shotgun": 30, "sniper": 0, "rocket": 0}


def run_prompt_duel(player1: DuelPlayer,
                    player2: DuelPlayer,
                    max_turns: int = 200,
                    map_size: int = 50,
                    llm_client: Optional[LLMClient] = None,
                    save_replay_to: Optional[str] = None,
                    shotgun_duel: bool = True) -> DuelResult:
    """跑一场 Prompt 对决

    Args:
        player1 / player2: DuelPlayer(name, prompt, persona)
        max_turns: 最大回合数
        map_size: 地图大小
        llm_client: LLM 客户端（None → 用 MockLLMClient）
        shotgun_duel: 是否双方预设霰弹枪（默认 True，让战斗更激烈）
        save_replay_to: 回放 HTML 保存路径（None → 不保存）

    Returns:
        DuelResult 包含胜负、击杀、决策次数、回放路径
    """
    # 默认 mock（不依赖真实 API）
    if llm_client is None:
        llm_client = MockLLMClient()

    # 创建两个 PromptAgent，共享同一个 LLM client（公平）
    agent1 = PromptAgent(
        name=player1.name,
        llm_client=llm_client,
        persona=player1.persona,
    )
    agent1.set_strategy(player1.prompt)

    agent2 = PromptAgent(
        name=player2.name,
        llm_client=llm_client,
        persona=player2.persona,
    )
    agent2.set_strategy(player2.prompt)

    # 预设武器：双方霰弹枪 + 满弹药（让对决频繁击杀）
    if shotgun_duel:
        _equip_shotgun(agent1)
        _equip_shotgun(agent2)

    # 创建游戏引擎（小地图更容易产生击杀）
    engine = GameEngine([agent1, agent2], map_size, map_size)

    # 跑比赛
    winner = engine.run(max_turns=max_turns, verbose=False)

    # 可选：保存 replay
    replay_html = None
    if save_replay_to:
        from visualizer.web_visualizer import WebVisualizer
        viz = WebVisualizer(map_width=map_size, map_height=map_size,
                            canvas_width=600, canvas_height=450)
        # 重新跑一遍记录帧（避免在 engine.run 里加侵入）
        agent1.health = 100; agent2.health = 100
        agent1.kills = 0; agent2.kills = 0
        agent1.position = (10, 25); agent2.position = (40, 25)
        engine2 = GameEngine([agent1, agent2], map_size, map_size)
        for turn in range(max_turns):
            state = engine2.step()
            if turn % 2 == 0:
                viz.record_frame(state)
            if engine2.state.get_winner(allow_score_judge=False):
                for _ in range(5):
                    viz.record_frame(engine2.step())
                break
        replay_html = viz.generate_html(save_replay_to, auto_play=True, fps=10)

    return DuelResult(
        winner_name=winner.name if winner else None,
        player1_name=player1.name,
        player2_name=player2.name,
        player1_health=agent1.health,
        player2_health=agent2.health,
        player1_kills=agent1.kills,
        player2_kills=agent2.kills,
        player1_decisions=len(agent1.decision_log),
        player2_decisions=len(agent2.decision_log),
        turns=engine.state.turn,
        replay_html=replay_html,
    )


def format_duel_report(result: DuelResult) -> str:
    """格式化对决结果为可读报告"""
    lines = [
        "=" * 60,
        f"  PROMPT 对决报告",
        "=" * 60,
        "",
        f"  胜者: {result.winner_name or '平局'}",
        f"  总回合: {result.turns}",
        "",
        f"  {result.player1_name:<15} 健康:{result.player1_health:>3} 击杀:{result.player1_kills} LLM 调用:{result.player1_decisions}",
        f"  {result.player2_name:<15} 健康:{result.player2_health:>3} 击杀:{result.player2_kills} LLM 调用:{result.player2_decisions}",
        "",
    ]
    if result.replay_html:
        lines.append(f"  回放: {result.replay_html}")
    return "\n".join(lines)
