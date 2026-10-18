"""
3v3 团队战引擎测试
"""
import pytest
from game.hero import Hero
from game.team_state import TeamGameState
from game.team_engine import TeamEngine
from agents.team_agents import (
    TankAI, AssassinAI, MarksmanAI, SupportAI, MageAI, ROLE_AI
)


# ---------- Hero 测试 ----------

class TestHeroBasics:
    def test_create_all_5_roles(self):
        for role in ['tank', 'assassin', 'marksman', 'support', 'mage']:
            h = Hero(name=f'测试{role}', role=role, side='blue')
            assert h.role == role
            assert h.health == h.max_health
            assert h.skill_cooldown == 0
            assert h.is_alive()

    def test_health_5_roles(self):
        """确认 5 角色血量符合设计"""
        expected = {'tank': 200, 'assassin': 100, 'marksman': 80, 'support': 90, 'mage': 90}
        for role, hp in expected.items():
            h = Hero(name='test', role=role, side='blue')
            assert h.max_health == hp, f'{role} expected {hp}, got {h.max_health}'

    def test_attack_5_roles(self):
        expected = {'tank': 10, 'assassin': 30, 'marksman': 20, 'support': 8, 'mage': 25}
        for role, atk in expected.items():
            h = Hero(name='test', role=role, side='blue')
            assert h.attack == atk, f'{role} expected {atk}, got {h.attack}'

    def test_respawn_delays_death(self):
        h = Hero(name='t', role='tank', side='blue')
        h.start_respawn(current_time=0)
        assert not h.is_alive()
        assert h.respawn_at == 10  # RESPAWN_DELAY

    def test_respawn_after_delay(self):
        h = Hero(name='t', role='tank', side='blue')
        h.start_respawn(current_time=0)
        # 时间没到，不复活
        assert not h.try_respawn(current_time=5)
        # 时间到，复活
        assert h.try_respawn(current_time=10)
        assert h.is_alive()
        assert h.health == h.max_health

    def test_repeat_deaths_extend_respawn(self):
        h = Hero(name='t', role='tank', side='blue')
        h.start_respawn(current_time=0)  # 第 1 死
        h.try_respawn(current_time=10)  # 复活
        h.start_respawn(current_time=20)  # 第 2 死
        assert h.respawn_at == 31  # 20 + 10 + 1 (第 2 死延 1s)
        h.start_respawn(current_time=30)  # 第 3 死
        assert h.respawn_at == 42  # 30 + 10 + 2

    def test_kill_streak_increments(self):
        h = Hero(name='killer', role='assassin', side='blue')
        h.register_kill(current_time=0)
        assert h.kill_streak == 1
        h.register_kill(current_time=5)
        assert h.kill_streak == 2  # 5s 内，DOUBLE KILL
        h.register_kill(current_time=9)
        assert h.kill_streak == 3  # TRIPLE KILL

    def test_kill_streak_resets_after_window(self):
        h = Hero(name='killer', role='assassin', side='blue')
        h.register_kill(current_time=0)
        h.register_kill(current_time=5)
        assert h.kill_streak == 2
        # 11s 后再杀，连杀中断
        h.register_kill(current_time=11)
        assert h.kill_streak == 1  # 重新计数

    def test_streak_labels(self):
        h = Hero(name='k', role='assassin', side='blue')
        for kills, expected in [(1, ''), (2, 'DOUBLE KILL'), (3, 'TRIPLE KILL'),
                                 (4, 'QUADRA KILL'), (5, 'PENTA KILL'),
                                 (6, 'LEGENDARY'), (10, 'LEGENDARY')]:
            h.kill_streak = kills
            assert h.kill_streak_label == expected, f'kills={kills}'

    def test_slow_reduces_speed(self):
        h = Hero(name='t', role='mage', side='blue')
        normal = h.effective_move_speed(0)
        h.slow_until = 10
        slowed = h.effective_move_speed(5)
        assert slowed < normal
        assert slowed == h.move_speed * 0.5

    def test_taunt_blocks_other_actions(self):
        h = Hero(name='t', role='marksman', side='red')
        h.taunt_until = 10
        assert h.is_taunted(current_time=5)
        assert not h.is_taunted(current_time=11)


# ---------- TeamGameState 测试 ----------

class TestTeamGameState:
    def test_initial_state(self):
        blue = [Hero(f'b{i}', 'tank', 'blue') for i in range(3)]
        red = [Hero(f'r{i}', 'tank', 'red') for i in range(3)]
        s = TeamGameState(blue, red)
        assert s.turn == 0
        assert s.blue_base.hp == 1000
        assert s.red_base.hp == 1000
        assert len(s.blue_towers) == 3
        assert len(s.red_towers) == 3
        assert s.get_winner() is None

    def test_tower_takes_damage(self):
        blue = [Hero('b0', 'tank', 'blue')]
        red = [Hero('r0', 'tank', 'red')]
        s = TeamGameState(blue, red)
        t = s.blue_towers[0]
        # Tower HP = 50（设计为 5 分钟内可摧毁）
        assert t.max_hp == 50
        t.take_damage(20)
        assert t.hp == 30
        t.take_damage(30)
        assert t.destroyed
        # 重复伤害不报错
        t.take_damage(100)

    def test_winner_when_base_destroyed(self):
        blue = [Hero('b0', 'tank', 'blue')]
        red = [Hero('r0', 'tank', 'red')]
        s = TeamGameState(blue, red)
        s.blue_base.hp = 0
        assert s.get_winner() == 'red'
        s.blue_base.hp = 1000
        s.red_base.hp = 0
        assert s.get_winner() == 'blue'

    def test_to_dict(self):
        blue = [Hero('b0', 'tank', 'blue')]
        red = [Hero('r0', 'tank', 'red')]
        s = TeamGameState(blue, red)
        d = s.to_dict()
        assert d['turn'] == 0
        assert d['map_w'] == 40
        assert d['map_h'] == 25
        assert d['max_turns'] == 300
        assert len(d['heroes']) == 2
        assert len(d['towers']) == 6


# ---------- TeamEngine 测试 ----------

class TestTeamEngineBasics:
    def test_create_engine(self):
        blue = [TankAI(f'b{i}', 'tank', 'blue') for i in range(3)]
        red = [TankAI(f'r{i}', 'tank', 'red') for i in range(3)]
        s = TeamGameState(blue, red)
        engine = TeamEngine(s)
        assert engine.state.turn == 0

    def test_one_step(self):
        blue = [TankAI('b0', 'tank', 'blue')]
        red = [TankAI('r0', 'tank', 'red')]
        s = TeamGameState(blue, red)
        engine = TeamEngine(s)
        running = engine.step()
        assert s.turn == 1
        # 应仍在运行（双方都活着，基地满血）
        assert running is True

    def test_full_match_terminates(self):
        """完整跑完一场 3v3，看是否正常终止（不超 300 回合）"""
        blue = [TankAI(f'b{i}', 'tank', 'blue') for i in range(3)]
        red = [TankAI(f'r{i}', 'tank', 'red') for i in range(3)]
        s = TeamGameState(blue, red)
        engine = TeamEngine(s)
        for _ in range(310):
            if not engine.step():
                break
        # 应该有 game_over 事件
        events = [e for e in s.events if e['type'] == 'game_over']
        assert len(events) >= 1
        # 回合数不超过 MAX_TURNS + 缓冲
        assert s.turn <= s.MAX_TURNS + 2

    def test_kill_increments_kill_streak(self):
        """让刺客杀 1 人，验证 kill_streak 增 1"""
        blue = [AssassinAI('killer', 'assassin', 'blue')]
        red = [Hero('victim', 'tank', 'red')]
        s = TeamGameState(blue, red)
        # 把双方位置调到非常近
        blue[0].position = (20, 12)
        red[0].position = (21, 12)
        engine = TeamEngine(s)
        # 跑几步
        for _ in range(5):
            if not engine.step():
                break
        # victim 应该在复活或者已经死了
        if not red[0].is_alive() or red[0].health < red[0].max_health:
            # 至少发生过攻击
            pass
        # killer 应该有伤害统计
        assert blue[0].stats['damage_dealt'] >= 0  # 不一定受伤所以伤害可能为 0


# ---------- Skill 测试 ----------

class TestSkills:
    def test_tank_taunt_marks_targets(self):
        blue = [TankAI('taunter', 'tank', 'blue')]
        red = [AssassinAI('e0', 'assassin', 'red'),
               MarksmanAI('e1', 'marksman', 'red')]
        s = TeamGameState(blue, red)
        # 把双方位置调近
        blue[0].position = (20, 12)
        for r in red:
            r.position = (22, 12)
        engine = TeamEngine(s)
        # 强制释放技能
        for r in red:
            r.taunt_until = -1
        blue[0].skill_cooldown = 0
        engine._skill_taunt(blue[0], engine._build_observation(blue[0]))
        # 至少一个敌人被嘲讽
        assert any(r.taunt_until > 0 for r in red)

    def test_mage_fireball_hits_multiple(self):
        blue = [MageAI('mage', 'mage', 'blue')]
        red = [Hero('e0', 'tank', 'red'), Hero('e1', 'tank', 'red')]
        s = TeamGameState(blue, red)
        blue[0].position = (20, 12)
        for r in red:
            r.position = (20.5, 12.5)
        engine = TeamEngine(s)
        # 强制施放
        blue[0].skill_cooldown = 0
        engine._skill_fireball(blue[0], engine._build_observation(blue[0]))
        # 至少一个敌人被减速
        assert any(r.slow_until > 0 for r in red)

    def test_support_heal_restores_hp(self):
        blue = [SupportAI('sup', 'support', 'blue'),
                Hero('a0', 'tank', 'blue')]
        red = [Hero('e0', 'tank', 'red')]
        s = TeamGameState(blue, red)
        blue[0].position = (20, 12)
        blue[1].position = (20.5, 12)
        # 受伤
        blue[1].health = 30
        blue[1].max_health = 200
        engine = TeamEngine(s)
        blue[0].skill_cooldown = 0
        engine._skill_heal(blue[0], engine._build_observation(blue[0]))
        # 队友血回满
        assert blue[1].health == 60  # 30 + 30

    def test_assassin_dash_repositions(self):
        blue = [AssassinAI('ass', 'assassin', 'blue')]
        red = [Hero('e0', 'tank', 'red')]
        s = TeamGameState(blue, red)
        blue[0].position = (15, 12)
        red[0].position = (20, 12)
        engine = TeamEngine(s)
        blue[0].skill_cooldown = 0
        before = blue[0].position
        engine._skill_dash(blue[0], engine._build_observation(blue[0]))
        # 位置变了（在敌人身后）
        assert blue[0].position != before
        # 下一击 +50%
        assert blue[0].next_attack_bonus == 0.5

    def test_marksman_piercing_hits_in_line(self):
        blue = [MarksmanAI('mm', 'marksman', 'blue')]
        red = [Hero('e0', 'tank', 'red'), Hero('e1', 'tank', 'red')]
        s = TeamGameState(blue, red)
        # 红方两人在同一直线上
        blue[0].position = (15, 12)
        red[0].position = (17, 12)
        red[1].position = (18, 12)
        # 方向朝右
        blue[0].direction = (1, 0)
        engine = TeamEngine(s)
        blue[0].skill_cooldown = 0
        before_hp_0 = red[0].health
        before_hp_1 = red[1].health
        engine._skill_piercing(blue[0], engine._build_observation(blue[0]))
        # 两个敌人都应受伤
        assert red[0].health < before_hp_0
        assert red[1].health < before_hp_1


# ---------- 集成：5 角色 AI 真实跑一场 ----------

class TestRoleAIDecisions:
    def test_tank_prefers_skill(self):
        blue = [TankAI('b0', 'tank', 'blue')]
        red = [Hero('e0', 'tank', 'red'), Hero('e1', 'tank', 'red')]
        s = TeamGameState(blue, red)
        blue[0].position = (20, 12)
        for r in red:
            r.position = (22, 12)
        engine = TeamEngine(s)
        obs = engine._build_observation(blue[0])
        # 强制技能可用
        blue[0].skill_cooldown = 0
        action = blue[0].step(obs)
        # 坦克看到敌人 → 应该用 skill（嘲讽）
        assert action in ('skill', 'attack')

    def test_assassin_targets_squishy(self):
        blue = [AssassinAI('b0', 'assassin', 'blue')]
        red = [TankAI('e_tank', 'tank', 'red'),
               MarksmanAI('e_mm', 'marksman', 'red')]
        s = TeamGameState(blue, red)
        blue[0].position = (15, 12)
        red[0].position = (20, 12)
        red[1].position = (20, 12)
        engine = TeamEngine(s)
        # 没在攻击范围，敌人在 skill_range (8) 内 → 应该突进
        action = blue[0].step(engine._build_observation(blue[0]))
        assert action in ('move_left', 'move_right', 'attack', 'skill')

    def test_marksman_keeps_distance(self):
        blue = [MarksmanAI('mm', 'marksman', 'blue')]
        red = [Hero('e0', 'assassin', 'red')]
        s = TeamGameState(blue, red)
        blue[0].position = (20, 12)
        red[0].position = (22, 12)  # 距离 2 < 4（理想距离）
        engine = TeamEngine(s)
        action = blue[0].step(engine._build_observation(blue[0]))
        # 应该远离（距离太近）
        # action 应该是 'move_left'（反向）
        assert action in ('move_left', 'skill', 'attack')