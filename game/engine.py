"""
游戏引擎核心逻辑
"""
import random
import math
import time
from typing import List, Dict, Tuple, Optional, Any
from .agent import Agent, Observation


class Bullet:
    """子弹类"""
    def __init__(self, x: float, y: float, dx: float, dy: float, owner: str, damage: int = 10,
                 speed: float = 5.0, kind: str = 'normal', splash_radius: float = 0.0):
        self.x = x
        self.y = y
        self.dx = dx  # 方向向量（标准化）
        self.dy = dy
        self.speed = speed
        self.owner = owner
        self.damage = damage
        self.kind = kind  # normal | shotgun | sniper | rocket
        self.splash_radius = splash_radius
        self.active = True
    
    def update(self, map_width: int, map_height: int):
        """更新子弹位置"""
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        
        # 检查边界
        if self.x < 0 or self.x >= map_width or self.y < 0 or self.y >= map_height:
            self.active = False
    
    def get_position(self) -> Tuple[float, float]:
        return (self.x, self.y)


class GameState:
    """游戏状态"""
    def __init__(self, agents: List[Agent], map_width: int = 100, map_height: int = 100):
        self.agents = agents
        self.map_width = map_width
        self.map_height = map_height
        self.bullets: List[Bullet] = []
        # 新元素
        # 障碍物作为轴对齐矩形（AABB），充当墙体
        # 结构：{'rect': (x, y, w, h)}，x,y 为左上角
        self.obstacles: List[Dict[str, Any]] = []
        self.supplies: List[Dict[str, Any]] = []   # {position:(x,y), type: 'health'|'ammo_shotgun'|'ammo_sniper'|'ammo_rocket'|'weapon_shotgun'|'weapon_sniper'|'weapon_rocket'}
        self.turn = 0
        self.max_turns = 2000  # 最大回合数，防止无限循环
        
        # 初始化Agent位置（随机分布）
        self._initialize_positions()
        # 初始化障碍物
        self._initialize_obstacles()
    
    def _initialize_positions(self):
        """初始化Agent位置"""
        positions = []
        max_attempts_per_agent = 1000  # 防止无限循环
        for agent in self.agents:
            attempts = 0
            while attempts < max_attempts_per_agent:
                attempts += 1
                x = random.uniform(20, self.map_width - 20)
                y = random.uniform(20, self.map_height - 20)
                pos = (x, y)
                # 确保位置不重叠
                if all(math.sqrt((x - px[0])**2 + (y - px[1])**2) > 15 for px in positions):
                    positions.append(pos)
                    agent.position = pos
                    # 随机初始方向
                    angle = random.uniform(0, 2 * math.pi)
                    agent.direction = (math.cos(angle), math.sin(angle))
                    break
            else:
                # 如果无法找到不重叠的位置，使用最后一个尝试的位置
                print(f"警告: Agent {agent.name} 位置初始化达到最大尝试次数，使用随机位置")
                agent.position = (x, y)
                angle = random.uniform(0, 2 * math.pi)
                agent.direction = (math.cos(angle), math.sin(angle))
                positions.append(agent.position)
    
    def _initialize_obstacles(self, num_obstacles: int = 4):
        """生成不重叠、尺寸适中的矩形障碍（墙），并远离初始Agent"""
        placed: List[Tuple[float, float, float, float]] = []  # (x, y, w, h)
        max_attempts = num_obstacles * 50
        attempts = 0
        # 更小的障碍尺寸范围
        min_w, max_w = 6.0, 12.0
        min_h, max_h = 4.0, 8.0
        margin = 6.0  # 障碍之间和与边界的安全间距
        agent_margin = 12.0  # 障碍与Agent的最小距离，避免出生即卡住/子弹立刻碰撞

        def rect_far_from_agents(x: float, y: float, w: float, h: float) -> bool:
            for a in self.agents:
                ax, ay = a.position
                # 点到矩形的最小距离
                rx1, ry1, rx2, ry2 = x, y, x + w, y + h
                cx = min(max(ax, rx1), rx2)
                cy = min(max(ay, ry1), ry2)
                dist = math.sqrt((ax - cx) ** 2 + (ay - cy) ** 2)
                if dist < agent_margin:
                    return False
            return True

        while len(placed) < num_obstacles and attempts < max_attempts:
            attempts += 1
            w = random.uniform(min_w, max_w)
            h = random.uniform(min_h, max_h)
            x = random.uniform(margin, self.map_width - margin - w)
            y = random.uniform(margin, self.map_height - margin - h)

            ok = True
            for (px, py, pw, ph) in placed:
                # AABB overlap with margin
                if not (x + w + margin < px or px + pw + margin < x or
                        y + h + margin < py or py + ph + margin < y):
                    ok = False
                    break
            if not ok:
                continue
            if not rect_far_from_agents(x, y, w, h):
                continue

            placed.append((x, y, w, h))

        # 保存
        self.obstacles = [{'rect': (x, y, w, h)} for (x, y, w, h) in placed]
    
    def get_alive_agents(self) -> List[Agent]:
        """获取存活的Agent列表"""
        return [a for a in self.agents if a.health > 0]
    
    def get_winner(self, allow_score_judge: bool = False) -> Optional[Agent]:
        """
        获取获胜者
        规则：
        1. 如果只有一个存活者，直接获胜
        2. 如果有多个存活者，只有在 allow_score_judge=True 时才按评分判定
        3. 否则返回None，让游戏继续
        
        Args:
            allow_score_judge: 是否允许通过评分判定获胜者（用于超时后的判定）
        """
        alive = self.get_alive_agents()
        if len(alive) == 1:
            return alive[0]
        if len(alive) == 0:
            return None
        
        # 如果有多个存活者，只有在明确允许的情况下才按评分判定
        # 这避免了游戏在早期就因为评分差异而过早结束
        if allow_score_judge:
            # 按评分排序：击杀数 > 剩余血量
            scored = [(a, a.kills * 10000 + a.health) for a in alive]
            scored.sort(key=lambda x: x[1], reverse=True)
            
            # 检查是否有明确的获胜者（评分最高且唯一）
            if len(scored) > 1 and scored[0][1] > scored[1][1]:
                return scored[0][0]
        
        # 多个存活者且不允许评分判定，或完全平局
        return None


class GameEngine:
    """游戏引擎"""
    
    def __init__(self, agents: List[Agent], map_width: int = 100, map_height: int = 100):
        self.state = GameState(agents, map_width, map_height)
        self.view_distance = 30.0  # 视野距离
        # 供应生成参数
        self.supply_spawn_chance = 0.02  # 每回合生成概率
        self.max_supplies = 8
    
    def step(self) -> Dict[str, Any]:
        """
        执行一个游戏回合
        
        Returns:
            游戏状态信息字典
        """
        self.state.turn += 1
        
        # 更新子弹冷却
        for agent in self.state.agents:
            if agent.shoot_cooldown > 0:
                agent.shoot_cooldown -= 1
        
        # 每个Agent执行一步
        self._maybe_spawn_supply()
        for agent in self.state.agents:
            if agent.health <= 0:
                continue
            
            # 构建观察
            observation = self._build_observation(agent)
            
            # Agent决策（带超时保护）
            try:
                start_time = time.time()
                action = agent.step(observation)
                elapsed = time.time() - start_time
                
                # 如果执行时间过长，警告
                if elapsed > 1.0:  # 超过1秒
                    print(f"警告: Agent {agent.name} 执行时间过长 ({elapsed:.2f}秒)，回合 {self.state.turn}")
                
                # 验证动作有效性
                valid_actions = ["move_up", "move_down", "move_left", "move_right",
                               "turn_left", "turn_right", "shoot", "idle"]
                if action is None or action not in valid_actions:
                    print(f"警告: Agent {agent.name} 返回了无效动作 '{action}'，使用 'idle'")
                    action = "idle"
            except Exception as e:
                print(f"Agent {agent.name} 执行出错 (回合 {self.state.turn}): {e}")
                import traceback
                traceback.print_exc()
                action = "idle"
            
            # 执行动作
            self._execute_action(agent, action)
        
        # 更新子弹
        for bullet in self.state.bullets[:]:
            bullet.update(self.state.map_width, self.state.map_height)
            if not bullet.active:
                self.state.bullets.remove(bullet)
        
        # 检测碰撞
        self._check_collisions()
        # 处理拾取
        self._check_pickups()
        # 解决角色之间的拥挤/重叠
        self._resolve_agent_collisions()
        
        # 返回状态
        return {
            'turn': self.state.turn,
            'alive_count': len(self.state.get_alive_agents()),
            'winner': (winner.name if (winner := self.state.get_winner(allow_score_judge=False)) else None),
            'winning_team': self._get_winning_team(),
            'agents': [
                {
                    'name': a.name,
                    'health': a.health,
                    'position': list(a.position),
                    'direction': list(a.direction),
                    'kills': a.kills,
                    'team_id': a.team_id,
                    'weapon': a.weapon,
                    'ammo': a.ammo
                }
                for a in self.state.agents
            ],
            'bullets': [
                {
                    'position': list(b.get_position()),
                    'direction': [b.dx, b.dy],
                    'owner': b.owner,
                    'kind': b.kind
                }
                for b in self.state.bullets
            ],
            'obstacles': [
                {
                    'rect': [o['rect'][0], o['rect'][1], o['rect'][2], o['rect'][3]]
                } for o in self.state.obstacles
            ],
            'supplies': [
                {
                    'position': list(s['position']),
                    'type': s['type']
                } for s in self.state.supplies
            ]
        }
    
    def _build_observation(self, agent: Agent) -> Observation:
        """为Agent构建观察"""
        # 视野内的敌人
        enemies_in_view = []
        for other in self.state.agents:
            if other == agent or other.health <= 0:
                continue
            # 同队不视为敌人
            if agent.team_id is not None and other.team_id is not None and agent.team_id == other.team_id:
                continue
            dist = agent.distance_to(other.position)
            if dist <= self.view_distance:
                enemies_in_view.append({
                    'name': other.name,
                    'position': list(other.position),
                    'health': other.health,
                    'direction': list(other.direction),
                    'distance': dist,
                    'team_id': other.team_id
                })
        
        # 视野内的子弹
        bullets_in_view = []
        for bullet in self.state.bullets:
            if bullet.owner == agent.name:
                continue
            dist = agent.distance_to(bullet.get_position())
            if dist <= self.view_distance:
                bullets_in_view.append({
                    'position': list(bullet.get_position()),
                    'direction': [bullet.dx, bullet.dy],
                    'distance': dist
                })
        
        # 视野内的障碍物（矩形墙体）
        obstacles_in_view = []
        for obs in self.state.obstacles:
            rx, ry, rw, rh = obs['rect']
            # 点到矩形的最近点
            cx = min(max(agent.position[0], rx), rx + rw)
            cy = min(max(agent.position[1], ry), ry + rh)
            dist = math.sqrt((agent.position[0] - cx) ** 2 + (agent.position[1] - cy) ** 2)
            if dist <= self.view_distance + 2.0:
                obstacles_in_view.append({
                    'rect': [rx, ry, rw, rh],
                    'nearest_point': [cx, cy],
                    'distance': dist
                })
        
        # 视野内的补给
        supplies_in_view = []
        for s in self.state.supplies:
            dist = agent.distance_to(s['position'])
            if dist <= self.view_distance:
                supplies_in_view.append({
                    'position': list(s['position']),
                    'type': s['type'],
                    'distance': dist
                })
        
        return Observation({
            'my_health': agent.health,
            'my_position': list(agent.position),
            'my_direction': list(agent.direction),
            'my_team': agent.team_id,
            'my_weapon': agent.weapon,
            'my_ammo': agent.ammo.get(agent.weapon, None) if agent.weapon != 'normal' else None,
            'enemies_in_view': enemies_in_view,
            'bullets_in_view': bullets_in_view,
            'obstacles_in_view': obstacles_in_view,
            'supplies_in_view': supplies_in_view,
            'map_boundary': [self.state.map_width, self.state.map_height],
            'shoot_cooldown': agent.shoot_cooldown
        })
    
    def _blocked_by_obstacle(self, new_pos: Tuple[float, float]) -> bool:
        """点是否被任何矩形障碍阻挡，考虑角色半径膨胀"""
        radius = 2.0
        x, y = new_pos
        for obs in self.state.obstacles:
            rx, ry, rw, rh = obs['rect']
            # 将矩形外扩 radius，判断点是否在外扩矩形内
            if (rx - radius) <= x <= (rx + rw + radius) and (ry - radius) <= y <= (ry + rh + radius):
                return True
        return False

    def _execute_action(self, agent: Agent, action: str):
        """执行Agent的动作"""
        move_speed = 2.0
        turn_speed = math.pi / 6  # 30度

        def try_move(nx: float, ny: float):
            nx = max(0, min(self.state.map_width - 1, nx))
            ny = max(0, min(self.state.map_height - 1, ny))
            if not self._blocked_by_obstacle((nx, ny)):
                agent.position = (nx, ny)
                return True
            # 尝试滑动（仅X或仅Y方向）
            if not self._blocked_by_obstacle((nx, agent.position[1])):
                agent.position = (nx, agent.position[1])
                return True
            if not self._blocked_by_obstacle((agent.position[0], ny)):
                agent.position = (agent.position[0], ny)
                return True
            return False
        
        if action == "move_up":
            try_move(agent.position[0], agent.position[1] - move_speed)
        elif action == "move_down":
            try_move(agent.position[0], agent.position[1] + move_speed)
        elif action == "move_left":
            try_move(agent.position[0] - move_speed, agent.position[1])
        elif action == "move_right":
            try_move(agent.position[0] + move_speed, agent.position[1])
        elif action == "turn_left":
            angle = math.atan2(agent.direction[1], agent.direction[0])
            angle -= turn_speed
            agent.direction = (math.cos(angle), math.sin(angle))
        elif action == "turn_right":
            angle = math.atan2(agent.direction[1], agent.direction[0])
            angle += turn_speed
            agent.direction = (math.cos(angle), math.sin(angle))
        elif action == "shoot":
            if agent.shoot_cooldown == 0:
                self._fire_weapon(agent)
        # "idle" 不执行任何动作

    def _get_winning_team(self) -> Optional[Any]:
        """
        获取获胜队伍（仅在所有存活者都属于同一队伍时返回该队伍ID）
        说明：
        - 在对战过程中，只在“只剩一个队伍存活”时结束战斗
        - 超时后的平局判定与按比分选队伍，在调用方（如 GUI / 示例）里单独处理
        """
        alive = self.state.get_alive_agents()
        if not alive:
            return None

        team_ids = {agent.team_id for agent in alive if hasattr(agent, 'team_id') and agent.team_id is not None}
        if len(team_ids) == 1:
            return list(team_ids)[0]
        return None
    
    def _resolve_agent_collisions(self):
        """简单的角色-角色分离，避免靠近后停滞/重叠"""
        min_dist = 5.0
        for i in range(len(self.state.agents)):
            a = self.state.agents[i]
            if a.health <= 0:
                continue
            for j in range(i + 1, len(self.state.agents)):
                b = self.state.agents[j]
                if b.health <= 0:
                    continue
                dx = b.position[0] - a.position[0]
                dy = b.position[1] - a.position[1]
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < 1e-5:
                    # 重合，随机一个小方向
                    ang = random.uniform(0, 2*math.pi)
                    dx, dy = math.cos(ang), math.sin(ang)
                    dist = 1.0
                if dist < min_dist:
                    overlap = (min_dist - dist) / 2.0
                    nx = dx / dist
                    ny = dy / dist
                    ax = a.position[0] - nx * overlap
                    ay = a.position[1] - ny * overlap
                    bx = b.position[0] + nx * overlap
                    by = b.position[1] + ny * overlap
                    # 约束在边界内，并避免推进进障碍
                    ax = max(0, min(self.state.map_width - 1, ax))
                    ay = max(0, min(self.state.map_height - 1, ay))
                    bx = max(0, min(self.state.map_width - 1, bx))
                    by = max(0, min(self.state.map_height - 1, by))
                    if not self._blocked_by_obstacle((ax, ay)):
                        a.position = (ax, ay)
                    if not self._blocked_by_obstacle((bx, by)):
                        b.position = (bx, by)
    
    def _fire_weapon(self, agent: Agent):
        """根据当前武器发射子弹并处理冷却与弹药"""
        wx, wy = agent.position
        dx, dy = agent.direction
        weapon = agent.weapon

        def add_bullet(dx, dy, damage=10, speed=5.0, kind='normal', splash=0.0):
            self.state.bullets.append(Bullet(wx, wy, dx, dy, agent.name, damage=damage, speed=speed, kind=kind, splash_radius=splash))

        if weapon == 'normal':
            add_bullet(dx, dy, damage=10, speed=5.0, kind='normal')
            agent.shoot_cooldown = 20
        elif weapon == 'shotgun' and agent.ammo['shotgun'] > 0:
            # 三发散射
            base_angle = math.atan2(dy, dx)
            spreads = [-0.2, 0.0, 0.2]
            for s in spreads:
                ang = base_angle + s
                add_bullet(math.cos(ang), math.sin(ang), damage=8, speed=4.5, kind='shotgun')
            agent.ammo['shotgun'] -= 1
            agent.shoot_cooldown = 25
        elif weapon == 'sniper' and agent.ammo['sniper'] > 0:
            add_bullet(dx, dy, damage=25, speed=8.0, kind='sniper')
            agent.ammo['sniper'] -= 1
            agent.shoot_cooldown = 35
        elif weapon == 'rocket' and agent.ammo['rocket'] > 0:
            add_bullet(dx, dy, damage=20, speed=3.5, kind='rocket', splash=8.0)
            agent.ammo['rocket'] -= 1
            agent.shoot_cooldown = 40
        else:
            # 无弹药时按普通射击
            add_bullet(dx, dy, damage=10, speed=5.0, kind='normal')
            agent.shoot_cooldown = 20

    def _check_collisions(self):
        """检测碰撞"""
        # 子弹与Agent/障碍碰撞
        for bullet in self.state.bullets[:]:
            if not bullet.active:
                continue
            # 子弹碰撞矩形障碍则失效（火箭产生溅射）
            hit_obstacle = False
            for obs in self.state.obstacles:
                rx, ry, rw, rh = obs['rect']
                if (rx <= bullet.x <= rx + rw) and (ry <= bullet.y <= ry + rh):
                    hit_obstacle = True
                    break
            if hit_obstacle:
                if bullet.kind == 'rocket' and bullet.splash_radius > 0:
                    self._apply_splash_damage(bullet)
                bullet.active = False
                if bullet in self.state.bullets:
                    self.state.bullets.remove(bullet)
                continue

            for agent in self.state.agents:
                if agent.name == bullet.owner or agent.health <= 0:
                    continue
                # 友伤检查
                owner = next((o for o in self.state.agents if o.name == bullet.owner), None)
                if owner and owner.team_id is not None and agent.team_id is not None and owner.team_id == agent.team_id:
                    continue
                dist = math.sqrt(
                    (bullet.x - agent.position[0]) ** 2 +
                    (bullet.y - agent.position[1]) ** 2
                )
                if dist < 3.0:  # 碰撞半径
                    if bullet.kind == 'rocket' and bullet.splash_radius > 0:
                        # 火箭弹溅射
                        self._apply_splash_damage(bullet)
                    else:
                        agent.health -= bullet.damage
                    bullet.active = False
                    if agent.health <= 0:
                        # 找到子弹所有者，增加击杀数
                        for owner in self.state.agents:
                            if owner.name == bullet.owner:
                                owner.kills += 1
                                agent.deaths += 1
                                break
                    if bullet in self.state.bullets:
                        self.state.bullets.remove(bullet)
                    break

    def _apply_splash_damage(self, bullet: Bullet):
        """对爆炸范围内的单位造成伤害"""
        for agent in self.state.agents:
            if agent.health <= 0:
                continue
            dist = math.sqrt((bullet.x - agent.position[0]) ** 2 + (bullet.y - agent.position[1]) ** 2)
            if dist <= bullet.splash_radius:
                dmg = max(0, int(bullet.damage * (1 - dist / bullet.splash_radius)))
                if dmg > 0:
                    agent.health -= dmg
                    if agent.health <= 0:
                        for owner in self.state.agents:
                            if owner.name == bullet.owner:
                                owner.kills += 1
                                agent.deaths += 1
                                break

    def _maybe_spawn_supply(self):
        """随机生成补给"""
        if len(self.state.supplies) >= self.max_supplies:
            return
        if random.random() < self.supply_spawn_chance:
            kinds = [
                'health', 'health',
                'ammo_shotgun', 'ammo_sniper', 'ammo_rocket',
                'weapon_shotgun', 'weapon_sniper', 'weapon_rocket'
            ]
            k = random.choice(kinds)
            # 生成在不与障碍重叠的位置
            for _ in range(20):
                x = random.uniform(10, self.state.map_width - 10)
                y = random.uniform(10, self.state.map_height - 10)
                if not self._blocked_by_obstacle((x, y)):
                    self.state.supplies.append({'position': (x, y), 'type': k})
                    break

    def _check_pickups(self):
        """检测补给拾取"""
        for agent in self.state.agents:
            if agent.health <= 0:
                continue
            for s in self.state.supplies[:]:
                dist = agent.distance_to(s['position'])
                if dist < 4.0:
                    t = s['type']
                    if t == 'health':
                        agent.health = min(100, agent.health + 25)
                    elif t == 'ammo_shotgun':
                        agent.ammo['shotgun'] += 5
                    elif t == 'ammo_sniper':
                        agent.ammo['sniper'] += 3
                    elif t == 'ammo_rocket':
                        agent.ammo['rocket'] += 2
                    elif t == 'weapon_shotgun':
                        agent.weapon = 'shotgun'
                    elif t == 'weapon_sniper':
                        agent.weapon = 'sniper'
                    elif t == 'weapon_rocket':
                        agent.weapon = 'rocket'
                    self.state.supplies.remove(s)

    
    def run(self, max_turns: int = 2000, verbose: bool = False, 
            enable_timeout: bool = True, timeout_seconds: float = 60.0) -> Optional[Agent]:
        """
        运行游戏直到结束
        
        Args:
            max_turns: 最大回合数
            verbose: 是否输出详细信息
            enable_timeout: 是否启用超时检测（默认True）
            timeout_seconds: 超时秒数，如果启用超时检测，超过此时间没有进展则强制结束（默认60秒）
            
        Returns:
            获胜的Agent，如果完全平局则返回None
        """
        last_progress_time = time.time()
        last_turn_time = time.time()
        self._last_alive_count = len(self.state.get_alive_agents())
        consecutive_slow_steps = 0  # 连续慢速回合计数
        max_consecutive_slow = 10  # 连续10个回合都慢才判定为卡住
        
        while self.state.turn < max_turns:
            step_start = time.time()
            state_info = self.step()
            step_elapsed = time.time() - step_start
            
            # 检查是否有进展（存活人数变化或回合数增加）
            current_alive = state_info['alive_count']
            current_time = time.time()
            
            # 每回合都更新时间（回合数增加就是进展）
            last_turn_time = current_time
            
            # 如果有存活人数变化，更新进展时间
            if current_alive != self._last_alive_count:
                last_progress_time = current_time
                self._last_alive_count = current_alive
                consecutive_slow_steps = 0  # 有进展，重置慢速计数
            
            # 每50回合输出一次进度
            if verbose and self.state.turn % 50 == 0:
                print(f"回合 {self.state.turn}: 存活 {current_alive} 人")
            
            # 超时检测（仅在启用时）
            if enable_timeout:
                time_since_progress = current_time - last_progress_time
                
                # 检查单步执行时间（仅警告，不强制结束）
                if step_elapsed > 2.0:
                    consecutive_slow_steps += 1
                    if verbose or step_elapsed > 5.0:
                        print(f"警告: 回合 {self.state.turn} 执行时间较长 ({step_elapsed:.2f}秒)")
                else:
                    consecutive_slow_steps = 0  # 正常速度，重置计数
                
                # 只有在以下情况才强制结束：
                # 1. 连续多个回合都很慢（可能是真正的卡住）
                # 2. 或者长时间完全没有进展（超过timeout_seconds）
                should_timeout = False
                timeout_reason = ""
                
                if consecutive_slow_steps >= max_consecutive_slow:
                    should_timeout = True
                    timeout_reason = f"连续 {consecutive_slow_steps} 个回合执行缓慢"
                elif time_since_progress > timeout_seconds and current_alive > 1:
                    should_timeout = True
                    timeout_reason = f"{timeout_seconds}秒内没有存活人数变化"
                
                if should_timeout:
                    print(f"错误: 游戏超时！回合 {self.state.turn}")
                    print(f"  - 原因: {timeout_reason}")
                    print(f"  - 单步执行时间: {step_elapsed:.2f}秒")
                    print(f"  - 距离上次进展: {time_since_progress:.2f}秒")
                    print(f"  - 当前存活: {current_alive} 人")
                    alive_agents = self.state.get_alive_agents()
                    for a in alive_agents:
                        print(f"  - {a.name}: 血量={a.health}, 位置={a.position}")
                    # 强制结束，返回当前评分最高的
                    winner = self.state.get_winner(allow_score_judge=True)
                    if winner:
                        return winner
                    # 如果没有明确获胜者，返回评分最高的
                    if alive_agents:
                        scored = [(a, a.kills * 10000 + a.health) for a in alive_agents]
                        scored.sort(key=lambda x: x[1], reverse=True)
                        return scored[0][0] if scored else None
                    return None
            
            winner = self.state.get_winner(allow_score_judge=False)
            if winner:
                if verbose:
                    print(f"游戏结束！获胜者: {winner.name} (击杀: {winner.kills}, 血量: {winner.health})")
                return winner
        
        # 超时后按评分判定获胜者
        winner = self.state.get_winner(allow_score_judge=True)
        if winner:
            if verbose:
                print(f"游戏超时（{max_turns}回合），按评分判定获胜者: {winner.name} (击杀: {winner.kills}, 血量: {winner.health})")
            return winner
        
        if verbose:
            alive = self.state.get_alive_agents()
            print(f"游戏超时（{max_turns}回合），完全平局，剩余存活: {len(alive)} 人")
            for a in alive:
                print(f"  - {a.name}: 击杀={a.kills}, 血量={a.health}")
        return None

