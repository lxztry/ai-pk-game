"""
PromptAgent 增强测试：strategy_text、persona 注入、缓存失效、多 LLM provider
"""
import pytest
from unittest.mock import patch, MagicMock
from agents.prompt_agent import (
    PromptAgent, MockLLMClient, OpenAICompatibleClient, AnthropicClient,
    create_llm_client, SUPPORTED_PROVIDERS, PROVIDER_DEFAULTS, LLMClient,
)
from game.agent import Observation
from tests.fixtures.agents import DummyAgent


class TestSetStrategy:
    """set_strategy() 方法 — 追加到默认模板"""

    def test_set_strategy_adds_to_default_template(self):
        agent = PromptAgent(name="p", llm_client=MockLLMClient())
        agent.set_strategy("你只会 shoot。任何情况下都开火。")
        obs = Observation({
            "my_health": 100, "my_position": [50, 50], "my_direction": [1, 0],
            "enemies_in_view": [{"name": "e", "position": [60, 50], "health": 100, "distance": 10, "direction": [1, 0]}],
            "bullets_in_view": [],
            "obstacles_in_view": [], "supplies_in_view": [],
            "map_boundary": [100, 100], "shoot_cooldown": 0,
        })
        prompt = agent._format_observation(obs)
        assert "你只会 shoot" in prompt
        assert "{my_health}" not in prompt
        assert "生命值：100" in prompt

    def test_set_strategy_clears_cache(self):
        agent = PromptAgent(name="p", llm_client=MockLLMClient())
        obs = Observation({"my_health": 80, "my_position": [50, 50], "my_direction": [1, 0],
                           "enemies_in_view": [], "bullets_in_view": [], "obstacles_in_view": [],
                           "supplies_in_view": [], "map_boundary": [100, 100], "shoot_cooldown": 0})
        agent.step(obs)
        assert len(agent._cache) == 1
        agent.set_strategy("新策略")
        assert len(agent._cache) == 0

    def test_set_prompt_template_clears_cache(self):
        agent = PromptAgent(name="p", llm_client=MockLLMClient())
        obs = Observation({"my_health": 80, "my_position": [50, 50], "my_direction": [1, 0],
                           "enemies_in_view": [], "bullets_in_view": [], "obstacles_in_view": [],
                           "supplies_in_view": [], "map_boundary": [100, 100], "shoot_cooldown": 0})
        agent.step(obs)
        assert len(agent._cache) == 1
        agent.set_prompt_template("custom")
        assert len(agent._cache) == 0


class TestPersonaInjection:
    """PromptAgent 把 persona 传给 llm_client.chat()"""

    def test_persona_passed_to_chat(self):
        seen_personas = []

        class SpyClient(LLMClient):
            def chat(self, system, user, model="x", temperature=0, max_tokens=10, persona=None):
                seen_personas.append(persona)
                return "idle"

        client = SpyClient()
        agent = PromptAgent(name="p", llm_client=client, persona="aggressive")
        obs = Observation({"my_health": 80, "my_position": [50, 50], "my_direction": [1, 0],
                           "enemies_in_view": [], "bullets_in_view": [], "obstacles_in_view": [],
                           "supplies_in_view": [], "map_boundary": [100, 100], "shoot_cooldown": 0})
        agent.step(obs)
        assert "aggressive" in seen_personas


class TestMockLLMBehavior:
    """Mock LLM 的决策应该与 persona 一致"""

    def _prompt_with_enemy(self, health=100, cooldown=0, has_enemy=True, my_pos=(50, 50), enemy_pos=(60, 50)):
        lines = [
            f"- 你的生命值：{health}",
            f"- 你的位置：({my_pos[0]}, {my_pos[1]})",
            "- 你的方向：(1, 0)",
            f"- 射击冷却：{cooldown} 回合",
            "- 地图大小：100 x 100",
        ]
        if has_enemy:
            lines.append("\n视野内的敌人：")
            lines.append(f"  - e: 位置({enemy_pos[0]}, {enemy_pos[1]}), 血量100, 距离10")
        else:
            lines.append("\n视野内的敌人：\n  无")
        lines.append("\n视野内的子弹：\n  无")
        return "\n".join(lines)

    def test_aggressive_shoots_at_enemy(self):
        client = MockLLMClient()
        prompt = self._prompt_with_enemy(health=100, cooldown=0)
        action = client.chat("s", prompt, persona="aggressive")
        assert action == "shoot"

    def test_aggressive_does_not_shoot_during_cooldown(self):
        client = MockLLMClient()
        prompt = self._prompt_with_enemy(health=100, cooldown=10)
        action = client.chat("s", prompt, persona="aggressive")
        assert action != "shoot"

    def test_aggressive_moves_toward_enemy(self):
        client = MockLLMClient()
        prompt = self._prompt_with_enemy(health=100, cooldown=10, my_pos=(50, 50), enemy_pos=(80, 50))
        for _ in range(10):
            action = client.chat("s", prompt, persona="aggressive")
            if action != "shoot":
                assert action == "move_right"

    def test_defensive_moves_away_from_enemy(self):
        client = MockLLMClient()
        prompt = self._prompt_with_enemy(health=100, cooldown=10, my_pos=(50, 50), enemy_pos=(80, 50))
        action = client.chat("s", prompt, persona="defensive")
        assert action == "move_left"

    def test_low_health_runs(self):
        client = MockLLMClient()
        prompt = self._prompt_with_enemy(health=20, cooldown=0)
        action = client.chat("s", prompt, persona="aggressive")
        assert action != "shoot"

    def test_no_enemy_moves_randomly(self):
        client = MockLLMClient()
        prompt = self._prompt_with_enemy(has_enemy=False)
        action = client.chat("s", prompt, persona="aggressive")
        assert action in ["move_up", "move_down", "move_left", "move_right"]


# ========== 多 LLM provider 测试 ==========

class TestProviderDefaults:
    """PROVIDER_DEFAULTS 配置完整性"""

    def test_all_providers_have_required_fields(self):
        required = {"base_url", "default_model", "api_key_env", "use_openai_sdk"}
        for name, cfg in PROVIDER_DEFAULTS.items():
            assert required <= set(cfg.keys()), f"{name} 缺少字段"

    def test_supported_providers_listed(self):
        assert "openai" in SUPPORTED_PROVIDERS
        assert "anthropic" in SUPPORTED_PROVIDERS
        assert "deepseek" in SUPPORTED_PROVIDERS
        assert "qwen" in SUPPORTED_PROVIDERS

    def test_default_models_reasonable(self):
        # 至少有默认模型名（不能空字符串）
        for name, cfg in PROVIDER_DEFAULTS.items():
            assert cfg["default_model"], f"{name} 没有默认模型"


class TestOpenAICompatibleClient:
    """OpenAI 兼容 API（OpenAI/DeepSeek/Qwen/Zhipu/Moonshot）"""

    def test_requires_api_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        with pytest.raises(ValueError, match="未找到 API key"):
            OpenAICompatibleClient(provider="openai")

    def test_reads_env_var(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")
        client = OpenAICompatibleClient(provider="openai")
        assert client.api_key == "sk-test-123"
        assert client.provider == "openai"

    def test_explicit_key_overrides_env(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-from-env")
        client = OpenAICompatibleClient(api_key="sk-explicit", provider="openai")
        assert client.api_key == "sk-explicit"

    def test_custom_base_url(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        client = OpenAICompatibleClient(
            provider="openai",
            base_url="http://localhost:11434/v1"
        )
        assert client.base_url == "http://localhost:11434/v1"

    def test_provider_default_base_url(self):
        """每个 provider 应该有自己的默认 base_url"""
        # DeepSeek
        from openai import OpenAI
        with patch.object(OpenAI, "__init__", return_value=None) as mock_init:
            OpenAICompatibleClient(api_key="sk-test", provider="deepseek")
            call_kwargs = mock_init.call_args.kwargs
            assert "deepseek.com" in call_kwargs.get("base_url", "")

    def test_get_default_model(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        client = OpenAICompatibleClient(provider="openai")
        assert client.get_default_model() == "gpt-4o-mini"


class TestFactory:
    """create_llm_client 工厂方法"""

    def test_factory_creates_openai_client(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        client = create_llm_client("openai")
        assert isinstance(client, OpenAICompatibleClient)
        assert client.provider == "openai"

    def test_factory_creates_deepseek_client(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-deepseek")
        client = create_llm_client("deepseek")
        assert isinstance(client, OpenAICompatibleClient)
        assert client.provider == "deepseek"
        assert client.api_key == "sk-deepseek"

    def test_factory_creates_qwen_client(self, monkeypatch):
        monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-qwen")
        client = create_llm_client("qwen")
        assert client.api_key == "sk-qwen"
        assert client.provider == "qwen"

    def test_factory_creates_anthropic_client(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant")
        client = create_llm_client("anthropic")
        assert isinstance(client, AnthropicClient)

    def test_factory_unknown_provider_uses_openai_compatible(self, monkeypatch):
        """未知 provider 走 OpenAI 兼容 fallback"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        client = create_llm_client("custom-llm-provider")
        assert isinstance(client, OpenAICompatibleClient)
        assert client.provider == "custom-llm-provider"

    def test_factory_case_insensitive(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        client = create_llm_client("OPENAI")
        assert client.provider == "openai"


class TestAnthropicClient:
    """Anthropic Claude 客户端"""

    def test_requires_api_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ValueError):
            AnthropicClient()

    def test_get_default_model(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant")
        client = AnthropicClient()
        assert "claude" in client.get_default_model().lower()


class TestProviderEnvironmentVariables:
    """每个 provider 有正确的环境变量名"""

    def test_env_var_names(self):
        assert PROVIDER_DEFAULTS["openai"]["api_key_env"] == "OPENAI_API_KEY"
        assert PROVIDER_DEFAULTS["anthropic"]["api_key_env"] == "ANTHROPIC_API_KEY"
        assert PROVIDER_DEFAULTS["deepseek"]["api_key_env"] == "DEEPSEEK_API_KEY"
        assert PROVIDER_DEFAULTS["qwen"]["api_key_env"] == "DASHSCOPE_API_KEY"
        assert PROVIDER_DEFAULTS["zhipu"]["api_key_env"] == "ZHIPUAI_API_KEY"
        assert PROVIDER_DEFAULTS["moonshot"]["api_key_env"] == "MOONSHOT_API_KEY"


class TestPromptAgentWithCustomProvider:
    """PromptAgent 接 OpenAI 兼容 provider"""

    def test_uses_provider_default_model(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        client = create_llm_client("openai")
        agent = PromptAgent(name="p", llm_client=client)
        # 默认模型应该是 gpt-4o-mini
        assert agent.model == "gpt-4o-mini"

    def test_custom_model_overrides(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        client = create_llm_client("openai")
        agent = PromptAgent(name="p", llm_client=client, model="gpt-4o")
        assert agent.model == "gpt-4o"

