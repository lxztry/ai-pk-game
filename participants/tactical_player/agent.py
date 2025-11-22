"""
战术型参赛者Agent - 基于障碍物、武器、补给包的智能策略
"""
import math
import random
from agents.code_agent import CodeAgent
from game.agent import Observation


class Agent(CodeAgent):
    """战术型Agent - 综合利用障碍物、武器和补给包"""
    
    def __init__(self, name: str = "TacticalPlayer"):
        super().__init__(name)
        self.last_action = None
        self.preferred_weapon = 'normal'  # 偏好武器
    
    def step(self, observation: Observation) -> str:
        """
        战术策略：
        1. 优先级1：躲避子弹（特别是近距离的）
        2. 优先级2：低血量时拾取血包或逃跑
        3. 优先级3：拾取有价值的补给（武器、弹药）
        4. 优先级4：利用障碍物作为掩体
        5. 优先级5：根据武器类型选择战斗策略
        6. 优先级6：攻击敌人
        """
        my_pos = observation.my_position
        my_health = observation.my_health
        my_weapon = observation.my_weapon
        
        # ========== 优先级1：躲避子弹 ==========
        if observation.bullets_in_view:
            dangerous_bullets = [b for b in observation.bullets_in_view if b['distance'] < 15]
            if dangerous_bullets:
                # 找到最近的威胁子弹
                closest_bullet = min(dangerous_bullets, key=lambda b: b['distance'])
                bullet_pos = tuple(closest_bullet['position'])
                bullet_dir = tuple(closest_bullet['direction'])
                
                # 计算躲避方向：垂直于子弹方向移动
                # 同时考虑障碍物，优先向障碍物方向躲避
                escape_dir = self._calculate_escape_direction(
                    observation, bullet_pos, bullet_dir
                )
                if escape_dir:
                    return escape_dir
                # 如果无法计算躲避方向，使用默认躲避
                return random.choice(["move_left", "move_right", "move_up", "move_down"])
        
        # ========== 优先级2：低血量时拾取血包或逃跑 ==========
        if my_health < 40:
            # 优先寻找血包
            health_supplies = [s for s in observation.supplies_in_view 
                             if s['type'] == 'health']
            if health_supplies:
                closest_health = min(health_supplies, key=lambda s: s['distance'])
                return self._move_towards(observation, tuple(closest_health['position']))
            
            # 没有血包，低血量时优先逃跑
            if observation.enemies_in_view:
                closest_enemy = min(observation.enemies_in_view, key=lambda e: e['distance'])
                if closest_enemy['distance'] < 20:
                    # 尝试移动到障碍物后面
                    cover_dir = self._find_cover_direction(observation, closest_enemy['position'])
                    if cover_dir:
                        return cover_dir
                    
                    # 没有掩体，直接远离
                    enemy_pos = tuple(closest_enemy['position'])
                    return self._move_away_from(observation, enemy_pos)
        
        # ========== 优先级3：拾取有价值的补给 ==========
        if observation.supplies_in_view:
            # 评估补给价值并选择最优的
            best_supply = self._evaluate_supplies(observation)
            if best_supply:
                supply_pos = tuple(best_supply['position'])
                # 如果距离很近，直接移动过去
                if best_supply['distance'] < 8:
                    return self._move_towards(observation, supply_pos)
                # 如果距离适中且没有敌人威胁，去拾取
                elif best_supply['distance'] < 20 and not observation.enemies_in_view:
                    return self._move_towards(observation, supply_pos)
        
        # ========== 优先级4：利用障碍物作为掩体 ==========
        if observation.enemies_in_view:
            closest_enemy = min(observation.enemies_in_view, key=lambda e: e['distance'])
            enemy_pos = tuple(closest_enemy['position'])
            
            # 如果敌人很近且没有掩体，寻找掩体
            if closest_enemy['distance'] < 15:
                cover_dir = self._find_cover_direction(observation, enemy_pos)
                if cover_dir:
                    return cover_dir
        
        # ========== 优先级5：根据武器类型选择战斗策略 ==========
        if observation.enemies_in_view:
            closest_enemy = min(observation.enemies_in_view, key=lambda e: e['distance'])
            enemy_pos = tuple(closest_enemy['position'])
            enemy_dist = closest_enemy['distance']
            
            # 根据武器类型选择最佳距离
            optimal_dist = self._get_optimal_distance(my_weapon)
            
            # 如果距离不合适，调整位置
            if enemy_dist < optimal_dist * 0.7:
                # 太近，后退
                return self._move_away_from(observation, enemy_pos)
            elif enemy_dist > optimal_dist * 1.5:
                # 太远，接近（但要小心）
                if my_health > 50:  # 只有血量充足时才接近
                    return self._move_towards(observation, enemy_pos)
                else:
                    # 血量不足，保持距离，转向敌人准备射击
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
                    else:
                        return "idle"  # 已经瞄准，等待冷却
            
            # 距离合适，准备攻击
            if self._is_aiming_at_from_obs(observation, enemy_pos, tolerance=0.4):
                if observation.shoot_cooldown == 0:
                    # 检查弹药（特殊武器需要弹药）
                    if my_weapon != 'normal':
                        ammo = observation.my_ammo
                        if ammo is None or ammo <= 0:
                            # 没有弹药，切换回普通武器或寻找弹药
                            pass  # 继续射击，引擎会自动切换
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
            else:
                # 已经瞄准，等待射击冷却
                return "idle"
        
        # ========== 默认行为：探索 ==========
        # 向地图中心移动，更容易遇到敌人和补给
        center_x = observation.map_boundary[0] / 2
        center_y = observation.map_boundary[1] / 2
        center_pos = (center_x, center_y)
        
        # 如果不在中心附近，向中心移动
        dist_to_center = math.sqrt(
            (my_pos[0] - center_x) ** 2 + (my_pos[1] - center_y) ** 2
        )
        if dist_to_center > 20:
            return self._move_towards(observation, center_pos)
        
        # 在中心附近，随机移动探索
        return random.choice(["move_up", "move_down", "move_left", "move_right"])
    
    def _calculate_escape_direction(self, observation: Observation, 
                                   bullet_pos: tuple, bullet_dir: tuple) -> str:
        """计算躲避子弹的最佳方向，优先向障碍物方向躲避"""
        my_pos = observation.my_position
        
        # 计算垂直于子弹方向的两个方向
        perp1 = (-bullet_dir[1], bullet_dir[0])  # 垂直方向1
        perp2 = (bullet_dir[1], -bullet_dir[0])  # 垂直方向2
        
        # 检查哪个方向有障碍物（可以作为掩体）
        directions = [
            ("move_up", (0, -1)),
            ("move_down", (0, 1)),
            ("move_left", (-1, 0)),
            ("move_right", (1, 0))
        ]
        
        # 优先选择朝向障碍物的方向
        best_dir = None
        best_score = -1
        
        for action, (dx, dy) in directions:
            # 计算这个方向与垂直方向的相似度
            dot1 = dx * perp1[0] + dy * perp1[1]
            dot2 = dx * perp2[0] + dy * perp2[1]
            perp_score = max(abs(dot1), abs(dot2))
            
            # 检查这个方向是否有障碍物
            new_pos = (my_pos[0] + dx * 5, my_pos[1] + dy * 5)
            has_cover = self._has_obstacle_towards(observation, new_pos)
            
            # 综合评分
            score = perp_score * 0.5 + (1.0 if has_cover else 0.0) * 0.5
            
            if score > best_score:
                best_score = score
                best_dir = action
        
        return best_dir if best_dir else random.choice(["move_left", "move_right", "move_up", "move_down"])
    
    def _has_obstacle_towards(self, observation: Observation, target_pos: tuple) -> bool:
        """检查目标位置方向是否有障碍物（可以作为掩体）"""
        my_pos = observation.my_position
        for obs in observation.obstacles_in_view:
            rect = obs['rect']
            rx, ry, rw, rh = rect[0], rect[1], rect[2], rect[3]
            
            # 检查障碍物是否在目标方向上
            # 简化：检查障碍物中心是否在目标方向附近
            obs_center = (rx + rw / 2, ry + rh / 2)
            to_obs = (obs_center[0] - my_pos[0], obs_center[1] - my_pos[1])
            to_target = (target_pos[0] - my_pos[0], target_pos[1] - my_pos[1])
            
            # 计算角度相似度
            if math.sqrt(to_obs[0]**2 + to_obs[1]**2) < 0.1:
                continue
            if math.sqrt(to_target[0]**2 + to_target[1]**2) < 0.1:
                continue
            
            dot = (to_obs[0] * to_target[0] + to_obs[1] * to_target[1]) / (
                math.sqrt(to_obs[0]**2 + to_obs[1]**2) * 
                math.sqrt(to_target[0]**2 + to_target[1]**2)
            )
            
            if dot > 0.5:  # 角度相似
                return True
        return False
    
    def _find_cover_direction(self, observation: Observation, enemy_pos: tuple) -> str:
        """寻找可以躲避敌人的障碍物方向"""
        my_pos = observation.my_position
        
        # 计算敌人方向
        to_enemy = (enemy_pos[0] - my_pos[0], enemy_pos[1] - my_pos[1])
        enemy_dist = math.sqrt(to_enemy[0]**2 + to_enemy[1]**2)
        if enemy_dist < 0.1:
            return None
        
        # 寻找在敌人和自身之间的障碍物
        best_cover = None
        best_score = -1
        
        for obs in observation.obstacles_in_view:
            rect = obs['rect']
            rx, ry, rw, rh = rect[0], rect[1], rect[2], rect[3]
            obs_center = (rx + rw / 2, ry + rh / 2)
            
            # 检查障碍物是否在敌人和自身之间
            to_obs = (obs_center[0] - my_pos[0], obs_center[1] - my_pos[1])
            to_obs_dist = math.sqrt(to_obs[0]**2 + to_obs[1]**2)
            
            # 计算障碍物是否在敌人方向上（作为掩体）
            dot = (to_obs[0] * to_enemy[0] + to_obs[1] * to_enemy[1]) / (to_obs_dist * enemy_dist)
            
            # 障碍物应该在敌人方向上，且距离适中
            if dot > 0.3 and 5 < to_obs_dist < 15:
                score = dot * (1.0 / to_obs_dist)  # 越近越好
                if score > best_score:
                    best_score = score
                    best_cover = obs_center
        
        if best_cover:
            return self._move_towards(observation, best_cover)
        
        return None
    
    def _evaluate_supplies(self, observation: Observation) -> dict:
        """评估补给的价值，返回最有价值的补给"""
        my_weapon = observation.my_weapon
        my_health = observation.my_health
        my_ammo = observation.my_ammo
        
        best_supply = None
        best_score = -1
        
        for supply in observation.supplies_in_view:
            score = 0
            supply_type = supply['type']
            distance = supply['distance']
            
            # 血包：低血量时价值高
            if supply_type == 'health':
                if my_health < 60:
                    score = (100 - my_health) / 100.0 * 100
                else:
                    score = 10
            
            # 武器：根据武器类型评分
            elif supply_type == 'weapon_rocket':
                score = 80 if my_weapon != 'rocket' else 5
            elif supply_type == 'weapon_sniper':
                score = 60 if my_weapon != 'sniper' else 5
            elif supply_type == 'weapon_shotgun':
                score = 40 if my_weapon != 'shotgun' else 5
            
            # 弹药：根据当前武器和弹药量评分
            elif supply_type == 'ammo_rocket':
                if my_weapon == 'rocket':
                    score = 50 if (my_ammo is None or my_ammo < 5) else 10
                else:
                    score = 20  # 未来可能用到
            elif supply_type == 'ammo_sniper':
                if my_weapon == 'sniper':
                    score = 50 if (my_ammo is None or my_ammo < 3) else 10
                else:
                    score = 20
            elif supply_type == 'ammo_shotgun':
                if my_weapon == 'shotgun':
                    score = 40 if (my_ammo is None or my_ammo < 5) else 10
                else:
                    score = 15
            
            # 距离惩罚：距离越远，价值越低
            distance_penalty = distance / 30.0
            final_score = score / (1 + distance_penalty)
            
            if final_score > best_score:
                best_score = final_score
                best_supply = supply
        
        return best_supply if best_score > 5 else None  # 只有价值足够高才去拾取
    
    def _get_optimal_distance(self, weapon: str) -> float:
        """根据武器类型返回最佳战斗距离"""
        if weapon == 'shotgun':
            return 8.0  # 近距离
        elif weapon == 'sniper':
            return 25.0  # 远距离
        elif weapon == 'rocket':
            return 15.0  # 中距离（利用溅射）
        else:  # normal
            return 15.0  # 中距离
    
    def _move_towards(self, observation: Observation, target_pos: tuple) -> str:
        """向目标位置移动"""
        my_pos = observation.my_position
        dx = target_pos[0] - my_pos[0]
        dy = target_pos[1] - my_pos[1]
        
        if abs(dx) > abs(dy):
            return "move_right" if dx > 0 else "move_left"
        else:
            return "move_down" if dy > 0 else "move_up"
    
    def _move_away_from(self, observation: Observation, target_pos: tuple) -> str:
        """远离目标位置"""
        my_pos = observation.my_position
        dx = my_pos[0] - target_pos[0]
        dy = my_pos[1] - target_pos[1]
        
        if abs(dx) > abs(dy):
            return "move_right" if dx > 0 else "move_left"
        else:
            return "move_down" if dy > 0 else "move_up"

