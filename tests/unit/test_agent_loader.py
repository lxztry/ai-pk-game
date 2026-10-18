"""
Agent 加载器单元测试

覆盖：utils/agent_loader.py 的异常处理（坏 agent 不能让扫描挂掉）
"""
import textwrap
import pytest


def _write_agent(tmp_path, agent_dir, body):
    """在 tmp_path/agent_dir/agent.py 写入指定代码"""
    agent_path = tmp_path / agent_dir / "agent.py"
    agent_path.parent.mkdir(parents=True, exist_ok=True)
    agent_path.write_text(textwrap.dedent(body), encoding="utf-8")
    return agent_path


class TestAgentLoader:
    def _loader(self, tmp_path):
        from utils.agent_loader import AgentLoader
        return AgentLoader(participants_dir=str(tmp_path))

    def test_discover_empty_dir(self, tmp_path):
        loader = self._loader(tmp_path)
        assert loader.discover_agents() == []

    def test_discover_one_agent(self, tmp_path):
        _write_agent(tmp_path, "alice", '''
            from game.agent import Agent
            from game.agent import Observation

            class Agent(Agent):
                def step(self, observation: Observation) -> str:
                    return "idle"
        ''')
        loader = self._loader(tmp_path)
        agents = loader.discover_agents()
        assert len(agents) == 1
        assert agents[0]["name"] == "alice"

    def test_crash_agent_doesnt_break_scan(self, tmp_path):
        """一个坏 agent 不能让整个扫描挂掉"""
        _write_agent(tmp_path, "good", '''
            from game.agent import Agent
            from game.agent import Observation

            class Agent(Agent):
                def step(self, observation: Observation) -> str:
                    return "idle"
        ''')
        _write_agent(tmp_path, "bad", '''
            import this_module_does_not_exist_xyz
        ''')
        loader = self._loader(tmp_path)
        agents = loader.discover_agents()
        # 至少 good 应该被加载
        names = [a["name"] for a in agents]
        assert "good" in names
        assert "bad" not in names

    def test_skip_underscore_directories(self, tmp_path):
        """_ 开头的目录应跳过"""
        _write_agent(tmp_path, "_hidden", '''
            from game.agent import Agent
            class Agent(Agent):
                def step(self, observation):
                    return "idle"
        ''')
        loader = self._loader(tmp_path)
        agents = loader.discover_agents()
        assert agents == []

    def test_skip_dotfiles(self, tmp_path):
        """. 开头应跳过"""
        _write_agent(tmp_path, ".secret", '''
            from game.agent import Agent
            class Agent(Agent):
                def step(self, observation):
                    return "idle"
        ''')
        loader = self._loader(tmp_path)
        agents = loader.discover_agents()
        assert agents == []

    def test_missing_agent_py_warns(self, tmp_path, capsys):
        """目录里没有 agent.py 时输出警告但不崩"""
        (tmp_path / "noagent").mkdir()
        loader = self._loader(tmp_path)
        agents = loader.discover_agents()
        assert agents == []
        captured = capsys.readouterr()
        assert "agent.py" in captured.out or "警告" in captured.out

    def test_create_instance_fallback_args(self, tmp_path):
        """Agent(name) 失败时尝试 name= 关键字"""
        _write_agent(tmp_path, "kwarg_only", '''
            from game.agent import Agent
            from game.agent import Observation

            class Agent(Agent):
                def __init__(self, name):
                    super().__init__(name)
                    self.label = "kwarg"

                def step(self, observation: Observation) -> str:
                    return "idle"
        ''')
        loader = self._loader(tmp_path)
        instances = loader.create_agent_instances()
        assert any(getattr(i, "label", None) == "kwarg" for i in instances)


class TestParticipantManager:
    def test_scan_returns_dicts(self, tmp_path):
        from utils.participant_manager import ParticipantManager
        _write_agent(tmp_path, "p1", '''
            from game.agent import Agent
            from game.agent import Observation

            class Agent(Agent):
                def step(self, observation: Observation) -> str:
                    return "idle"
        ''')
        pm = ParticipantManager(participants_dir=str(tmp_path), data_file=str(tmp_path / "data.json"))
        discovered = pm.scan_participants_directory()
        assert len(discovered) == 1
        assert discovered[0]["id"] == "p1"
        assert discovered[0]["type"] in ("ai", "human")

    def test_analyze_agent_infers_prompt_via_keyword(self, tmp_path):
        """含 'openai' 关键字的源代码被识别为 ai + Prompt Engineering"""
        from utils.participant_manager import ParticipantManager
        _write_agent(tmp_path, "prompt_user", '''
            import openai
            from game.agent import Agent
            from game.agent import Observation

            class Agent(Agent):
                def step(self, observation: Observation) -> str:
                    return openai_call()
        ''')
        pm = ParticipantManager(participants_dir=str(tmp_path), data_file=str(tmp_path / "data.json"))
        discovered = pm.scan_participants_directory()
        assert discovered[0]["type"] == "ai"
        assert "Prompt" in discovered[0]["developer"]
