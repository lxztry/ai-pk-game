"""
每日赛事运行脚本
自动执行每日比赛、积分更新、报告生成

使用方法:
    python run_daily_tournament.py              # 运行今日赛事
    python run_daily_tournament.py --date 2026-03-30  # 指定日期
    python run_daily_tournament.py --dry-run    # 模拟运行（不实际比赛）
"""
import argparse
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from game.engine import GameEngine
from utils.database import get_database
from utils.participant_manager import ParticipantManager
from tournament.scheduler import MatchScheduler
from tournament.ranking import RankingManager
from tournament.reporting import DailyReportGenerator


class DailyTournament:
    """每日赛事管理器"""
    
    def __init__(self, date: str = None, dry_run: bool = False):
        self.date = date or datetime.now().strftime('%Y-%m-%d')
        self.dry_run = dry_run
        self.results = []
        
        # 初始化组件
        self.db = get_database()
        self.participant_manager = ParticipantManager()
        self.scheduler = None
        self.ranking_manager = RankingManager()
        
        # 数据目录
        self.data_dir = Path("data")
        self.daily_dir = self.data_dir / "daily" / self.date
        self.replays_dir = self.data_dir / "matches" / self.date
        
    def run(self):
        """执行每日赛事"""
        print(f"\n{'='*60}")
        print(f"🏟️  AI竞技平台 每日赛事 - {self.date}")
        print(f"{'='*60}\n")
        
        if self.dry_run:
            print("⚠️  模拟模式：不执行实际比赛\n")
        
        # 1. 加载选手
        print("📋 步骤1: 加载选手...")
        participants = self.participant_manager.load_from_data_file()
        print(f"   已加载 {len(participants)} 名选手")
        
        # 2. 生成赛程
        print("\n📅 步骤2: 生成赛程...")
        self.scheduler = MatchScheduler(participants, matches_per_day=3)
        schedule = self.scheduler.generate_daily_schedule(self.date)
        print(f"   已生成 {len(schedule)} 场比赛")
        
        # 3. 运行比赛
        print("\n⚔️  步骤3: 运行比赛...")
        if not self.dry_run:
            self._run_matches(schedule, participants)
        else:
            # 模拟比赛结果
            for match in schedule:
                match['status'] = 'simulated'
                match['winner_id'] = match['players'][0]
                self.results.append(match)
        
        # 4. 更新积分
        print("\n📊 步骤4: 更新积分...")
        if not self.dry_run:
            self._update_rankings()
        
        # 5. 生成报告
        print("\n📝 步骤5: 生成报告...")
        report = self._generate_report(schedule)
        report_gen = DailyReportGenerator()
        report_gen.generate_report(self.date)
        
        # 6. 保存结果
        print("\n💾 步骤6: 保存结果...")
        self._save_results(schedule, report)
        
        print(f"\n{'='*60}")
        print(f"✅ 每日赛事完成！")
        print(f"   比赛场次: {len(schedule)}")
        print(f"   参赛选手: {len(participants)}")
        print(f"{'='*60}\n")
        
        return report
    
    def _run_matches(self, schedule: List[Dict], participants: List[Dict]):
        """运行所有比赛"""
        participant_map = {p['id']: p for p in participants}
        
        for i, match in enumerate(schedule):
            print(f"   比赛 {i+1}/{len(schedule)}: ", end="")
            
            player_ids = match['players']
            
            # 创建 Agent 实例
            try:
                agents = []
                for pid in player_ids:
                    agent = self.participant_manager.create_agent_instance(pid)
                    agents.append(agent)
                
                # 运行比赛
                engine = GameEngine(agents, map_width=100, map_height=100)
                winner = engine.run(max_turns=500)
                
                # 记录结果
                match['status'] = 'completed'
                match['winner_id'] = winner.name if winner else None
                
                # 更新数据库
                for agent in agents:
                    is_win = (winner and agent.name == winner.name)
                    points = 3 if is_win else 0
                    if is_win:
                        points += 1 if agent.kills > 3 else 0
                    
                    # 更新选手统计
                    self.db.update_participant_stats(
                        agent.name, 
                        points=points,
                        kills=agent.kills,
                        is_win=is_win
                    )
                    
                    # 记录积分历史
                    if points > 0:
                        self.db.record_point_history(
                            agent.name, 
                            self.date, 
                            points,
                            reason=f"match_win" if is_win else "participation"
                        )
                
                print(f"胜者: {match['winner_id']}")
                
            except Exception as e:
                print(f"错误: {e}")
                match['status'] = 'error'
                match['error'] = str(e)
            
            self.results.append(match)
    
    def _update_rankings(self):
        """更新排行榜"""
        self.ranking_manager.generate_daily_rankings(self.date)
        self.ranking_manager.generate_leaderboard_snapshot()
    
    def _generate_report(self, schedule: List[Dict]) -> Dict[str, Any]:
        """生成每日报告"""
        # 获取排行榜
        rankings = self.ranking_manager.get_latest_rankings()
        
        # 统计
        total_matches = len(schedule)
        completed = sum(1 for m in schedule if m['status'] == 'completed')
        errors = sum(1 for m in schedule if m['status'] == 'error')
        
        # AI vs Human 统计
        ai_vs_human = self.ranking_manager.get_ai_vs_human_stats()
        
        report = {
            'date': self.date,
            'summary': {
                'total_matches': total_matches,
                'completed': completed,
                'errors': errors
            },
            'top_players': rankings['overall'][:10] if rankings else [],
            'ai_vs_human': ai_vs_human,
            'generated_at': datetime.now().isoformat()
        }
        
        return report
    
    def _save_results(self, schedule: List[Dict], report: Dict[str, Any]):
        """保存结果到文件"""
        self.daily_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存赛程
        schedule_file = self.daily_dir / "schedule.json"
        with open(schedule_file, 'w', encoding='utf-8') as f:
            json.dump(schedule, f, ensure_ascii=False, indent=2)
        print(f"   赛程已保存: {schedule_file}")
        
        # 保存报告
        report_file = self.daily_dir / "report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"   报告已保存: {report_file}")
        
        # 生成 Markdown 报告
        md_report = self._generate_markdown_report(report, schedule)
        md_file = self.daily_dir / "report.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_report)
        print(f"   Markdown报告: {md_file}")
    
    def _generate_markdown_report(self, report: Dict, schedule: List[Dict]) -> str:
        """生成 Markdown 格式报告"""
        md = f"""# 📅 {self.date} 每日赛事报告

## 赛事概览

- **总比赛场次**: {report['summary']['total_matches']}
- **完成场次**: {report['summary']['completed']}
- **错误场次**: {report['summary']['errors']}

## 总积分榜 TOP 10

| 排名 | 选手 | 类型 | 积分 | 场次 | 胜率 |
|------|------|------|------|------|------|
"""
        
        for p in report.get('top_players', [])[:10]:
            ptype = "🤖" if p['type'] == 'ai' else "👤"
            md += f"| {p['rank']} | {p['display_name']} | {ptype} | {p['total_points']} | {p['total_matches']} | {p.get('win_rate', 0)}% |\n"
        
        md += f"""
## AI vs Human 对决

- 🤖 AI选手总胜率: {report['ai_vs_human'].get('ai_win_rate', 0)}%
- 👤 人类选手总胜率: {report['ai_vs_human'].get('human_win_rate', 0)}%

## 今日比赛记录

"""
        
        for match in schedule[:20]:
            players = ", ".join(match['players'])
            status = "✅" if match['status'] == 'completed' else "❌"
            winner = match.get('winner_id', 'N/A')
            md += f"- {status} #{match['match_index']}: {players} → 胜者: {winner}\n"
        
        if len(schedule) > 20:
            md += f"- ... 还有 {len(schedule) - 20} 场比赛\n"
        
        md += f"""
---
报告生成时间: {report['generated_at']}
"""
        
        return md


def main():
    parser = argparse.ArgumentParser(description='AI竞技平台 - 每日赛事')
    parser.add_argument('--date', type=str, help='指定日期 (YYYY-MM-DD)')
    parser.add_argument('--dry-run', action='store_true', help='模拟运行（不执行实际比赛）')
    
    args = parser.parse_args()
    
    tournament = DailyTournament(date=args.date, dry_run=args.dry_run)
    report = tournament.run()
    
    print("\n📊 报告预览:")
    print(f"   TOP 1: {report['top_players'][0]['display_name']} - {report['top_players'][0]['total_points']}分")


if __name__ == "__main__":
    main()
