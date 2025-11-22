"""
Agent基类定义
"""
from typing import Dict, Any, List, Tuple
from abc import ABC, abstractmethod
import math


class Observation:
    """游戏状态观察对象"""
    def __init__(self, data: Dict[str, Any]):
        self.my_health = data.get('my_health', 100)
        self.my_position = tuple(data.get('my_position', [0, 0]))
        self.my_direction = tuple(data.get('my_direction', [1, 0]))
        self.my_team = data.get('my_team', None)
        self.my_weapon = data.get('my_weapon', 'normal')
        self.my_ammo = data.get('my_ammo', None)  # None 表示无限/不适用
        self.enemies_in_view = data.get('enemies_in_view', [])
        self.bullets_in_view = data.get('bullets_in_view', [])
        self.obstacles_in_view = data.get('obstacles_in_view', [])
        self.supplies_in_view = data.get('supplies_in_view', [])
        self.map_boundary = tuple(data.get('map_boundary', [100, 100]))
        self.shoot_cooldown = data.get('shoot_cooldown', 0)
        self._raw = data
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'my_health': self.my_health,
            'my_position': list(self.my_position),
            'my_direction': list(self.my_direction),
            'my_team': self.my_team,
            'my_weapon': self.my_weapon,
            'my_ammo': self.my_ammo,
            'enemies_in_view': self.enemies_in_view,
            'bullets_in_view': self.bullets_in_view,
            'obstacles_in_view': self.obstacles_in_view,
            'supplies_in_view': self.supplies_in_view,
            'map_boundary': list(self.map_boundary),
            'shoot_cooldown': self.shoot_cooldown
        }


class Agent(ABC):
    """Agent基类，所有参与者需要继承此类"""
    
    def __init__(self, name: str):
        self.name = name
        self.health = 100
        self.position = (0, 0)
        self.direction = (1, 0)  # 方向向量，标准化
        self.team_id = None  # 支持组队：同队不互相伤害
        self.shoot_cooldown = 0
        self.kills = 0
        self.deaths = 0
        # 武器与弹药（默认普通武器，不消耗弹药）
        self.weapon = 'normal'  # normal | shotgun | sniper | rocket
        self.ammo = {
            'shotgun': 0,
            'sniper': 0,
            'rocket': 0
        }
    
    @abstractmethod
    def step(self, observation: Observation) -> str:
        """
        核心方法！参与者需要重写此方法。
        
        Args:
            observation: 当前游戏状态观察对象
            
        Returns:
            行动指令字符串，可选值：
            - "move_up", "move_down", "move_left", "move_right"
            - "turn_left", "turn_right"
            - "shoot"
            - "idle" (不执行任何动作)
        """
        pass
    
    def reset(self):
        """重置Agent状态"""
        self.health = 100
        self.position = (0, 0)
        self.direction = (1, 0)
        self.shoot_cooldown = 0
        # 保留 team_id，允许外部在赛前设置队伍
        self.weapon = 'normal'
        self.ammo = {
            'shotgun': 0,
            'sniper': 0,
            'rocket': 0
        }
    
    def distance_to(self, pos: Tuple[float, float]) -> float:
        """计算到指定位置的距离"""
        return math.sqrt(
            (self.position[0] - pos[0]) ** 2 + 
            (self.position[1] - pos[1]) ** 2
        )
    
    def angle_to(self, target_pos: Tuple[float, float]) -> float:
        """计算到目标位置的角度（弧度）"""
        dx = target_pos[0] - self.position[0]
        dy = target_pos[1] - self.position[1]
        return math.atan2(dy, dx)
    
    def is_aiming_at(self, target_pos: Tuple[float, float], tolerance: float = 0.3) -> bool:
        """判断是否正在瞄准目标位置"""
        target_angle = self.angle_to(target_pos)
        current_angle = math.atan2(self.direction[1], self.direction[0])
        angle_diff = abs(target_angle - current_angle)
        # 处理角度环绕
        angle_diff = min(angle_diff, 2 * math.pi - angle_diff)
        return angle_diff < tolerance

