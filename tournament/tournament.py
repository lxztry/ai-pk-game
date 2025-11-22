"""
比赛系统实现（支持回放）
"""
import random
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from game.engine import GameEngine
from game.agent import Agent
from visualizer.web_visualizer import WebVisualizer


class Tournament:
    """比赛基类（支持回放）"""
    
    def __init__(self, agents: List[Agent], map_width: int = 100, map_height: int = 100,
                 save_replay: bool = True, replay_dir: str = "replays", max_turns: int = 2000):
        self.agents = agents
        self.map_width = map_width
        self.map_height = map_height
        self.save_replay = save_replay
        self.replay_dir = Path(replay_dir)
        self.replay_dir.mkdir(exist_ok=True)
        self.max_turns = max_turns
        
        self.results: Dict[str, Dict[str, int]] = {}  # {agent_name: {wins: X, losses: Y, kills: Z}}
        self.match_replays: List[Dict] = []  # 存储每场比赛的回放数据
        
        # 初始化结果记录
        for agent in agents:
            self.results[agent.name] = {
                'wins': 0,
                'losses': 0,
                'kills': 0,
                'deaths': 0,
                'points': 0
            }
    
    def play_match(self, agents: List[Agent], match_name: str = "", verbose: bool = False) -> Optional[Agent]:
        """进行一场比赛并记录回放"""
        # 重置所有Agent状态
        for agent in agents:
            agent.reset()
        
        # 创建可视化器（如果需要保存回放）
        visualizer = None
        if self.save_replay:
            visualizer = WebVisualizer(self.map_width, self.map_height)
        
        # 创建游戏引擎
        engine = GameEngine(agents, self.map_width, self.map_height)
        
        # 运行游戏并记录
        frame_interval = 2  # 每2回合记录一帧
        winner = None
        while engine.state.turn < self.max_turns:
            state_info = engine.step()
            
            # 记录帧
            if self.save_replay and visualizer:
                if engine.state.turn % frame_interval == 0:
                    visualizer.record_frame(state_info)
            
            # 检查是否有获胜者
            winner = engine.state.get_winner()
            if winner:
                # 记录最后几帧
                if self.save_replay and visualizer:
                    for _ in range(10):
                        state_info = engine.step()
                        visualizer.record_frame(state_info)
                break
        
        # 超时后按评分判定获胜者（如果还没有）
        if winner is None:
            winner = engine.state.get_winner()
        
        # 更新统计
        for agent in agents:
            stats = self.results[agent.name]
            stats['kills'] += agent.kills
            stats['deaths'] += agent.deaths
            
            if winner and agent == winner:
                stats['wins'] += 1
                stats['points'] += 3
            else:
                stats['losses'] += 1
        
        # 保存回放
        if self.save_replay and visualizer and visualizer.replay_data:
            replay_info = {
                'match_name': match_name,
                'agents': [a.name for a in agents],
                'winner': winner.name if winner else None,
                'visualizer': visualizer
            }
            self.match_replays.append(replay_info)
        
        return winner
    
    def get_rankings(self) -> List[Tuple[str, Dict[str, int]]]:
        """获取排名"""
        rankings = sorted(
            self.results.items(),
            key=lambda x: (x[1]['points'], x[1]['wins'], x[1]['kills'] - x[1]['deaths']),
            reverse=True
        )
        return rankings
    
    def print_results(self):
        """打印比赛结果"""
        rankings = self.get_rankings()
        print("\n" + "="*80)
        print("比赛结果")
        print("="*80)
        print(f"{'排名':<6} {'名称':<20} {'胜场':<8} {'负场':<8} {'击杀':<8} {'死亡':<8} {'积分':<8}")
        print("-"*80)
        
        for rank, (name, stats) in enumerate(rankings, 1):
            print(f"{rank:<6} {name:<20} {stats['wins']:<8} {stats['losses']:<8} "
                  f"{stats['kills']:<8} {stats['deaths']:<8} {stats['points']:<8}")
        print("="*80)
    
    def save_all_replays(self):
        """保存所有比赛的回放文件"""
        if not self.save_replay or not self.match_replays:
            return
        
        print(f"\n正在保存 {len(self.match_replays)} 场比赛的回放...")
        
        saved_files = []
        for i, replay_info in enumerate(self.match_replays, 1):
            visualizer = replay_info['visualizer']
            match_name = replay_info['match_name'] or f"match_{i}"
            
            # 生成文件名（清理特殊字符）
            safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in match_name)
            # 如果文件名太长，截断
            if len(safe_name) > 50:
                safe_name = safe_name[:50]
            filename = f"{safe_name}_{i}.html"
            filepath = self.replay_dir / filename
            
            # 生成HTML文件
            html_file = visualizer.generate_html(str(filepath), auto_play=True, fps=15)
            saved_files.append(html_file)
            
            if i <= 10 or i % 10 == 0:  # 只显示前10个和每10个
                print(f"  [{i}/{len(self.match_replays)}] 已保存: {html_file}")
        
        print(f"\n所有回放文件已保存到: {self.replay_dir.absolute()}")
        return saved_files


class RoundRobinTournament(Tournament):
    """循环赛 - 每个Agent与其他所有Agent对战"""
    
    def run(self, verbose: bool = False):
        """运行循环赛"""
        print(f"\n开始循环赛，共 {len(self.agents)} 名参赛者")
        print(f"将进行 {len(self.agents) * (len(self.agents) - 1) // 2} 场比赛\n")
        
        match_count = 0
        total_matches = len(self.agents) * (len(self.agents) - 1) // 2
        
        for i in range(len(self.agents)):
            for j in range(i + 1, len(self.agents)):
                match_count += 1
                agent1 = self.agents[i]
                agent2 = self.agents[j]
                
                if verbose:
                    print(f"\n比赛 {match_count}/{total_matches}: {agent1.name} vs {agent2.name}")
                
                winner = self.play_match([agent1, agent2], verbose=verbose)
                
                if verbose and winner:
                    print(f"获胜者: {winner.name}")
                elif verbose:
                    print("平局（超时）")
        
        self.print_results()
        
        # 保存所有回放
        if self.save_replay:
            self.save_all_replays()
        
        return self.get_rankings()


class EliminationTournament(Tournament):
    """淘汰赛 - 单败淘汰制"""
    
    def run(self, verbose: bool = False):
        """运行淘汰赛"""
        print(f"\n开始淘汰赛，共 {len(self.agents)} 名参赛者\n")
        
        # 随机打乱顺序
        participants = self.agents.copy()
        random.shuffle(participants)
        
        round_num = 1
        
        while len(participants) > 1:
            print(f"\n{'='*60}")
            print(f"第 {round_num} 轮，剩余 {len(participants)} 名参赛者")
            print(f"{'='*60}\n")
            
            next_round = []
            
            # 两两对战
            match_num = 0
            for i in range(0, len(participants), 2):
                if i + 1 < len(participants):
                    agent1 = participants[i]
                    agent2 = participants[i + 1]
                    match_num += 1
                    match_name = f"Round{round_num}_Match{match_num}_{agent1.name}_vs_{agent2.name}"
                    
                    if verbose:
                        print(f"{agent1.name} vs {agent2.name}")
                    
                    winner = self.play_match([agent1, agent2], match_name=match_name, verbose=verbose)
                    
                    if winner:
                        next_round.append(winner)
                        if verbose:
                            print(f"→ {winner.name} 晋级\n")
                    else:
                        # 平局时随机选择
                        winner = random.choice([agent1, agent2])
                        next_round.append(winner)
                        if verbose:
                            print(f"→ {winner.name} 晋级（平局随机选择）\n")
                else:
                    # 奇数个参赛者，轮空
                    next_round.append(participants[i])
                    if verbose:
                        print(f"{participants[i].name} 轮空晋级\n")
            
            participants = next_round
            round_num += 1
        
        champion = participants[0]
        print(f"\n{'='*60}")
        print(f"冠军: {champion.name}")
        print(f"{'='*60}\n")
        
        self.print_results()
        
        # 保存所有回放
        if self.save_replay:
            self.save_all_replays()
        
        return champion

