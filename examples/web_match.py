"""
网页版对战示例 - 生成HTML回放文件
"""
import time
from agents.code_agent import RandomAgent, AggressiveAgent, DefensiveAgent, SmartAgent
from game.engine import GameEngine
from visualizer.web_visualizer import WebVisualizer


def main():
    """运行一场对战并生成网页回放"""
    print("AI竞技平台 - 网页版对战示例\n")
    
    # 创建Agent
    agents = [
        AggressiveAgent("激进者"),
        DefensiveAgent("防御者"),
        SmartAgent("智者"),
        RandomAgent("随机者")
    ]
    
    # 创建网页可视化器
    visualizer = WebVisualizer(map_width=100, map_height=100, 
                               canvas_width=800, canvas_height=600)
    
    # 创建游戏引擎
    engine = GameEngine(agents, map_width=100, map_height=100)
    
    print("游戏开始！正在记录游戏过程...")
    print("（这将生成一个HTML文件，可在浏览器中查看精美的游戏回放）\n")
    
    # 运行游戏并记录每一帧
    max_turns = 2000
    frame_interval = 2  # 每2回合记录一帧（减少文件大小）
    
    while engine.state.turn < max_turns:
        state_info = engine.step()
        
        # 记录帧（每隔几帧记录一次以减小文件大小）
        if engine.state.turn % frame_interval == 0:
            visualizer.record_frame(state_info)
        
        # 显示进度
        if engine.state.turn % 100 == 0:
            print(f"回合 {engine.state.turn}/{max_turns} - 存活: {state_info['alive_count']}")
        
        # 检查是否有获胜者（只允许在只剩一个存活者时判定）
        winner = engine.state.get_winner(allow_score_judge=False)
        if winner:
            # 记录最后几帧
            for _ in range(10):
                state_info = engine.step()
                visualizer.record_frame(state_info)
            print(f"\n游戏结束！获胜者: {winner.name} (击杀: {winner.kills})")
            break
    
    # 超时后按评分判定获胜者（如果还没有）
    if winner is None:
        winner = engine.state.get_winner(allow_score_judge=True)
        # 如果有获胜者，更新回放数据中的获胜者信息
        if winner:
            visualizer.set_winner(winner.name)
            print(f"\n游戏超时！按评分判定获胜者: {winner.name} (击杀: {winner.kills}, 血量: {winner.health})")
    
    # 生成HTML回放文件
    print("\n正在生成网页回放文件...")
    html_file = visualizer.render_replay(output_file="game_replay.html", 
                                         auto_play=True, fps=15)
    
    # 显示最终统计
    print("\n最终统计:")
    for agent in agents:
        print(f"{agent.name}: 击杀 {agent.kills}, 死亡 {agent.deaths}")
    
    print(f"\n✓ 回放文件已生成: {html_file}")
    print("请在浏览器中打开查看精美的游戏回放！")


if __name__ == "__main__":
    main()

