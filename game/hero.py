"""
Hero 类：5 个定位的 AI 英雄
"""
from typing import Optional, Tuple
from game.agent import Agent, Observation


# 5 个英雄定位的默认配置
HERO_CONFIGS = {
    "tank": {
        "display_name": "🛡️ 坦克",
        "max_health": 200,
        "attack": 10,
        "move_speed": 1.2,
        "attack_range": 2.0,
        "skill_name": "嘲讽",
        "skill_desc": "强制 8 格内 2 个敌人攻击自己 3 秒",
        "skill_cooldown": 12,
        "skill_range": 8.0,
        "skill_duration": 3,
        "preferred_lane": "mid",  # 坦克喜欢中路顶前
    },
    "assassin": {
        "display_name": "🗡️ 刺客",
        "max_health": 100,
        "attack": 30,
        "move_speed": 2.0,
        "attack_range": 1.5,
        "skill_name": "突进",
        "skill_desc": "瞬移到 8 格内 1 个敌人身后 + 下一击 +50%",
        "skill_cooldown": 8,
        "skill_range": 8.0,
        "skill_duration": 1,
        "preferred_lane": "top",
    },
    "marksman": {
        "display_name": "🏹 射手",
        "max_health": 80,
        "attack": 20,
        "move_speed": 1.5,
        "attack_range": 5.0,
        "skill_name": "穿透箭",
        "skill_desc": "直线上 3 格内所有敌人 50% 伤害",
        "skill_cooldown": 6,
        "skill_range": 8.0,
        "skill_duration": 0,
        "preferred_lane": "bot",
    },
    "support": {
        "display_name": "💚 辅助",
        "max_health": 90,
        "attack": 8,
        "move_speed": 1.5,
        "attack_range": 2.0,
        "skill_name": "治疗",
        "skill_desc": "半径 6 格内所有友军 +30 HP",
        "skill_cooldown": 10,
        "skill_range": 6.0,
        "skill_duration": 0,
        "preferred_lane": "mid",
    },
    "mage": {
        "display_name": "🔥 法师",
        "max_health": 90,
        "attack": 25,
        "move_speed": 1.4,
        "attack_range": 4.0,
        "skill_name": "火球",
        "skill_desc": "5x5 AOE 40 伤害 + 减速 2s",
        "skill_cooldown": 9,
        "skill_range": 6.0,
        "skill_duration": 0,
        "preferred_lane": "mid",
    },
}


class Hero(Agent):
    """英雄：5 定位的 AI

    比普通 Agent 多：
    - role（角色定位）
    - skill_cooldown（技能冷却）
    - kill_streak（连杀数）
    - respawn_at（复活时间）
    - 全局统计（kill/death/assist/tower_damage）
    """

    def __init__(self, name: str, role: str, side: str, lane: str = "mid"):
        """Args:
        name: 英雄名
        role: tank/assassin/marksman/support/mage
        side: 'blue' 或 'red'
        lane: 'top'/'mid'/'bot'
        """
        super().__init__(name)
        cfg = HERO_CONFIGS[role]
        self.role = role
        # 武器类型（按 role 分配，每种武器有不同动画/效果）
        from game.weapons import ROLE_WEAPON
        self.weapon_type = ROLE_WEAPON.get(role, 'cannon')
        self.side = side
        self.lane = lane
        self.max_health = cfg["max_health"]
        self.attack = cfg["attack"]
        self.move_speed = cfg["move_speed"]
        self.attack_range = cfg["attack_range"]
        self.skill_name = cfg["skill_name"]
        self.skill_desc = cfg["skill_desc"]
        self.skill_max_cooldown = cfg["skill_cooldown"]
        self.skill_cooldown = 0  # 一开始技能可用
        self.skill_range = cfg["skill_range"]
        self.skill_duration = cfg["skill_duration"]
        # 弹药/护盾/buff 状态（新机制）
        self.ammo = 30  # 弹药
        self.max_ammo = 30
        self.shield = 0  # 护盾值
        self.shield_until = -1  # 护盾结束时间
        self.damage_buff_until = -1  # 攻击 buff 结束时间

        # 战斗状态
        self.health = self.max_health
        self.kill_streak = 0
        self.last_kill_time = -100  # 上一击杀时间（回合数）
        self.streak_start_time = -100  # 当前连杀起点
        self.deaths = 0
        self.respawn_at = -1  # -1 = 活着
        self.respawn_delay = 10  # 复活时间（秒/回合）

        # 全局统计
        self.stats = {
            "kills": 0,
            "deaths": 0,
            "assists": 0,
            "tower_damage": 0,
            "damage_taken": 0,
            "damage_dealt": 0,
            "healing_done": 0,
            "skills_used": 0,
        }

        # Buff/debuff
        self.taunt_until = -1     # 嘲讽到时间
        self.slow_until = -1       # 减速到时间

        # next_attack_bonus：突进等技能用的"下一击加成"
        self.next_attack_bonus = 0

    def is_alive(self) -> bool:
        return self.respawn_at < 0

    def is_taunted(self, current_time: int) -> bool:
        return self.taunt_until > current_time

    def is_slowed(self, current_time: int) -> bool:
        return self.slow_until > current_time

    def start_respawn(self, current_time: int):
        """开始复活倒计时"""
        self.deaths += 1
        # 第 1 死：respawn_delay；第 2 死：+1s；第 3 死：+2s；最多 +10s
        extra = max(0, min(self.deaths - 1, 10))
        self.respawn_at = current_time + self.respawn_delay + extra

    def try_respawn(self, current_time: int) -> bool:
        """检查是否该复活。返回是否复生。"""
        if self.respawn_at > 0 and current_time >= self.respawn_at:
            self.respawn_at = -1
            self.health = self.max_health
            # 重置连杀
            self.kill_streak = 0
            # 回到基地位置（蓝左中 / 红右中）
            if self.side == 'blue':
                self.position = (2, 12)
            else:
                self.position = (37, 12)
            return True
        return False

    def register_kill(self, current_time: int):
        """记录一次击杀，触发连杀

        连杀窗口：10s 内从 streak 起点开始的连续击杀
        """
        self.stats["kills"] += 1
        KILL_STREAK_WINDOW = 10
        streak_window_end = self.streak_start_time + KILL_STREAK_WINDOW
        if (self.kill_streak == 0
                or current_time > streak_window_end
                or current_time - self.last_kill_time > KILL_STREAK_WINDOW):
            # 重新开始连杀
            self.kill_streak = 1
            self.streak_start_time = current_time
        else:
            self.kill_streak += 1
        self.last_kill_time = current_time

    def reset_streak_if_stale(self, current_time: int):
        """10s 内没新击杀，连杀中断"""
        if self.kill_streak > 0 and current_time - self.last_kill_time > 10:
            self.kill_streak = 0

    @property
    def kill_streak_label(self) -> str:
        """返回连杀等级标签"""
        labels = {0: "", 2: "DOUBLE KILL", 3: "TRIPLE KILL", 4: "QUADRA KILL", 5: "PENTA KILL"}
        if self.kill_streak >= 6:
            return "LEGENDARY"
        return labels.get(self.kill_streak, "")

    def effective_move_speed(self, current_time: int) -> float:
        """考虑 debuff 后的实际速度"""
        if self.is_slowed(current_time):
            return self.move_speed * 0.5
        return self.move_speed

    def reset(self):
        """重置（用于新一局）"""
        super().reset()
        self.health = self.max_health
        self.skill_cooldown = 0
        self.kill_streak = 0
        self.last_kill_time = -100
        self.respawn_at = -1
        self.deaths = 0
        self.stats = {k: 0 for k in self.stats}
        self.taunt_until = -1
        self.slow_until = -1
        self.next_attack_bonus = 0

    def step(self, observation) -> str:
        """默认 step：什么都没干好的 AI（如挂机用）。子类（team_agents）覆盖。"""
        return 'idle'

    def find_priority_target(self, observation):
        """找优先级目标

        距离 < 5 推敌人，>= 5 推塔。死亡次数高时强制推塔。
        """
        obs = observation
        # 死亡 ≥ 2 次：强制推塔（老将经验）
        if self.deaths >= 2:
            towers = [t for t in obs.get('enemy_towers', []) if not t['destroyed']]
            if towers:
                towers.sort(key=lambda t: (t['position'][0] - self.position[0]) ** 2 +
                                           (t['position'][1] - self.position[1]) ** 2)
                return towers[0]['position']

        # 1. 攻击范围内敌人 → 攻击
        for e in obs.get('enemies', []):
            if e['distance'] <= self.attack_range:
                return e['position']
        # 2. 距离 ≥ 5：优先推塔
        closest_enemy_dist = min((e['distance'] for e in obs.get('enemies', [])), default=999)
        if closest_enemy_dist >= 5:
            towers = [t for t in obs.get('enemy_towers', []) if not t['destroyed']]
            if towers:
                towers.sort(key=lambda t: (t['position'][0] - self.position[0]) ** 2 +
                                           (t['position'][1] - self.position[1]) ** 2)
                return towers[0]['position']
        # 3. 距离 < 5：推最近敌人
        if obs.get('enemies'):
            return min(obs['enemies'], key=lambda x: x['distance'])['position']
        # 4. 没敌人 → 推塔
        towers = [t for t in obs.get('enemy_towers', []) if not t['destroyed']]
        if towers:
            towers.sort(key=lambda t: (t['position'][0] - self.position[0]) ** 2 +
                                       (t['position'][1] - self.position[1]) ** 2)
            return towers[0]['position']
        return None

    def move_action_toward(self, target_pos):
        """返回朝目标移动的 action 字符串"""
        dx = target_pos[0] - self.position[0]
        dy = target_pos[1] - self.position[1]
        if abs(dx) > abs(dy):
            return 'move_right' if dx > 0 else 'move_left'
        return 'move_down' if dy > 0 else 'move_up'