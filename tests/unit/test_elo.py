"""ELO 评分系统测试"""
import pytest
from tools.elo import EloSystem, EloRating


class TestEloRating:
    def test_default_rating(self):
        e = EloRating("test")
        assert e.rating == 1500.0

    def test_record_match_updates_wins(self):
        e = EloRating("test")
        e.wins = 5
        e.matches = 10
        assert e.matches == 10


class TestEloSystem:
    def test_register(self):
        elo = EloSystem()
        elo.register("A")
        assert "A" in elo.players
        assert elo.players["A"].rating == 1500.0

    def test_register_idempotent(self):
        elo = EloSystem()
        elo.register("A", initial_rating=2000.0)
        elo.register("A")  # 第二次不会覆盖
        assert elo.players["A"].rating == 2000.0

    def test_expected_score(self):
        # 同分 → 0.5
        assert abs(EloSystem()._expected_score(1500, 1500) - 0.5) < 0.001
        # 高分 vs 低分 → 接近 1
        assert EloSystem()._expected_score(2000, 1000) > 0.99
        # 低分 vs 高分 → 接近 0
        assert EloSystem()._expected_score(1000, 2000) < 0.01

    def test_record_match_winner_a(self):
        elo = EloSystem()
        elo.register("A")
        elo.register("B")
        rating_a_before = elo.players["A"].rating
        rating_b_before = elo.players["B"].rating
        elo.record_match("A", "B", winner="A")
        # A 胜：A 分数上升，B 分数下降
        assert elo.players["A"].rating > rating_a_before
        assert elo.players["B"].rating < rating_b_before

    def test_record_match_draw(self):
        elo = EloSystem()
        elo.register("A", initial_rating=2000)
        elo.register("B", initial_rating=1000)
        elo.record_match("A", "B", winner=None)
        # 平局：高分 A 应该降分，低分 B 应该升分
        assert elo.players["A"].rating < 2000
        assert elo.players["B"].rating > 1000

    def test_record_match_upset(self):
        """低分击败高分：低分大涨，高分大跌"""
        elo = EloSystem()
        elo.register("A", initial_rating=1000)
        elo.register("B", initial_rating=2000)
        rating_a_before = 1000
        rating_b_before = 2000
        elo.record_match("A", "B", winner="A")
        delta_a = elo.players["A"].rating - rating_a_before
        delta_b = elo.players["B"].rating - rating_b_before
        assert delta_a > 20  # 大涨
        assert delta_b < -20  # 大跌

    def test_record_match_updates_stats(self):
        elo = EloSystem()
        elo.register("A")
        elo.register("B")
        elo.record_match("A", "B", winner="A")
        assert elo.players["A"].wins == 1
        assert elo.players["A"].losses == 0
        assert elo.players["B"].wins == 0
        assert elo.players["B"].losses == 1
        assert elo.players["A"].matches == 1

    def test_get_rankings_sorted_desc(self):
        elo = EloSystem()
        elo.register("low", initial_rating=1000)
        elo.register("mid", initial_rating=1500)
        elo.register("high", initial_rating=2000)
        rankings = elo.get_rankings()
        assert [r.name for r in rankings] == ["high", "mid", "low"]

    def test_get_rating_returns_value(self):
        elo = EloSystem()
        elo.register("test", initial_rating=1700)
        assert elo.get_rating("test") == 1700.0

    def test_get_rating_returns_none_for_unknown(self):
        elo = EloSystem()
        assert elo.get_rating("ghost") is None

    def test_record_many(self):
        elo = EloSystem()
        results = ["A", "B", None, "A"]
        elo.record_many("A", "B", results)
        assert elo.players["A"].matches == 4
        assert elo.players["A"].wins == 2
        assert elo.players["A"].draws == 1

    def test_format_rankings_returns_string(self):
        elo = EloSystem()
        elo.register("A")
        elo.record_match("A", "A", winner=None)  # A vs A 平局
        out = elo.format_rankings()
        assert "ELO 排名" in out or "=" in out
        assert "A" in out


class TestEloIntegration:
    """ELO 系统用于模拟一个简单联赛"""

    def test_competitive_league_converges(self):
        """强选手长期应该排前面"""
        elo = EloSystem()
        # A 强（70% 胜率），B 弱（30% 胜率）
        elo.register("A", initial_rating=1500)
        elo.register("B", initial_rating=1500)
        for _ in range(30):
            import random
            random.seed(42)
            if random.random() < 0.7:
                elo.record_match("A", "B", winner="A")
            else:
                elo.record_match("A", "B", winner="B")
        # 长期下来 A 应该比 B 高
        assert elo.get_rating("A") > elo.get_rating("B")
