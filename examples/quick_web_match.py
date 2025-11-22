"""
快速网页版对战示例 - 生成较短的HTML回放（用于快速测试）
"""
from agents.code_agent import RandomAgent, AggressiveAgent, DefensiveAgent, SmartAgent
from game.engine import GameEngine
from visualizer.web_visualizer import WebVisualizer


def main():
    """运行一场较短的对战并生成网页回放"""
    print("AI斗兽场 - 快速网页版对战示例\n")
    
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
    
    # 运行游戏并记录每一帧（较短的版本）
    max_turns = 1000  # 减少最大回合数
    frame_interval = 1  # 每回合都记录（更流畅）
    
    while engine.state.turn < max_turns:
        state_info = engine.step()
        
        # 记录每一帧
        visualizer.record_frame(state_info)
        
        # 显示进度
        if engine.state.turn % 50 == 0:
            print(f"回合 {engine.state.turn}/{max_turns} - 存活: {state_info['alive_count']}")
        
        # 检查是否有获胜者
        winner = engine.state.get_winner()
        if winner:
            # 记录最后几帧
            for _ in range(20):
                state_info = engine.step()
                visualizer.record_frame(state_info)
            print(f"\n游戏结束！获胜者: {winner.name} (击杀: {winner.kills})")
            break
    
    # 生成HTML回放文件
    print("\n正在生成网页回放文件...")
    html_file = visualizer.render_replay(output_file="game_replay.html", 
                                         auto_play=True, fps=20)
    
    # 显示最终统计
    print("\n最终统计:")
    for agent in agents:
        print(f"{agent.name}: 击杀 {agent.kills}, 死亡 {agent.deaths}")
    
    print(f"\n✓ 回放文件已生成: {html_file}")
    print("请在浏览器中打开查看精美的游戏回放！")
    print(f"\n提示：可以直接双击 {html_file} 文件，或在浏览器中打开")


if __name__ == "__main__":
    main()

