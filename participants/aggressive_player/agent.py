"""
激进型参赛者Agent - 主动攻击策略
"""
import math
import random
from agents.code_agent import CodeAgent
from game.agent import Observation


class Agent(CodeAgent):
    """激进型Agent - 主动寻找并攻击敌人"""
    
    def step(self, observation: Observation) -> str:
        """
        激进策略：
        1. 优先攻击最近的敌人
        2. 快速移动寻找敌人
        3. 血量充足时主动出击
        """
        enemies = observation.enemies_in_view
        
        # 如果有敌人，优先攻击
        if enemies:
            # 选择最近的敌人作为目标
            target = min(enemies, key=lambda e: e['distance'])
            enemy_pos = tuple(target['position'])
            
            # 如果距离很近且已瞄准，立即射击
            if target['distance'] < 15:
                if self._is_aiming_at_from_obs(observation, enemy_pos, tolerance=0.5):
                    if observation.shoot_cooldown == 0:
                        return "shoot"
            
            # 转向目标
            target_angle = self._angle_to_from_obs(observation, enemy_pos)
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
            
            # 如果角度差较大，先转向
            if abs(angle_diff) > 0.3:
                return "turn_right" if angle_diff > 0 else "turn_left"
            
            # 如果距离较远，向敌人移动
            if target['distance'] > 20:
                # 计算移动方向
                dx = enemy_pos[0] - observation.my_position[0]
                dy = enemy_pos[1] - observation.my_position[1]
                
                if abs(dx) > abs(dy):
                    return "move_right" if dx > 0 else "move_left"
                else:
                    return "move_down" if dy > 0 else "move_up"
            
            # 距离适中，可以射击
            if observation.shoot_cooldown == 0:
                return "shoot"
        
        # 没有敌人，主动寻找（向中心移动，更容易遇到敌人）
        center_x = observation.map_boundary[0] / 2
        center_y = observation.map_boundary[1] / 2
        dx = center_x - observation.my_position[0]
        dy = center_y - observation.my_position[1]
        
        if abs(dx) > abs(dy):
            return "move_right" if dx > 0 else "move_left"
        else:
            return "move_down" if dy > 0 else "move_up"

