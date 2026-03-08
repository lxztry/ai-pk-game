"""
智能参赛选手 - 混合策略AI
"""
import math
import random
from game.agent import Agent, Observation
from agents.code_agent import CodeAgent


class SmartAgent(CodeAgent):
    """智能参赛选手 - 采用混合策略"""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.last_shoot_target = None
        self.target_direction = (1, 0)
        self.emergency_mode = False
        self.supply_threshold = 50  # 血量低于50时紧急寻找补给
        self.weapon_preference = {
            'sniper': 0.8,  # 狙击枪优先级
            'shotgun': 0.6,  # 霰弹枪优先级
            'rocket': 0.7    # 火箭筒优先级
        }
    
    def step(self, observation: Observation) -> str:
        """
        智能决策逻辑：
        1. 优先躲避危险（子弹、低血量）
        2. 主动攻击最近敌人
        3. 寻找补给恢复血量
        4. 选择合适的武器
        """
        
        # 第一步：检查紧急情况（躲避子弹、低血量）
        action = self._handle_emergency(observation)
        if action:
            return action
        
        # 第二步：攻击敌人
        action = self._attack_enemies(observation)
        if action:
            return action
        
        # 第三步：寻找补给
        if observation.my_health < self.supply_threshold:
            action = self._find_supplies(observation)
            if action:
                return action
        
        # 第四步：优化武器选择
        action = self._optimize_weapon(observation)
        if action:
            return action
        
        # 默认行为：随机移动
        return self._default_movement(observation)
    
    def _handle_emergency(self, observation: Observation) -> str:
        """处理紧急情况：躲避子弹、低血量"""
        
        # 1. 躲避敌方子弹
        danger_bullets = self._get_danger_bullets(observation)
        if danger_bullets:
            return self._dodge_bullets(observation, danger_bullets)
        
        # 2. 如果血量极低，优先寻找补给
        if observation.my_health < 30:
            self.emergency_mode = True
            # 寻找最近的补给
            closest_supply = self._find_closest_supply(observation)
            if closest_supply:
                return self._move_towards(observation, closest_supply['position'])
        
        return None
    
    def _get_danger_bullets(self, observation: Observation) -> list:
        """获取危险的子弹（会击中自己的）"""
        danger_bullets = []
        
        for bullet in observation.bullets_in_view:
            bullet_pos = tuple(bullet['position'])
            bullet_dir = tuple(bullet['direction'])
            bullet_speed = bullet.get('speed', 1.0)
            
            # 预测子弹轨迹
            future_pos = self._predict_bullet_trajectory(bullet_pos, bullet_dir, bullet_speed, 3)
            
            # 检查是否会击中自己
            if self._will_bullet_hit_me(observation, future_pos, 0.5):
                danger_bullets.append(bullet)
        
        return danger_bullets
    
    def _predict_bullet_trajectory(self, pos, direction, speed, steps):
        """预测子弹轨迹"""
        predicted = []
        current_pos = list(pos)
        
        for _ in range(steps):
            current_pos[0] += direction[0] * speed
            current_pos[1] += direction[1] * speed
            predicted.append(tuple(current_pos))
        
        return predicted
    
    def _will_bullet_hit_me(self, observation, bullet_trajectory, tolerance=0.5):
        """判断子弹是否会击中自己"""
        my_pos = observation.my_position
        
        for bullet_pos in bullet_trajectory:
            distance = math.sqrt((my_pos[0] - bullet_pos[0])**2 + (my_pos[1] - bullet_pos[1])**2)
            if distance < tolerance:
                return True
        
        return False
    
    def _dodge_bullets(self, observation, danger_bullets) -> str:
        """躲避子弹策略"""
        # 选择最危险的子弹
        most_dangerous = max(danger_bullets, 
                           key=lambda b: self._bullet_threat_level(b, observation))
        
        # 计算逃跑方向（垂直于子弹方向）
        bullet_dir = most_dangerous['direction']
        
        # 两个可能的逃跑方向
        dodge_options = [
            (-bullet_dir[1], bullet_dir[0]),  # 90度旋转
            (bullet_dir[1], -bullet_dir[0])   # -90度旋转
        ]
        
        # 选择能移动的方向
        for dodge_dir in dodge_options:
            new_pos = (
                observation.my_position[0] + dodge_dir[0] * 2,
                observation.my_position[1] + dodge_dir[1] * 2
            )
            
            # 检查是否碰到障碍物
            if not self._would_hit_obstacle(observation, new_pos):
                # 移动到该方向
                if dodge_dir[0] > 0:
                    return "move_right"
                elif dodge_dir[0] < 0:
                    return "move_left"
                elif dodge_dir[1] > 0:
                    return "move_down"
                else:
                    return "move_up"
        
        # 如果无法躲避，转向背对子弹
        bullet_angle = math.atan2(bullet_dir[1], bullet_dir[0])
        my_angle = math.atan2(observation.my_direction[1], observation.my_direction[0])
        
        angle_diff = bullet_angle - my_angle
        angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi
        
        if abs(angle_diff) > math.pi / 2:
            return "turn_right"
        else:
            return "turn_left"
    
    def _bullet_threat_level(self, bullet, observation):
        """计算子弹威胁等级"""
        bullet_pos = tuple(bullet['position'])
        distance = self._distance_between(observation.my_position, bullet_pos)
        return -distance  # 距离越小威胁越大
    
    def _attack_enemies(self, observation: Observation) -> str:
        """攻击敌人策略"""
        enemies = observation.enemies_in_view
        
        if not enemies:
            return None
        
        # 选择最近的敌人作为目标
        closest_enemy = min(enemies, key=lambda e: e['distance'])
        enemy_pos = tuple(closest_enemy['position'])
        
        # 检查是否正在瞄准敌人
        if self._is_aiming_at_from_obs(observation, enemy_pos):
            # 如果射击冷却结束，射击
            if observation.shoot_cooldown <= 0:
                self.last_shoot_target = enemy_pos
                return "shoot"
        else:
            # 调整方向瞄准敌人
            target_angle = self._angle_to_from_obs(observation, enemy_pos)
            current_angle = math.atan2(observation.my_direction[1], observation.my_direction[0])
            
            angle_diff = target_angle - current_angle
            angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi
            
            if abs(angle_diff) > 0.3:  # 如果角度差太大，需要转向
                if angle_diff > 0:
                    return "turn_right"
                else:
                    return "turn_left"
            
            # 如果角度合适，移动靠近敌人
            return self._move_towards(observation, enemy_pos)
        
        return None
    
    def _find_supplies(self, observation: Observation) -> str:
        """寻找补给策略"""
        health_supplies = [s for s in observation.supplies_in_view if s['type'] == 'health']
        
        if health_supplies:
            closest_supply = min(health_supplies, key=lambda s: s['distance'])
            return self._move_towards(observation, closest_supply['position'])
        
        return None
    
    def _optimize_weapon(self, observation: Observation) -> str:
        """优化武器选择策略"""
        # 检查视野内的武器
        weapons = [s for s in observation.supplies_in_view if s['type'] in ['weapon_shotgun', 'weapon_sniper', 'weapon_rocket']]
        
        if not weapons:
            return None
        
        # 选择最适合当前情况的武器
        best_weapon = None
        best_score = -1
        
        for weapon in weapons:
            weapon_type = weapon['type'].replace('weapon_', '')
            distance = weapon['distance']
            
            # 评分系统：距离越近、武器优先级越高越好
            score = self.weapon_preference.get(weapon_type, 0.5) * (1.0 / max(distance, 1.0))
            
            if score > best_score:
                best_score = score
                best_weapon = weapon
        
        if best_weapon and best_score > 0.5:  # 只有足够好的武器才捡
            return self._move_towards(observation, best_weapon['position'])
        
        return None
    
    def _move_towards(self, observation, target_pos) -> str:
        """向目标位置移动"""
        my_pos = observation.my_position
        
        # 如果目标在左边
        if target_pos[0] < my_pos[0] - 2:
            return "move_left"
        # 如果目标在右边
        elif target_pos[0] > my_pos[0] + 2:
            return "move_right"
        # 如果目标在上面
        elif target_pos[1] < my_pos[1] - 2:
            return "move_up"
        # 如果目标在下面
        elif target_pos[1] > my_pos[1] + 2:
            return "move_down"
        
        return "idle"
    
    def _find_closest_supply(self, observation: Observation) -> dict:
        """寻找最近的补给"""
        if not observation.supplies_in_view:
            return None
        
        return min(observation.supplies_in_view, key=lambda s: s['distance'])
    
    def _would_hit_obstacle(self, observation, pos):
        """检查是否会撞到障碍物"""
        # 检查是否在障碍物内
        for obstacle in observation.obstacles_in_view:
            if (pos[0] >= obstacle['x'] and pos[0] <= obstacle['x'] + obstacle['width'] and
                pos[1] >= obstacle['y'] and pos[1] <= obstacle['y'] + obstacle['height']):
                return True
        return False
    
    def _distance_between(self, pos1, pos2):
        """计算两点间距离"""
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    def _default_movement(self, observation: Observation) -> str:
        """默认移动策略"""
        # 随机探索
        actions = ["move_up", "move_down", "move_left", "move_right"]
        return random.choice(actions)