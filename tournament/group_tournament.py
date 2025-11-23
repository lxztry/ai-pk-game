"""
分组比赛系统 - 支持大规模参赛者
支持小组赛 + 淘汰赛的混合赛制
"""
import random
import math
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from game.engine import GameEngine
from game.agent import Agent
from tournament.tournament import Tournament
from visualizer.web_visualizer import WebVisualizer


class GroupTournament:
    """分组比赛系统 - 适合大规模参赛者（支持回放）"""
    
    def __init__(self, agents: List[Agent], 
                 group_size: int = 4,
                 advance_per_group: int = 2,
                 map_width: int = 100,
                 map_height: int = 100,
                 save_replay: bool = True,
                 replay_dir: str = "replays",
                 max_turns: int = 500):
        """
        初始化分组比赛
        
        Args:
            agents: 所有参赛Agent列表
            group_size: 每组大小（默认4人一组）
            advance_per_group: 每组出线人数（默认前2名）
            map_width: 地图宽度
            map_height: 地图高度
            save_replay: 是否保存回放
            replay_dir: 回放文件目录
            max_turns: 最大轮次（默认500）
        """
        self.agents = agents
        self.group_size = group_size
        self.advance_per_group = advance_per_group
        self.map_width = map_width
        self.map_height = map_height
        self.save_replay = save_replay
        self.replay_dir = Path(replay_dir)
        self.replay_dir.mkdir(exist_ok=True)
        self.max_turns = max_turns
        
        self.results: Dict[str, Dict[str, any]] = {}
        self.group_results: List[Dict] = []  # 小组赛结果
        self.final_results: List[Dict] = []  # 最终结果
        self.match_replays: List[Dict] = []  # 存储所有比赛的回放数据
        
        # 初始化结果记录
        for agent in agents:
            self.results[agent.name] = {
                'wins': 0,
                'losses': 0,
                'kills': 0,
                'deaths': 0,
                'points': 0,
                'group': None,
                'group_rank': None,
                'advanced': False,
                'final_rank': None
            }
    
    def create_groups(self, shuffle: bool = True) -> List[List[Agent]]:
        """
        创建分组
        
        Args:
            shuffle: 是否随机打乱
            
        Returns:
            分组列表，每个元素是一个Agent列表
        """
        agents = self.agents.copy()
        if shuffle:
            random.shuffle(agents)
        
        groups = []
        num_groups = math.ceil(len(agents) / self.group_size)
        
        for i in range(num_groups):
            start_idx = i * self.group_size
            end_idx = min(start_idx + self.group_size, len(agents))
            group = agents[start_idx:end_idx]
            groups.append(group)
            
            # 记录每个Agent所在的小组
            for agent in group:
                self.results[agent.name]['group'] = i + 1
        
        return groups
    
    def play_group_match(self, agents: List[Agent], group_num: int, match_name: str = "") -> Dict:
        """
        进行小组内的一场比赛并记录回放
        
        Args:
            agents: 参赛Agent列表（通常是2个）
            group_num: 小组编号
            match_name: 比赛名称
            
        Returns:
            比赛结果字典
        """
        # 重置Agent状态
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
        last_state_info = None  # 保存最后一帧的状态信息
        while engine.state.turn < self.max_turns:
            state_info = engine.step()
            last_state_info = state_info  # 保存最后一帧
            
            # 记录帧
            if self.save_replay and visualizer:
                if engine.state.turn % frame_interval == 0:
                    visualizer.record_frame(state_info)
            
            # 检查是否有获胜者（只允许在只剩一个存活者时判定）
            winner = engine.state.get_winner(allow_score_judge=False)
            if winner:
                # 记录最后几帧
                if self.save_replay and visualizer:
                    for _ in range(10):
                        state_info = engine.step()
                        visualizer.record_frame(state_info)
                break
        
        # 超时后按评分判定获胜者（如果还没有）
        if winner is None:
            # 确保记录最后一帧（如果还没有记录）
            if self.save_replay and visualizer and last_state_info:
                # 如果最后一帧的回合数不同，说明需要记录新帧
                if not visualizer.replay_data or visualizer.replay_data[-1]['turn'] != last_state_info['turn']:
                    visualizer.record_frame(last_state_info)
            
            winner = engine.state.get_winner(allow_score_judge=True)
            # 如果有获胜者，更新回放数据中的获胜者信息
            if winner and self.save_replay and visualizer:
                visualizer.set_winner(winner.name)
        
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
                'match_name': match_name or f"Group{group_num}_{agents[0].name}_vs_{agents[1].name}",
                'agents': [a.name for a in agents],
                'winner': winner.name if winner else None,
                'visualizer': visualizer
            }
            self.match_replays.append(replay_info)
        
        return {
            'group': group_num,
            'agents': [a.name for a in agents],
            'winner': winner.name if winner else None
        }
    
    def run_group_stage(self, groups: List[List[Agent]], verbose: bool = False) -> List[Agent]:
        """
        运行小组赛阶段
        
        Args:
            groups: 分组列表
            verbose: 是否显示详细信息
            
        Returns:
            出线的Agent列表
        """
        if verbose:
            print(f"\n{'='*80}")
            print(f"小组赛阶段 - 共 {len(groups)} 个小组")
            print(f"{'='*80}\n")
        
        advanced_agents = []
        
        for group_idx, group in enumerate(groups, 1):
            if verbose:
                print(f"\n小组 {group_idx} ({len(group)} 人): {', '.join([a.name for a in group])}")
            
            # 小组内循环赛
            group_tournament = Tournament(group, self.map_width, self.map_height,
                                         save_replay=self.save_replay, replay_dir=str(self.replay_dir),
                                         max_turns=self.max_turns)
            
            match_count = 0
            total_matches = len(group) * (len(group) - 1) // 2
            
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    match_count += 1
                    agent1 = group[i]
                    agent2 = group[j]
                    
                    match_name = f"Group{group_idx}_{agent1.name}_vs_{agent2.name}"
                    
                    if verbose and match_count % 10 == 0:
                        print(f"  进度: {match_count}/{total_matches}")
                    
                    group_tournament.play_match([agent1, agent2], match_name=match_name, verbose=False)
            
            # 收集小组赛的回放
            if self.save_replay:
                self.match_replays.extend(group_tournament.match_replays)
            
            # 获取小组排名
            rankings = group_tournament.get_rankings()
            group_result = {
                'group': group_idx,
                'rankings': rankings
            }
            self.group_results.append(group_result)
            
            # 选择出线Agent
            for rank, (name, stats) in enumerate(rankings[:self.advance_per_group], 1):
                self.results[name]['group_rank'] = rank
                self.results[name]['advanced'] = True
                # 找到对应的Agent对象
                for agent in group:
                    if agent.name == name:
                        advanced_agents.append(agent)
                        break
            
            if verbose:
                print(f"  出线: {', '.join([name for name, _ in rankings[:self.advance_per_group]])}")
        
        if verbose:
            print(f"\n小组赛完成！共 {len(advanced_agents)} 人出线")
        
        return advanced_agents
    
    def run_elimination_stage(self, agents: List[Agent], verbose: bool = False) -> Agent:
        """
        运行淘汰赛阶段
        
        Args:
            agents: 出线的Agent列表
            verbose: 是否显示详细信息
            
        Returns:
            冠军Agent
        """
        if verbose:
            print(f"\n{'='*80}")
            print(f"淘汰赛阶段 - 共 {len(agents)} 人")
            print(f"{'='*80}\n")
        
        participants = agents.copy()
        round_num = 1
        
        while len(participants) > 1:
            if verbose:
                print(f"\n第 {round_num} 轮，剩余 {len(participants)} 人")
            
            next_round = []
            
            # 两两对战
            match_num = 0
            for i in range(0, len(participants), 2):
                if i + 1 < len(participants):
                    agent1 = participants[i]
                    agent2 = participants[i + 1]
                    match_num += 1
                    match_name = f"Elimination_Round{round_num}_Match{match_num}_{agent1.name}_vs_{agent2.name}"
                    
                    if verbose:
                        print(f"  {agent1.name} vs {agent2.name}")
                    
                    # 重置状态
                    agent1.reset()
                    agent2.reset()
                    
                    # 创建可视化器（如果需要保存回放）
                    visualizer = None
                    if self.save_replay:
                        visualizer = WebVisualizer(self.map_width, self.map_height)
                    
                    # 创建游戏引擎
                    engine = GameEngine([agent1, agent2], self.map_width, self.map_height)
                    
                    # 运行游戏并记录
                    frame_interval = 2
                    winner = None
                    last_state_info = None  # 保存最后一帧的状态信息
                    while engine.state.turn < self.max_turns:
                        state_info = engine.step()
                        last_state_info = state_info  # 保存最后一帧
                        
                        if self.save_replay and visualizer:
                            if engine.state.turn % frame_interval == 0:
                                visualizer.record_frame(state_info)
                        
                        winner = engine.state.get_winner(allow_score_judge=False)
                        if winner:
                            if self.save_replay and visualizer:
                                for _ in range(10):
                                    state_info = engine.step()
                                    visualizer.record_frame(state_info)
                            break
                    
                    # 超时后按评分判定获胜者（如果还没有）
                    if winner is None:
                        # 确保记录最后一帧（如果还没有记录）
                        if self.save_replay and visualizer and last_state_info:
                            # 如果最后一帧的回合数不同，说明需要记录新帧
                            if not visualizer.replay_data or visualizer.replay_data[-1]['turn'] != last_state_info['turn']:
                                visualizer.record_frame(last_state_info)
                        
                        winner = engine.state.get_winner(allow_score_judge=True)
                        # 如果有获胜者，更新回放数据中的获胜者信息
                        if winner and self.save_replay and visualizer:
                            visualizer.set_winner(winner.name)
                    
                    # 保存回放
                    if self.save_replay and visualizer and visualizer.replay_data:
                        replay_info = {
                            'match_name': match_name,
                            'agents': [agent1.name, agent2.name],
                            'winner': winner.name if winner else None,
                            'visualizer': visualizer
                        }
                        self.match_replays.append(replay_info)
                    
                    if winner:
                        next_round.append(winner)
                        if verbose:
                            print(f"    → {winner.name} 晋级")
                    else:
                        # 平局时随机选择
                        winner = random.choice([agent1, agent2])
                        next_round.append(winner)
                        if verbose:
                            print(f"    → {winner.name} 晋级（平局）")
                else:
                    # 奇数个参赛者，轮空
                    next_round.append(participants[i])
                    if verbose:
                        print(f"  {participants[i].name} 轮空晋级")
            
            participants = next_round
            round_num += 1
        
        champion = participants[0]
        self.results[champion.name]['final_rank'] = 1
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"冠军: {champion.name}")
            print(f"{'='*80}")
        
        return champion
    
    def run(self, shuffle: bool = True, verbose: bool = False) -> Dict:
        """
        运行完整的分组比赛
        
        Args:
            shuffle: 是否随机分组
            verbose: 是否显示详细信息
            
        Returns:
            比赛结果字典
        """
        # 创建分组
        groups = self.create_groups(shuffle=shuffle)
        
        # 小组赛
        advanced_agents = self.run_group_stage(groups, verbose=verbose)
        
        # 淘汰赛
        champion = self.run_elimination_stage(advanced_agents, verbose=verbose)
        
        # 生成最终排名
        self._generate_final_rankings()
        
        # 保存所有回放
        if self.save_replay:
            self._save_all_replays()
        
        return {
            'champion': champion,
            'groups': len(groups),
            'advanced': len(advanced_agents),
            'results': self.results
        }
    
    def _save_all_replays(self):
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
            
            if i <= 10 or i % 50 == 0:  # 只显示前10个和每50个
                print(f"  [{i}/{len(self.match_replays)}] 已保存: {html_file}")
        
        print(f"\n所有回放文件已保存到: {self.replay_dir.absolute()}")
        return saved_files
    
    def _generate_final_rankings(self):
        """生成最终排名"""
        # 按积分、胜场、击杀数排序
        sorted_agents = sorted(
            self.results.items(),
            key=lambda x: (
                x[1]['final_rank'] if x[1]['final_rank'] else 999,
                x[1]['points'],
                x[1]['wins'],
                x[1]['kills'] - x[1]['deaths']
            )
        )
        
        self.final_results = sorted_agents
    
    def print_results(self):
        """打印比赛结果"""
        print("\n" + "="*80)
        print("最终排名")
        print("="*80)
        print(f"{'排名':<6} {'名称':<20} {'小组':<8} {'小组排名':<10} {'胜场':<8} {'击杀':<8} {'积分':<8}")
        print("-"*80)
        
        for rank, (name, stats) in enumerate(self.final_results[:20], 1):  # 只显示前20名
            group = stats['group'] if stats['group'] else '-'
            group_rank = stats['group_rank'] if stats['group_rank'] else '-'
            print(f"{rank:<6} {name:<20} {group:<8} {group_rank:<10} "
                  f"{stats['wins']:<8} {stats['kills']:<8} {stats['points']:<8}")
        
        if len(self.final_results) > 20:
            print(f"... (共 {len(self.final_results)} 名参赛者)")
        
        print("="*80)

