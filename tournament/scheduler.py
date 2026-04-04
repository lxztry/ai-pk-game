"""
赛程生成器
为每日赛事生成比赛安排
"""
import random
import math
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict


class MatchScheduler:
    """赛程生成器"""
    
    def __init__(self, participants: List[Dict[str, Any]], 
                 matches_per_day: int = 5,
                 players_per_match: int = 4):
        """
        初始化赛程生成器
        
        Args:
            participants: 选手列表
            matches_per_day: 每个选手每天比赛场数
            players_per_match: 每场比赛参赛人数
        """
        self.participants = participants
        self.matches_per_day = matches_per_day
        self.players_per_match = players_per_match
        
        # 按积分分组
        self._group_by_points()
    
    def _group_by_points(self):
        """按积分将选手分组"""
        self.participants_by_tier = defaultdict(list)
        for p in self.participants:
            tier = min(p.get('stats', {}).get('total_points', 0) // 30, 10)
            self.participants_by_tier[tier].append(p['id'])
    
    def generate_daily_schedule(self, date: str = None) -> List[Dict[str, Any]]:
        """
        生成每日赛程
        
        Args:
            date: 日期字符串，默认为今天
            
        Returns:
            赛程列表，每项包含比赛信息和参赛选手
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        schedule = []
        match_index = 1
        
        # 确保每个选手都有足够的比赛
        player_match_count = {p['id']: 0 for p in self.participants}
        
        # 计算总场次
        total_matches = (len(self.participants) * self.matches_per_day) // self.players_per_match
        
        for _ in range(total_matches):
            # 选择参赛选手
            selected = self._select_players_for_match(player_match_count)
            
            if selected and len(selected) == self.players_per_match:
                schedule.append({
                    'date': date,
                    'match_index': match_index,
                    'players': selected,
                    'status': 'pending'
                })
                match_index += 1
                
                # 更新计数器
                for pid in selected:
                    player_match_count[pid] += 1
        
        return schedule
    
    def _select_players_for_match(self, player_match_count: Dict[str, int]) -> List[str]:
        """为一场比赛选择选手"""
        available = []
        
        for p in self.participants:
            pid = p['id']
            if player_match_count[pid] < self.matches_per_day:
                available.append(pid)
        
        if len(available) < self.players_per_match:
            available = list(player_match_count.keys())
        
        # 同积分段匹配策略
        if available:
            # 优先选择积分接近的选手
            candidates = available[:]
            selected = [candidates.pop(random.randrange(len(candidates)))]
            
            while len(selected) < self.players_per_match and candidates:
                # 找与已选选手积分最接近的
                ref_points = self._get_avg_points(selected)
                candidates.sort(key=lambda x: abs(self._get_points(x) - ref_points))
                
                # 从接近的候选中随机选
                top_candidates = candidates[:min(3, len(candidates))]
                chosen = random.choice(top_candidates)
                selected.append(chosen)
                candidates.remove(chosen)
            
            return selected
        
        return []
    
    def _get_points(self, participant_id: str) -> int:
        """获取选手积分"""
        for p in self.participants:
            if p['id'] == participant_id:
                return p.get('stats', {}).get('total_points', 0)
        return 0
    
    def _get_avg_points(self, participant_ids: List[str]) -> float:
        """计算选手列表的平均积分"""
        if not participant_ids:
            return 0
        total = sum(self._get_points(pid) for pid in participant_ids)
        return total / len(participant_ids)
    
    def generate_knockout_schedule(self, participants: List[str], date: str = None) -> List[Dict[str, Any]]:
        """
        生成淘汰赛赛程
        
        Args:
            participants: 参赛选手ID列表
            date: 日期
            
        Returns:
            淘汰赛对阵表
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        schedule = []
        match_index = 1
        
        # 填充到2的幂
        n = len(participants)
        if n < 2:
            return schedule
        
        # 凑成2的幂
        next_power = 2 ** math.ceil(math.log2(n))
        bye_count = next_power - n
        
        # 随机打乱顺序
        random.shuffle(participants)
        
        # 生成首轮对阵
        current_round = []
        i = 0
        
        # 添加首轮比赛
        while i + 1 < len(participants):
            if bye_count > 0 and random.random() < bye_count / (len(participants) - i):
                # 轮空
                current_round.append({
                    'date': date,
                    'match_index': match_index,
                    'players': [participants[i]],
                    'winner_advances': True,
                    'status': 'bye'
                })
                bye_count -= 1
                match_index += 1
            else:
                current_round.append({
                    'date': date,
                    'match_index': match_index,
                    'players': [participants[i], participants[i + 1]],
                    'status': 'pending'
                })
                match_index += 1
            i += 2
        
        # 如果还有剩余单人
        if i < len(participants):
            current_round.append({
                'date': date,
                'match_index': match_index,
                'players': [participants[i]],
                'status': 'bye'
            })
        
        schedule.extend(current_round)
        return schedule
    
    def generate_round_robin_schedule(self, participants: List[str], 
                                      date: str = None) -> List[Dict[str, Any]]:
        """
        生成循环赛赛程（每个选手都要与其他所有选手对战）
        
        Args:
            participants: 参赛选手ID列表
            date: 日期
            
        Returns:
            循环赛对阵表
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        schedule = []
        match_index = 1
        
        n = len(participants)
        
        # 循环赛：每个选手与其他所有选手对战
        for i in range(n):
            for j in range(i + 1, n):
                # 4人赛需要凑齐4人，这里简化处理
                # 实际应该分组或允许2人对战
                if self.players_per_match == 2:
                    schedule.append({
                        'date': date,
                        'match_index': match_index,
                        'players': [participants[i], participants[j]],
                        'status': 'pending'
                    })
                    match_index += 1
                else:
                    # 对于4人赛，随机选择其他2人
                    others = [p for k, p in enumerate(participants) if k != i and k != j]
                    if len(others) >= 2:
                        extra = random.sample(others, 2)
                        schedule.append({
                            'date': date,
                            'match_index': match_index,
                            'players': [participants[i], participants[j]] + extra,
                            'status': 'pending'
                        })
                        match_index += 1
        
        return schedule
    
    def save_schedule(self, schedule: List[Dict[str, Any]], filepath: str):
        """保存赛程到文件"""
        import json
        from pathlib import Path
        
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(schedule, f, ensure_ascii=False, indent=2)
    
    def load_schedule(self, filepath: str) -> List[Dict[str, Any]]:
        """从文件加载赛程"""
        import json
        from pathlib import Path
        
        path = Path(filepath)
        if not path.exists():
            return []
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)


# 使用示例
if __name__ == "__main__":
    # 模拟选手数据
    sample_participants = [
        {'id': 'player1', 'type': 'ai', 'stats': {'total_points': 45}},
        {'id': 'player2', 'type': 'ai', 'stats': {'total_points': 38}},
        {'id': 'player3', 'type': 'human', 'stats': {'total_points': 30}},
        {'id': 'player4', 'type': 'ai', 'stats': {'total_points': 25}},
        {'id': 'player5', 'type': 'ai', 'stats': {'total_points': 20}},
        {'id': 'player6', 'type': 'human', 'stats': {'total_points': 15}},
        {'id': 'player7', 'type': 'ai', 'stats': {'total_points': 10}},
        {'id': 'player8', 'type': 'ai', 'stats': {'total_points': 5}},
    ]
    
    scheduler = MatchScheduler(sample_participants, matches_per_day=3)
    schedule = scheduler.generate_daily_schedule()
    
    print(f"生成了 {len(schedule)} 场比赛:")
    for match in schedule[:5]:
        print(f"  #{match['match_index']}: {match['players']}")
