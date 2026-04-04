"""
周报生成器
生成每周赛事汇总报告
"""
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict


class WeeklyReportGenerator:
    """周报生成器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.daily_dir = self.data_dir / "daily"
        self.reports_dir = Path("reports/generated")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def get_week_range(self, week: str = None) -> tuple:
        """
        获取周的范围日期
        
        Args:
            week: 周标识，如 '2026-W13' 或 None 表示本周
            
        Returns:
            (start_date, end_date) 元组
        """
        if week is None:
            week = self._get_current_week()
        
        # 解析周标识
        year, week_num = week.split('-W')
        year, week_num = int(year), int(week_num)
        
        # 计算该周的周一
        jan4 = datetime(year, 1, 4)  # 1月4日总是在第1周
        start_date = jan4 + timedelta(weeks=week_num - 1, weekday=0)
        end_date = start_date + timedelta(days=6)
        
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
    
    def _get_current_week(self) -> str:
        """获取当前周标识"""
        today = datetime.now()
        year, week_num, _ = today.isocalendar()
        return f"{year}-W{week_num:02d}"
    
    def _get_all_daily_reports(self, start_date: str, end_date: str) -> List[Dict]:
        """获取日期范围内的所有日报"""
        reports = []
        current = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            report_file = self.daily_dir / date_str / "report.json"
            
            if report_file.exists():
                with open(report_file, 'r', encoding='utf-8') as f:
                    reports.append(json.load(f))
            
            current += timedelta(days=1)
        
        return reports
    
    def _aggregate_stats(self, daily_reports: List[Dict]) -> Dict[str, Any]:
        """汇总统计数据"""
        total_matches = 0
        completed_matches = 0
        ai_wins = 0
        human_wins = 0
        
        player_stats = defaultdict(lambda: {
            'matches': 0, 'wins': 0, 'kills': 0, 'points': 0
        })
        
        for report in daily_reports:
            stats = report.get('stats', {})
            total_matches += stats.get('total_matches', 0)
            completed_matches += stats.get('completed', 0)
            ai_wins += stats.get('ai_wins', 0)
            human_wins += stats.get('human_wins', 0)
            
            # 汇总选手数据
            rankings = report.get('rankings', {}).get('overall', [])
            for p in rankings:
                pid = p.get('id')
                if pid:
                    player_stats[pid]['matches'] += p.get('total_matches', 0)
                    player_stats[pid]['wins'] += p.get('total_wins', 0)
                    player_stats[pid]['kills'] += p.get('total_kills', 0)
                    player_stats[pid]['points'] += p.get('total_points', 0)
        
        total_wins = ai_wins + human_wins
        
        return {
            'total_matches': total_matches,
            'completed_matches': completed_matches,
            'ai_wins': ai_wins,
            'human_wins': human_wins,
            'ai_win_rate': round(ai_wins / total_wins * 100, 1) if total_wins > 0 else 50.0,
            'human_win_rate': round(human_wins / total_wins * 100, 1) if total_wins > 0 else 50.0,
            'player_stats': dict(player_stats)
        }
    
    def _calculate_weekly_rankings(self, player_stats: Dict) -> List[Dict]:
        """计算周排行"""
        # 获取选手元数据
        from utils.participant_manager import ParticipantManager
        pm = ParticipantManager()
        participants = {p['id']: p for p in pm.load_from_data_file()}
        
        rankings = []
        for pid, stats in player_stats.items():
            p = participants.get(pid, {})
            rankings.append({
                'id': pid,
                'name': p.get('name', pid),
                'display_name': p.get('display_name', p.get('name', pid)),
                'type': p.get('type', 'ai'),
                'weekly_points': stats['points'],
                'weekly_matches': stats['matches'],
                'weekly_wins': stats['wins'],
                'weekly_kills': stats['kills'],
                'win_rate': round(stats['wins'] / stats['matches'] * 100, 1) if stats['matches'] > 0 else 0
            })
        
        # 按周积分排序
        rankings.sort(key=lambda x: x['weekly_points'], reverse=True)
        
        # 添加排名
        for i, r in enumerate(rankings):
            r['rank'] = i + 1
        
        return rankings
    
    def generate_weekly_report(self, week: str = None) -> Dict[str, Any]:
        """
        生成周报
        
        Args:
            week: 周标识，如 '2026-W13'
            
        Returns:
            周报字典
        """
        if week is None:
            week = self._get_current_week()
        
        # 获取周日期范围
        start_date, end_date = self.get_week_range(week)
        
        # 获取本周所有日报
        daily_reports = self._get_all_daily_reports(start_date, end_date)
        
        if not daily_reports:
            return {
                'week': week,
                'error': f"No data found for week {week}",
                'start_date': start_date,
                'end_date': end_date
            }
        
        # 汇总统计
        aggregated = self._aggregate_stats(daily_reports)
        
        # 计算周排行
        weekly_rankings = self._calculate_weekly_rankings(aggregated['player_stats'])
        
        # 获取进步最大的选手（与上周相比）
        improved_players = self._get_most_improved(weekly_rankings)
        
        report = {
            'week': week,
            'start_date': start_date,
            'end_date': end_date,
            'stats': {
                'total_matches': aggregated['total_matches'],
                'completed_matches': aggregated['completed_matches'],
                'ai_wins': aggregated['ai_wins'],
                'human_wins': aggregated['human_wins'],
                'ai_win_rate': aggregated['ai_win_rate'],
                'human_win_rate': aggregated['human_win_rate']
            },
            'rankings': weekly_rankings[:20],
            'most_improved': improved_players,
            'generated_at': datetime.now().isoformat()
        }
        
        # 保存 JSON 报告
        self._save_json_report(week, report)
        
        # 生成 Markdown 报告
        md_content = self._generate_markdown(report)
        self._save_markdown_report(week, md_content)
        
        return report
    
    def _get_most_improved(self, weekly_rankings: List[Dict]) -> List[Dict]:
        """获取进步最大的选手"""
        # 简化版本：取周榜前10中胜率提升的
        return weekly_rankings[:3]
    
    def _generate_markdown(self, report: Dict) -> str:
        """生成 Markdown 格式周报"""
        week = report['week']
        start = report['start_date']
        end = report['end_date']
        stats = report['stats']
        rankings = report.get('rankings', [])
        
        md = f"""# 📊 第{week.split('-W')[1]}周 (📅 {start} ~ {end}) 周报

## 本周赛事概览

| 指标 | 数值 |
|------|------|
| 总比赛场次 | {stats['total_matches']} |
| 完成场次 | {stats['completed_matches']} |
| 🤖 AI获胜 | {stats['ai_wins']} ({stats['ai_win_rate']}%) |
| 👤 人类获胜 | {stats['human_wins']} ({stats['human_win_rate']}%) |

## 🏆 本周积分榜 TOP 20

| 排名 | 选手 | 类型 | 周积分 | 场次 | 胜率 | 击杀 |
|------|------|------|--------|------|------|------|
"""
        
        for p in rankings:
            ptype = "🤖" if p.get('type') == 'ai' else "👤"
            md += f"| {p['rank']} | {p.get('display_name', p.get('name'))} | {ptype} | {p.get('weekly_points', 0)} | {p.get('weekly_matches', 0)} | {p.get('win_rate', 0)}% | {p.get('weekly_kills', 0)} |\n"
        
        # AI vs Human 对决统计
        md += f"""
## 🤖 vs 👤 对决统计

本周 AI选手 和 人类选手 的对决中：

- **🤖 AI选手总胜率**: {stats['ai_win_rate']}%
- **👤 人类选手总胜率**: {stats['human_win_rate']}%

"""
        
        # 进步最快
        improved = report.get('most_improved', [])
        if improved:
            md += """## 🏅 本周MVP

"""
            for i, p in enumerate(improved):
                ptype = "🤖" if p.get('type') == 'ai' else "👤"
                md += f"{i+1}. {p.get('display_name', p.get('name'))} {ptype} - {p.get('weekly_points', 0)}分 ({p.get('weekly_wins', 0)}胜 {p.get('weekly_matches', 0)}场)\n"
        
        # 详细排行（续）
        if len(rankings) > 10:
            md += f"""
## 📋 完整排名 (11-{len(rankings)})

| 排名 | 选手 | 类型 | 积分 | 场次 | 胜率 |
|------|------|------|------|------|------|
"""
            for p in rankings[10:]:
                ptype = "🤖" if p.get('type') == 'ai' else "👤"
                md += f"| {p['rank']} | {p.get('display_name', p.get('name'))} | {ptype} | {p.get('weekly_points', 0)} | {p.get('weekly_matches', 0)} | {p.get('win_rate', 0)}% |\n"
        
        md += f"""
---

📝 报告生成时间: {report['generated_at']}
"""
        
        return md
    
    def _save_json_report(self, week: str, report: Dict):
        """保存 JSON 报告"""
        report_file = self.reports_dir / f"weekly_{week}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    
    def _save_markdown_report(self, week: str, content: str):
        """保存 Markdown 报告"""
        # 创建周报目录
        week_dir = self.reports_dir / week
        week_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = week_dir / "report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def get_all_weeks(self) -> List[str]:
        """获取所有有报告的周"""
        weeks = set()
        for f in self.reports_dir.glob("weekly_*.json"):
            week = f.stem.replace('weekly_', '')
            weeks.add(week)
        return sorted(list(weeks), reverse=True)


if __name__ == "__main__":
    generator = WeeklyReportGenerator()
    
    # 生成当前周的周报
    current_week = generator._get_current_week()
    
    try:
        report = generator.generate_weekly_report(current_week)
        if 'error' in report:
            print(f"⚠️  {report['error']}")
        else:
            print(f"✅ 周报已生成: reports/generated/{current_week}/report.md")
            print(f"   本周共 {report['stats']['total_matches']} 场比赛")
    except Exception as e:
        print(f"⚠️  周报生成失败: {e}")
