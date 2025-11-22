"""
代码派Agent - 通过编写代码实现策略
"""
import random
import math
from game.agent import Agent, Observation


class CodeAgent(Agent):
    """代码派Agent基类"""
    
    def step(self, observation: Observation) -> str:
        """子类需要实现此方法"""
        return "idle"
    
    def _angle_to_from_obs(self, observation: Observation, target_pos: tuple) -> float:
        """从observation计算到目标位置的角度"""
        dx = target_pos[0] - observation.my_position[0]
        dy = target_pos[1] - observation.my_position[1]
        return math.atan2(dy, dx)
    
    def _is_aiming_at_from_obs(self, observation: Observation, target_pos: tuple, tolerance: float = 0.3) -> bool:
        """从observation判断是否正在瞄准目标位置"""
        target_angle = self._angle_to_from_obs(observation, target_pos)
        current_angle = math.atan2(observation.my_direction[1], observation.my_direction[0])
        angle_diff = abs(target_angle - current_angle)
        angle_diff = min(angle_diff, 2 * math.pi - angle_diff)
        return angle_diff < tolerance


class RandomAgent(CodeAgent):
    """随机Agent - 完全随机行动"""
    
    def step(self, observation: Observation) -> str:
        actions = ["move_up", "move_down", "move_left", "move_right", 
                  "turn_left", "turn_right", "shoot", "idle"]
        return random.choice(actions)


class AggressiveAgent(CodeAgent):
    """激进型Agent - 主动攻击最近敌人"""
    
    def step(self, observation: Observation) -> str:
        enemies = observation.enemies_in_view
        
        # 如果有敌人，攻击最近的
        if enemies:
            closest_enemy = min(enemies, key=lambda e: e['distance'])
            enemy_pos = tuple(closest_enemy['position'])
            
            # 计算需要转向的角度
            target_angle = self.angle_to(enemy_pos)
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
            
            # 如果已经瞄准，射击
            if abs(angle_diff) < 0.3 and observation.shoot_cooldown == 0:
                return "shoot"
            # 否则转向
            elif angle_diff > 0:
                return "turn_right"
            else:
                return "turn_left"
        
        # 没有敌人，随机移动寻找
        return random.choice(["move_up", "move_down", "move_left", "move_right"])


class DefensiveAgent(CodeAgent):
    """防御型Agent - 优先躲避，伺机反击"""
    
    def step(self, observation: Observation) -> str:
        # 如果血量低，优先逃跑
        if observation.my_health < 30:
            # 远离最近的敌人
            if observation.enemies_in_view:
                closest_enemy = min(observation.enemies_in_view, key=lambda e: e['distance'])
                enemy_pos = tuple(closest_enemy['position'])
                
                # 计算远离方向
                dx = observation.my_position[0] - enemy_pos[0]
                dy = observation.my_position[1] - enemy_pos[1]
                
                # 选择移动方向
                if abs(dx) > abs(dy):
                    return "move_right" if dx < 0 else "move_left"
                else:
                    return "move_down" if dy < 0 else "move_up"
        
        # 如果有子弹接近，躲避
        if observation.bullets_in_view:
            closest_bullet = min(observation.bullets_in_view, key=lambda b: b['distance'])
            if closest_bullet['distance'] < 10:
                # 快速转向躲避
                return random.choice(["turn_left", "turn_right", "move_left", "move_right"])
        
        # 如果有敌人且距离适中，攻击
        if observation.enemies_in_view:
            closest_enemy = min(observation.enemies_in_view, key=lambda e: e['distance'])
            if 10 < closest_enemy['distance'] < 25:
                enemy_pos = tuple(closest_enemy['position'])
                if self._is_aiming_at_from_obs(observation, enemy_pos) and observation.shoot_cooldown == 0:
                    return "shoot"
                else:
                    # 转向敌人
                    target_angle = self._angle_to_from_obs(observation, enemy_pos)
                    current_angle = math.atan2(
                        observation.my_direction[1],
                        observation.my_direction[0]
                    )
                    angle_diff = target_angle - current_angle
                    if angle_diff > math.pi:
                        angle_diff -= 2 * math.pi
                    elif angle_diff < -math.pi:
                        angle_diff += 2 * math.pi
                    
                    if abs(angle_diff) > 0.3:
                        return "turn_right" if angle_diff > 0 else "turn_left"
        
        # 默认行为：向中心移动
        center_x = observation.map_boundary[0] / 2
        center_y = observation.map_boundary[1] / 2
        dx = center_x - observation.my_position[0]
        dy = center_y - observation.my_position[1]
        
        if abs(dx) > abs(dy):
            return "move_right" if dx > 0 else "move_left"
        else:
            return "move_down" if dy > 0 else "move_up"


class SmartAgent(CodeAgent):
    """智能Agent - 综合策略"""
    
    def step(self, observation: Observation) -> str:
        # 优先级1: 躲避子弹
        if observation.bullets_in_view:
            for bullet in observation.bullets_in_view:
                if bullet['distance'] < 8:
                    # 计算子弹方向，垂直移动躲避
                    return random.choice(["move_left", "move_right", "move_up", "move_down"])
        
        # 优先级2: 低血量时逃跑
        if observation.my_health < 25:
            if observation.enemies_in_view:
                closest = min(observation.enemies_in_view, key=lambda e: e['distance'])
                if closest['distance'] < 15:
                    # 远离
                    enemy_pos = tuple(closest['position'])
                    dx = observation.my_position[0] - enemy_pos[0]
                    dy = observation.my_position[1] - enemy_pos[1]
                    if abs(dx) > abs(dy):
                        return "move_right" if dx < 0 else "move_left"
                    else:
                        return "move_down" if dy < 0 else "move_up"
        
        # 优先级3: 攻击敌人
        if observation.enemies_in_view:
            # 优先攻击血量低的敌人
            target = min(observation.enemies_in_view, 
                        key=lambda e: (e['health'], e['distance']))
            enemy_pos = tuple(target['position'])
            
            # 如果距离合适且已瞄准，射击
            if 8 < target['distance'] < 20:
                if self._is_aiming_at_from_obs(observation, enemy_pos, tolerance=0.4) and observation.shoot_cooldown == 0:
                    return "shoot"
            
            # 转向目标
            target_angle = self._angle_to_from_obs(observation, enemy_pos)
            current_angle = math.atan2(
                observation.my_direction[1],
                observation.my_direction[0]
            )
            angle_diff = target_angle - current_angle
            if angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            elif angle_diff < -math.pi:
                angle_diff += 2 * math.pi
            
            if abs(angle_diff) > 0.2:
                return "turn_right" if angle_diff > 0 else "turn_left"
        
        # 默认：探索
        return random.choice(["move_up", "move_down", "move_left", "move_right"])

