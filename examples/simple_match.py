"""
简单对战示例
"""
import time
from agents.code_agent import RandomAgent, AggressiveAgent, DefensiveAgent, SmartAgent
from game.engine import GameEngine
from visualizer.console_visualizer import ConsoleVisualizer


def main():
    """运行一场简单的对战"""
    print("AI竞技平台 - 简单对战示例\n")
    
    # 创建Agent
    agents = [
        AggressiveAgent("激进者"),
        DefensiveAgent("防御者"),
        SmartAgent("智者"),
        RandomAgent("随机者")
    ]
    
    # 创建可视化器
    visualizer = ConsoleVisualizer(map_width=100, map_height=100)
    
    # 创建游戏引擎
    engine = GameEngine(agents, map_width=100, map_height=100)
    
    print("游戏开始！按 Ctrl+C 可提前结束\n")
    
    try:
        # 运行游戏并实时显示
        while engine.state.turn < 500:
            state_info = engine.step()
            
            # 每5回合显示一次
            if engine.state.turn % 5 == 0:
                visualizer.render(state_info, clear=True)
                time.sleep(0.2)
            
            # 检查是否有获胜者（只允许在只剩一个存活者时判定）
            winner = engine.state.get_winner(allow_score_judge=False)
            if winner:
                visualizer.render(state_info, clear=True)
                print(f"\n{winner.name} 获胜！")
                break
    except KeyboardInterrupt:
        print("\n\n游戏被用户中断")
    
    # 显示最终统计
    print("\n最终统计:")
    for agent in agents:
        print(f"{agent.name}: 击杀 {agent.kills}, 死亡 {agent.deaths}")


if __name__ == "__main__":
    main()

