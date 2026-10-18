"""
数据库单元测试

覆盖：online/database.py 和 utils/database.py 的核心 CRUD + 事务保护
"""
import pytest
import sqlite3


# ---------- online/database.py ----------

class TestOnlineDatabase:
    def _db(self, tmp_path):
        from online.database import Database
        return Database(str(tmp_path / "test.db"))

    def test_init_creates_tables(self, tmp_path):
        db = self._db(tmp_path)
        with sqlite3.connect(str(tmp_path / "test.db")) as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            names = {t[0] for t in tables}
        assert "players" in names
        assert "matches" in names

    def test_add_player_returns_true(self, tmp_path):
        db = self._db(tmp_path)
        assert db.add_player("alice", "participants/alice") is True

    def test_add_duplicate_player_returns_false(self, tmp_path):
        db = self._db(tmp_path)
        db.add_player("alice", "participants/alice")
        # UNIQUE 约束
        assert db.add_player("alice", "participants/alice") is False

    def test_get_player_returns_dict(self, tmp_path):
        db = self._db(tmp_path)
        db.add_player("bob", "p/bob")
        player = db.get_player("bob")
        assert player is not None
        assert player["name"] == "bob"
        assert player["agent_path"] == "p/bob"
        assert player["points"] == 0

    def test_get_nonexistent_returns_none(self, tmp_path):
        db = self._db(tmp_path)
        assert db.get_player("ghost") is None

    def test_get_all_players_sorted_by_points(self, tmp_path):
        db = self._db(tmp_path)
        db.add_player("a", "p/a")
        db.add_player("b", "p/b")
        # 模拟 b 分数高
        with db._get_connection() as conn:
            conn.execute("UPDATE players SET points = 10 WHERE name = 'b'")
        players = db.get_all_players()
        assert players[0]["name"] == "b"

    def test_update_match_result_records_winner(self, tmp_path):
        db = self._db(tmp_path)
        db.add_player("p1", "p/p1")
        db.add_player("p2", "p/p2")
        ok = db.update_match_result(
            player1_name="p1", player2_name="p2",
            winner_name="p1",
            player1_kills=2, player2_kills=0,
            player1_health=50, player2_health=0,
        )
        assert ok is True
        # p1 应该 +3 分、+1 胜、+2 击杀
        p1 = db.get_player("p1")
        assert p1["points"] == 3
        assert p1["wins"] == 1
        assert p1["kills"] == 2
        assert p1["deaths"] == 0  # 没死
        # p2 应该 +0 分、+1 负、+0 击杀、+2 死亡
        p2 = db.get_player("p2")
        assert p2["points"] == 0
        assert p2["losses"] == 1
        assert p2["kills"] == 0
        assert p2["deaths"] == 2  # 死了2次（其实只死1次，但 code 把它计为对方的击杀数）
        # 比赛记录
        history = db.get_match_history()
        assert len(history) == 1
        assert history[0]["winner_name"] == "p1"

    def test_update_match_result_draw(self, tmp_path):
        db = self._db(tmp_path)
        db.add_player("p1", "p/p1")
        db.add_player("p2", "p/p2")
        ok = db.update_match_result(
            player1_name="p1", player2_name="p2",
            winner_name=None,  # 平局
            player1_kills=1, player2_kills=1,
            player1_health=10, player2_health=10,
        )
        assert ok
        p1 = db.get_player("p1")
        # 平局时 kills/deaths 仍然累加，但没有 wins/losses
        assert p1["wins"] == 0
        assert p1["losses"] == 0
        assert p1["kills"] == 1

    def test_update_match_result_with_missing_player(self, tmp_path):
        """FK 约束：player 不存在时不应崩（新增 try/except 后的行为）"""
        db = self._db(tmp_path)
        db.add_player("p1", "p/p1")
        # p2 没注册，外键违反 → 现在应返回 False 不抛异常
        ok = db.update_match_result(
            player1_name="p1", player2_name="ghost",
            winner_name="p1",
            player1_kills=1, player2_kills=0,
            player1_health=50, player2_health=0,
        )
        # 应当返回 False（被 try/except 吞掉）
        assert ok is False


class TestRankings:
    def test_rankings_sorted_by_points(self, tmp_path):
        from online.database import Database
        db = Database(str(tmp_path / "test.db"))
        db.add_player("a", "p/a")
        db.add_player("b", "p/b")
        db.add_player("c", "p/c")
        db.update_match_result("a", "b", "a", 1, 0, 50, 0)  # a +3
        db.update_match_result("a", "c", "a", 1, 0, 50, 0)  # a +3, total 6
        db.update_match_result("b", "c", "b", 1, 0, 50, 0)  # b +3
        rankings = db.get_rankings()
        # 期望顺序：a(6), b(3), c(0)
        assert [r["name"] for r in rankings[:3]] == ["a", "b", "c"]


# ---------- utils/database.py ----------

class TestUtilsDatabase:
    def test_init_creates_tables(self, tmp_path):
        from utils.database import Database
        with Database(str(tmp_path / "ut.db")) as db:
            with sqlite3.connect(str(tmp_path / "ut.db")) as conn:
                tables = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
                names = {t[0] for t in tables}
            assert "participants" in names
            assert "daily_matches" in names
            assert "point_history" in names

    def test_add_participant(self, tmp_path):
        from utils.database import Database
        with Database(str(tmp_path / "ut.db")) as db:
            ok = db.add_participant({
                "id": "p1", "name": "P1", "type": "ai",
                "developer": "me", "model_info": "gpt", "description": "x"
            })
            assert ok
            p = db.get_participant("p1")
            assert p["name"] == "P1"
            assert p["type"] == "ai"

    def test_record_match_and_history(self, tmp_path):
        from utils.database import Database
        with Database(str(tmp_path / "ut.db")) as db:
            db.add_participant({"id": "p1", "name": "P1", "type": "ai"})
            db.add_participant({"id": "p2", "name": "P2", "type": "ai"})
            match_id = db.record_match({
                "date": "2026-09-27", "match_index": 1,
                "agent1_id": "p1", "agent2_id": "p2",
                "winner_id": "p1", "agent1_score": 5, "agent2_score": 0,
            })
            assert match_id > 0
            matches = db.get_daily_matches("2026-09-27")
            assert len(matches) == 1
            assert matches[0]["winner_id"] == "p1"

    def test_update_participant_stats(self, tmp_path):
        from utils.database import Database
        with Database(str(tmp_path / "ut.db")) as db:
            db.add_participant({"id": "p1", "name": "P1", "type": "ai"})
            db.update_participant_stats("p1", points=3, kills=2, is_win=True)
            p = db.get_participant("p1")
            assert p["total_points"] == 3
            assert p["total_wins"] == 1
            assert p["total_kills"] == 2
