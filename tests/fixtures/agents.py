"""
测试用 Agent fixtures

包含：
- DummyAgent / AlwaysActionAgent：基础哑 agent，用于隔离测试引擎逻辑
- RandomAgent：完整实现（从 agents.code_agent 复用）
"""
import random
from typing import Optional
import math
from game.agent import Agent, Observation


class DummyAgent(Agent):
    """哑 agent：什么都不做"""
    def step(self, observation: Observation) -> str:
        return "idle"


class AlwaysActionAgent(Agent):
    """永远返回指定动作"""
    def __init__(self, name: str, action: str):
        super().__init__(name)
        self.action = action

    def step(self, observation: Observation) -> str:
        return self.action


class MoveAwayAgent(Agent):
    """朝远离原点的方向移动一格（用于测试移动逻辑）"""
    def step(self, observation: Observation) -> str:
        # 简单测试：x=0 时向右，否则向上
        if observation.my_position[0] < 50:
            return "move_right"
        return "move_up"


class CrashAgent(Agent):
    """在 step() 里抛异常"""
    def step(self, observation: Observation) -> str:
        raise RuntimeError("boom")


class SlowAgent(Agent):
    """在 step() 里 sleep"""
    def __init__(self, name: str, sleep_seconds: float = 5.0):
        super().__init__(name)
        self.sleep_seconds = sleep_seconds

    def step(self, observation: Observation) -> str:
        import time
        time.sleep(self.sleep_seconds)
        return "idle"


class InvalidActionAgent(Agent):
    """返回非法动作"""
    def step(self, observation: Observation) -> str:
        return "moonwalk"


class AlwaysShootAgent(Agent):
    """瞄准 + 射击（假设敌人在正前方）"""
    def step(self, observation: Observation) -> str:
        # 直接开火（不做瞄准，靠冷却判断）
        if observation.shoot_cooldown == 0:
            return "shoot"
        return "idle"


class TurnLeftForeverAgent(Agent):
    """永远左转"""
    def step(self, observation: Observation) -> str:
        return "turn_left"


def make_agent(name: str, behavior: str = "idle", **kwargs) -> Agent:
    """工厂函数：按字符串创建测试 agent"""
    builders = {
        "idle": lambda n: DummyAgent(n),
        "shoot": lambda n: AlwaysShootAgent(n),
        "crash": lambda n: CrashAgent(n),
        "slow": lambda n: SlowAgent(n, kwargs.get("sleep", 5.0)),
        "invalid": lambda n: InvalidActionAgent(n),
        "turn_left": lambda n: TurnLeftForeverAgent(n),
        "action": lambda n: AlwaysActionAgent(n, kwargs.get("action", "idle")),
        "random": lambda n: _RandomAgentWrapper(n),
    }
    return builders[behavior](name)


class _RandomAgentWrapper(Agent):
    """每次随机选一个动作"""
    ACTIONS = ["move_up", "move_down", "move_left", "move_right",
               "turn_left", "turn_right", "shoot", "idle"]

    def step(self, observation: Observation) -> str:
        return random.choice(self.ACTIONS)
