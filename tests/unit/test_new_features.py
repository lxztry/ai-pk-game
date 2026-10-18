"""
新功能模块测试：Prompt 对决 / AI 教练 / 每日挑战 / Mock LLM
"""
import pytest
from agents.prompt_agent import PromptAgent, MockLLMClient, OpenAIClient
from tournament.prompt_duel import run_prompt_duel, DuelPlayer, format_duel_report, DuelResult
from tools.coach import analyze_decision_log, format_coach_report, CoachReport
from tools.daily_challenge import (
    get_today_challenge, list_all_challenges, format_challenge,
    DailyChallengeRule, CHALLENGE_TEMPLATES,
)


# ========== Mock LLM ==========

class TestMockLLMClient:
    def test_chat_returns_string(self):
        client = MockLLMClient(persona="aggressive")
        r = client.chat("system", "user prompt")
        assert isinstance(r, str)

    def test_chat_counts_calls(self):
        client = MockLLMClient()
        assert client.call_count == 0
        client.chat("s", "u")
        client.chat("s", "u")
        assert client.call_count == 2

    def test_low_health_returns_move(self):
        client = MockLLMClient(persona="aggressive")
        prompt = """
- 你的生命值：10
- 敌人：x 位置(50,50) 距离10
"""
        action = client.chat("s", prompt)
        assert action in ["move_up", "move_down", "move_left", "move_right", "idle"]

    def test_aggressive_shoots_when_enemy_visible(self):
        client = MockLLMClient(persona="aggressive")
        # 提供完整 prompt：位置 + 方向（已对准）+ 敌人
        prompt = """
- 你的生命值：100
- 你的位置：(40.0, 50.0)
- 你的方向：(1.00, 0.00)
- 射击冷却：0 回合
视野内的敌人：
  - e: 位置(50.0,50.0), 血量100, 距离10
视野内的子弹：无
"""
        action = client.chat("s", prompt)
        # 激进派看到敌人且已瞄准，cooldown=0 → 应该 shoot
        assert action == "shoot"


# ========== PromptAgent with mock ==========

class TestPromptAgentWithMock:
    def test_step_returns_valid_action(self):
        agent = PromptAgent(name="p1", llm_client=MockLLMClient(), persona="balanced")
        from game.agent import Observation
        obs = Observation({
            "my_health": 100, "my_position": [50, 50], "my_direction": [1, 0],
            "enemies_in_view": [], "bullets_in_view": [],
            "obstacles_in_view": [], "supplies_in_view": [],
            "map_boundary": [100, 100], "shoot_cooldown": 0,
        })
        action = agent.step(obs)
        assert action in ["move_up", "move_down", "move_left", "move_right",
                          "turn_left", "turn_right", "shoot", "idle"]

    def test_decision_log_records(self):
        agent = PromptAgent(name="p1", llm_client=MockLLMClient())
        from game.agent import Observation
        obs = Observation({
            "my_health": 80, "my_position": [50, 50], "my_direction": [1, 0],
            "enemies_in_view": [], "bullets_in_view": [],
            "obstacles_in_view": [], "supplies_in_view": [],
            "map_boundary": [100, 100], "shoot_cooldown": 0,
        })
        for _ in range(5):
            agent.step(obs)
        assert len(agent.decision_log) == 5

    def test_cache_works(self):
        """相同 obs 不重复调用 LLM"""
        client = MockLLMClient()
        agent = PromptAgent(name="p1", llm_client=client)
        from game.agent import Observation
        obs = Observation({
            "my_health": 80, "my_position": [50, 50], "my_direction": [1, 0],
            "enemies_in_view": [], "bullets_in_view": [],
            "obstacles_in_view": [], "supplies_in_view": [],
            "map_boundary": [100, 100], "shoot_cooldown": 0,
        })
        agent.step(obs)
        agent.step(obs)  # 应该命中缓存
        agent.step(obs)  # 应该命中缓存
        # 1 次 LLM 调用（首次），2 次缓存命中
        assert client.call_count == 1

    def test_custom_prompt_template(self):
        """set_prompt_template 后缓存必须失效（行为可观测）"""
        from game.agent import Observation
        agent = PromptAgent(name="p1", llm_client=MockLLMClient(persona="balanced"))
        obs = Observation({
            "my_health": 80, "my_position": [50, 50], "my_direction": [1, 0],
            "enemies_in_view": [], "bullets_in_view": [],
            "obstacles_in_view": [], "supplies_in_view": [],
            "map_boundary": [100, 100], "shoot_cooldown": 0,
        })
        agent.step(obs)
        cache_size_before = len(agent._cache)
        # 改 prompt 模板 → 缓存应被清空
        agent.set_prompt_template("新 prompt")
        assert len(agent._cache) == 0, "改 prompt 后缓存应清空"


# ========== Prompt Duel ==========

class TestPromptDuel:
    def test_run_prompt_duel_returns_result(self):
        a = DuelPlayer(name="A", prompt="你是 A", persona="aggressive")
        b = DuelPlayer(name="B", prompt="你是 B", persona="defensive")
        result = run_prompt_duel(a, b, max_turns=20, map_size=30)
        assert isinstance(result, DuelResult)
        assert result.player1_name == "A"
        assert result.player2_name == "B"
        assert result.turns <= 20

    def test_duel_records_llm_calls(self):
        a = DuelPlayer(name="A", prompt="你是 A")
        b = DuelPlayer(name="B", prompt="你是 B")
        result = run_prompt_duel(a, b, max_turns=10)
        # 每个 agent 至少应该有 1 次 LLM 调用
        assert result.player1_decisions >= 1
        assert result.player2_decisions >= 1

    def test_duel_saves_replay(self):
        import os
        a = DuelPlayer(name="A", prompt="你是 A")
        b = DuelPlayer(name="B", prompt="你是 B")
        out = "/tmp/test_duel_replay.html"
        if os.path.exists(out):
            os.remove(out)
        result = run_prompt_duel(a, b, max_turns=10, save_replay_to=out)
        assert result.replay_html == out
        assert os.path.exists(out)

    def test_format_duel_report(self):
        result = DuelResult(
            winner_name="A", player1_name="A", player2_name="B",
            player1_health=50, player2_health=0,
            player1_kills=1, player2_kills=0,
            player1_decisions=10, player2_decisions=10,
            turns=20,
        )
        report = format_duel_report(result)
        assert "PROMPT 对决报告" in report
        assert "A" in report
        assert "胜者" in report


# ========== AI 教练 ==========

class TestAICoach:
    def _log(self, decisions):
        """构造 decision_log"""
        return [
            {
                "turn": i, "hash": f"h{i}", "health": d[0],
                "enemies_visible": d[1], "bullets_visible": 0,
                "action": d[2],
            }
            for i, d in enumerate(decisions)
        ]

    def test_empty_log(self):
        report = analyze_decision_log("p", [])
        assert report.total_decisions == 0
        assert "决策日志为空" in report.recommendations[0]

    def test_high_idle_warning(self):
        log = self._log([(100, 1, "idle")] * 80 + [(100, 0, "move_up")] * 20)
        report = analyze_decision_log("p", log)
        assert "idle" in str(report.recommendations)

    def test_low_shoot_rate_warning(self):
        # 80 回合有敌但 90% 在转向
        log = self._log([(100, 1, "turn_left")] * 80 + [(100, 0, "move_up")] * 20)
        report = analyze_decision_log("p", log)
        # 视野有敌 80 回合，射击率 0%
        assert report.enemy_visible_shoot_rate == 0.0
        assert any("射击率仅" in r for r in report.recommendations)

    def test_low_health_running(self):
        log = self._log([(10, 1, "move_up")] * 10 + [(100, 0, "idle")] * 10)
        report = analyze_decision_log("p", log)
        assert report.low_health_turns == 10
        assert "低血量" in str(report.recommendations)

    def test_action_distribution(self):
        log = self._log([
            (100, 0, "move_up"), (100, 0, "move_down"),
            (100, 0, "turn_left"), (100, 0, "shoot"),
        ])
        report = analyze_decision_log("p", log)
        assert report.action_distribution["move_up"] == 1
        assert report.action_distribution["shoot"] == 1
        assert report.total_decisions == 4

    def test_format_coach_report(self):
        log = self._log([(100, 1, "shoot")] * 10)
        report = analyze_decision_log("p", log)
        out = format_coach_report(report)
        assert "AI 教练报告" in out
        assert "动作分布" in out


# ========== 每日挑战 ==========

class TestDailyChallenge:
    def test_get_today_returns_rule(self):
        rule = get_today_challenge()
        assert isinstance(rule, DailyChallengeRule)
        assert rule.title
        assert rule.code

    def test_list_all_seven(self):
        rules = list_all_challenges()
        assert len(rules) == 7
        # 每天一个
        weekdays = {r.weekday for r in rules}
        assert len(weekdays) == 7

    def test_each_challenge_has_modifiers(self):
        for rule in CHALLENGE_TEMPLATES.values():
            assert rule.modifiers, f"{rule.code} 无 modifier"

    def test_format_challenge(self):
        rule = get_today_challenge()
        out = format_challenge(rule)
        assert "每日挑战" in out
        assert rule.title in out

    def test_apply_to_engine(self):
        from game.engine import GameEngine
        from tests.fixtures.agents import DummyAgent
        rule = DailyChallengeRule(
            code="test", title="Test", description="x",
            weekday="monday", modifiers={"max_health": 30, "view_distance": 10},
        )
        engine = GameEngine([DummyAgent("a"), DummyAgent("b")], 100, 100)
        rule.apply_to_engine(engine)
        assert engine.state.agents[0].health == 30
        assert engine.view_distance == 10
