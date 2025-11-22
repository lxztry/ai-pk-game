"""
示例参赛者Agent
这是一个示例，展示如何创建自己的Agent
"""
import math
import random
from agents.code_agent import CodeAgent
from game.agent import Observation


class Agent(CodeAgent):
    """示例Agent - 简单的攻击策略"""
    
    def step(self, observation: Observation) -> str:
        """
        简单的策略：优先攻击最近的敌人
        """
        # 如果有敌人，攻击最近的
        if observation.enemies_in_view:
            closest_enemy = min(observation.enemies_in_view, key=lambda e: e['distance'])
            enemy_pos = tuple(closest_enemy['position'])
            
            # 如果已瞄准且可以射击，就射击
            if (self._is_aiming_at_from_obs(observation, enemy_pos) and 
                observation.shoot_cooldown == 0):
                return "shoot"
            
            # 否则转向敌人
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
        
        # 没有敌人时，随机移动
        return random.choice(["move_up", "move_down", "move_left", "move_right"])

