"""
数据库管理模块
使用SQLite存储玩家信息、对战记录、积分排名
"""
import sqlite3
import json
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from contextlib import contextmanager


class Database:
    """数据库管理类"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 默认使用项目根目录下的 online/rankings.db
            from pathlib import Path
            project_root = Path(__file__).parent.parent
            self.db_path = project_root / "online" / "rankings.db"
        else:
            self.db_path = Path(db_path)
            if not self.db_path.is_absolute():
                # 如果是相对路径，基于项目根目录
                project_root = Path(__file__).parent.parent
                self.db_path = project_root / self.db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    @contextmanager
    def _get_connection(self, timeout: float = 5.0):
        """获取数据库连接的上下文管理器，自动处理连接关闭"""
        conn = None
        retries = 3
        for attempt in range(retries):
            try:
                conn = sqlite3.connect(
                    str(self.db_path),
                    timeout=timeout,
                    check_same_thread=False  # 允许多线程访问
                )
                # 设置WAL模式以提高并发性能
                conn.execute("PRAGMA journal_mode=WAL")
                yield conn
                conn.commit()
                break
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower() and attempt < retries - 1:
                    time.sleep(0.1 * (attempt + 1))  # 指数退避
                    if conn:
                        try:
                            conn.close()
                        except:
                            pass
                    continue
                raise
            finally:
                if conn:
                    try:
                        conn.close()
                    except:
                        pass
    
    def _init_database(self):
        """初始化数据库表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 玩家表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    agent_path TEXT NOT NULL,
                    points INTEGER DEFAULT 0,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    kills INTEGER DEFAULT 0,
                    deaths INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 对战记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player1_name TEXT NOT NULL,
                    player2_name TEXT NOT NULL,
                    winner_name TEXT,
                    player1_kills INTEGER DEFAULT 0,
                    player2_kills INTEGER DEFAULT 0,
                    player1_health INTEGER DEFAULT 0,
                    player2_health INTEGER DEFAULT 0,
                    replay_file TEXT,
                    match_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (player1_name) REFERENCES players(name),
                    FOREIGN KEY (player2_name) REFERENCES players(name)
                )
            """)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_players_points ON players(points DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date DESC)")
    
    def add_player(self, name: str, agent_path: str) -> bool:
        """添加玩家"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO players (name, agent_path) 
                    VALUES (?, ?)
                """, (name, agent_path))
            return True
        except sqlite3.IntegrityError:
            return False  # 玩家已存在
    
    def get_player(self, name: str) -> Optional[Dict]:
        """获取玩家信息"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM players WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None
    
    def get_all_players(self) -> List[Dict]:
        """获取所有玩家列表"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM players ORDER BY points DESC, wins DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_rankings(self, limit: int = 100) -> List[Dict]:
        """获取排名列表"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, points, wins, losses, kills, deaths,
                       (wins + losses) as total_matches
                FROM players 
                ORDER BY points DESC, wins DESC, (kills - deaths) DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def update_match_result(self, player1_name: str, player2_name: str, 
                           winner_name: Optional[str],
                           player1_kills: int, player2_kills: int,
                           player1_health: int, player2_health: int,
                           replay_file: Optional[str] = None):
        """更新对战结果"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 插入对战记录
            cursor.execute("""
                INSERT INTO matches 
                (player1_name, player2_name, winner_name, 
                 player1_kills, player2_kills, player1_health, player2_health, replay_file)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (player1_name, player2_name, winner_name,
                  player1_kills, player2_kills, player1_health, player2_health, replay_file))
            
            # 更新玩家统计
            if winner_name == player1_name:
                # player1 获胜
                cursor.execute("""
                    UPDATE players 
                    SET points = points + 3, wins = wins + 1, 
                        kills = kills + ?, deaths = deaths + ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE name = ?
                """, (player1_kills, player2_kills, player1_name))
                
                cursor.execute("""
                    UPDATE players 
                    SET losses = losses + 1,
                        kills = kills + ?, deaths = deaths + ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE name = ?
                """, (player2_kills, player1_kills, player2_name))
            elif winner_name == player2_name:
                # player2 获胜
                cursor.execute("""
                    UPDATE players 
                    SET points = points + 3, wins = wins + 1,
                        kills = kills + ?, deaths = deaths + ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE name = ?
                """, (player2_kills, player1_kills, player2_name))
                
                cursor.execute("""
                    UPDATE players 
                    SET losses = losses + 1,
                        kills = kills + ?, deaths = deaths + ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE name = ?
                """, (player1_kills, player2_kills, player1_name))
            else:
                # 平局（超时）
                cursor.execute("""
                    UPDATE players 
                    SET kills = kills + ?, deaths = deaths + ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE name = ?
                """, (player1_kills, player2_kills, player1_name))
                
                cursor.execute("""
                    UPDATE players 
                    SET kills = kills + ?, deaths = deaths + ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE name = ?
                """, (player2_kills, player1_kills, player2_name))
    
    def get_match_history(self, player_name: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """获取对战历史"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if player_name:
                cursor.execute("""
                    SELECT * FROM matches 
                    WHERE player1_name = ? OR player2_name = ?
                    ORDER BY match_date DESC
                    LIMIT ?
                """, (player_name, player_name, limit))
            else:
                cursor.execute("""
                    SELECT * FROM matches 
                    ORDER BY match_date DESC
                    LIMIT ?
                """, (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_player_stats(self, name: str) -> Optional[Dict]:
        """获取玩家详细统计"""
        player = self.get_player(name)
        if not player:
            return None
        
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 获取最近对战记录
            cursor.execute("""
                SELECT * FROM matches 
                WHERE player1_name = ? OR player2_name = ?
                ORDER BY match_date DESC
                LIMIT 10
            """, (name, name))
            recent_matches = [dict(row) for row in cursor.fetchall()]
        
        return {
            **player,
            'recent_matches': recent_matches,
            'win_rate': player['wins'] / (player['wins'] + player['losses']) * 100 
                        if (player['wins'] + player['losses']) > 0 else 0
        }

