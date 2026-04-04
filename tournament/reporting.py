"""
每日比赛报告生成器
生成详细的每日赛事报告
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class DailyReportGenerator:
    """每日报告生成器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.daily_dir = self.data_dir / "daily"
        self.reports_dir = Path("reports/generated")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(self, date: str) -> Dict[str, Any]:
        """
        生成指定日期的报告
        
        Args:
            date: 日期字符串 (YYYY-MM-DD)
            
        Returns:
            报告字典
        """
        # 加载赛程和结果
        schedule_file = self.daily_dir / date / "schedule.json"
        if not schedule_file.exists():
            return {"error": f"No schedule found for {date}"}
        
        with open(schedule_file, 'r', encoding='utf-8') as f:
            schedule = json.load(f)
        
        # 加载选手数据
        from utils.participant_manager import ParticipantManager
        pm = ParticipantManager()
        participants = {p['id']: p for p in pm.load_from_data_file()}
        
        # 生成统计
        stats = self._calculate_stats(schedule, participants)
        
        # 获取排行榜
        from tournament.ranking import RankingManager
        rm = RankingManager()
        rankings = rm.get_latest_rankings()
        
        report = {
            'date': date,
            'stats': stats,
            'matches': schedule,
            'rankings': rankings,
            'generated_at': datetime.now().isoformat()
        }
        
        # 保存 JSON 报告
        self._save_json_report(date, report)
        
        # 生成 Markdown 报告
        md_content = self._generate_markdown(report, participants)
        self._save_markdown_report(date, md_content)
        
        return report
    
    def _calculate_stats(self, schedule: List[Dict], participants: Dict) -> Dict[str, Any]:
        """计算统计数据"""
        total = len(schedule)
        completed = sum(1 for m in schedule if m.get('status') == 'completed')
        errors = sum(1 for m in schedule if m.get('status') == 'error')
        
        # AI vs Human 胜率
        ai_wins = 0
        human_wins = 0
        ai_matches = 0
        human_matches = 0
        
        for match in schedule:
            if match.get('status') != 'completed':
                continue
            winner_id = match.get('winner_id')
            if winner_id and winner_id in participants:
                winner_type = participants[winner_id].get('type', 'ai')
                if winner_type == 'ai':
                    ai_wins += 1
                else:
                    human_wins += 1
            
            # 统计参赛者类型
            for pid in match.get('players', []):
                if pid in participants:
                    ptype = participants[pid].get('type', 'ai')
                    if ptype == 'ai':
                        ai_matches += 1
                    else:
                        human_matches += 1
        
        total_wins = ai_wins + human_wins
        if total_wins > 0:
            ai_win_rate = round(ai_wins / total_wins * 100, 1)
            human_win_rate = round(human_wins / total_wins * 100, 1)
        else:
            ai_win_rate = human_win_rate = 50.0
        
        return {
            'total_matches': total,
            'completed': completed,
            'errors': errors,
            'ai_wins': ai_wins,
            'human_wins': human_wins,
            'ai_win_rate': ai_win_rate,
            'human_win_rate': human_win_rate
        }
    
    def _generate_markdown(self, report: Dict, participants: Dict) -> str:
        """生成 Markdown 格式报告"""
        date = report['date']
        stats = report['stats']
        matches = report['matches']
        rankings = report.get('rankings', {})
        
        md = f"""# 📅 {date} 每日赛事报告

## 赛事概览

| 指标 | 数值 |
|------|------|
| 总比赛场次 | {stats['total_matches']} |
| 完成场次 | {stats['completed']} |
| 错误场次 | {stats['errors']} |

## 🤖 vs 👤 对决统计

| 类型 | 胜场数 | 胜率 |
|------|--------|------|
| 🤖 AI选手 | {stats['ai_wins']} | {stats['ai_win_rate']}% |
| 👤 人类选手 | {stats['human_wins']} | {stats['human_win_rate']}% |

## 📊 总积分榜 TOP 10

| 排名 | 选手 | 类型 | 积分 | 场次 | 胜率 | 击杀 |
|------|------|------|------|------|------|------|
"""
        
        overall = rankings.get('overall', [])
        for p in overall[:10]:
            ptype = "🤖" if p.get('type') == 'ai' else "👤"
            md += f"| {p.get('rank', '-')} | {p.get('display_name', p.get('name', '-'))} | {ptype} | {p.get('total_points', 0)} | {p.get('total_matches', 0)} | {p.get('win_rate', 0)}% | {p.get('total_kills', 0)} |\n"
        
        md += f"""
## 🎮 今日比赛记录

"""
        
        # 按状态分组显示
        completed_matches = [m for m in matches if m.get('status') == 'completed']
        error_matches = [m for m in matches if m.get('status') == 'error']
        
        if completed_matches:
            md += f"### ✅ 完成 ({len(completed_matches)}场)\n\n"
            for match in completed_matches[:15]:
                winner = match.get('winner_id', 'N/A')
                players = " vs ".join(match.get('players', []))
                md += f"- #{match['match_index']:03d}: {players} → **胜者: {winner}**\n"
            
            if len(completed_matches) > 15:
                md += f"- ... 还有 {len(completed_matches) - 15} 场比赛\n"
        
        if error_matches:
            md += f"\n### ❌ 错误 ({len(error_matches)}场)\n\n"
            for match in error_matches:
                md += f"- #{match['match_index']:03d}: {' vs '.join(match.get('players', []))} - 错误: {match.get('error', 'Unknown')}\n"
        
        # AI 选手榜
        ai_ranking = rankings.get('ai_only', [])
        if ai_ranking:
            md += f"""
## 🤖 AI选手榜 TOP 5

| 排名 | 选手 | 积分 | 场次 | 胜率 |
|------|------|------|------|------|
"""
            for p in ai_ranking[:5]:
                md += f"| {p.get('rank', '-')} | {p.get('display_name', p.get('name', '-'))} | {p.get('total_points', 0)} | {p.get('total_matches', 0)} | {p.get('win_rate', 0)}% |\n"
        
        # 人类选手榜
        human_ranking = rankings.get('human_only', [])
        if human_ranking:
            md += f"""
## 👤 人类选手榜 TOP 5

| 排名 | 选手 | 积分 | 场次 | 胜率 |
|------|------|------|------|------|
"""
            for p in human_ranking[:5]:
                md += f"| {p.get('rank', '-')} | {p.get('display_name', p.get('name', '-'))} | {p.get('total_points', 0)} | {p.get('total_matches', 0)} | {p.get('win_rate', 0)}% |\n"
        
        md += f"""
---

📝 报告生成时间: {report['generated_at']}
"""
        
        return md
    
    def _save_json_report(self, date: str, report: Dict):
        """保存 JSON 报告"""
        report_file = self.reports_dir / f"daily_{date}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    
    def _save_markdown_report(self, date: str, content: str):
        """保存 Markdown 报告"""
        report_file = self.reports_dir / f"daily_{date}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def get_latest_reports(self, limit: int = 7) -> List[Dict]:
        """获取最近的报告列表"""
        reports = []
        for f in sorted(self.reports_dir.glob("daily_*.json"), reverse=True)[:limit]:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
                reports.append({
                    'date': data['date'],
                    'file': f.name,
                    'stats': data.get('stats', {})
                })
        return reports


if __name__ == "__main__":
    generator = DailyReportGenerator()
    
    # 尝试为今天生成报告
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    
    try:
        report = generator.generate_report(today)
        print(f"✅ 报告已生成: reports/generated/daily_{today}.md")
    except Exception as e:
        print(f"⚠️  报告生成失败: {e}")
        print("（这可能是因为今天还没有运行每日赛事）")
