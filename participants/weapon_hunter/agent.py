"""
武器猎手 - 擅长寻找和使用各种武器的Agent
优先寻找武器，然后寻找弹药，最后使用武器进行战斗
"""
import math
import random
from agents.code_agent import CodeAgent
from game.agent import Observation


class Agent(CodeAgent):
    """武器猎手 - 专注于武器收集和使用的策略"""
    
    def step(self, observation: Observation) -> str:
        """
        策略优先级：
        1. 躲避危险（子弹、近距离敌人）
        2. 寻找武器（优先火箭筒 > 狙击枪 > 霰弹枪）
        3. 寻找弹药（当前武器的弹药）
        4. 寻找血包（低血量时）
        5. 攻击敌人（使用当前武器）
        6. 探索地图（寻找更多补给）
        """
        
        # 1. 躲避危险子弹
        if observation.bullets_in_view:
            dangerous_bullets = [
                b for b in observation.bullets_in_view 
                if b['distance'] < 8  # 近距离子弹
            ]
            if dangerous_bullets:
                closest_bullet = min(dangerous_bullets, key=lambda b: b['distance'])
                bullet_pos = tuple(closest_bullet['position'])
                # 远离子弹
                return self._move_away_from(observation, bullet_pos)
        
        # 2. 如果有敌人很近且血量低，优先逃跑
        if observation.enemies_in_view and observation.my_health < 30:
            closest_enemy = min(observation.enemies_in_view, key=lambda e: e['distance'])
            if closest_enemy['distance'] < 15:
                enemy_pos = tuple(closest_enemy['position'])
                return self._move_away_from(observation, enemy_pos)
        
        # 3. 寻找武器（最高优先级）
        if observation.supplies_in_view:
            # 武器优先级：rocket > sniper > shotgun
            weapon_priority = ['weapon_rocket', 'weapon_sniper', 'weapon_shotgun']
            
            # 如果还没有武器，或者有更好的武器，就去寻找
            current_weapon = observation.my_weapon or 'normal'
            weapon_value = {'normal': 0, 'shotgun': 1, 'sniper': 2, 'rocket': 3}
            current_value = weapon_value.get(current_weapon, 0)
            
            for weapon_type in weapon_priority:
                # 检查是否需要这个武器
                target_weapon = weapon_type.replace('weapon_', '')
                target_value = weapon_value.get(target_weapon, 0)
                
                if target_value > current_value:
                    # 寻找这个武器
                    weapons = [s for s in observation.supplies_in_view if s['type'] == weapon_type]
                    if weapons:
                        target = min(weapons, key=lambda s: s['distance'])
                        return self._move_towards(observation, tuple(target['position']))
            
            # 4. 如果有武器，寻找对应弹药
            if current_weapon != 'normal':
                ammo_type = f'ammo_{current_weapon}'
                current_ammo = observation.my_ammo if observation.my_ammo is not None else 0
                
                # 如果弹药不足（少于5发），优先寻找弹药
                if current_ammo < 5:
                    ammos = [s for s in observation.supplies_in_view if s['type'] == ammo_type]
                    if ammos:
                        target = min(ammos, key=lambda s: s['distance'])
                        return self._move_towards(observation, tuple(target['position']))
            
            # 5. 低血量时寻找血包
            if observation.my_health < 60:
                healths = [s for s in observation.supplies_in_view if s['type'] == 'health']
                if healths:
                    target = min(healths, key=lambda s: s['distance'])
                    return self._move_towards(observation, tuple(target['position']))
        
        # 6. 攻击敌人（根据武器类型调整策略）
        if observation.enemies_in_view:
            # 选择目标：优先攻击血量低的敌人
            target_enemy = min(observation.enemies_in_view, key=lambda e: (e['health'], e['distance']))
            enemy_pos = tuple(target_enemy['position'])
            
            # 根据武器类型调整攻击距离
            current_weapon = observation.my_weapon or 'normal'
            optimal_range = {
                'normal': 20,      # 普通武器：中等距离
                'shotgun': 12,     # 霰弹枪：近距离
                'sniper': 30,      # 狙击枪：远距离
                'rocket': 25       # 火箭筒：中远距离（溅射）
            }
            optimal = optimal_range.get(current_weapon, 20)
            distance = target_enemy['distance']
            
            # 如果距离合适且可以射击，就射击
            if (abs(distance - optimal) < 10 and 
                self._is_aiming_at_from_obs(observation, enemy_pos, tolerance=0.4) and
                observation.shoot_cooldown == 0):
                return "shoot"
            
            # 如果距离太远（狙击枪除外），靠近敌人
            if distance > optimal + 5 and current_weapon != 'sniper':
                return self._move_towards(observation, enemy_pos)
            # 如果距离太近（狙击枪），远离敌人
            elif distance < optimal - 5 and current_weapon == 'sniper':
                return self._move_away_from(observation, enemy_pos)
            # 否则转向敌人
            else:
                return self._turn_towards(observation, enemy_pos)
        
        # 7. 没有敌人时，探索地图寻找补给
        # 向地图中心移动，更容易遇到补给
        center_x = observation.map_boundary[0] / 2
        center_y = observation.map_boundary[1] / 2
        center_pos = (center_x, center_y)
        
        # 如果不在中心附近，向中心移动
        dist_to_center = math.sqrt(
            (observation.my_position[0] - center_x) ** 2 +
            (observation.my_position[1] - center_y) ** 2
        )
        
        if dist_to_center > 20:
            return self._move_towards(observation, center_pos)
        
        # 在中心附近时，随机移动探索
        return random.choice(["move_up", "move_down", "move_left", "move_right"])
    
    def _move_towards(self, observation: Observation, target_pos: tuple) -> str:
        """移动到目标位置"""
        dx = target_pos[0] - observation.my_position[0]
        dy = target_pos[1] - observation.my_position[1]
        
        # 选择移动方向
        if abs(dx) > abs(dy):
            return "move_right" if dx > 0 else "move_left"
        else:
            return "move_down" if dy > 0 else "move_up"
    
    def _move_away_from(self, observation: Observation, target_pos: tuple) -> str:
        """远离目标位置"""
        dx = observation.my_position[0] - target_pos[0]
        dy = observation.my_position[1] - target_pos[1]
        
        # 选择远离方向
        if abs(dx) > abs(dy):
            return "move_right" if dx > 0 else "move_left"
        else:
            return "move_down" if dy > 0 else "move_up"
    
    def _turn_towards(self, observation: Observation, target_pos: tuple) -> str:
        """转向目标位置"""
        target_angle = self._angle_to_from_obs(observation, target_pos)
        current_angle = math.atan2(
            observation.my_direction[1],
            observation.my_direction[0]
        )
        
        angle_diff = target_angle - current_angle
        # 处理角度环绕
        if angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        elif angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        
        if abs(angle_diff) < 0.1:
            return "idle"
        
        return "turn_right" if angle_diff > 0 else "turn_left"

