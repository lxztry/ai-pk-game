"""
Prompt派Agent - 通过LLM生成决策

支持多 LLM provider：
- OpenAI（gpt-4o-mini / gpt-4 / o1 等）
- Anthropic Claude（claude-3-5-sonnet 等）
- DeepSeek（deepseek-chat / deepseek-reasoner）
- 通义千问 Qwen（qwen-plus / qwen-turbo）
- 其他任何 OpenAI 兼容 API（自定义 base_url）
- Mock LLM（离线 demo / 测试）

通过环境变量配置 API key：
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- DEEPSEEK_API_KEY
- DASHSCOPE_API_KEY（Qwen）
- LLM_BASE_URL（自定义）

也可以显式传入 api_key=... 参数。
"""
import os
import time
import hashlib
from typing import Optional, Callable, Dict, Any
from game.agent import Agent, Observation

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


# ---------- Provider 配置 ----------

# 每个 provider 的默认 base_url 和默认模型
PROVIDER_DEFAULTS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "api_key_env": "OPENAI_API_KEY",
        "use_openai_sdk": True,
    },
    "anthropic": {
        "base_url": None,  # Anthropic SDK 自己处理
        "default_model": "claude-3-5-sonnet-20241022",
        "api_key_env": "ANTHROPIC_API_KEY",
        "use_openai_sdk": False,
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "api_key_env": "DEEPSEEK_API_KEY",
        "use_openai_sdk": True,
    },
    "qwen": {
        # 通义千问的 OpenAI 兼容端点
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-plus",
        "api_key_env": "DASHSCOPE_API_KEY",
        "use_openai_sdk": True,
    },
    "zhipu": {
        # 智谱 GLM（OpenAI 兼容）
        "base_url": "https://open.bigmodel.cn/api/paas/v4/",
        "default_model": "glm-4-plus",
        "api_key_env": "ZHIPUAI_API_KEY",
        "use_openai_sdk": True,
    },
    "moonshot": {
        # 月之暗面 Kimi（OpenAI 兼容）
        "base_url": "https://api.moonshot.cn/v1",
        "default_model": "moonshot-v1-32k",
        "api_key_env": "MOONSHOT_API_KEY",
        "use_openai_sdk": True,
    },
}


# ---------- LLM 客户端抽象 ----------

class LLMClient:
    """LLM 客户端抽象基类"""
    provider_name: str = "base"

    def chat(self, system: str, user: str, model: str = None,
             temperature: float = 0.3, max_tokens: int = 10,
             persona: Optional[str] = None) -> str:
        """同步调用，返回文本"""
        raise NotImplementedError

    def get_default_model(self) -> str:
        raise NotImplementedError


class OpenAICompatibleClient(LLMClient):
    """通用 OpenAI 兼容 API 客户端（用于 OpenAI/DeepSeek/Qwen/Zhipu/Moonshot 等）"""

    def __init__(self, api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 provider: str = "openai"):
        if not OPENAI_AVAILABLE:
            raise ImportError("需要安装 openai 库: pip install openai")

        info = PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS["openai"])
        env_key = info["api_key_env"]

        # 取 API key（参数 > 环境变量 > 自定义 base_url 推断）
        self.api_key = api_key or os.getenv(env_key)
        if not self.api_key:
            # 兜底：用 LLM_API_KEY
            self.api_key = api_key or os.getenv("LLM_API_KEY")
        if not self.api_key:
            raise ValueError(
                f"未找到 API key。请设置环境变量 {env_key} 或传入 api_key=..."
            )

        # 取 base_url（参数 > PROVIDER 默认 > OPENAI_BASE_URL 环境变量）
        self.base_url = (
            base_url
            or info.get("base_url")
            or os.getenv("LLM_BASE_URL")
        )

        self.provider = provider
        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.provider_name = provider

    def get_default_model(self) -> str:
        return PROVIDER_DEFAULTS.get(self.provider, {}).get("default_model", "gpt-4o-mini")

    def chat(self, system, user, model=None, temperature=0.3, max_tokens=10, persona=None):
        if model is None:
            model = self.get_default_model()
        r = self._client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return r.choices[0].message.content.strip()


class AnthropicClient(LLMClient):
    """Anthropic Claude 客户端"""

    def __init__(self, api_key: Optional[str] = None):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("需要安装 anthropic 库: pip install anthropic")
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("需要提供 ANTHROPIC_API_KEY 或设置环境变量")
        self._client = anthropic.Anthropic(api_key=api_key)
        self.provider_name = "anthropic"

    def get_default_model(self) -> str:
        return PROVIDER_DEFAULTS["anthropic"]["default_model"]

    def chat(self, system, user, model=None, temperature=0.3, max_tokens=10, persona=None):
        if model is None:
            model = self.get_default_model()
        # Claude 3.5 用 messages 接口
        r = self._client.messages.create(
            model=model,
            system=system,
            messages=[{"role": "user", "content": user}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        # Claude 返回 content list
        return r.content[0].text.strip()


# 别名（向后兼容）
OpenAIClient = OpenAICompatibleClient


# ---------- LLM Factory ----------

def create_llm_client(provider: str = "openai",
                      api_key: Optional[str] = None,
                      base_url: Optional[str] = None,
                      model: Optional[str] = None,
                      persona: Optional[str] = None) -> LLMClient:
    """LLM 客户端工厂方法

    Args:
        provider: openai / anthropic / deepseek / qwen / zhipu / moonshot / mock
        api_key: 显式传入的 API key（可选）
        base_url: 自定义 base_url（可选，用于代理或自部署）
        model: 默认模型名（可选，会传给 PromptAgent）
        persona: personality hint（仅 mock 用）

    Returns:
        LLMClient 实例

    Examples:
        >>> client = create_llm_client("openai")
        >>> client = create_llm_client("anthropic")
        >>> client = create_llm_client("deepseek", api_key="sk-...")
        >>> client = create_llm_client("qwen")
        >>> # 自定义 base_url（用于本地 Ollama / vLLM / 等）
        >>> client = create_llm_client("openai", base_url="http://localhost:11434/v1")
        >>> # Mock（无需 API key，用于 demo/测试）
        >>> client = create_llm_client("mock")
    """
    provider = provider.lower()
    if provider == "mock":
        return MockLLMClient(persona=persona or "balanced")
    if provider == "anthropic":
        return AnthropicClient(api_key=api_key)
    # OpenAI 兼容 API（OpenAI/DeepSeek/Qwen/Zhipu/Moonshot/自部署）
    return OpenAICompatibleClient(api_key=api_key, base_url=base_url, provider=provider)


# 列出所有支持的 provider（用于文档和错误提示）
SUPPORTED_PROVIDERS = list(PROVIDER_DEFAULTS.keys())



class MockLLMClient(LLMClient):
    """Mock LLM 客户端 — 根据 prompt 内容启发式返回合理动作

    用于离线 demo / 测试 / Prompt 对决时观察不同 prompt 的效果。
    """
    def __init__(self, persona: str = "balanced"):
        """
        Args:
            persona: 性格影响决策风格
                - "aggressive": 倾向于接近敌人并射击
                - "defensive": 倾向于逃跑、保持距离
                - "sniper": 远距离优先，找掩护
                - "balanced": 通用
        """
        self.persona = persona
        self.call_count = 0  # 统计调用次数（用于演示）

    def chat(self, system, user, model="mock", temperature=0.0, max_tokens=10, persona=None):
        # 用调用方传进来的 persona 覆盖（PromptAgent 才是 source of truth）
        effective_persona = persona or self.persona
        self.call_count += 1
        time.sleep(0.001)  # 模拟网络延迟
        return self._decide(user, effective_persona)

    def _decide(self, user_prompt: str, persona: Optional[str] = None) -> str:
        """根据 prompt 内容启发式决策

        Mock LLM 会真的"瞄准"敌人：解析 prompt 里的位置和方向，
        计算角度差，再决定 turn/shoot/move。
        """
        import re
        import math
        persona = persona or self.persona

        # ---- 解析 prompt ----
        my_health = 100
        my_pos = None
        my_dir = None
        shoot_cooldown = 0
        enemy_pos = None
        has_enemy = False

        m = re.search(r"生命值[：:]\s*(\d+)", user_prompt)
        if m:
            my_health = int(m.group(1))
        m = re.search(r"你的位置[：:]\s*\(([\d.]+),\s*([\d.]+)\)", user_prompt)
        if m:
            my_pos = (float(m.group(1)), float(m.group(2)))
        m = re.search(r"你的方向[：:]\s*\(([-\d.]+),\s*([-\d.]+)\)", user_prompt)
        if m:
            my_dir = (float(m.group(1)), float(m.group(2)))
        m = re.search(r"射击冷却[：:]\s*(\d+)", user_prompt)
        if m:
            shoot_cooldown = int(m.group(1))

        if "视野内的敌人：" in user_prompt and "视野内的子弹：" in user_prompt:
            block = user_prompt.split("视野内的敌人：")[1].split("视野内的子弹：")[0]
            has_enemy = "距离" in block
            if has_enemy:
                m = re.search(r"位置\(([\d.]+),\s*([\d.]+)\)", block)
                if m:
                    enemy_pos = (float(m.group(1)), float(m.group(2)))

        # 通用瞄准辅助
        def angle_to_target(my_pos, my_dir, target_pos):
            """返回 (差角, 距离)"""
            dx = target_pos[0] - my_pos[0]
            dy = target_pos[1] - my_pos[1]
            target_angle = math.atan2(dy, dx)
            current_angle = math.atan2(my_dir[1], my_dir[0])
            diff = target_angle - current_angle
            # wrap to [-π, π]
            while diff > math.pi:
                diff -= 2 * math.pi
            while diff < -math.pi:
                diff += 2 * math.pi
            return diff

        def aimed(my_pos, my_dir, target_pos, tolerance=0.5):
            return abs(angle_to_target(my_pos, my_dir, target_pos)) < tolerance

        def turn_toward(my_pos, my_dir, target_pos):
            """转一次（30°）朝敌人"""
            diff = angle_to_target(my_pos, my_dir, target_pos)
            return "turn_left" if diff < 0 else "turn_right"

        # ---- 根据 persona 决策 ----

        # 低血：所有 persona 都跑
        if my_health < 30 and my_pos and enemy_pos:
            return self._move_away(my_pos, enemy_pos)

        # 视野内有敌人子弹且不是自己射的 → 主动闪避
        if "视野内的子弹" in user_prompt:
            block = user_prompt.split("视野内的子弹：")[1].split("\n")[0] if "视野内的子弹" in user_prompt else ""
            if "距离" in block and my_pos:
                # 有敌方子弹近 → 闪避
                if random.random() < 0.55:
                    return random.choice(["dodge_left", "dodge_right"])

        if persona == "aggressive":
            # 有敌且冷却好 → 瞄准就 shoot，否则转向
            if has_enemy and shoot_cooldown == 0 and my_pos and my_dir and enemy_pos:
                if aimed(my_pos, my_dir, enemy_pos):
                    return "shoot"
                else:
                    return turn_toward(my_pos, my_dir, enemy_pos)
            if has_enemy and my_pos and my_dir and enemy_pos:
                # 冷却中，朝敌人转 + 移动
                if not aimed(my_pos, my_dir, enemy_pos, tolerance=0.8):
                    return turn_toward(my_pos, my_dir, enemy_pos)
                return self._move_toward(my_pos, enemy_pos)
            # 没敌人，随机探索
            return random.choice(["move_up", "move_down", "move_left", "move_right"])

        elif persona == "defensive":
            # 血量中等 → 远程射击（容忍度大）；血量低 → 远离
            if my_health < 60 and my_pos and enemy_pos:
                return self._move_away(my_pos, enemy_pos)
            if has_enemy and shoot_cooldown == 0 and my_pos and my_dir and enemy_pos:
                if aimed(my_pos, my_dir, enemy_pos, tolerance=0.8):
                    return "shoot"
                return turn_toward(my_pos, my_dir, enemy_pos)
            # 没敌人 → 横向移动
            return random.choice(["move_left", "move_right"])

        elif persona == "sniper":
            # 远距离更耐心
            if has_enemy and shoot_cooldown == 0 and my_pos and my_dir and enemy_pos:
                if aimed(my_pos, my_dir, enemy_pos, tolerance=0.3):
                    return "shoot"
                return turn_toward(my_pos, my_dir, enemy_pos)
            return random.choice(["turn_left", "turn_right"])

        # balanced
        if has_enemy and shoot_cooldown == 0 and my_pos and my_dir and enemy_pos:
            if aimed(my_pos, my_dir, enemy_pos):
                return "shoot"
            return turn_toward(my_pos, my_dir, enemy_pos)
        return random.choice(["turn_left", "turn_right", "move_up", "move_down"])

    @staticmethod
    def _move_toward(my_pos, target_pos):
        """朝目标移动"""
        dx = target_pos[0] - my_pos[0]
        dy = target_pos[1] - my_pos[1]
        if abs(dx) > abs(dy):
            return "move_right" if dx > 0 else "move_left"
        return "move_down" if dy > 0 else "move_up"

    @staticmethod
    def _move_away(my_pos, target_pos):
        """远离目标"""
        dx = my_pos[0] - target_pos[0]
        dy = my_pos[1] - target_pos[1]
        if abs(dx) > abs(dy):
            return "move_right" if dx > 0 else "move_left"
        return "move_down" if dy > 0 else "move_up"

    def reset_stats(self):
        self.call_count = 0


import random


# ---------- PromptAgent ----------

class PromptAgent(Agent):
    """通过 Prompt 调用 LLM 生成决策的 Agent"""

    def __init__(self, name: str, llm_client: Optional[LLMClient] = None,
                 persona: str = "balanced", model: str = "gpt-4o-mini"):
        super().__init__(name)
        self.model = model

        # 兼容旧 API：没传 client 就用 OpenAI
        if llm_client is None:
            llm_client = OpenAIClient()
        self.llm_client = llm_client
        self.persona = persona
        self.prompt_template = self._default_prompt_template()
        # 用户自定义策略说明（追加到默认模板的"策略建议"部分）
        self.strategy_text: str = ""
        # 决策缓存：相同 observation 不重复调用 LLM
        self._cache: Dict[str, str] = {}
        # 决策历史（用于 AI 教练分析）
        self.decision_log: list = []

    def _default_prompt_template(self) -> str:
        return """你是一个顶级的战斗特工AI。你的目标是生存并击败所有敌人。

当前游戏状态：
- 你的生命值：{my_health}
- 你的位置：({my_position[0]:.1f}, {my_position[1]:.1f})
- 你的方向：({my_direction[0]:.2f}, {my_direction[1]:.2f})
- 射击冷却：{shoot_cooldown} 回合
- 地图大小：{map_boundary[0]} x {map_boundary[1]}

视野内的敌人：
{enemies_info}

视野内的子弹：
{bullets_info}

你可以执行的动作：
- "move_up": 向上移动
- "move_down": 向下移动
- "move_left": 向左移动
- "move_right": 向右移动
- "turn_left": 向左转向
- "turn_right": 向右转向
- "shoot": 射击（需要冷却时间为0）
- "idle": 不执行任何动作

策略建议：
1. 如果生命值低（<30），优先躲避和移动，远离敌人和子弹
2. 如果敌人正在瞄准你或距离很近，快速移动或转向躲避
3. 如果敌人在你的正前方且距离适中（10-20），优先射击
4. 尽量利用地图边界作为掩护
5. 注意射击冷却时间，不要浪费射击机会
6. 优先攻击血量低的敌人

请根据当前状态，分析最优策略，只返回一个动作字符串，不要有任何其他解释。
你的决策是："""

    def _format_observation(self, observation: Observation) -> str:
        """格式化 observation 为 prompt 文本"""
        if observation.enemies_in_view:
            enemies_info = "\n".join([
                f"  - {e['name']}: 位置({e['position'][0]:.1f}, {e['position'][1]:.1f}), "
                f"血量{e['health']}, 距离{e['distance']:.1f}"
                for e in observation.enemies_in_view
            ])
        else:
            enemies_info = "  无"

        if observation.bullets_in_view:
            bullets_info = "\n".join([
                f"  - 位置({b['position'][0]:.1f}, {b['position'][1]:.1f}), 距离{b['distance']:.1f}"
                for b in observation.bullets_in_view
            ])
        else:
            bullets_info = "  无"

        return self._effective_prompt_template().format(
            my_health=observation.my_health,
            my_position=observation.my_position,
            my_direction=observation.my_direction,
            shoot_cooldown=observation.shoot_cooldown,
            map_boundary=observation.map_boundary,
            enemies_info=enemies_info,
            bullets_info=bullets_info,
        )

    def _obs_hash(self, observation: Observation) -> str:
        """对 observation 算 hash 用于缓存"""
        data = (
            observation.my_health,
            tuple(observation.my_position),
            tuple(observation.my_direction),
            observation.shoot_cooldown,
            observation.my_weapon,
            len(observation.enemies_in_view),
            len(observation.bullets_in_view),
            len(observation.supplies_in_view),
        )
        return hashlib.md5(str(data).encode()).hexdigest()

    def step(self, observation: Observation) -> str:
        """通过 LLM 生成决策"""
        obs_hash = self._obs_hash(observation)
        if obs_hash in self._cache:
            action = self._cache[obs_hash]
        else:
            prompt = self._format_observation(observation)
            try:
                response = self.llm_client.chat(
                    system="你是一个战斗AI，只返回动作指令，不要有任何解释。",
                    user=prompt,
                    model=self.model,
                    persona=self.persona,  # 让 Mock LLM 知道是哪种性格
                )
                action = self._parse_action(response)
                self._cache[obs_hash] = action
            except Exception as e:
                print(f"PromptAgent {self.name} LLM调用失败: {e}")
                action = "idle"

        # 记录决策日志（供 AI 教练分析）
        self.decision_log.append({
            "turn": getattr(observation, "_turn", None),
            "hash": obs_hash,
            "health": observation.my_health,
            "enemies_visible": len(observation.enemies_in_view),
            "bullets_visible": len(observation.bullets_in_view),
            "action": action,
        })

        return action

    def _parse_action(self, raw: str) -> str:
        """解析 LLM 输出到有效动作"""
        valid_actions = [
            "move_up", "move_down", "move_left", "move_right",
            "turn_left", "turn_right", "shoot", "idle"
        ]
        action = raw.strip().lower()

        # 精确匹配
        if action in valid_actions:
            return action

        # 子串匹配
        for v in valid_actions:
            if v in action:
                return v

        return "idle"

    def set_prompt_template(self, template: str):
        """设置自定义 Prompt 模板（高级用法，需要含所有占位符）"""
        self.prompt_template = template
        self._cache.clear()  # 模板变了，缓存失效

    def set_strategy(self, strategy: str):
        """设置策略说明（追加到默认模板的"策略建议"部分，普通用法）

        用法示例：
            agent.set_strategy("你是个激进派，看到敌人就射击，血量 < 20 才考虑逃跑。")
        """
        self.strategy_text = strategy
        self._cache.clear()

    def _effective_prompt_template(self) -> str:
        """合并默认模板 + 策略说明"""
        if not self.strategy_text:
            return self.prompt_template
        return self.prompt_template.replace(
            "策略建议：\n1. 如果生命值低（<30），优先躲避和移动，远离敌人和子弹\n",
            f"策略建议：\n{self.strategy_text}\n",
        )
