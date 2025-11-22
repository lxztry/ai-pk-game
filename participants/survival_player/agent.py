"""
生存型参赛者Agent - 优先生存策略
"""
import math
import random
from agents.code_agent import CodeAgent
from game.agent import Observation


class Agent(CodeAgent):
    """生存型Agent - 优先保证生存，伺机反击"""
    
    def step(self, observation: Observation) -> str:
        """
        生存策略：
        1. 低血量时优先躲避
        2. 躲避子弹
        3. 保持安全距离
        4. 血量充足时反击
        """
        # 优先级1：躲避子弹
        if observation.bullets_in_view:
            for bullet in observation.bullets_in_view:
                if bullet['distance'] < 12:
                    # 计算子弹方向，垂直移动躲避
                    bullet_dir = bullet['direction']
                    # 垂直于子弹方向移动
                    if abs(bullet_dir[0]) > abs(bullet_dir[1]):
                        # 子弹主要是水平方向，垂直躲避
                        return random.choice(["move_up", "move_down"])
                    else:
                        # 子弹主要是垂直方向，水平躲避
                        return random.choice(["move_left", "move_right"])
        
        # 优先级2：低血量时逃跑
        if observation.my_health < 40:
            if observation.enemies_in_view:
                # 找到最近的敌人
                closest = min(observation.enemies_in_view, key=lambda e: e['distance'])
                if closest['distance'] < 20:
                    # 远离敌人
                    enemy_pos = tuple(closest['position'])
                    dx = observation.my_position[0] - enemy_pos[0]
                    dy = observation.my_position[1] - enemy_pos[1]
                    
                    # 选择远离方向
                    if abs(dx) > abs(dy):
                        return "move_right" if dx < 0 else "move_left"
                    else:
                        return "move_down" if dy < 0 else "move_up"
            
            # 没有敌人，向边缘移动（更安全）
            edge_x = observation.map_boundary[0] * 0.2
            edge_y = observation.map_boundary[1] * 0.2
            dx = edge_x - observation.my_position[0]
            dy = edge_y - observation.my_position[1]
            
            if abs(dx) > abs(dy):
                return "move_left" if dx < 0 else "move_right"
            else:
                return "move_up" if dy < 0 else "move_down"
        
        # 优先级3：血量充足时，保持安全距离攻击
        if observation.enemies_in_view:
            closest = min(observation.enemies_in_view, key=lambda e: e['distance'])
            enemy_pos = tuple(closest['position'])
            
            # 保持安全距离（15-25之间）
            if 15 < closest['distance'] < 25:
                # 如果已瞄准，射击
                if self._is_aiming_at_from_obs(observation, enemy_pos, tolerance=0.4):
                    if observation.shoot_cooldown == 0:
                        return "shoot"
                
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
                
                if abs(angle_diff) > 0.2:
                    return "turn_right" if angle_diff > 0 else "turn_left"
            
            # 距离太近，后退
            elif closest['distance'] < 15:
                dx = observation.my_position[0] - enemy_pos[0]
                dy = observation.my_position[1] - enemy_pos[1]
                if abs(dx) > abs(dy):
                    return "move_right" if dx < 0 else "move_left"
                else:
                    return "move_down" if dy < 0 else "move_up"
            
            # 距离太远，接近
            else:
                dx = enemy_pos[0] - observation.my_position[0]
                dy = enemy_pos[1] - observation.my_position[1]
                if abs(dx) > abs(dy):
                    return "move_right" if dx > 0 else "move_left"
                else:
                    return "move_down" if dy > 0 else "move_up"
        
        # 没有敌人，缓慢移动探索
        return random.choice(["move_up", "move_down", "move_left", "move_right"])

