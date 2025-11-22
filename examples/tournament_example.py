"""
比赛系统示例
"""
from agents.code_agent import RandomAgent, AggressiveAgent, DefensiveAgent, SmartAgent
from tournament.tournament import RoundRobinTournament, EliminationTournament


def main():
    """运行比赛示例"""
    print("AI竞技平台 - 比赛系统示例\n")
    
    # 创建多个Agent
    agents = [
        AggressiveAgent("激进者"),
        DefensiveAgent("防御者"),
        SmartAgent("智者"),
        RandomAgent("随机者"),
        AggressiveAgent("激进者2"),
        DefensiveAgent("防御者2")
    ]
    
    print("选择比赛模式:")
    print("1. 循环赛（每个Agent与其他所有Agent对战）")
    print("2. 淘汰赛（单败淘汰制）")
    
    choice = input("\n请输入选择 (1/2): ").strip()
    
    if choice == "1":
        tournament = RoundRobinTournament(agents, save_replay=True, replay_dir="replays")
        tournament.run(verbose=True)
    elif choice == "2":
        tournament = EliminationTournament(agents, save_replay=True, replay_dir="replays")
        tournament.run(verbose=True)
    else:
        print("无效选择，使用循环赛")
        tournament = RoundRobinTournament(agents, save_replay=True, replay_dir="replays")
        tournament.run(verbose=True)


if __name__ == "__main__":
    main()

