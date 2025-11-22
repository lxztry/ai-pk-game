"""
AI竞技平台 - 自动运行比赛（非交互式版本）
自动加载所有参赛者Agent并运行循环赛
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.agent_loader import AgentLoader
from agents.code_agent import RandomAgent, AggressiveAgent, DefensiveAgent, SmartAgent
from agents.prompt_agent import PromptAgent
from tournament.tournament import RoundRobinTournament, EliminationTournament
from tournament.group_tournament import GroupTournament


def create_default_agents():
    """创建默认的代码Agent（用于测试）"""
    return [
        AggressiveAgent("激进者"),
        DefensiveAgent("防御者"),
        SmartAgent("智者"),
        RandomAgent("随机者"),
    ]


def main():
    """主程序"""
    print("="*80)
    print(" " * 25 + "AI竞技平台 - 自动比赛")
    print("="*80)
    print()
    
    # 创建Agent列表
    agents = []
    
    # 自动加载参赛者Agent
    print("正在加载参赛者Agent...")
    print("-" * 80)
    loader = AgentLoader(participants_dir="participants")
    participant_agents = loader.create_agent_instances()
    agents.extend(participant_agents)
    print("-" * 80)
    
    # 如果没有加载到参赛者，使用默认Agent
    if len(agents) == 0:
        print("未找到参赛者Agent，使用默认Agent进行演示")
        agents = create_default_agents()
    
    if len(agents) < 2:
        print("错误: 至少需要2个Agent才能进行比赛")
        return
    
    print(f"\n共加载 {len(agents)} 个Agent:")
    for i, agent in enumerate(agents, 1):
        agent_type = agent.__class__.__name__
        print(f"  {i}. {agent.name} ({agent_type})")
    
    print("\n" + "="*80)
    print("开始循环赛（将自动生成回放）...")
    print("="*80)
    
    # 自动运行循环赛（默认启用回放）
    tournament = RoundRobinTournament(agents, save_replay=True, replay_dir="replays")
    tournament.run(verbose=True)
    
    print("\n" + "="*80)
    print("比赛完成！")
    print("="*80)


if __name__ == "__main__":
    main()

