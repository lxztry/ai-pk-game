"""
碰撞系统测试：子弹不穿墙 + agent 不穿墙 + dodge 闪避动作
"""
import pytest
from tests.fixtures.agents import DummyAgent


class TestBulletWallCollision:
    """子弹撞墙：单帧跨过薄墙也要能检测"""

    def _engine_with_wall(self, agents, wall_rect):
        from game.engine import GameEngine, Bullet
        e = GameEngine(agents, 100, 100)
        # 清掉默认障碍
        e.state.obstacles = [{'rect': wall_rect}]
        return e

    def test_bullet_terminates_at_wall_when_endpoint_inside(self):
        from game.engine import GameEngine
        a = DummyAgent("s"); a.direction = (1, 0)
        engine = GameEngine([a], 100, 100)
        a.position = (10, 50)
        engine.state.obstacles = [{'rect': (35, 20, 10, 60)}]
        from game.engine import Bullet
        b = Bullet(33, 50, 1, 0, owner="s", damage=10, speed=3.0)
        engine.state.bullets.append(b)
        b.update(100, 100)  # 子弹到 (36, 50)
        engine._check_collisions()
        assert len(engine.state.bullets) == 0

    def test_bullet_cant_tunnel_thin_wall(self):
        """关键测试：子弹速度 > 墙厚度时，线段扫描要能命中"""
        from game.engine import GameEngine
        a = DummyAgent("s"); a.direction = (1, 0)
        engine = GameEngine([a], 100, 100)
        a.position = (10, 50)
        engine.state.obstacles = [{'rect': (35, 30, 3, 40)}]
        from game.engine import Bullet
        b = Bullet(32, 50, 1, 0, owner="s", damage=10, speed=3.0)
        b.prev_x, b.prev_y = 32, 50
        engine.state.bullets.append(b)
        b.update(100, 100)
        engine._check_collisions()
        assert len(engine.state.bullets) == 0, \
            "子弹穿过薄墙！线段-矩形碰撞检测失败"

    def test_bullet_tunnel_without_segment_scan_would_fail(self):
        """确认现有修复真的有效：起点在墙内的情况"""
        from game.engine import GameEngine
        a = DummyAgent("s"); a.direction = (1, 0)
        engine = GameEngine([a], 100, 100)
        a.position = (10, 50)
        engine.state.obstacles = [{'rect': (20, 30, 5, 40)}]
        from game.engine import Bullet
        b = Bullet(22, 50, 1, 0, owner="s", damage=10, speed=5.0)
        b.prev_x, b.prev_y = 22, 50
        engine.state.bullets.append(b)
        b.update(100, 100)
        engine._check_collisions()
        assert len(engine.state.bullets) == 0


class TestSegmentRectIntersect:
    """Liang-Barsky 线段-矩形裁剪算法"""

    def test_segment_passes_through_rectangle(self):
        from game.engine import GameEngine
        # 线段 (0,0) → (10,0) 穿过矩形 (4, -1, 3, 2)
        hit = GameEngine._segment_rect_intersect(0, 0, 10, 0, 4, -1, 7, 1)
        assert hit is not None
        # 应该在线段起点端相交
        assert hit[0] >= 3.5 and hit[0] <= 4.5

    def test_segment_misses_rectangle(self):
        from game.engine import GameEngine
        # 线段 (0,0) → (10, 10) 不穿过 (20, 0, 5, 5)
        hit = GameEngine._segment_rect_intersect(0, 0, 10, 10, 20, 0, 25, 5)
        assert hit is None

    def test_segment_starts_inside_rectangle(self):
        from game.engine import GameEngine
        # 线段 (5,5) → (15, 5) 起点 (5,5) 在矩形 (3, 3, 5, 5) 内
        hit = GameEngine._segment_rect_intersect(5, 5, 15, 5, 3, 3, 8, 8)
        # 起点在矩形内：算法应返回起点
        assert hit is not None

    def test_horizontal_bullet_hits_vertical_wall(self):
        """水平子弹撞垂直墙（实际游戏场景）"""
        from game.engine import GameEngine
        # 子弹从 (0,50) 飞到 (10, 50)，墙在 (5, 0, 1, 100)
        hit = GameEngine._segment_rect_intersect(0, 50, 10, 50, 5, 0, 6, 100)
        assert hit is not None
        assert hit[0] == pytest.approx(5, abs=0.01)


class TestDodgeAction:
    """闪避动作测试"""

    def _setup(self):
        from game.engine import GameEngine
        from tests.fixtures.agents import DummyAgent
        a = DummyAgent("s")
        engine = GameEngine([a], 100, 100)
        # 初始化后设方向和位置（覆盖随机值）
        a.position = (50, 50)
        a.direction = (1, 0)
        return engine, a

    def test_dodge_left_moves_perpendicular(self):
        engine, a = self._setup()
        engine._execute_action(a, "dodge_left")
        # 朝向 (1, 0) → dodge_left perp = (0, 1) → (50, 54)
        assert a.position == (50, 54)
        assert getattr(a, 'is_dodging', False)

    def test_dodge_right_moves_perpendicular(self):
        engine, a = self._setup()
        engine._execute_action(a, "dodge_right")
        # 朝向 (1, 0) → dodge_right perp = (0, -1) → (50, 46)
        assert a.position == (50, 46)

    def test_dodge_faster_than_normal_move(self):
        engine, a = self._setup()
        before = a.position
        engine._execute_action(a, "dodge_left")
        distance = abs(a.position[0] - before[0]) + abs(a.position[1] - before[1])
        assert distance == pytest.approx(4.0, abs=0.1)

    def test_dodge_blocked_by_wall(self):
        from game.engine import GameEngine
        from tests.fixtures.agents import DummyAgent
        a = DummyAgent("s")
        engine = GameEngine([a], 100, 100)
        a.position = (50, 50)
        a.direction = (1, 0)
        # 墙在 dodge_left 路径上（(50, 54) 周围）
        engine.state.obstacles = [{'rect': (45, 52, 10, 4)}]
        engine._execute_action(a, "dodge_left")
        # 滑动碰撞：可能滑动到 x 方向但 y 不动
        assert a.position != (50, 54)

    def test_dodge_action_accepted(self):
        engine, a = self._setup()
        engine._execute_action(a, "dodge_left")
        engine._execute_action(a, "dodge_right")


class TestAgentMovementNoWallTunnel:
    """Agent 不穿墙（已有滑动碰撞保护）"""

    def test_move_into_wall_blocked(self):
        from game.engine import GameEngine
        from tests.fixtures.agents import DummyAgent
        a = DummyAgent("s")
        engine = GameEngine([a], 100, 100)
        a.position = (50, 50)
        a.direction = (1, 0)
        engine.state.obstacles = [{'rect': (52, 48, 5, 4)}]
        engine._execute_action(a, "move_right")
        # 应该被阻止或滑动（但不能移到 (52, 50) 中心）
        assert a.position[0] <= 51

    def test_move_slides_along_wall(self):
        """朝墙走会被滑到墙边沿方向（简化版）"""
        from game.engine import GameEngine
        from tests.fixtures.agents import DummyAgent
        a = DummyAgent("s")
        engine = GameEngine([a], 100, 100)
        # a 朝右走 8 次，应接近墙边 (x≈48)
        a.position = (30, 50)
        a.direction = (1, 0)
        engine.state.obstacles = [{'rect': (52, 0, 3, 100)}]
        for _ in range(8):
            engine._execute_action(a, "move_right")
        # 30 + 8*2 = 46，但墙 (52,0,3,100) 在 x=52，挡 x>48 的移动
        # a 应停在 x≈46-48
        assert a.position[0] >= 45 and a.position[0] <= 48, \
            f"应在墙边 x=45-48, 实际 {a.position}"