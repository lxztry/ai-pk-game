"""
ELO 联赛 Demo

3 个 prompt 互相打 30 场，看谁的 ELO 分数最高。
"""
import os
import sys
import random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tournament.prompt_duel import run_prompt_duel, DuelPlayer
from tools.elo import EloSystem

os.makedirs("outputs", exist_ok=True)


PLAYERS = [
    DuelPlayer(
        name="激进派",
        persona="aggressive",
        prompt="你是激进特工。看到敌人立即射击。血 < 20 才考虑逃跑。",
    ),
    DuelPlayer(
        name="防守派",
        persona="defensive",
        prompt="你是防守特工。距离 > 15 才开火。血 < 50 立刻远离敌人。",
    ),
    DuelPlayer(
        name="战术派",
        persona="balanced",
        prompt="你是战术特工。优先攻击血量低的敌人。看到敌人先瞄准再射击。",
    ),
]


def main(n_matches_per_pair: int = 10, map_size: int = 25, max_turns: int = 60):
    print()
    print("╔" + "═" * 58 + "╗")
    print("║  🏆 ELO 联赛 Demo                                       ║")
    print("╚" + "═" * 58 + "╝")
    print()
    print(f"  参赛: {len(PLAYERS)} 个 prompt")
    print(f"  赛制: 循环赛，每对打 {n_matches_per_pair} 场")
    print(f"  地图: {map_size}x{map_size}, 每场 {max_turns} 回合")
    print()
    print(f"  玩家:")
    for p in PLAYERS:
        print(f"    - {p.name:<10} ({p.persona}, prompt {len(p.prompt)} 字)")
    print()

    # 初始化 ELO
    elo = EloSystem()
    for p in PLAYERS:
        elo.register(p.name, initial_rating=1500.0)
    print(f"  初始 ELO: {[(p.name, int(elo.get_rating(p.name))) for p in PLAYERS]}")
    print()

    # 循环赛
    print("  🏟️  循环赛进行中...")
    matches = []
    for i, p1 in enumerate(PLAYERS):
        for j, p2 in enumerate(PLAYERS):
            if i >= j:
                continue
            for k in range(n_matches_per_pair):
                # 每次随机种子不同，结果不一样
                random.seed(k * 1000 + i * 100 + j * 10)
                result = run_prompt_duel(p1, p2, max_turns=max_turns, map_size=map_size)
                winner_name = result.winner_name
                # 平局（按评分判定）→ 算平
                matches.append((p1.name, p2.name, winner_name, k + 1))
                elo.record_match(p1.name, p2.name, winner=winner_name)

    # 按场次展示
    print()
    print(f"  📊 比赛记录（共 {len(matches)} 场）:")
    by_pair = {}
    for a, b, w, k in matches:
        pair = (a, b) if a < b else (b, a)
        by_pair.setdefault(pair, []).append((k, w))
    for (a, b), games in by_pair.items():
        wins_a = sum(1 for _, w in games if w == a)
        wins_b = sum(1 for _, w in games if w == b)
        draws = sum(1 for _, w in games if w is None)
        print(f"    {a:<6} vs {b:<6}: {a} 胜 {wins_a}, {b} 胜 {wins_b}, 平 {draws}")

    # 最终排行
    print()
    print(elo.format_rankings())

    # 评分上升/下降
    print()
    print("  📈 评分变化:")
    for p in PLAYERS:
        cur = elo.get_rating(p.name)
        delta = cur - 1500
        arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "─")
        print(f"    {p.name:<10} {arrow} {delta:+.0f} (最终 {cur:.0f})")


if __name__ == "__main__":
    main()
