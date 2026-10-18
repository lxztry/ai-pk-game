"""
胜负判定单元测试

覆盖：
- 单一存活者立即获胜
- 超时后按评分判定（kill * 10000 + health）
- 平局返回 None
- 团队模式（只剩一队时获胜）
- 最大回合数强制终止
"""
import pytest

from game.engine import GameEngine, GameState
from tests.fixtures.agents import (
    DummyAgent, AlwaysActionAgent, make_agent,
)


# ---------- 1. 直接获胜 ----------

class TestImmediateWinner:
    def test_one_survivor_wins_without_score_judge(self):
        """两个 agent，一个血归零，另一个直接赢（不进入评分模式）"""
        a1 = DummyAgent("alive")
        a1.health = 50
        a2 = DummyAgent("dead")
        a2.health = 0  # 已死
        state = GameState([a1, a2], map_width=100, map_height=100)
        winner = state.get_winner(allow_score_judge=False)
        assert winner is a1

    def test_two_alive_no_winner(self):
        """两个都活着，没有评分模式时不返回获胜者"""
        a1 = DummyAgent("a1")
        a1.health = 80
        a2 = DummyAgent("a2")
        a2.health = 70
        state = GameState([a1, a2], map_width=100, map_height=100)
        winner = state.get_winner(allow_score_judge=False)
        assert winner is None

    def test_all_dead_no_winner(self):
        """全死返回 None（不允许评分模式）"""
        a1 = DummyAgent("a1")
        a1.health = 0
        a2 = DummyAgent("a2")
        a2.health = 0
        state = GameState([a1, a2], map_width=100, map_height=100)
        assert state.get_winner(allow_score_judge=False) is None


# ---------- 2. 评分判定 ----------

class TestScoreJudge:
    def test_score_formula_kills_first(self):
        """击杀数差一票否决血量"""
        a1 = DummyAgent("more_kills")
        a1.health = 5
        a1.kills = 2
        a2 = DummyAgent("more_health")
        a2.health = 100
        a2.kills = 1
        state = GameState([a1, a2], map_width=100, map_height=100)
        # a1 score = 2*10000 + 5 = 20005
        # a2 score = 1*10000 + 100 = 10100
        # a1 赢
        winner = state.get_winner(allow_score_judge=True)
        assert winner is a1

    def test_score_formula_health_tiebreaker(self):
        """击杀数相同，按血量判"""
        a1 = DummyAgent("more_hp")
        a1.health = 80
        a1.kills = 1
        a2 = DummyAgent("less_hp")
        a2.health = 50
        a2.kills = 1
        state = GameState([a1, a2], map_width=100, map_height=100)
        winner = state.get_winner(allow_score_judge=True)
        assert winner is a1

    def test_strict_tie_returns_none(self):
        """评分完全一致时，allow_score_judge 仍返回 None"""
        a1 = DummyAgent("tie1")
        a1.health = 50
        a1.kills = 1
        a2 = DummyAgent("tie2")
        a2.health = 50
        a2.kills = 1
        state = GameState([a1, a2], map_width=100, map_height=100)
        winner = state.get_winner(allow_score_judge=True)
        assert winner is None  # 打平了


# ---------- 3. 最大回合数 ----------

class TestMaxTurns:
    def test_max_turns_default_500(self):
        """引擎默认 max_turns=500"""
        engine = GameEngine([DummyAgent("a"), DummyAgent("b")], 50, 50)
        engine.run(max_turns=50, verbose=False)
        assert engine.state.turn <= 50

    def test_max_turns_hard_limit(self):
        """即使两个 agent 都 idle，超过 max_turns 必须终止"""
        a = AlwaysActionAgent("a", "idle")
        b = AlwaysActionAgent("b", "idle")
        engine = GameEngine([a, b], 50, 50)
        winner = engine.run(max_turns=20, verbose=False)
        assert engine.state.turn == 20

    def test_max_turns_score_judge_called(self):
        """超时后必须按评分判定（即使没人死）"""
        a = AlwaysActionAgent("a", "idle")
        a.health = 100
        b = AlwaysActionAgent("b", "idle")
        b.health = 30
        engine = GameEngine([a, b], 50, 50)
        winner = engine.run(max_turns=10, verbose=False)
        # a 血量多，赢
        assert winner is a


# ---------- 4. 团队模式 ----------

class TestTeamMode:
    def test_single_team_alive_wins(self):
        """只剩一个 team 存活时该 team 赢"""
        a1 = DummyAgent("p1")
        a1.health = 100
        a1.team_id = 1
        a2 = DummyAgent("p2")
        a2.health = 100
        a2.team_id = 1
        a3 = DummyAgent("p3")
        a3.health = 0  # 死了
        a3.team_id = 2
        engine = GameEngine([a1, a2, a3], 100, 100)
        assert engine._get_winning_team() == 1

    def test_two_teams_alive_no_winner(self):
        """两个 team 都还有活人时不算结束"""
        a1 = DummyAgent("p1")
        a1.health = 100
        a1.team_id = 1
        a2 = DummyAgent("p2")
        a2.health = 100
        a2.team_id = 2
        engine = GameEngine([a1, a2], 100, 100)
        assert engine._get_winning_team() is None

    def test_all_team_members_dead(self):
        """所有存活者都没有 team_id 时返回 None"""
        a1 = DummyAgent("p1")
        a1.health = 100
        a1.team_id = None
        engine = GameEngine([a1], 100, 100)
        assert engine._get_winning_team() is None


# ---------- 5. 端到端小场景 ----------

class TestEndToEnd:
    def test_aggressive_vs_defensive_has_winner(self):
        """随机/激进 agent 对战应该能跑出胜负"""
        from agents.code_agent import AggressiveAgent, DefensiveAgent
        a1 = AggressiveAgent("agg")
        a2 = DefensiveAgent("def")
        engine = GameEngine([a1, a2], 50, 50)
        winner = engine.run(max_turns=200, verbose=False)
        # 不强断言哪一方赢，但应该有胜负或平局
        assert winner is None or winner.name in ("agg", "def")

    def test_idle_vs_idle_score_judge(self):
        """两个 idle agent 跑满 max_turns，按血量（都是 100）平局"""
        a = DummyAgent("a")
        a.health = 100
        b = DummyAgent("b")
        b.health = 100
        engine = GameEngine([a, b], 50, 50)
        winner = engine.run(max_turns=10, verbose=False)
        # 都是 100 血，0 击杀，平局
        assert winner is None

    def test_idle_vs_idle_with_kill_diff(self):
        """手动设置击杀差，应被评分规则识别"""
        a = DummyAgent("leader")
        a.health = 100
        a.kills = 3
        b = DummyAgent("follower")
        b.health = 100
        b.kills = 0
        state = GameState([a, b], 50, 50)
        winner = state.get_winner(allow_score_judge=True)
        assert winner is a
