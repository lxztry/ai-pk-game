"""
实时解说模块：把数据流变成故事

基于事件触发的规则引擎，每帧检测重要事件并生成解说词。
不依赖 LLM 即可用（可后续替换为 LLM 模式）。
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class CommentaryLine:
    """一条解说"""
    turn: int
    text: str
    importance: int = 1  # 1=日常, 2=重要, 3=高潮


# 事件模板（中文，简洁、有趣）
TEMPLATES = {
    "first_blood": [
        "🎯 首次命中！{target} 被 {attacker} 击退！",
        "💥 开局首杀！{attacker} 给 {target} 来了一发！",
    ],
    "kill": [
        "☠️  {attacker} K.O. {target}！全场沸腾！",
        "🔥 完美击杀！{target} 倒下了，{attacker} 还有 {hp}% 血！",
        "⚡ 终结技！{attacker} 拿下 {target}！",
    ],
    "low_health": [
        "😰 {name} 残血了！只剩 {hp}% 血！",
        "🩸 {name} 血线告急 ({hp}%)，需要补给！",
        "💔 {name} 命悬一线！",
    ],
    "dodge": [
        "💨 {name} 完美闪避！子弹擦肩而过！",
        "🌪️  {name} 来了一波走位，漂亮！",
        "👻 {name} 灵活如鬼，敌人瞄不准！",
    ],
    "wall_block": [
        "🧱 子弹撞墙了！{attacker} 的射击被弹开",
        "🏰 墙救了 {target} 一命！",
    ],
    "comeback": [
        "🔥 逆转！{name} 残血反杀！",
        "⚡ {name} 不到最后一刻不放弃！",
    ],
    "supplier_pickup": [
        "📦 {name} 拾取补给！",
    ],
    "approach": [
        "👀 {a} 慢慢靠近 {b}，距离 {dist}",
        "😬 紧张！{a} 和 {b} 距离只剩 {dist}",
    ],
    "fight_starts": [
        "🎬 比赛开始！{a} VS {b}",
        "⚔️  {a} 对决 {b}，谁是最终胜者？",
    ],
    "final_kill": [
        "🏆 比赛结束！{winner} 击败 {loser}！",
        "👑 加冕！{winner} 是最终胜者！",
    ],
}


class CommentaryEngine:
    """解说引擎"""

    def __init__(self):
        self.lines: List[CommentaryLine] = []
        self.last_health: Dict[str, int] = {}
        self.last_dodge_turn: Dict[str, int] = {}
        self.kill_count: int = 0

    def process_frame(self, turn: int, agents: list, bullets: list,
                      obstacles: list, prev_agents: list = None) -> List[CommentaryLine]:
        """处理一帧，返回新增的解说"""
        new_lines = []

        # 0. 比赛开始（turn 0）
        if turn == 0 and len(agents) >= 2:
            self._add(new_lines, turn, "fight_starts", a=agents[0]["name"], b=agents[1]["name"], importance=3)

        # 1. 首次命中（turn 1 之后第一个血量下降）
        for a in agents:
            name = a["name"]
            cur_hp = a["health"]
            if name in self.last_health and self.last_health[name] > cur_hp:
                lost = self.last_health[name] - cur_hp
                if self.kill_count == 0 and lost >= 5:
                    # 找攻击者（找不是自己的、最近距离的敌人）
                    attacker = self._find_attacker(a, agents, bullets)
                    target = name
                    self._add(new_lines, turn, "first_blood", attacker=attacker, target=target, importance=3)
                    self.kill_count += 1

        # 2. 击杀（health 变 0）
        for a in agents:
            name = a["name"]
            cur_hp = a["health"]
            if name in self.last_health and self.last_health[name] > 0 and cur_hp <= 0:
                attacker = self._find_attacker(a, agents, bullets)
                self._add(new_lines, turn, "kill",
                         attacker=attacker, target=name,
                         hp=int(attacker.split()[-1]) if False else 100,
                         importance=3)
                # 比赛结束
                winner = next((x for x in agents if x["name"] != name and x["health"] > 0), None)
                if winner:
                    self._add(new_lines, turn, "final_kill",
                             winner=winner["name"], loser=name, importance=3)

        # 3. 残血警告（< 30 血）
        for a in agents:
            name = a["name"]
            cur_hp = a["health"]
            if 0 < cur_hp < 30 and self.last_health.get(name, 100) >= 30:
                self._add(new_lines, turn, "low_health", name=name, hp=int(cur_hp), importance=2)

        # 4. 闪避（agent 突然垂直移动 = dodge）
        for i, a in enumerate(agents):
            name = a["name"]
            if prev_agents and i < len(prev_agents):
                prev = prev_agents[i]
                dx = a["position"][0] - prev["position"][0]
                dy = a["position"][1] - prev["position"][1]
                # 移动距离 > 3 且方向垂直于朝向 = 闪避
                import math
                dir_angle = math.atan2(a["direction"][1], a["direction"][0])
                # 如果移动方向与朝向垂直：dot ≈ 0
                if abs(dx) + abs(dy) > 3 and self.last_dodge_turn.get(name, -10) < turn - 3:
                    move_angle = math.atan2(dy, dx)
                    diff = abs(move_angle - dir_angle)
                    if diff > 1.0:  # 接近垂直（60度以上）
                        self._add(new_lines, turn, "dodge", name=name, importance=2)
                        self.last_dodge_turn[name] = turn

        # 5. 撞墙
        # （需要 bullet hit_wall 事件，简化跳过）

        # 6. 反杀（之前血量低于对手，现在反超）
        if prev_agents and len(agents) >= 2 and len(prev_agents) >= 2:
            cur_total_a = agents[0]["health"] + agents[0]["kills"] * 50
            cur_total_b = agents[1]["health"] + agents[1]["kills"] * 50
            prev_total_a = prev_agents[0]["health"] + prev_agents[0]["kills"] * 50
            prev_total_b = prev_agents[1]["health"] + prev_agents[1]["kills"] * 50
            if prev_total_a < prev_total_b and cur_total_a > cur_total_b:
                self._add(new_lines, turn, "comeback", name=agents[0]["name"], importance=3)
            elif prev_total_b < prev_total_a and cur_total_b > cur_total_a:
                self._add(new_lines, turn, "comeback", name=agents[1]["name"], importance=3)

        # 更新 last_health
        for a in agents:
            self.last_health[a["name"]] = a["health"]

        self.lines.extend(new_lines)
        return new_lines

    def _add(self, lines, turn, event, importance=1, **kwargs):
        """添加一条解说"""
        import random
        templates = TEMPLATES.get(event, [])
        if not templates:
            return
        text = random.choice(templates).format(**kwargs)
        lines.append(CommentaryLine(turn=turn, text=text, importance=importance))

    def _find_attacker(self, victim, agents, bullets):
        """找攻击者（简化为非 victim 的另一个）"""
        for a in agents:
            if a["name"] != victim["name"]:
                return a["name"]
        return "未知"

    def get_recent(self, n: int = 5) -> List[CommentaryLine]:
        """获取最近的 N 条"""
        return self.lines[-n:]


def format_commentary(lines: List[CommentaryLine]) -> str:
    """格式化解说为可显示文本"""
    if not lines:
        return ""
    return "\n".join(
        f"[回合 {l.turn:>3}] {l.text}"
        for l in lines
    )