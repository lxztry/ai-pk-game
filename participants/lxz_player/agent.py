"""
更智能的参赛者：lxz_player
策略要点：
- 躲避近距离子弹
- 智能争抢补给（低血量优先回血；缺弹优先补弹；捡更强武器）
- 利用障碍（避免撞墙，贴边滑移）
- 面对敌人时合理距离与射击节奏
"""
import math
import random
from game.agent import Agent as BaseAgent, Observation


class Agent(BaseAgent):
    """lxz_player - 面向补给与地形优化的智能策略"""

    def __init__(self, name: str = None, **kwargs):
        super().__init__(name=name or "lxz_player")
        # 随机初始观测探索方向，避免原地抖动
        self._explore_axis = random.choice(["x", "y"])
        self._explore_dir = random.choice([-1, 1])

    # --------------- 小工具 ---------------
    def _angle_between(self, v1, v2):
        a1 = math.atan2(v1[1], v1[0])
        a2 = math.atan2(v2[1], v2[0])
        d = a2 - a1
        if d > math.pi:
            d -= 2 * math.pi
        elif d < -math.pi:
            d += 2 * math.pi
        return d

    def _is_aiming_at(self, observation: Observation, target_pos, tol=0.35):
        tx, ty = target_pos
        sx, sy = observation.my_position
        target_vec = (tx - sx, ty - sy)
        cur_dir = observation.my_direction
        return abs(self._angle_between(cur_dir, target_vec)) < tol

    def _turn_towards(self, observation: Observation, target_pos):
        tx, ty = target_pos
        sx, sy = observation.my_position
        target_vec = (tx - sx, ty - sy)
        cur_dir = observation.my_direction
        d = self._angle_between(cur_dir, target_vec)
        return "turn_right" if d > 0 else "turn_left"

    def _project_move(self, observation: Observation, move: str, step=2.0):
        x, y = observation.my_position
        if move == "move_up":
            return (x, y - step)
        if move == "move_down":
            return (x, y + step)
        if move == "move_left":
            return (x - step, y)
        if move == "move_right":
            return (x + step, y)
        return (x, y)

    def _pos_inside_any_rect(self, pos, rects):
        px, py = pos
        for r in rects:
            x, y, w, h = r
            if x <= px <= x + w and y <= py <= y + h:
                return True
        return False

    def _safe_move_choices(self, observation: Observation):
        rects = [o["rect"] for o in observation.obstacles_in_view] if hasattr(observation, "obstacles_in_view") else []
        candidates = ["move_up", "move_down", "move_left", "move_right"]
        safe = []
        for mv in candidates:
            np = self._project_move(observation, mv, step=2.0)
            if not self._pos_inside_any_rect(np, rects):
                safe.append(mv)
        return safe or candidates

    def _move_towards(self, observation: Observation, target_pos):
        sx, sy = observation.my_position
        tx, ty = target_pos
        dx = tx - sx
        dy = ty - sy
        primary = "move_right" if dx > 0 else "move_left"
        secondary = "move_down" if dy > 0 else "move_up"
        choices = [primary, secondary]
        safe = self._safe_move_choices(observation)
        for mv in choices:
            if mv in safe:
                return mv
        return random.choice(safe)

    def _move_away(self, observation: Observation, target_pos):
        sx, sy = observation.my_position
        tx, ty = target_pos
        dx = sx - tx
        dy = sy - ty
        primary = "move_right" if dx > 0 else "move_left"
        secondary = "move_down" if dy > 0 else "move_up"
        choices = [primary, secondary]
        safe = self._safe_move_choices(observation)
        for mv in choices:
            if mv in safe:
                return mv
        return random.choice(safe)

    # --------------- 策略 ---------------
    def step(self, observation: Observation) -> str:
        # 1) 躲避近距离子弹
        for b in observation.bullets_in_view:
            if b["distance"] < 7.5:
                # 简单横向/纵向闪避
                safe = self._safe_move_choices(observation)
                return random.choice(safe)

        # 2) 补给策略
        supplies = observation.supplies_in_view if hasattr(observation, "supplies_in_view") else []
        if supplies:
            # 血量低优先 health
            if observation.my_health < 45:
                healths = [s for s in supplies if s["type"] == "health"]
                if healths:
                    target = min(healths, key=lambda s: s["distance"])
                    return self._move_towards(observation, tuple(target["position"]))
            # 弹药不足优先补弹
            if observation.my_weapon and observation.my_weapon != "normal":
                ammo_key = f"ammo_{observation.my_weapon}"
                has_ammo = observation.my_ammo if observation.my_ammo is not None else 0
                if has_ammo is not None and has_ammo < 2:
                    ammos = [s for s in supplies if s["type"] == ammo_key]
                    if ammos:
                        target = min(ammos, key=lambda s: s["distance"])
                        return self._move_towards(observation, tuple(target["position"]))
            # 捡更强武器（优先级：rocket > sniper > shotgun）
            prefer = ["weapon_rocket", "weapon_sniper", "weapon_shotgun"]
            for t in prefer:
                cand = [s for s in supplies if s["type"] == t]
                if cand:
                    target = min(cand, key=lambda s: s["distance"])
                    return self._move_towards(observation, tuple(target["position"]))

        # 3) 敌人交战策略
        enemies = observation.enemies_in_view
        if enemies:
            # 选择目标：血量低/距离近
            target = min(enemies, key=lambda e: (e["health"], e["distance"]))
            enemy_pos = tuple(target["position"])

            # 尝试开火
            if self._is_aiming_at(observation, enemy_pos, tol=0.4) and observation.shoot_cooldown == 0:
                return "shoot"
            # 未对准则转向
            return self._turn_towards(observation, enemy_pos)

        # 4) 没敌人时：向中心探索，带障碍规避
        cx = observation.map_boundary[0] / 2
        cy = observation.map_boundary[1] / 2
        mv = self._move_towards(observation, (cx, cy))
        if random.random() < 0.1:
            # 偶尔转向，利于更快搜敌
            return random.choice(["turn_left", "turn_right", mv])
        return mv


