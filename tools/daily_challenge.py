"""
每日挑战 — 每天发布一个特殊规则，所有 agent 在同一规则下比赛

规则可手工定义，也可由 LLM 生成。

内置规则模板（不同星期不同挑战）：
- 周一: "弹药无限" — 所有武器冷却减半
- 周二: "狙击对决" — 只能用狙击枪
- 周三: "血量 30" — 所有人 1 击必杀
- 周四: "无视野" — view_distance = 5（盲战）
- 周五: "加速模式" — 所有 agent 移动速度 × 2
- 周六: "镜像赛" — 双方位置对称
- 周日: "社区投票" — 由玩家提交规则
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from pathlib import Path


@dataclass
class DailyChallengeRule:
    """每日挑战规则"""
    code: str           # 唯一标识，如 "mon-ammo-infinite"
    title: str          # 显示标题
    description: str    # 详细说明
    weekday: str        # monday/tuesday/...
    modifiers: Dict[str, Any] = field(default_factory=dict)
    """应用到 engine 的参数覆盖，例如:
       {"max_health": 30, "view_distance": 5, "move_speed": 2.0}
    """
    created_at: str = ""
    expires_at: str = ""

    def apply_to_engine(self, engine):
        """把规则应用到 GameEngine 实例"""
        mods = self.modifiers
        if "max_health" in mods:
            for a in engine.state.agents:
                a.health = mods["max_health"]
        if "view_distance" in mods:
            engine.view_distance = mods["view_distance"]
        if "move_speed" in mods:
            # engine 里 _execute_action 用 move_speed = 2.0（硬编码），暂不支持
            pass
        if "weapon_only" in mods:
            # 限制只能用某种武器
            for a in engine.state.agents:
                a.weapon = mods["weapon_only"]
                if mods["weapon_only"] != "normal":
                    a.ammo[mods["weapon_only"]] = 99  # 给足弹药
        return engine


# ---------- 内置挑战模板 ----------

CHALLENGE_TEMPLATES: Dict[str, DailyChallengeRule] = {
    "monday_ammo": DailyChallengeRule(
        code="mon-ammo-infinite",
        title="周一弹药无限",
        description="所有武器冷却时间减半，弹药补给包数量翻倍",
        weekday="monday",
        modifiers={"cooldown_divisor": 2},
    ),
    "tuesday_sniper": DailyChallengeRule(
        code="tue-sniper-only",
        title="周二狙击对决",
        description="所有 agent 只能用狙击枪（高伤害高冷却）",
        weekday="tuesday",
        modifiers={"weapon_only": "sniper"},
    ),
    "wednesday_oneshot": DailyChallengeRule(
        code="wed-one-shot",
        title="周三一击必杀",
        description="所有人血量降到 30，1 击必死",
        weekday="wednesday",
        modifiers={"max_health": 30},
    ),
    "thursday_blind": DailyChallengeRule(
        code="thu-blind",
        title="周四盲战",
        description="视野距离从 30 降到 5，几乎盲打",
        weekday="thursday",
        modifiers={"view_distance": 5},
    ),
    "friday_speed": DailyChallengeRule(
        code="fri-speed",
        title="周五加速模式",
        description="所有 agent 移动速度翻倍（持续命中难度增加）",
        weekday="friday",
        modifiers={"move_speed": 2.0},
    ),
    "saturday_mirror": DailyChallengeRule(
        code="sat-mirror",
        title="周六镜像赛",
        description="双方位置对称，开局立即交战",
        weekday="saturday",
        modifiers={"mirror": True},
    ),
    "sunday_chaos": DailyChallengeRule(
        code="sun-chaos",
        title="周日混沌赛",
        description="所有规则随机化（武器/血量/视野）",
        weekday="sunday",
        modifiers={"chaos": True},
    ),
}


def get_today_challenge() -> DailyChallengeRule:
    """根据今天是星期几返回对应挑战"""
    weekday = datetime.now().strftime("%A").lower()
    code_map = {
        "monday": "monday_ammo",
        "tuesday": "tuesday_sniper",
        "wednesday": "wednesday_oneshot",
        "thursday": "thursday_blind",
        "friday": "friday_speed",
        "saturday": "saturday_mirror",
        "sunday": "sunday_chaos",
    }
    code = code_map.get(weekday, "monday_ammo")
    return CHALLENGE_TEMPLATES[code]


def list_all_challenges() -> List[DailyChallengeRule]:
    """列出所有内置挑战"""
    return list(CHALLENGE_TEMPLATES.values())


def format_challenge(rule: DailyChallengeRule) -> str:
    """格式化挑战规则显示"""
    lines = [
        "=" * 60,
        f"  每日挑战 — {rule.title}",
        "=" * 60,
        f"  代码: {rule.code}",
        f"  星期: {rule.weekday}",
        f"  说明: {rule.description}",
        "",
        f"  规则覆盖: {json.dumps(rule.modifiers, ensure_ascii=False)}",
        "=" * 60,
    ]
    return "\n".join(lines)
