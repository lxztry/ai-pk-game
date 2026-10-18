"""
武器 & 补给系统单元测试
"""
import pytest
from game.engine import GameEngine, GameState
from tests.fixtures.agents import DummyAgent


def _engine_with(agents, **kw):
    engine = GameEngine(agents, 100, 100)
    for k, v in kw.items():
        setattr(engine.state, k, v)
    return engine


class TestWeaponFire:
    """武器发射 + 冷却"""

    def test_normal_weapon_damage_10(self):
        shooter = DummyAgent("shooter")
        shooter.weapon = "normal"
        engine = _engine_with([shooter])
        shooter.position = (50, 50)
        shooter.direction = (1, 0)
        engine._fire_weapon(shooter)
        # 一颗子弹，伤害 10
        assert len(engine.state.bullets) == 1
        assert engine.state.bullets[0].damage == 10
        assert engine.state.bullets[0].kind == "normal"

    def test_normal_weapon_cooldown_3(self):
        """普通武器 cooldown 为 5（让节奏更清楚，方便看闪避动作）"""
        shooter = DummyAgent("shooter")
        engine = _engine_with([shooter])
        shooter.position = (50, 50)
        shooter.direction = (1, 0)
        engine._fire_weapon(shooter)
        assert shooter.shoot_cooldown == 5

    def test_shotgun_fires_three_bullets(self):
        shooter = DummyAgent("shooter")
        shooter.weapon = "shotgun"
        shooter.ammo["shotgun"] = 5
        engine = _engine_with([shooter])
        shooter.position = (50, 50)
        shooter.direction = (1, 0)
        engine._fire_weapon(shooter)
        # 三发散射
        assert len(engine.state.bullets) == 3
        for b in engine.state.bullets:
            assert b.kind == "shotgun"
            assert b.damage == 8
        assert shooter.ammo["shotgun"] == 4

    def test_sniper_one_high_damage_bullet(self):
        shooter = DummyAgent("shooter")
        shooter.weapon = "sniper"
        shooter.ammo["sniper"] = 3
        engine = _engine_with([shooter])
        shooter.position = (50, 50)
        shooter.direction = (1, 0)
        engine._fire_weapon(shooter)
        assert len(engine.state.bullets) == 1
        b = engine.state.bullets[0]
        assert b.kind == "sniper"
        assert b.damage == 25
        assert b.speed == 6.0
        assert shooter.ammo["sniper"] == 2

    def test_rocket_has_splash_radius(self):
        shooter = DummyAgent("shooter")
        shooter.weapon = "rocket"
        shooter.ammo["rocket"] = 2
        engine = _engine_with([shooter])
        shooter.position = (50, 50)
        shooter.direction = (1, 0)
        engine._fire_weapon(shooter)
        b = engine.state.bullets[0]
        assert b.kind == "rocket"
        assert b.splash_radius == 8.0
        assert shooter.ammo["rocket"] == 1

    def test_no_ammo_falls_back_to_normal(self):
        """特殊武器但没弹药时按普通射击"""
        shooter = DummyAgent("shooter")
        shooter.weapon = "sniper"
        shooter.ammo["sniper"] = 0  # 没弹药
        engine = _engine_with([shooter])
        shooter.position = (50, 50)
        shooter.direction = (1, 0)
        engine._fire_weapon(shooter)
        # 回退为普通子弹
        assert engine.state.bullets[0].kind == "normal"
        assert engine.state.bullets[0].damage == 10


class TestPickupSupply:
    """补给拾取"""

    def _setup(self, supply_type, supply_pos):
        agent = DummyAgent("p")
        agent.position = (50, 50)
        engine = _engine_with([agent], supplies=[{"position": supply_pos, "type": supply_type}])
        agent.position = (50, 50)
        return engine, agent

    def test_health_supply_caps_at_100(self):
        engine, agent = self._setup("health", (52, 50))
        agent.health = 90
        engine._check_pickups()
        assert agent.health == 100  # 90 + 25 = 115 → cap 100

    def test_health_supply_heals_25(self):
        engine, agent = self._setup("health", (52, 50))
        agent.health = 50
        engine._check_pickups()
        assert agent.health == 75

    def test_shotgun_ammo_pickup(self):
        engine, agent = self._setup("ammo_shotgun", (52, 50))
        engine._check_pickups()
        assert agent.ammo["shotgun"] == 5

    def test_sniper_ammo_pickup(self):
        engine, agent = self._setup("ammo_sniper", (52, 50))
        engine._check_pickups()
        assert agent.ammo["sniper"] == 3

    def test_rocket_ammo_pickup(self):
        engine, agent = self._setup("ammo_rocket", (52, 50))
        engine._check_pickups()
        assert agent.ammo["rocket"] == 2

    def test_weapon_shotgun_switches_weapon(self):
        engine, agent = self._setup("weapon_shotgun", (52, 50))
        engine._check_pickups()
        assert agent.weapon == "shotgun"

    def test_weapon_sniper_switches_weapon(self):
        engine, agent = self._setup("weapon_sniper", (52, 50))
        engine._check_pickups()
        assert agent.weapon == "sniper"

    def test_weapon_rocket_switches_weapon(self):
        engine, agent = self._setup("weapon_rocket", (52, 50))
        engine._check_pickups()
        assert agent.weapon == "rocket"

    def test_supply_pickup_removes_from_world(self):
        engine, agent = self._setup("health", (52, 50))
        assert len(engine.state.supplies) == 1
        engine._check_pickups()
        assert engine.state.supplies == []

    def test_supply_too_far_not_picked_up(self):
        engine, agent = self._setup("health", (60, 50))  # 距离 10 > 4
        engine._check_pickups()
        # 没拾到：supply 仍在 list 里
        assert len(engine.state.supplies) == 1
        assert agent.health == 100


class TestWeaponCooldownEnforced:
    """冷却期间不能再开火（move_shoot 会被引擎 ignore）"""

    def test_cooldown_blocks_fire_in_step(self):
        shooter = DummyAgent("shooter")
        engine = _engine_with([shooter])
        shooter.position = (50, 50)
        shooter.direction = (1, 0)
        engine._fire_weapon(shooter)
        first_count = len(engine.state.bullets)
        # 第二次开火：cooldown=19，应该被阻止（_fire_weapon 本身不查 cooldown）
        # 但 execute_action 里 shoot 才查 cooldown
        shooter.shoot_cooldown = 10
        engine._execute_action(shooter, "shoot")
        # step 里 _execute_action 看到 cooldown>0，跳过
        # 子弹数不变（只有第一发）
        assert len(engine.state.bullets) == first_count
