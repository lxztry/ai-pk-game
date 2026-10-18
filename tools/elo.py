"""
ELO 评分系统

每个 prompt 对一个 ELO 分数。多次对决后能看出谁更会写 prompt。
"""
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple


@dataclass
class EloRating:
    """单个选手的 ELO 分数"""
    name: str
    rating: float = 1500.0
    matches: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0


class EloSystem:
    """ELO 评分管理器

    用法：
        elo = EloSystem()
        elo.register("激进派")
        elo.register("防守派")
        elo.record_match("激进派", "防守派", winner="激进派")
        print(elo.get_rankings())
    """
    K_FACTOR = 32  # 调整幅度

    def __init__(self):
        self.players: Dict[str, EloRating] = {}

    def register(self, name: str, initial_rating: float = 1500.0) -> None:
        """注册一个新选手（已存在则忽略）"""
        if name not in self.players:
            self.players[name] = EloRating(name=name, rating=initial_rating)

    def _expected_score(self, rating_a: float, rating_b: float) -> float:
        """A 对 B 的预期胜率（0-1）"""
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    def record_match(self, name_a: str, name_b: str,
                     winner: Optional[str] = None) -> Tuple[float, float]:
        """记录一场对决，更新双方 ELO

        Args:
            name_a / name_b: 双方名字（自动 register）
            winner: 胜者名字；None 或 "draw" 表示平局

        Returns:
            (A 的新分数, B 的新分数)
        """
        self.register(name_a)
        self.register(name_b)
        a = self.players[name_a]
        b = self.players[name_b]

        exp_a = self._expected_score(a.rating, b.rating)
        exp_b = 1 - exp_a

        if winner == name_a:
            score_a, score_b = 1.0, 0.0
            a.wins += 1; b.losses += 1
        elif winner == name_b:
            score_a, score_b = 0.0, 1.0
            a.losses += 1; b.wins += 1
        else:
            # 平局
            score_a, score_b = 0.5, 0.5
            a.draws += 1; b.draws += 1

        delta_a = self.K_FACTOR * (score_a - exp_a)
        delta_b = self.K_FACTOR * (score_b - exp_b)
        a.rating += delta_a
        b.rating += delta_b
        a.matches += 1
        b.matches += 1

        return a.rating, b.rating

    def record_many(self, name_a: str, name_b: str,
                    results: list) -> None:
        """批量记录多场对决结果

        results: list of winner_name or None
        """
        for w in results:
            self.record_match(name_a, name_b, winner=w)

    def get_rankings(self) -> list:
        """获取排行榜（按分数倒序）"""
        return sorted(self.players.values(), key=lambda p: -p.rating)

    def get_rating(self, name: str) -> Optional[float]:
        """获取某选手当前分数"""
        p = self.players.get(name)
        return p.rating if p else None

    def format_rankings(self) -> str:
        """格式化为可读排行榜"""
        rankings = self.get_rankings()
        if not rankings:
            return "（暂无选手）"
        lines = [
            "=" * 60,
            f"  {'#':<4} {'名称':<20} {'ELO':<8} {'胜':<4} {'负':<4} {'平':<4} {'场次':<6}",
            "=" * 60,
        ]
        for i, p in enumerate(rankings, 1):
            lines.append(
                f"  {i:<4} {p.name:<20} {p.rating:<8.0f} {p.wins:<4} {p.losses:<4} {p.draws:<4} {p.matches:<6}"
            )
        lines.append("=" * 60)
        return "\n".join(lines)


def elo_demo():
    """演示 ELO 评分：3 个 prompt 互打 100 场"""
    import random
    random.seed(42)
    elo = EloSystem()
    players = ["激进派", "防守派", "战术派"]
    elo.register(players[0])
    elo.register(players[1])
    elo.register(players[2])
    # 模拟：激进派最强，防守派中等，战术派最弱
    # 但每次对决有随机胜率
    win_probs = {
        ("激进派", "防守派"): 0.6,
        ("激进派", "战术派"): 0.7,
        ("防守派", "战术派"): 0.6,
    }

    for _ in range(50):
        a, b = random.sample(players, 2)
        r = random.random()
        if r < win_probs.get((a, b), 0.5):
            elo.record_match(a, b, winner=a)
        elif r < win_probs.get((a, b), 0.5) + win_probs.get((b, a), 0.5):
            elo.record_match(a, b, winner=b)
        else:
            elo.record_match(a, b, winner=None)

    print(elo.format_rankings())


if __name__ == "__main__":
    elo_demo()
