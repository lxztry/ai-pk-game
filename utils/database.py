"""
数据库管理模块 - SQLite
管理选手数据、比赛记录、积分历史
"""
import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime


class Database:
    """SQLite数据库管理器"""
    
    def __init__(self, db_path: str = "data/tournament.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """建立数据库连接"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
    
    def _create_tables(self):
        """创建所有表"""
        cursor = self.conn.cursor()
        
        # 选手表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS participants (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                display_name TEXT,
                type TEXT CHECK(type IN ('ai', 'human')) NOT NULL,
                developer_info TEXT,
                model_info TEXT,
                description TEXT,
                total_points INTEGER DEFAULT 0,
                total_matches INTEGER DEFAULT 0,
                total_wins INTEGER DEFAULT 0,
                total_kills INTEGER DEFAULT 0,
                total_deaths INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 每日比赛表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                match_index INTEGER NOT NULL,
                agent1_id TEXT,
                agent2_id TEXT,
                agent3_id TEXT,
                agent4_id TEXT,
                winner_id TEXT,
                agent1_score INTEGER DEFAULT 0,
                agent2_score INTEGER DEFAULT 0,
                agent3_score INTEGER DEFAULT 0,
                agent4_score INTEGER DEFAULT 0,
                replay_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent1_id) REFERENCES participants(id),
                FOREIGN KEY (agent2_id) REFERENCES participants(id),
                FOREIGN KEY (agent3_id) REFERENCES participants(id),
                FOREIGN KEY (agent4_id) REFERENCES participants(id),
                FOREIGN KEY (winner_id) REFERENCES participants(id)
            )
        """)
        
        # 积分变动表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS point_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id TEXT NOT NULL,
                date TEXT NOT NULL,
                points_earned INTEGER NOT NULL,
                match_id INTEGER,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (participant_id) REFERENCES participants(id),
                FOREIGN KEY (match_id) REFERENCES daily_matches(id)
            )
        """)
        
        # 周榜表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weekly_rankings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week TEXT NOT NULL,
                participant_id TEXT NOT NULL,
                rank INTEGER NOT NULL,
                points INTEGER DEFAULT 0,
                matches INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                kills INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (participant_id) REFERENCES participants(id),
                UNIQUE(week, participant_id)
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_date ON daily_matches(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_point_history_date ON point_history(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_weekly_rankings_week ON weekly_rankings(week)")
        
        self.conn.commit()
    
    def add_participant(self, participant: Dict[str, Any]) -> bool:
        """添加选手"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO participants 
                (id, name, display_name, type, developer_info, model_info, description, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                participant['id'],
                participant['name'],
                participant.get('display_name'),
                participant['type'],
                participant.get('developer'),
                participant.get('model_info'),
                participant.get('description'),
                datetime.now().isoformat()
            ))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error adding participant: {e}")
            return False
    
    def get_participant(self, participant_id: str) -> Optional[Dict]:
        """获取选手信息"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM participants WHERE id = ?", (participant_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_participants(self) -> List[Dict]:
        """获取所有选手"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM participants ORDER BY total_points DESC")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_participants_by_type(self, ptype: str) -> List[Dict]:
        """按类型获取选手"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM participants WHERE type = ? ORDER BY total_points DESC", (ptype,))
        return [dict(row) for row in cursor.fetchall()]
    
    def record_match(self, match_data: Dict[str, Any]) -> int:
        """记录比赛"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO daily_matches 
            (date, match_index, agent1_id, agent2_id, agent3_id, agent4_id, 
             winner_id, agent1_score, agent2_score, agent3_score, agent4_score, replay_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            match_data['date'],
            match_data['match_index'],
            match_data.get('agent1_id'),
            match_data.get('agent2_id'),
            match_data.get('agent3_id'),
            match_data.get('agent4_id'),
            match_data.get('winner_id'),
            match_data.get('agent1_score', 0),
            match_data.get('agent2_score', 0),
            match_data.get('agent3_score', 0),
            match_data.get('agent4_score', 0),
            match_data.get('replay_path')
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_participant_stats(self, participant_id: str, points: int = 0, 
                                  kills: int = 0, is_win: bool = False):
        """更新选手统计"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE participants SET
                total_points = total_points + ?,
                total_matches = total_matches + 1,
                total_wins = total_wins + ?,
                total_kills = total_kills + ?,
                updated_at = ?
            WHERE id = ?
        """, (points, 1 if is_win else 0, kills, datetime.now().isoformat(), participant_id))
        self.conn.commit()
    
    def record_point_history(self, participant_id: str, date: str, points: int, 
                            match_id: int = None, reason: str = ""):
        """记录积分变动历史"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO point_history (participant_id, date, points_earned, match_id, reason)
            VALUES (?, ?, ?, ?, ?)
        """, (participant_id, date, points, match_id, reason))
        self.conn.commit()
    
    def get_daily_matches(self, date: str) -> List[Dict]:
        """获取某日所有比赛"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM daily_matches WHERE date = ? ORDER BY match_index", (date,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_rankings(self, limit: int = 20) -> List[Dict]:
        """获取总积分榜"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT p.*, 
                   ROW_NUMBER() OVER (ORDER BY total_points DESC) as rank
            FROM participants p
            ORDER BY total_points DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_rankings_by_type(self, ptype: str, limit: int = 20) -> List[Dict]:
        """获取某类型选手积分榜"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT p.*,
                   ROW_NUMBER() OVER (ORDER BY total_points DESC) as rank
            FROM participants p
            WHERE p.type = ?
            ORDER BY total_points DESC
            LIMIT ?
        """, (ptype, limit))
        return [dict(row) for row in cursor.fetchall()]
    
    def save_weekly_ranking(self, week: str, rankings: List[Dict]):
        """保存周榜"""
        cursor = self.conn.cursor()
        for r in rankings:
            cursor.execute("""
                INSERT OR REPLACE INTO weekly_rankings 
                (week, participant_id, rank, points, matches, wins, kills)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (week, r['id'], r['rank'], r['total_points'], 
                  r.get('total_matches', 0), r.get('total_wins', 0), 
                  r.get('total_kills', 0)))
        self.conn.commit()
    
    def get_weekly_ranking(self, week: str) -> List[Dict]:
        """获取某周排行榜"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT w.*, p.name, p.display_name, p.type, p.developer_info
            FROM weekly_rankings w
            JOIN participants p ON w.participant_id = p.id
            WHERE w.week = ?
            ORDER BY w.rank
        """, (week,))
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 全局数据库实例
_db_instance: Optional[Database] = None

def get_database(db_path: str = "data/tournament.db") -> Database:
    """获取数据库单例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(db_path)
    return _db_instance
