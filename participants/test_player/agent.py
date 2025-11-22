"""
测试参赛者Agent
"""
import math
import random
from agents.code_agent import CodeAgent
from game.agent import Observation


class Agent(CodeAgent):
    """测试Agent - 防御型策略"""
    
    def step(self, observation: Observation) -> str:
        """
        防御型策略：优先躲避，伺机反击
        """
        # 如果血量低，优先逃跑
        if observation.my_health < 30:
            if observation.enemies_in_view:
                closest_enemy = min(observation.enemies_in_view, key=lambda e: e['distance'])
                enemy_pos = tuple(closest_enemy['position'])
                
                # 远离敌人
                dx = observation.my_position[0] - enemy_pos[0]
                dy = observation.my_position[1] - enemy_pos[1]
                
                if abs(dx) > abs(dy):
                    return "move_right" if dx < 0 else "move_left"
                else:
                    return "move_down" if dy < 0 else "move_up"
        
        # 如果有子弹接近，躲避
        if observation.bullets_in_view:
            closest_bullet = min(observation.bullets_in_view, key=lambda b: b['distance'])
            if closest_bullet['distance'] < 10:
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

