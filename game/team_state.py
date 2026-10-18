"""
TeamGameState：NvN 团队战状态（支持 1v1 / 3v3 / 5v5 等）
"""
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional


@dataclass
class Supply:
    """地图补给：弹药包 / 血包 / 护盾 / 攻击 buff"""
    supply_type: str  # 'ammo' / 'health' / 'shield' / 'damage'
    position: Tuple[float, float]
    spawned_at: int = 0
    expires_at: int = 0
    consumed: bool = False


@dataclass
class Tower:
    """防御塔"""
    lane: int  # 0=上, 1=中, 2=下
    side: str  # 'blue' | 'red'
    hp: int = 50
    max_hp: int = 50
    attack: int = 8
    attack_range: float = 4.0
    position: Tuple[float, float] = (0, 0)
    destroyed: bool = False

    def take_damage(self, dmg: int) -> int:
        if self.destroyed:
            return 0
        self.hp = max(0, self.hp - dmg)
        if self.hp <= 0:
            self.destroyed = True
            return dmg
        return dmg


@dataclass
class Base:
    """基地/老营"""
    side: str
    hp: int = 1000
    max_hp: int = 1000
    position: Tuple[float, float] = (0, 0)

    def take_damage(self, dmg: int) -> int:
        self.hp = max(0, self.hp - dmg)
        return dmg


class TeamGameState:
    """3v3 团队战状态"""

    # 地图：横屏宽 40x25（适合电脑屏幕）
    MAP_W = 40
    MAP_H = 25
    MAX_TURNS = 300  # 5 分钟 = 300 秒 = 300 回合
    RESPAWN_DELAY = 10
    KILL_STREAK_WINDOW = 10

    def __init__(self, blue_heroes: list, red_heroes: list):
        """
        Args:
            blue_heroes: 3 个 Hero（系统默认）
            red_heroes: 3 个 Hero（用户定义）
        """
        self.heroes: List = blue_heroes + red_heroes
        self.blue_heroes = blue_heroes
        self.red_heroes = red_heroes

        # 基地
        self.blue_base = Base(side='blue', position=(0, 12))
        self.red_base = Base(side='red', position=(39, 12))

        # 防御塔：每方每路 1 座
        self.blue_towers: List[Tower] = []
        self.red_towers: List[Tower] = []
        for lane in range(3):
            # 蓝塔靠近蓝方基地（地图左边）
            self.blue_towers.append(Tower(
                lane=lane, side='blue',
                position=(8, 4 + lane * 8),
            ))
            # 红塔靠近红方基地（地图右边）
            self.red_towers.append(Tower(
                lane=lane, side='red',
                position=(31, 4 + lane * 8),
            ))

        # 全局事件日志
        self.events: List[Dict] = []  # [{turn, type, ...}]
        self.kill_log: List[Dict] = []  # [{turn, killer, victim, streak}]

        # 比分
        self.score = {'blue': 0, 'red': 0}

        # 地图补给（新机制）
        self.supplies: List[Supply] = []
        self.next_supply_spawn = 20  # 20 回合后第一次生成补给

        # 时间
        self.turn = 0

    @property
    def alive_heroes(self):
        return [h for h in self.heroes if h.is_alive()]

    @property
    def alive_blue(self):
        return [h for h in self.blue_heroes if h.is_alive()]

    @property
    def alive_red(self):
        return [h for h in self.red_heroes if h.is_alive()]

    def log_event(self, type_: str, **kwargs):
        """记录事件"""
        self.events.append({'turn': self.turn, 'type': type_, **kwargs})

    def lane_towers(self, side: str, lane: int) -> List[Tower]:
        """返回某方某路的塔（按从近到远）"""
        if side == 'blue':
            return sorted([t for t in self.blue_towers if t.lane == lane and not t.destroyed],
                         key=lambda t: t.position[0], reverse=True)  # 远的在前
        else:
            return sorted([t for t in self.red_towers if t.lane == lane and not t.destroyed],
                         key=lambda t: t.position[0])  # 远的在前

    def get_winner(self) -> Optional[str]:
        """返回胜方 'blue'/'red' 或 None"""
        if self.blue_base.hp <= 0:
            return 'red'
        if self.red_base.hp <= 0:
            return 'blue'
        return None

    def to_dict(self) -> Dict:
        """序列化为 dict（用于持久化/UI）"""
        return {
            'turn': self.turn,
            'max_turns': self.MAX_TURNS,
            'map_w': self.MAP_W,
            'map_h': self.MAP_H,
            'blue_base_hp': self.blue_base.hp,
            'red_base_hp': self.red_base.hp,
            'score': dict(self.score),
            'heroes': [
                {
                    'name': h.name,
                    'role': h.role,
                    'side': h.side,
                    'lane': h.lane,
                    'health': h.health,
                    'max_health': h.max_health,
                    'position': list(h.position),
                    'direction': list(h.direction),
                    'alive': h.is_alive(),
                    'respawn_at': h.respawn_at,
                    'kill_streak': h.kill_streak,
                    'stats': dict(h.stats),
                }
                for h in self.heroes
            ],
            'towers': [
                {
                    'lane': t.lane,
                    'side': t.side,
                    'hp': t.hp,
                    'max_hp': t.max_hp,
                    'position': list(t.position),
                    'destroyed': t.destroyed,
                }
                for t in (self.blue_towers + self.red_towers)
            ],
        }