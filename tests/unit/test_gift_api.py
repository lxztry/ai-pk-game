"""
观众打赏 API 测试
"""
import sys
import json
import pytest


@pytest.fixture
def client():
    """Flask test client"""
    sys.path.insert(0, '.')
    from online.server import app
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


class TestGiftPost:
    def test_post_valid_gift(self, client):
        r = client.post('/api/duel/test123/gift',
                         json={'type': 'health', 'target': 'player1', 'user': 'tester'})
        assert r.status_code == 200
        data = r.get_json()
        assert data['ok'] is True
        assert data['gift']['type'] == 'health'
        assert data['gift']['target'] == 'player1'
        assert data['gift']['user'] == 'tester'
        assert data['used'] == 1
        assert data['remaining'] == 2

    def test_post_invalid_type(self, client):
        r = client.post('/api/duel/test123/gift',
                         json={'type': 'invalid_type', 'target': 'player1'})
        assert r.status_code == 400
        data = r.get_json()
        assert data['ok'] is False
        assert '无效' in data['error']

    def test_post_invalid_target(self, client):
        r = client.post('/api/duel/test123/gift',
                         json={'type': 'health', 'target': 'enemy'})
        assert r.status_code == 400
        data = r.get_json()
        assert data['ok'] is False
        assert 'player1 或 player2' in data['error']


class TestGiftRateLimit:
    def test_max_3_gifts_per_match(self, client):
        duel_id = 'rate_limit_test'
        # 发 3 个打赏
        for i in range(3):
            r = client.post(f'/api/duel/{duel_id}/gift',
                             json={'type': 'health', 'target': 'player1'})
            assert r.status_code == 200
        # 第 4 个应该被限流
        r = client.post(f'/api/duel/{duel_id}/gift',
                         json={'type': 'ammo', 'target': 'player2'})
        assert r.status_code == 429
        data = r.get_json()
        assert data['ok'] is False
        assert data['used'] == 3
        assert data['limit'] == 3


class TestGiftQuery:
    def test_get_gifts_empty(self, client):
        r = client.get('/api/duel/empty_match/gifts')
        assert r.status_code == 200
        data = r.get_json()
        assert data['ok'] is True
        assert data['count'] == 0
        assert data['gifts'] == []

    def test_get_gifts_after_post(self, client):
        duel_id = 'query_test'
        client.post(f'/api/duel/{duel_id}/gift',
                    json={'type': 'shield', 'target': 'player1', 'user': 'Alice'})
        client.post(f'/api/duel/{duel_id}/gift',
                    json={'type': 'boost', 'target': 'player2', 'user': 'Bob'})
        r = client.get(f'/api/duel/{duel_id}/gifts')
        data = r.get_json()
        assert data['count'] == 2
        assert data['gifts'][0]['user'] == 'Alice'
        assert data['gifts'][1]['user'] == 'Bob'

    def test_clear_gifts(self, client):
        duel_id = 'clear_test'
        client.post(f'/api/duel/{duel_id}/gift',
                    json={'type': 'health', 'target': 'player1'})
        r = client.delete(f'/api/duel/{duel_id}/gifts')
        assert r.status_code == 200
        r2 = client.get(f'/api/duel/{duel_id}/gifts')
        assert r2.get_json()['count'] == 0


class TestGiftApply:
    """测试打赏对 agent 状态的影响"""

    def test_health_gift_increases_health(self):
        from online.server import _apply_gift_to_agent
        from tests.fixtures.agents import DummyAgent
        a = DummyAgent('test')
        a.health = 30
        _apply_gift_to_agent(a, {'type': 'health', 'target': 'player1'})
        assert a.health == 60  # 30 + 30

    def test_health_gift_caps_at_100(self):
        from online.server import _apply_gift_to_agent
        from tests.fixtures.agents import DummyAgent
        a = DummyAgent('test')
        a.health = 90
        _apply_gift_to_agent(a, {'type': 'health', 'target': 'player1'})
        assert a.health == 100  # 不会超过 100

    def test_ammo_gift_increases_ammo(self):
        from online.server import _apply_gift_to_agent
        from tests.fixtures.agents import DummyAgent
        a = DummyAgent('test')
        a.ammo = {'shotgun': 5, 'sniper': 0, 'rocket': 0}
        _apply_gift_to_agent(a, {'type': 'ammo', 'target': 'player1'})
        assert a.ammo['shotgun'] == 20  # 5 + 15

    def test_slow_gift_adds_cooldown(self):
        from online.server import _apply_gift_to_agent
        from tests.fixtures.agents import DummyAgent
        a = DummyAgent('test')
        a.shoot_cooldown = 0
        _apply_gift_to_agent(a, {'type': 'slow', 'target': 'player1'})
        assert a.shoot_cooldown == 5

    def test_shield_gift_sets_shield(self):
        from online.server import _apply_gift_to_agent
        from tests.fixtures.agents import DummyAgent
        a = DummyAgent('test')
        _apply_gift_to_agent(a, {'type': 'shield', 'target': 'player1'})
        assert a.shield_turns == 10

    def test_boost_gift_resets_cooldown(self):
        from online.server import _apply_gift_to_agent
        from tests.fixtures.agents import DummyAgent
        a = DummyAgent('test')
        a.shoot_cooldown = 8
        _apply_gift_to_agent(a, {'type': 'boost', 'target': 'player1'})
        assert a.shoot_cooldown == 0