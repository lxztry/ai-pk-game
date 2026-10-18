"""
5 角色定位的 AI 行为（继承 Hero，自动决策）

每个角色根据"性格"做不同决策：
- 坦克：前排顶，技能嘲讽吸引火力
- 刺客：抓单，突进后排
- 射手：后排输出，技能穿透
- 辅助：跟队友，治疗优先
- 法师：中距离 AOE
"""
import math
import random
from typing import Dict, Optional

from game.hero import Hero


def _dist(p1, p2) -> float:
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


class TankAI(Hero):
    """🛡️ 坦克：前排顶，嘲讽吸引火力"""
    def step(self, observation: Dict) -> str:
        if not self.is_alive():
            return 'idle'
        obs = observation
        # 死亡 ≥ 1：推塔模式（但先看是否能打到塔）
        if self.deaths >= 1:
            # 塔在攻击范围内 → 直接 attack
            for t in obs['enemy_towers']:
                if t['destroyed']:
                    continue
                d = ((t['position'][0] - self.position[0]) ** 2 +
                     (t['position'][1] - self.position[1]) ** 2) ** 0.5
                if d <= self.attack_range:
                    return 'attack'
            # 否则朝最近塔走
            towers = [t for t in obs['enemy_towers'] if not t['destroyed']]
            if towers:
                towers.sort(key=lambda t: (t['position'][0] - self.position[0]) ** 2 +
                                           (t['position'][1] - self.position[1]) ** 2)
                return self.move_action_toward(towers[0]['position'])
        # 嘲讽技能（附近有敌人）
        if self.skill_cooldown == 0 and obs['enemies']:
            near = [e for e in obs['enemies'] if e['distance'] <= self.skill_range]
            if len(near) >= 1:
                return 'skill'
        # 攻击范围 → 攻击
        if obs['enemies']:
            for e in obs['enemies']:
                if e['distance'] <= self.attack_range:
                    return 'attack'
        # 50% 概率推塔
        import random
        if random.random() < 0.5:
            towers = [t for t in obs['enemy_towers'] if not t['destroyed']]
            if towers:
                towers.sort(key=lambda t: (t['position'][0] - self.position[0]) ** 2 +
                                           (t['position'][1] - self.position[1]) ** 2)
                return self.move_action_toward(towers[0]['position'])
        # 找目标
        target = self.find_priority_target(obs)
        if target:
            return self.move_action_toward(target)
        return 'idle'


class AssassinAI(Hero):
    """🗡️ 刺客：抓单，突进后排"""
    def step(self, observation: Dict) -> str:
        if not self.is_alive():
            return 'idle'
        obs = observation
        # 死亡 ≥ 1：强制推塔
        if self.deaths >= 1:
            towers = [t for t in obs['enemy_towers'] if not t['destroyed']]
            if towers:
                towers.sort(key=lambda t: (t['position'][0] - self.position[0]) ** 2 +
                                           (t['position'][1] - self.position[1]) ** 2)
                return self.move_action_toward(towers[0]['position'])
        # 突进：敌人在技能范围
        if self.skill_cooldown == 0 and obs['enemies']:
            in_range = [e for e in obs['enemies'] if e['distance'] <= self.skill_range]
            if in_range:
                return 'skill'
        # 攻击范围
        if obs['enemies']:
            for e in obs['enemies']:
                if e['distance'] <= self.attack_range:
                    return 'attack'
        # 50% 推塔
        import random
        if random.random() < 0.5:
            towers = [t for t in obs['enemy_towers'] if not t['destroyed']]
            if towers:
                towers.sort(key=lambda t: (t['position'][0] - self.position[0]) ** 2 +
                                           (t['position'][1] - self.position[1]) ** 2)
                return self.move_action_toward(towers[0]['position'])
        # 推塔/基地
        target = self.find_priority_target(obs)
        if target:
            return self.move_action_toward(target)
        return 'idle'


class MarksmanAI(Hero):
    """🏹 射手：后排输出"""
    def step(self, observation: Dict) -> str:
        if not self.is_alive():
            return 'idle'
        obs = observation
        # 死亡 ≥ 1：强制推塔
        if self.deaths >= 1:
            towers = [t for t in obs['enemy_towers'] if not t['destroyed']]
            if towers:
                towers.sort(key=lambda t: (t['position'][0] - self.position[0]) ** 2 +
                                           (t['position'][1] - self.position[1]) ** 2)
                return self.move_action_toward(towers[0]['position'])
        # 穿透箭
        if self.skill_cooldown == 0 and obs['enemies']:
            in_range = [e for e in obs['enemies'] if e['distance'] <= self.skill_range]
            if in_range:
                return 'skill'
        # 攻击范围
        if obs['enemies']:
            for e in obs['enemies']:
                if e['distance'] <= self.attack_range:
                    return 'attack'
        # 50% 推塔
        import random
        if random.random() < 0.5:
            towers = [t for t in obs['enemy_towers'] if not t['destroyed']]
            if towers:
                towers.sort(key=lambda t: (t['position'][0] - self.position[0]) ** 2 +
                                           (t['position'][1] - self.position[1]) ** 2)
                return self.move_action_toward(towers[0]['position'])
        # 太近就后退
        if obs['enemies']:
            e = min(obs['enemies'], key=lambda x: x['distance'])
            d = e['distance']
            if d < 4:
                dx = self.position[0] - e['position'][0]
                dy = self.position[1] - e['position'][1]
                if abs(dx) > abs(dy):
                    return 'move_left' if dx > 0 else 'move_right'
                return 'move_up' if dy > 0 else 'move_down'
        # 找塔/基地
        target = self.find_priority_target(obs)
        if target:
            return self.move_action_toward(target)
        return 'idle'


class SupportAI(Hero):
    """💚 辅助：跟队友治疗"""
    def step(self, observation: Dict) -> str:
        if not self.is_alive():
            return 'idle'
        obs = observation
        # 优先治疗（队友血 < 70%）
        if self.skill_cooldown == 0 and obs['allies']:
            injured = [a for a in obs['allies'] if a['health'] < a['health'] * 0.7]
            if injured or obs['self_health'] < self.max_health * 0.7:
                return 'skill'
        # 跟最近的队友（不要独行）
        if obs['allies']:
            ally = min(obs['allies'], key=lambda a: _dist(self.position, a['position']))
            d = _dist(self.position, ally['position'])
            if d > 5:
                return self.move_action_toward(ally['position'])
        # 攻击范围有敌人 → 攻击
        if obs['enemies']:
            for e in obs['enemies']:
                if e['distance'] <= self.attack_range:
                    return 'attack'
        # 推塔/基地
        target = self.find_priority_target(obs)
        if target:
            return self.move_action_toward(target)
        return 'idle'


class MageAI(Hero):
    """🔥 法师：中距离 AOE"""
    def step(self, observation: Dict) -> str:
        if not self.is_alive():
            return 'idle'
        obs = observation
        # 火球（多个敌人聚集）
        if self.skill_cooldown == 0 and obs['enemies']:
            in_range = [e for e in obs['enemies'] if e['distance'] <= self.skill_range]
            if len(in_range) >= 2:
                return 'skill'
        # 攻击范围
        if obs['enemies']:
            for e in obs['enemies']:
                if e['distance'] <= self.attack_range:
                    return 'attack'
        # 太近后退
        if obs['enemies']:
            e = min(obs['enemies'], key=lambda x: x['distance'])
            d = e['distance']
            if d < 3:
                dx = self.position[0] - e['position'][0]
                dy = self.position[1] - e['position'][1]
                if abs(dx) > abs(dy):
                    return 'move_left' if dx > 0 else 'move_right'
                return 'move_up' if dy > 0 else 'move_down'
        # 推塔/基地
        target = self.find_priority_target(obs)
        if target:
            return self.move_action_toward(target)
        return 'idle'


# 角色 → AI 类 映射
ROLE_AI = {
    'tank': TankAI,
    'assassin': AssassinAI,
    'marksman': MarksmanAI,
    'support': SupportAI,
    'mage': MageAI,
}