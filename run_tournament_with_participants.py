"""
AI竞技平台 - 主程序（支持自动加载参赛者Agent）
自动发现并加载participants目录下的所有Agent
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


def create_default_agents():
    """创建默认的代码Agent（用于测试）"""
    return [
        AggressiveAgent("激进者"),
        DefensiveAgent("防御者"),
        SmartAgent("智者"),
        RandomAgent("随机者"),
    ]


def create_prompt_agents():
    """创建Prompt Agent（如果API Key可用）"""
    agents = []
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key:
        try:
            agents.append(PromptAgent("Prompt大师", api_key=api_key, model="gpt-4o-mini"))
            print("✓ 已加载 Prompt Agent")
        except Exception as e:
            print(f"✗ 加载 Prompt Agent 失败: {e}")
    else:
        print("ℹ 未设置 OPENAI_API_KEY，跳过 Prompt Agent")
    
    return agents


def main():
    """主程序"""
    print("="*80)
    print(" " * 25 + "AI竞技平台")
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
    
    # 可选：添加Prompt Agent
    try:
        use_prompt = input("\n是否添加Prompt Agent? (y/n): ").strip().lower()
        if use_prompt == 'y':
            prompt_agents = create_prompt_agents()
            agents.extend(prompt_agents)
    except (EOFError, KeyboardInterrupt):
        # 非交互式环境或用户取消，跳过Prompt Agent
        print("\n跳过Prompt Agent")
    
    if len(agents) < 2:
        print("错误: 至少需要2个Agent才能进行比赛")
        return
    
    print(f"\n共加载 {len(agents)} 个Agent:")
    for i, agent in enumerate(agents, 1):
        agent_type = agent.__class__.__name__
        print(f"  {i}. {agent.name} ({agent_type})")
    
    print("\n" + "="*80)
    print("选择比赛模式:")
    print("  1. 循环赛（每个Agent与其他所有Agent对战）")
    print("  2. 淘汰赛（单败淘汰制）")
    print("  3. 退出")
    print("="*80)
    
    while True:
        try:
            choice = input("\n请输入选择 (1/2/3): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n用户取消操作")
            sys.exit(0)
        
        if choice == "1":
            print("\n开始循环赛（将自动生成回放）...")
            tournament = RoundRobinTournament(agents, save_replay=True, replay_dir="replays")
            tournament.run(verbose=True)
            break
        elif choice == "2":
            print("\n开始淘汰赛（将自动生成回放）...")
            tournament = EliminationTournament(agents, save_replay=True, replay_dir="replays")
            tournament.run(verbose=True)
            break
        elif choice == "3":
            print("退出")
            sys.exit(0)
        else:
            print("无效选择，请输入 1、2 或 3")


if __name__ == "__main__":
    main()

