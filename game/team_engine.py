"""
TeamEngine：3v3 团队战引擎

每回合（1 秒）：
1. 复活检查
2. 技能 cooldown 减少
3. 每个存活英雄调 step() 决策
4. 应用决策（移动 / 攻击 / 技能）
5. 攻击/技能碰撞检测
6. 防御塔攻击
7. 死亡 / 复活 / 连杀处理
"""
import math
import random
from typing import Optional, Dict, List, Tuple

from game.hero import Hero, HERO_CONFIGS
from game.team_state import TeamGameState, Tower, Base


# 移动方向定义（4 方向 + idle）
ACTIONS = {
    'move_up': (0, -1),
    'move_down': (0, 1),
    'move_left': (-1, 0),
    'move_right': (1, 0),
    'turn_up': (0, -1),
    'turn_down': (0, 1),
    'turn_left': (-1, 0),
    'turn_right': (1, 0),
    'attack': 'ATTACK',
    'skill': 'SKILL',
    'idle': (0, 0),
}


class TeamEngine:
    """3v3 团队战引擎"""

    def __init__(self, state: TeamGameState):
        self.state = state
        self.running = True
        # 嘲讽：被嘲讽的英雄只能攻击嘲讽者
        self._taunt_source: Dict[int, str] = {}  # hero_id -> taunter_name

    def step(self) -> bool:
        """跑 1 回合。返回是否还在运行"""
        s = self.state

        # 1. 复活检查
        for h in s.heroes:
            if h.try_respawn(s.turn):
                s.log_event('respawn', name=h.name, role=h.role, side=h.side)

        # 2. 技能 cooldown 减少
        for h in s.heroes:
            if h.skill_cooldown > 0:
                h.skill_cooldown -= 1
            # 移除过期 debuff
            if h.taunt_until > 0 and h.taunt_until <= s.turn:
                h.taunt_until = -1
            if h.slow_until > 0 and h.slow_until <= s.turn:
                h.slow_until = -1

        # 3. 每个英雄决策 + 应用
        for h in s.alive_heroes:
            obs = self._build_observation(h)
            action = h.step(obs)
            self._apply_action(h, action, obs)

        # 4. 防御塔攻击
        self._tower_attack()

        # 5. 检查胜负
        s.turn += 1
        s.score['blue'] = sum(h.stats['kills'] for h in s.blue_heroes)
        s.score['red'] = sum(h.stats['kills'] for h in s.red_heroes)
        winner = s.get_winner()
        if winner:
            s.log_event('game_over', winner=winner, reason='base_destroyed')
            return False
        if s.turn >= s.MAX_TURNS:
            s.log_event('game_over', winner=winner or 'draw', reason='timeout')
            return False
        return True

    def _build_observation(self, hero: Hero) -> Dict:
        """构造英雄的观察"""
        s = self.state
        allies = [h for h in s.heroes if h.side == hero.side and h != hero and h.is_alive()]
        enemies = [h for h in s.heroes if h.side != hero.side and h.is_alive()]
        ally_towers = s.blue_towers if hero.side == 'blue' else s.red_towers
        enemy_towers = s.red_towers if hero.side == 'blue' else s.blue_towers
        enemy_base = s.red_base if hero.side == 'blue' else s.blue_base
        ally_base = s.blue_base if hero.side == 'blue' else s.red_base

        return {
            'hero': hero,
            'turn': s.turn,
            'self_health': hero.health,
            'self_max_health': hero.max_health,
            'self_skill_cd': hero.skill_cooldown,
            'self_kill_streak': hero.kill_streak,
            'allies': [{'name': a.name, 'role': a.role, 'position': list(a.position),
                        'health': a.health} for a in allies],
            'enemies': [{'name': e.name, 'role': e.role, 'position': list(e.position),
                          'health': e.health,
                          'distance': self._dist(hero.position, e.position)} for e in enemies],
            'ally_towers': [{'hp': t.hp, 'max_hp': t.max_hp, 'lane': t.lane,
                              'position': list(t.position), 'destroyed': t.destroyed}
                             for t in ally_towers],
            'enemy_towers': [{'hp': t.hp, 'max_hp': t.max_hp, 'lane': t.lane,
                              'position': list(t.position), 'destroyed': t.destroyed}
                             for t in enemy_towers],
            'enemy_base_hp': enemy_base.hp,
            'enemy_base_max_hp': enemy_base.max_hp,
            'ally_base_hp': ally_base.hp,
            'taunted_by': self._taunt_source.get(id(hero)),
        }

    def _dist(self, p1, p2) -> float:
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    def _nearest_enemy(self, hero: Hero, max_dist: float = 100):
        s = self.state
        best = None
        best_d = max_dist
        for e in s.heroes:
            if e.side == hero.side or not e.is_alive():
                continue
            d = self._dist(hero.position, e.position)
            if d < best_d:
                best_d = d
                best = e
        return best

    def _apply_action(self, hero: Hero, action: str, obs: Dict):
        """应用英雄的决策"""
        s = self.state

        # 嘲讽：只能攻击嘲讽者
        if hero.taunt_until > s.turn and self._taunt_source.get(id(hero)):
            taunter_name = self._taunt_source[id(hero)]
            taunter = next((h for h in s.heroes if h.name == taunter_name and h.is_alive()), None)
            if taunter:
                # 强制转向嘲讽者
                dx = taunter.position[0] - hero.position[0]
                dy = taunter.position[1] - hero.position[1]
                if abs(dx) > abs(dy):
                    hero.direction = (1 if dx > 0 else -1, 0)
                else:
                    hero.direction = (0, 1 if dy > 0 else -1)
                # 如果在攻击范围就攻击
                if self._dist(hero.position, taunter.position) <= hero.attack_range:
                    self._do_attack(hero, taunter)
                else:
                    self._move_toward(hero, taunter.position)
                return

        action = (action or 'idle').lower().strip()
        if action == 'attack':
            self._do_hero_attack(hero, obs)
        elif action == 'skill':
            self._do_skill(hero, obs)
        elif action in ACTIONS:
            v = ACTIONS[action]
            if isinstance(v, tuple):
                # 移动
                self._move_hero(hero, v[0], v[1])
            elif v == 'ATTACK':
                self._do_hero_attack(hero, obs)
            elif v == 'SKILL':
                self._do_skill(hero, obs)

    def _move_hero(self, hero: Hero, dx: float, dy: float):
        """按方向移动"""
        speed = hero.effective_move_speed(self.state.turn)
        nx = hero.position[0] + dx * speed
        ny = hero.position[1] + dy * speed
        nx = max(1, min(self.state.MAP_W - 1, nx))
        ny = max(1, min(self.state.MAP_H - 1, ny))
        # 不能进塔/基地
        if not self._is_blocked(hero, (nx, ny)):
            hero.position = (nx, ny)
        # 方向更新
        hero.direction = (dx, dy)

    def _move_toward(self, hero: Hero, target_pos):
        dx = target_pos[0] - hero.position[0]
        dy = target_pos[1] - hero.position[1]
        d = math.sqrt(dx*dx + dy*dy)
        if d > 0:
            self._move_hero(hero, dx/d, dy/d)

    def _is_blocked(self, hero, pos) -> bool:
        """是否被塔/基地阻挡"""
        s = self.state
        # 不可穿越对方基地中心
        if hero.side == 'blue' and self._dist(pos, s.red_base.position) < 3 and s.red_base.hp > 0:
            return True
        if hero.side == 'red' and self._dist(pos, s.blue_base.position) < 3 and s.blue_base.hp > 0:
            return True
        return False

    def _do_hero_attack(self, hero: Hero, obs: Dict):
        """英雄普通攻击"""
        # 找最近敌人（在攻击范围内）
        target = self._find_attack_target(hero, obs)
        if target:
            self._do_attack(hero, target)
        else:
            # 朝最近敌人移动
            e = self._nearest_enemy(hero)
            if e:
                self._move_toward(hero, e.position)

    def _find_attack_target(self, hero: Hero, obs: Dict):
        """找攻击目标：死亡 ≥1 时优先塔，否则优先敌人"""
        s = self.state
        # 死亡 ≥1 时优先塔（老兵推塔模式）
        if hero.deaths >= 1:
            enemy_towers = s.red_towers if hero.side == 'blue' else s.blue_towers
            for t in enemy_towers:
                if t.destroyed:
                    continue
                if self._dist(hero.position, t.position) <= hero.attack_range:
                    return ('tower', t)
            enemy_base = s.red_base if hero.side == 'blue' else s.blue_base
            if self._dist(hero.position, enemy_base.position) <= hero.attack_range:
                return ('base', enemy_base)
            # 没塔没基地 → 打敌人
        # 默认：优先敌人
        for e in s.heroes:
            if e.side == hero.side or not e.is_alive():
                continue
            if self._dist(hero.position, e.position) <= hero.attack_range:
                return e
        # 然后塔
        enemy_towers = s.red_towers if hero.side == 'blue' else s.blue_towers
        for t in enemy_towers:
            if t.destroyed:
                continue
            if self._dist(hero.position, t.position) <= hero.attack_range:
                return ('tower', t)
        # 基地
        enemy_base = s.red_base if hero.side == 'blue' else s.blue_base
        if self._dist(hero.position, enemy_base.position) <= hero.attack_range:
            return ('base', enemy_base)
        return None

    def _do_attack(self, hero: Hero, target):
        """对目标造成伤害"""
        s = self.state
        dmg = hero.attack
        if hero.next_attack_bonus > 0:
            dmg = int(dmg * (1 + hero.next_attack_bonus))
            hero.next_attack_bonus = 0
        if isinstance(target, Hero):
            target.health = max(0, target.health - dmg)
            target.stats['damage_taken'] += dmg
            hero.stats['damage_dealt'] += dmg
            if target.health <= 0:
                self._handle_kill(hero, target)
        elif isinstance(target, tuple):
            kind, obj = target
            if kind == 'tower':
                obj.take_damage(dmg)
                hero.stats['tower_damage'] += dmg
                s.log_event('tower_damage', attacker=hero.name, tower_lane=obj.lane,
                            side=obj.side, hp_left=obj.hp, destroyed=obj.destroyed)
                if obj.destroyed:
                    s.log_event('tower_destroyed', attacker=hero.name, lane=obj.lane, side=obj.side)
            elif kind == 'base':
                obj.take_damage(dmg)
                hero.stats['tower_damage'] += dmg
                s.log_event('base_damage', attacker=hero.name, hp_left=obj.hp)

    def _do_skill(self, hero: Hero, obs: Dict):
        """释放技能（按 role 分发）"""
        if hero.skill_cooldown > 0:
            return
        role = hero.role
        if role == 'tank':
            self._skill_taunt(hero, obs)
        elif role == 'assassin':
            self._skill_dash(hero, obs)
        elif role == 'marksman':
            self._skill_piercing(hero, obs)
        elif role == 'support':
            self._skill_heal(hero, obs)
        elif role == 'mage':
            self._skill_fireball(hero, obs)
        hero.skill_cooldown = hero.skill_max_cooldown
        hero.stats['skills_used'] += 1

    def _skill_taunt(self, hero: Hero, obs: Dict):
        """嘲讽：强制 2 个最近敌人攻击自己 3 秒"""
        s = self.state
        enemies = sorted(
            [h for h in s.heroes if h.side != hero.side and h.is_alive() and
             self._dist(hero.position, h.position) <= hero.skill_range],
            key=lambda h: self._dist(hero.position, h.position)
        )[:2]
        for e in enemies:
            e.taunt_until = s.turn + hero.skill_duration
            self._taunt_source[id(e)] = hero.name
        s.log_event('skill_taunt', hero=hero.name, targets=[e.name for e in enemies])

    def _skill_dash(self, hero: Hero, obs: Dict):
        """突进：瞬移到 8 格内敌人身后 + 下一击 +50%"""
        s = self.state
        enemies = [h for h in s.heroes if h.side != hero.side and h.is_alive() and
                   self._dist(hero.position, h.position) <= hero.skill_range]
        if not enemies:
            return
        target = min(enemies, key=lambda h: self._dist(hero.position, h.position))
        # 计算身后位置
        dx = target.position[0] - hero.position[0]
        dy = target.position[1] - hero.position[1]
        d = math.sqrt(dx*dx + dy*dy)
        if d > 0:
            # 身后 1.5 格
            new_x = target.position[0] + dx/d * 1.5
            new_y = target.position[1] + dy/d * 1.5
            hero.position = (new_x, new_y)
        hero.next_attack_bonus = 0.5
        s.log_event('skill_dash', hero=hero.name, target=target.name)

    def _skill_piercing(self, hero: Hero, obs: Dict):
        """穿透箭：直线上 3 格内所有敌人 50% 伤害"""
        s = self.state
        dx, dy = hero.direction
        if dx == 0 and dy == 0:
            dx, dy = 1, 0
        mag = math.sqrt(dx*dx + dy*dy)
        dx, dy = dx/mag, dy/mag
        dmg = int(hero.attack * 0.5)
        hit = 0
        for e in s.heroes:
            if e.side == hero.side or not e.is_alive():
                continue
            # 点到直线距离
            ex, ey = e.position
            # 向量投影
            proj = (ex - hero.position[0]) * dx + (ey - hero.position[1]) * dy
            if 0 < proj <= 3:
                perp = abs((ex - hero.position[0]) * dy - (ey - hero.position[1]) * dx)
                if perp < 1.0:
                    e.health = max(0, e.health - dmg)
                    e.stats['damage_taken'] += dmg
                    hero.stats['damage_dealt'] += dmg
                    hit += 1
                    if e.health <= 0:
                        self._handle_kill(hero, e)
        s.log_event('skill_piercing', hero=hero.name, hit=hit, dmg=dmg)

    def _skill_heal(self, hero: Hero, obs: Dict):
        """治疗：半径 6 格内友军 +30 HP"""
        s = self.state
        heal = 30
        count = 0
        for a in s.heroes:
            if a.side != hero.side or not a.is_alive():
                continue
            if self._dist(hero.position, a.position) <= hero.skill_range:
                a.health = min(a.max_health, a.health + heal)
                a.stats['healing_done'] = a.stats.get('healing_done', 0) + heal
                hero.stats['healing_done'] += heal
                count += 1
        s.log_event('skill_heal', hero=hero.name, count=count, amount=heal)

    def _skill_fireball(self, hero: Hero, obs: Dict):
        """火球：5x5 AOE 40 伤害 + 减速 2s"""
        s = self.state
        cx, cy = hero.position
        dmg = 40
        hit = 0
        for e in s.heroes:
            if e.side == hero.side or not e.is_alive():
                continue
            if abs(e.position[0] - cx) < 2.5 and abs(e.position[1] - cy) < 2.5:
                e.health = max(0, e.health - dmg)
                e.stats['damage_taken'] += dmg
                hero.stats['damage_dealt'] += dmg
                e.slow_until = s.turn + 2
                hit += 1
                if e.health <= 0:
                    self._handle_kill(hero, e)
        s.log_event('skill_fireball', hero=hero.name, hit=hit, dmg=dmg)

    def _handle_kill(self, killer: Hero, victim: Hero):
        """处理击杀"""
        s = self.state
        # 记录
        s.kill_log.append({
            'turn': s.turn,
            'killer': killer.name,
            'killer_role': killer.role,
            'victim': victim.name,
            'victim_role': victim.role,
        })
        # 触发连杀
        killer.register_kill(s.turn)
        # 给附近助攻（同一回合造成伤害的队友）
        s.log_event('kill', killer=killer.name, killer_role=killer.role,
                    victim=victim.name, victim_role=victim.role,
                    streak=killer.kill_streak,
                    streak_label=killer.kill_streak_label)
        # 死亡
        victim.start_respawn(s.turn)
        s.score[killer.side] += 1
        # 检查 PENTA/LEGENDARY 触发
        if killer.kill_streak >= 2:
            s.log_event('streak', hero=killer.name, streak=killer.kill_streak,
                        label=killer.kill_streak_label)

    def _tower_attack(self):
        """每座活着的塔攻击范围内最近的敌人英雄"""
        s = self.state
        for t in s.blue_towers + s.red_towers:
            if t.destroyed:
                continue
            # 找最近敌人
            target = None
            target_d = t.attack_range
            for h in s.heroes:
                if h.side == t.side or not h.is_alive():
                    continue
                d = self._dist(t.position, h.position)
                if d < target_d:
                    target_d = d
                    target = h
            if target:
                target.health = max(0, target.health - t.attack)
                target.stats['damage_taken'] += t.attack
                s.log_event('tower_attacks_hero', tower_side=t.side, tower_lane=t.lane,
                            target=target.name, damage=t.attack)
                if target.health <= 0:
                    # 塔击杀不算"英雄击杀"，不记入个人 kill_streak
                    target.start_respawn(s.turn)
                    s.kill_log.append({
                        'turn': s.turn, 'killer': f'塔-{t.lane}', 'killer_role': 'tower',
                        'victim': target.name, 'victim_role': target.role,
                    })
                    s.log_event('kill', killer=f'蓝塔{t.lane}' if t.side == 'blue' else f'红塔{t.lane}',
                                killer_role='tower', victim=target.name,
                                victim_role=target.role, streak=0, streak_label='')