"""
测试武器猎手Agent - 体验武器效果
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.agent_loader import AgentLoader
from agents.code_agent import AggressiveAgent, DefensiveAgent, RandomAgent
from game.engine import GameEngine
from visualizer.web_visualizer import WebVisualizer


def main():
    """运行武器猎手对战测试"""
    print("="*60)
    print("武器猎手测试 - 体验武器效果")
    print("="*60)
    print()
    
    # 加载武器猎手
    loader = AgentLoader(participants_dir="participants")
    all_agents = loader.create_agent_instances()
    
    weapon_hunter = next((a for a in all_agents if a.name == "weapon_hunter"), None)
    
    if not weapon_hunter:
        print("错误: 找不到 weapon_hunter，请确保 participants/weapon_hunter/agent.py 存在")
        return
    
    # 创建对手（使用默认Agent）
    opponents = [
        AggressiveAgent("激进者"),
        DefensiveAgent("防御者"),
        RandomAgent("随机者")
    ]
    
    # 创建Agent列表
    agents = [weapon_hunter] + opponents
    
    print(f"对战双方：")
    for i, agent in enumerate(agents, 1):
        print(f"  {i}. {agent.name}")
    print()
    
    # 创建网页可视化器
    visualizer = WebVisualizer(map_width=100, map_height=100, 
                               canvas_width=800, canvas_height=600)
    
    # 创建游戏引擎
    engine = GameEngine(agents, map_width=100, map_height=100)
    
    print("游戏开始！正在记录游戏过程...")
    print("（武器猎手会优先寻找武器，然后使用武器进行战斗）\n")
    
    # 运行游戏并记录每一帧
    max_turns = 500
    frame_interval = 1  # 每回合都记录，更流畅
    
    weapon_found = False
    weapon_used = False
    
    while engine.state.turn < max_turns:
        state_info = engine.step()
        
        # 检查武器猎手是否找到武器
        for agent_info in state_info['agents']:
            if agent_info['name'] == 'weapon_hunter':
                if agent_info['weapon'] != 'normal' and not weapon_found:
                    weapon_found = True
                    print(f"🎯 回合 {engine.state.turn}: 武器猎手找到了 {agent_info['weapon']} 武器！")
                # 检查是否有弹药（ammo可能是数字或None）
                ammo = agent_info.get('ammo')
                if agent_info['weapon'] != 'normal' and ammo is not None:
                    if isinstance(ammo, dict):
                        ammo = ammo.get(agent_info['weapon'], 0)
                    if ammo and ammo > 0:
                        weapon_used = True
        
        # 记录每一帧
        visualizer.record_frame(state_info)
        
        # 显示进度
        if engine.state.turn % 50 == 0:
            print(f"回合 {engine.state.turn}/{max_turns} - 存活: {state_info['alive_count']}")
            # 显示武器猎手状态
            for agent_info in state_info['agents']:
                if agent_info['name'] == 'weapon_hunter' and agent_info['health'] > 0:
                    weapon = agent_info.get('weapon', 'normal')
                    ammo_info = agent_info.get('ammo', None)
                    if weapon == 'normal':
                        ammo = '∞'
                    elif isinstance(ammo_info, dict):
                        ammo = ammo_info.get(weapon, 0)
                    else:
                        ammo = ammo_info if ammo_info is not None else 0
                    print(f"  武器猎手: 血量={agent_info['health']}, 武器={weapon}, 弹药={ammo}, 击杀={agent_info['kills']}")
        
        # 检查是否有获胜者
        winner = engine.state.get_winner(allow_score_judge=False)
        if winner:
            # 记录最后几帧
            for _ in range(20):
                state_info = engine.step()
                visualizer.record_frame(state_info)
            
            print(f"\n游戏结束！获胜者: {winner.name} (击杀: {winner.kills}, 血量: {winner.health})")
            if winner.name == 'weapon_hunter':
                print("🏆 武器猎手获胜！")
            break
    
    # 超时后按评分判定
    if winner is None:
        winner = engine.state.get_winner(allow_score_judge=True)
        if winner:
            visualizer.set_winner(winner.name)
            print(f"\n游戏超时！按评分判定获胜者: {winner.name} (击杀: {winner.kills}, 血量: {winner.health})")
    
    # 生成HTML回放文件
    print("\n正在生成网页回放文件...")
    html_file = visualizer.generate_html(output_file="weapon_hunter_test.html", 
                                         auto_play=True, fps=20)
    
    # 显示最终统计
    print("\n最终统计:")
    for agent in agents:
        weapon = agent.weapon if hasattr(agent, 'weapon') else 'normal'
        if weapon != 'normal' and hasattr(agent, 'ammo') and isinstance(agent.ammo, dict):
            ammo = agent.ammo.get(weapon, 0)
        elif weapon == 'normal':
            ammo = '∞'
        else:
            ammo = 'N/A'
        print(f"  {agent.name}: 击杀={agent.kills}, 死亡={agent.deaths}, 最终武器={weapon}, 剩余弹药={ammo}")
    
    print(f"\n✓ 回放文件已生成: {html_file}")
    print("请在浏览器中打开查看，观察武器猎手如何寻找和使用武器！")
    print("\n提示：注意观察不同武器的视觉效果：")
    print("  - 普通武器：小圆点")
    print("  - 霰弹枪：多个小点（散射）")
    print("  - 狙击枪：细长线条（带光晕）")
    print("  - 火箭筒：大圆点（带尾焰）")


if __name__ == "__main__":
    main()

