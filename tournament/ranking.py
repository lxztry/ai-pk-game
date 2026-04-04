"""
排行榜生成器
生成各类积分排行榜
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict


class RankingManager:
    """排行榜管理器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.rankings_dir = self.data_dir / "rankings"
        self.rankings_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_daily_rankings(self, date: str = None) -> Dict[str, Any]:
        """
        生成每日排行榜
        
        Args:
            date: 日期字符串
            
        Returns:
            包含各类排行榜的字典
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        from utils.database import get_database
        db = get_database()
        
        # 获取所有选手
        all_participants = db.get_all_participants()
        
        # 计算排名
        rankings = {
            'date': date,
            'overall': self._calculate_rankings(all_participants),
            'ai_only': self._calculate_rankings(
                [p for p in all_participants if p['type'] == 'ai']
            ),
            'human_only': self._calculate_rankings(
                [p for p in all_participants if p['type'] == 'human']
            ),
            'generated_at': datetime.now().isoformat()
        }
        
        # 保存每日排行
        self._save_daily_ranking(date, rankings)
        
        return rankings
    
    def _calculate_rankings(self, participants: List[Dict]) -> List[Dict]:
        """计算排行榜"""
        # 按积分排序
        sorted_pts = sorted(participants, 
                           key=lambda p: p.get('total_points', 0), 
                           reverse=True)
        
        rankings = []
        for rank, p in enumerate(sorted_pts, 1):
            rankings.append({
                'rank': rank,
                'id': p['id'],
                'name': p.get('name', p['id']),
                'display_name': p.get('display_name', p['id']),
                'type': p.get('type', 'ai'),
                'total_points': p.get('total_points', 0),
                'total_matches': p.get('total_matches', 0),
                'total_wins': p.get('total_wins', 0),
                'total_kills': p.get('total_kills', 0),
                'total_deaths': p.get('total_deaths', 0),
                'win_rate': self._calc_win_rate(p),
                'developer_info': p.get('developer_info', '')
            })
        
        return rankings
    
    def _calc_win_rate(self, participant: Dict) -> float:
        """计算胜率"""
        matches = participant.get('total_matches', 0)
        if matches == 0:
            return 0.0
        wins = participant.get('total_wins', 0)
        return round(wins / matches * 100, 1)
    
    def _save_daily_ranking(self, date: str, rankings: Dict):
        """保存每日排行"""
        ranking_file = self.rankings_dir / "daily" / f"{date}.json"
        ranking_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(ranking_file, 'w', encoding='utf-8') as f:
            json.dump(rankings, f, ensure_ascii=False, indent=2)
    
    def get_latest_rankings(self) -> Optional[Dict]:
        """获取最新的排行榜"""
        daily_dir = self.rankings_dir / "daily"
        if not daily_dir.exists():
            return None
        
        # 找最新的文件
        files = list(daily_dir.glob("*.json"))
        if not files:
            return None
        
        latest = max(files, key=lambda f: f.stem)
        
        with open(latest, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def generate_weekly_rankings(self, week: str = None) -> List[Dict]:
        """
        生成周榜
        
        Args:
            week: 周标识，如 '2026-W13'
            
        Returns:
            周榜列表
        """
        if week is None:
            week = self._get_current_week()
        
        from utils.database import get_database
        db = get_database()
        
        # 获取本周数据
        rankings = db.get_weekly_ranking(week)
        
        if not rankings:
            # 如果没有本周数据，生成
            all_participants = db.get_all_participants()
            rankings = self._calculate_rankings(all_participants)
            
            # 保存到数据库
            db.save_weekly_ranking(week, rankings)
        
        return rankings
    
    def _get_current_week(self) -> str:
        """获取当前周标识"""
        today = datetime.now()
        year, week_num, _ = today.isocalendar()
        return f"{year}-W{week_num:02d}"
    
    def get_ai_vs_human_stats(self) -> Dict[str, Any]:
        """获取 AI vs Human 对战统计"""
        from utils.database import get_database
        db = get_database()
        
        all_participants = db.get_all_participants()
        ai_players = [p for p in all_participants if p['type'] == 'ai']
        human_players = [p for p in all_participants if p['type'] == 'human']
        
        # 简化计算：基于总积分
        ai_total = sum(p.get('total_points', 0) for p in ai_players)
        human_total = sum(p.get('total_points', 0) for p in human_players)
        total = ai_total + human_total
        
        if total == 0:
            return {
                'ai_win_rate': 50.0,
                'human_win_rate': 50.0,
                'total_matches': 0
            }
        
        return {
            'ai_win_rate': round(ai_total / total * 100, 1),
            'human_win_rate': round(human_total / total * 100, 1),
            'total_ai_participants': len(ai_players),
            'total_human_participants': len(human_players)
        }
    
    def generate_leaderboard_snapshot(self) -> Dict[str, Any]:
        """生成排行榜快照（用于网页展示）"""
        rankings = self.get_latest_rankings()
        
        if not rankings:
            rankings = self.generate_daily_rankings()
        
        ai_vs_human = self.get_ai_vs_human_stats()
        
        snapshot = {
            'updated_at': datetime.now().isoformat(),
            'overall': rankings['overall'][:20] if rankings else [],
            'ai_leaderboard': rankings.get('ai_only', [])[:10] if rankings else [],
            'human_leaderboard': rankings.get('human_only', [])[:10] if rankings else [],
            'ai_vs_human': ai_vs_human,
            'total_participants': len(rankings['overall']) if rankings else 0
        }
        
        # 保存快照
        snapshot_file = self.data_dir / "leaderboard.json"
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
        
        return snapshot


# 使用示例
if __name__ == "__main__":
    manager = RankingManager()
    snapshot = manager.generate_leaderboard_snapshot()
    
    print("=== 排行榜快照 ===")
    print(f"更新时间: {snapshot['updated_at']}")
    print(f"总选手数: {snapshot['total_participants']}")
    print(f"\n总榜 TOP 5:")
    for p in snapshot['overall'][:5]:
        print(f"  #{p['rank']} {p['display_name']} - {p['total_points']}分")
    
    print(f"\nAI vs Human:")
    print(f"  AI胜率: {snapshot['ai_vs_human']['ai_win_rate']}%")
    print(f"  人类胜率: {snapshot['ai_vs_human']['human_win_rate']}%")
