"""
碰撞检测单元测试

覆盖：
- 子弹基础移动与边界
- 子弹与 Agent 碰撞（直接命中、距离边界）
- 子弹与障碍物碰撞
- 火箭弹溅射伤害
- 友军伤害（team_id）
- 死亡后击杀计数
"""
import math
import pytest

from game.engine import Bullet, GameEngine, GameState
from tests.fixtures.agents import DummyAgent


def _make_engine(agents, map_size=100):
    """工厂：创建引擎后手动改 agent 位置（绕过 _initialize_positions 的随机）"""
    engine = GameEngine(agents, map_size, map_size)
    return engine


# ---------- 1. 子弹基础行为 ----------

class TestBullet:
    def test_bullet_moves_along_direction(self):
        b = Bullet(x=10, y=10, dx=1, dy=0, owner="p1", speed=5)
        b.update(100, 100)
        assert (b.x, b.y) == (15, 10)

    def test_bullet_diagonal_movement(self):
        b = Bullet(x=10, y=10, dx=math.sqrt(0.5), dy=math.sqrt(0.5),
                   owner="p1", speed=10)
        b.update(100, 100)
        assert abs(b.x - 10 - 7.07) < 0.01
        assert abs(b.y - 10 - 7.07) < 0.01

    def test_bullet_out_of_bounds_right(self):
        b = Bullet(x=99, y=10, dx=1, dy=0, owner="p1", speed=5)
        b.update(100, 100)
        assert not b.active

    def test_bullet_out_of_bounds_left(self):
        b = Bullet(x=0, y=10, dx=-1, dy=0, owner="p1", speed=5)
        b.update(100, 100)
        assert not b.active

    def test_bullet_out_of_bounds_top(self):
        b = Bullet(x=10, y=0, dx=0, dy=-1, owner="p1", speed=5)
        b.update(100, 100)
        assert not b.active

    def test_bullet_out_of_bounds_bottom(self):
        b = Bullet(x=10, y=99, dx=0, dy=1, owner="p1", speed=5)
        b.update(100, 100)
        assert not b.active

    def test_bullet_within_bounds_stays_active(self):
        b = Bullet(x=50, y=50, dx=1, dy=0, owner="p1", speed=5)
        b.update(100, 100)
        assert b.active


# ---------- 2. 子弹与 Agent 碰撞 ----------

class TestBulletHitsAgent:
    def _setup_collision(self, victim_pos=(15, 50), bullet_pos=(13, 50),
                        shooter_pos=(0, 50), damage=20):
        shooter = DummyAgent("shooter")
        shooter.position = shooter_pos
        shooter.direction = (1, 0)
        victim = DummyAgent("victim")
        victim.position = victim_pos
        engine = _make_engine([shooter, victim])
        # 引擎 init 会覆盖位置，重新设置
        shooter.position = shooter_pos
        victim.position = victim_pos
        engine.state.bullets.append(
            Bullet(bullet_pos[0], bullet_pos[1], 1, 0,
                   owner="shooter", damage=damage)
        )
        return engine, shooter, victim

    def test_bullet_within_3_units_hits(self):
        engine, shooter, victim = self._setup_collision(
            victim_pos=(15, 50), bullet_pos=(13, 50)
        )
        engine._check_collisions()
        assert victim.health < 100, f"expected hit, health={victim.health}"

    def test_bullet_outside_3_units_misses(self):
        # bullet 在 20，victim 在 50 → 距离 30 > 3，不命中
        engine, shooter, victim = self._setup_collision(
            victim_pos=(50, 50), bullet_pos=(20, 50)
        )
        engine._check_collisions()
        assert victim.health == 100

    def test_hit_records_kill(self):
        engine, shooter, victim = self._setup_collision(damage=200)
        engine._check_collisions()
        assert shooter.kills == 1
        assert victim.deaths == 1
        assert victim.health <= 0

    def test_friendly_fire_blocked_same_team(self):
        shooter = DummyAgent("p1")
        shooter.team_id = 1
        shooter.position = (0, 50)
        teammate = DummyAgent("p2")
        teammate.team_id = 1
        teammate.position = (15, 50)
        enemy = DummyAgent("p3")
        enemy.team_id = 2
        enemy.position = (15, 80)

        engine = _make_engine([shooter, teammate, enemy])
        shooter.position = (0, 50)
        teammate.position = (15, 50)
        enemy.position = (15, 80)
        engine.state.bullets.append(
            Bullet(13, 50, 1, 0, owner="p1", damage=50)
        )
        engine._check_collisions()
        # 队友无伤
        assert teammate.health == 100
        # 敌人挨打（如果距离够近）
        # enemy 在 (15, 80)，bullet 在 (13, 50)，距离 ~30，不命中
        assert enemy.health == 100

    def test_friendly_fire_works_different_team(self):
        shooter = DummyAgent("p1")
        shooter.team_id = 1
        shooter.position = (0, 50)
        enemy = DummyAgent("p3")
        enemy.team_id = 2
        enemy.position = (15, 50)

        engine = _make_engine([shooter, enemy])
        shooter.position = (0, 50)
        enemy.position = (15, 50)
        engine.state.bullets.append(
            Bullet(13, 50, 1, 0, owner="p1", damage=50)
        )
        engine._check_collisions()
        assert enemy.health < 100


# ---------- 3. 子弹与障碍物碰撞 ----------

class TestBulletHitsObstacle:
    def test_bullet_hits_obstacle_disappears(self):
        shooter = DummyAgent("shooter")
        shooter.position = (0, 50)
        engine = _make_engine([shooter])
        shooter.position = (0, 50)
        engine.state.obstacles = [{"rect": (30, 40, 10, 20)}]
        # bullet 起点在墙里，update() 不动它，但 check_collisions 会撞墙
        engine.state.bullets.append(
            Bullet(32, 50, 1, 0, owner="shooter", damage=10)
        )
        engine._check_collisions()
        assert engine.state.bullets == []

    def test_bullet_passes_obstacle_gap(self):
        shooter = DummyAgent("shooter")
        shooter.position = (0, 50)
        engine = _make_engine([shooter])
        shooter.position = (0, 50)
        engine.state.obstacles = [{"rect": (30, 0, 10, 20)}]  # 上方墙
        # bullet 在 y=50（墙在 y=0-20），且 x 也不在墙里
        engine.state.bullets.append(
            Bullet(20, 50, 1, 0, owner="shooter", damage=10)
        )
        engine._check_collisions()
        assert len(engine.state.bullets) == 1


# ---------- 4. 火箭弹溅射伤害 ----------

class TestRocketSplashDamage:
    def _setup_rocket(self, splash=8.0, damage=20):
        shooter = DummyAgent("shooter")
        shooter.position = (0, 50)
        near = DummyAgent("near")
        near.position = (35, 50)  # 距爆心 2
        mid = DummyAgent("mid")
        mid.position = (38, 50)  # 距爆心 5
        far = DummyAgent("far")
        far.position = (50, 50)  # 距爆心 17 > splash
        engine = _make_engine([shooter, near, mid, far])
        shooter.position = (0, 50)
        near.position = (35, 50)
        mid.position = (38, 50)
        far.position = (50, 50)
        engine.state.bullets.append(
            Bullet(33, 50, 1, 0, owner="shooter",
                   damage=damage, splash_radius=splash)
        )
        return engine, shooter, near, mid, far

    def test_splash_hits_close_target(self):
        engine, shooter, near, mid, far = self._setup_rocket()
        engine._check_collisions()
        assert near.health < 100
        assert far.health == 100  # 距离 17 > splash=8

    def test_splash_records_kills(self):
        engine, shooter, near, mid, far = self._setup_rocket(damage=200)
        engine._check_collisions()
        assert shooter.kills >= 1

    def test_splash_damage_decreases_with_distance(self):
        """近目标伤害 > 远目标伤害"""
        engine, shooter, near, mid, far = self._setup_rocket()
        engine._check_collisions()
        near_loss = 100 - near.health
        mid_loss = 100 - mid.health
        assert near_loss > mid_loss, \
            f"近目标伤害({near_loss}) 应 > 中距离伤害({mid_loss})"


# ---------- 5. 移动阻挡 ----------

class TestMoveBlockedByObstacle:
    def test_blocked_by_obstacle_inside(self):
        shooter = DummyAgent("shooter")
        engine = _make_engine([shooter])
        engine.state.obstacles = [{"rect": (55, 45, 10, 10)}]
        assert engine._blocked_by_obstacle((60, 50))

    def test_blocked_by_obstacle_outside(self):
        shooter = DummyAgent("shooter")
        engine = _make_engine([shooter])
        engine.state.obstacles = [{"rect": (55, 45, 10, 10)}]
        assert not engine._blocked_by_obstacle((40, 50))


# ---------- 6. 角色间分离 ----------

class TestAgentCollisionResolve:
    def test_two_agents_close_apart(self):
        a = DummyAgent("a")
        a.position = (50, 50)
        b = DummyAgent("b")
        b.position = (52, 50)
        engine = _make_engine([a, b])
        # 重新设置位置
        a.position = (50, 50)
        b.position = (52, 50)
        engine._resolve_agent_collisions()
        dist = math.sqrt((a.position[0]-b.position[0])**2 + (a.position[1]-b.position[1])**2)
        assert dist >= 5.0, f"agents too close after resolve: dist={dist}"

    def test_two_agents_far_apart_unchanged(self):
        a = DummyAgent("a")
        a.position = (10, 10)
        b = DummyAgent("b")
        b.position = (80, 80)
        engine = _make_engine([a, b])
        a.position = (10, 10)
        b.position = (80, 80)
        before_a = a.position
        before_b = b.position
        engine._resolve_agent_collisions()
        assert a.position == before_a
        assert b.position == before_b
