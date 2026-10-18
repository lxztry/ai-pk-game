"""
Prompt 对决 Demo — 改良版

特性：
- 小地图（25x25）→ 容易产生击杀
- 每回合打印双方动作（前 15 回合带解说）
- 最终彩色 ASCII 战报（血量进度条）
- 自动重跑 N 次统计胜率
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tournament.prompt_duel import run_prompt_duel, format_duel_report, DuelPlayer
from agents.prompt_agent import PromptAgent, MockLLMClient
from game.engine import GameEngine
from tools.coach import analyze_decision_log, format_coach_report

os.makedirs("outputs", exist_ok=True)


PLAYER_A = DuelPlayer(
    name="激进派",
    persona="aggressive",
    description="主张快速接近敌人，正面硬刚",
    prompt="""你是一个激进的战斗特工。规则：
1. 视野里有敌人立即射击
2. 没敌人时朝敌人最后位置冲锋
3. 血量 < 20 才逃跑
只返回动作字符串。""",
)

PLAYER_B = DuelPlayer(
    name="防守派",
    persona="defensive",
    description="主张保持距离，伺机反击",
    prompt="""你是一个谨慎的战斗特工。规则：
1. 距离敌人 > 15 才射击，避免近战
2. 持续移动，不 idle
3. 血量 < 50 立刻逃跑
只返回动作字符串。""",
)


def _setup_weapons(a1, a2):
    """给双方预设霰弹枪 + 弹药，让战斗更激烈"""
    for a in (a1, a2):
        a.weapon = "shotgun"
        a.ammo = {"shotgun": 30, "sniper": 0, "rocket": 0}


# ---------- 动作 emoji 映射 ----------

ACTION_EMOJI = {
    "move_up": "↑", "move_down": "↓",
    "move_left": "←", "move_right": "→",
    "turn_left": "↺", "turn_right": "↻",
    "shoot": "💥", "idle": "💤",
}


# ---------- 回合解说 ----------

def play_with_commentary(llm, p1, p2, map_size, max_turns):
    """带解说的对决（返回完整 result + 决策日志）"""
    a1 = PromptAgent(name=p1.name, llm_client=llm, persona=p1.persona)
    a1.set_strategy(p1.prompt)
    a2 = PromptAgent(name=p2.name, llm_client=llm, persona=p2.persona)
    a2.set_strategy(p2.prompt)
    _setup_weapons(a1, a2)

    engine = GameEngine([a1, a2], map_size, map_size)

    print()
    print("📺 实时解说（前 15 回合）：")
    print("=" * 60)

    for turn in range(max_turns):
        state_before = engine.step()
        a1.decision_log[-1]["turn"] = turn if a1.decision_log else None
        a2.decision_log[-1]["turn"] = turn if a2.decision_log else None

        if turn < 15:
            act1 = a1.decision_log[-1]["action"]
            act2 = a2.decision_log[-1]["action"]
            h1 = a1.health
            h2 = a2.health
            en1 = state_before.get("alive_count", 2)
            d1 = int(a1.decision_log[-1]["enemies_visible"])
            d2 = int(a2.decision_log[-1]["enemies_visible"])
            print(f" 回合{turn:>3} │ "
                  f"{p1.name} {ACTION_EMOJI[act1]} (血{h1:>3} 视敌{d1}) │ "
                  f"{p2.name} {ACTION_EMOJI[act2]} (血{h2:>3} 视敌{d2})")

        winner = engine.state.get_winner(allow_score_judge=False)
        if winner:
            for _ in range(5):
                engine.step()
            break

    winner = engine.state.get_winner(allow_score_judge=True)
    print("=" * 60)
    return a1, a2, engine, winner


# ---------- ASCII 战报 ----------

def print_battle_report(p1, p2, a1, a2, engine, winner):
    print()
    print("=" * 60)
    print("  🏆 最终战报")
    print("=" * 60)
    print()

    def bar(health, max_h=100, width=20):
        filled = int(health / max_h * width)
        return "█" * filled + "░" * (width - filled)

    print(f"  {p1.name:<10} 血量 {a1.health:>3}/100  {bar(a1.health)}")
    print(f"  {p2.name:<10} 血量 {a2.health:>3}/100  {bar(a2.health)}")
    print()

    if winner:
        emoji = "🥇" if winner.name == p1.name else "🥇"
        print(f"  {emoji} 胜者：{winner.name}")
    else:
        print("  🤝 平局")
    print()

    print(f"  回合数: {engine.state.turn}")
    print(f"  {p1.name} 击杀: {a1.kills}  LLM 调用: {len(a1.decision_log)}")
    print(f"  {p2.name} 击杀: {a2.kills}  LLM 调用: {len(a2.decision_log)}")
    print()


# ---------- 统计胜率（跑 N 次）----------

def tournament(p1, p2, n=3, max_turns=50, map_size=25):
    """跑 N 次，统计胜率"""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║  🏟️  PROMPT 对决 - 多场统计                                  ║")
    print("╚" + "═" * 58 + "╝")
    print(f"\n  配置: 地图 {map_size}x{map_size}, 每场 {max_turns} 回合, 共 {n} 场")
    print(f"  玩家 A: {p1.name}")
    print(f"  玩家 B: {p2.name}")

    wins = {p1.name: 0, p2.name: 0, "draw": 0}
    results = []
    for i in range(n):
        llm = MockLLMClient()
        result = run_prompt_duel(p1, p2, max_turns=max_turns, map_size=map_size, llm_client=llm)
        winner_key = result.winner_name or "draw"
        wins[winner_key] = wins.get(winner_key, 0) + 1
        results.append(result)
        print(f"  场 {i+1}: 胜={result.winner_name or '平局':<10} "
              f"A血={result.player1_health} B血={result.player2_health} "
              f"A杀={result.player1_kills} B杀={result.player2_kills}")

    print()
    print("=" * 60)
    print("  📊 战绩汇总")
    print("=" * 60)
    total = sum(wins.values())
    for k, v in wins.items():
        name = k if k == "draw" else f"{k} 胜"
        pct = v / total * 100 if total else 0
        bar_str = "█" * int(pct / 5)
        print(f"  {name:<10} {v}/{total} ({pct:>5.1f}%) {bar_str}")
    print()


# ---------- 完整 demo ----------

def main():
    print()
    print("╔" + "═" * 58 + "╗")
    print("║  PROMPT 对决 Demo (升级版)                              ║")
    print("╚" + "═" * 58 + "╝")
    print()
    print(f"  玩家 A: {PLAYER_A.name} (prompt {len(PLAYER_A.prompt)} 字)")
    print(f"  玩家 B: {PLAYER_B.name} (prompt {len(PLAYER_B.prompt)} 字)")

    # 1) 单场 + 解说 + 战报
    print()
    print("┌─ 单场 + 实时解说 ─────────────────────────────────────┐")
    llm = MockLLMClient()
    a1, a2, engine, winner = play_with_commentary(
        llm, PLAYER_A, PLAYER_B, map_size=25, max_turns=50
    )
    print_battle_report(PLAYER_A, PLAYER_B, a1, a2, engine, winner)

    # 2) AI 教练分析
    print("┌─ AI 教练诊断 ────────────────────────────────────────┐")
    print(format_coach_report(analyze_decision_log(PLAYER_A.name, a1.decision_log)))
    print()

    # 3) 多场统计
    print("┌─ 多场胜率统计 ────────────────────────────────────────┐")
    tournament(PLAYER_A, PLAYER_B, n=5, max_turns=50, map_size=25)

    # 4) 保存回放
    out = "outputs/prompt_duel_demo.html"
    print(f"  💾 回放 HTML: {out}")


if __name__ == "__main__":
    main()
