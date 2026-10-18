"""
Tier 1 三件套 Demo：Prompt 对决 + AI 教练 + 每日挑战
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tournament.prompt_duel import run_prompt_duel, format_duel_report, DuelPlayer
from tools.coach import analyze_decision_log, format_coach_report
from tools.daily_challenge import get_today_challenge, list_all_challenges, format_challenge
from agents.prompt_agent import PromptAgent, MockLLMClient
from game.engine import GameEngine

os.makedirs("outputs", exist_ok=True)


# ========== 1. Prompt 对决 ==========

print()
print("╔" + "═" * 58 + "╗")
print("║  第 1 件事：Prompt 对决                                  ║")
print("╚" + "═" * 58 + "╝")

PLAYER_A = DuelPlayer(
    name="激进派",
    persona="aggressive",
    prompt="你是激进特工。看到敌人就射击，血量 < 20 才考虑逃跑。",
)
PLAYER_B = DuelPlayer(
    name="防守派",
    persona="defensive",
    prompt="你是防守特工。距离 > 20 才开火，血量 < 50 立刻逃跑。",
)

print(f"\n  玩家 A: {PLAYER_A.name} (prompt={len(PLAYER_A.prompt)}字)")
print(f"  玩家 B: {PLAYER_B.name} (prompt={len(PLAYER_B.prompt)}字)")
print("\n  正在用 Mock LLM 跑对决...")

result = run_prompt_duel(PLAYER_A, PLAYER_B, max_turns=100, map_size=50)
print(format_duel_report(result))


# ========== 2. AI 教练 ==========

print()
print("╔" + "═" * 58 + "╗")
print("║  第 2 件事：AI 教练分析                                  ║")
print("╚" + "═" * 58 + "╝")

# 重新跑一遍拿 decision_log
llm = MockLLMClient()
a1 = PromptAgent(name=result.player1_name, llm_client=llm, persona="aggressive")
a1.set_prompt_template(PLAYER_A.prompt)
a2 = PromptAgent(name=result.player2_name, llm_client=llm, persona="defensive")
a2.set_prompt_template(PLAYER_B.prompt)
engine = GameEngine([a1, a2], 50, 50)
for t in range(100):
    state = engine.step()
    a1.decision_log[-1]["turn"] = t if a1.decision_log else None
    a2.decision_log[-1]["turn"] = t if a2.decision_log else None

report_a = analyze_decision_log(result.player1_name, a1.decision_log)
print()
print(format_coach_report(report_a))
print()

report_b = analyze_decision_log(result.player2_name, a2.decision_log)
print()
print(format_coach_report(report_b))


# ========== 3. 每日挑战 ==========

print()
print("╔" + "═" * 58 + "╗")
print("║  第 3 件事：每日挑战                                    ║")
print("╚" + "═" * 58 + "╝")

print("\n  今天的挑战：")
today = get_today_challenge()
print()
print(format_challenge(today))

print("\n  所有可用的挑战：")
for rule in list_all_challenges():
    print(f"    - [{rule.weekday:<10}] {rule.title} — {rule.description}")
