"""
武器效果演示 - 确保武器猎手能找到并使用武器
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.agent_loader import AgentLoader
from agents.code_agent import AggressiveAgent
from game.engine import GameEngine
from visualizer.web_visualizer import WebVisualizer
import random


def main():
    """运行武器效果演示"""
    print("="*60)
    print("武器效果演示 - 确保武器猎手能找到并使用武器")
    print("="*60)
    print()
    
    # 加载武器猎手
    loader = AgentLoader(participants_dir="participants")
    all_agents = loader.create_agent_instances()
    
    weapon_hunter = next((a for a in all_agents if a.name == "weapon_hunter"), None)
    
    if not weapon_hunter:
        print("错误: 找不到 weapon_hunter")
        return
    
    # 创建对手
    opponent = AggressiveAgent("激进对手")
    
    # 创建Agent列表
    agents = [weapon_hunter, opponent]
    
    print(f"对战双方：")
    print(f"  1. {weapon_hunter.name} (武器猎手)")
    print(f"  2. {opponent.name} (激进对手)")
    print()
    
    # 创建网页可视化器
    visualizer = WebVisualizer(map_width=100, map_height=100, 
                               canvas_width=1000, canvas_height=800)
    
    # 创建游戏引擎
    engine = GameEngine(agents, map_width=100, map_height=100)
    
    # 预先在地图上放置一些武器和弹药，确保武器猎手能找到
    print("预先放置武器和弹药...")
    weapon_types = ['weapon_rocket', 'weapon_sniper', 'weapon_shotgun']
    ammo_types = ['ammo_rocket', 'ammo_sniper', 'ammo_shotgun']
    
    # 在地图中心区域放置武器和对应的弹药
    center_x, center_y = 50, 50
    placed = 0
    
    # 放置3个武器，每个武器附近放置对应的弹药
    for i in range(3):
        # 武器位置
        angle = (i / 3) * 2 * 3.14159
        radius = 20
        wx = center_x + radius * (1.0 if i % 2 == 0 else -1.0) * (0.5 if i < 2 else 0)
        wy = center_y + radius * (1.0 if i < 1 else -1.0) * (0.5 if i == 1 else 1.0)
        wx = max(15, min(85, wx))
        wy = max(15, min(85, wy))
        
        # 放置武器
        engine.state.supplies.append({
            'position': (wx, wy),
            'type': weapon_types[i]
        })
        placed += 1
        
        # 在武器附近放置对应的弹药（多个）
        for j in range(3):
            ax = wx + (j - 1) * 5
            ay = wy + (j - 1) * 5
            ax = max(15, min(85, ax))
            ay = max(15, min(85, ay))
            engine.state.supplies.append({
                'position': (ax, ay),
                'type': ammo_types[i]
            })
            placed += 1
    
    print(f"已放置 {placed} 个补给（3个武器 + 9个弹药）")
    print()
    
    print("游戏开始！")
    print("武器猎手会优先寻找武器，然后使用武器进行战斗")
    print("注意观察不同武器的视觉效果！\n")
    
    # 运行游戏并记录每一帧
    max_turns = 500
    weapons_found = []
    
    while engine.state.turn < max_turns:
        state_info = engine.step()
        
        # 检查武器猎手是否找到新武器
        for agent_info in state_info['agents']:
            if agent_info['name'] == 'weapon_hunter':
                weapon = agent_info.get('weapon', 'normal')
                if weapon != 'normal' and weapon not in weapons_found:
                    weapons_found.append(weapon)
                    ammo_info = agent_info.get('ammo', None)
                    if isinstance(ammo_info, dict):
                        ammo = ammo_info.get(weapon, 0)
                    else:
                        ammo = ammo_info if ammo_info is not None else 0
                    print(f"🎯 回合 {engine.state.turn}: 武器猎手找到了 {weapon} 武器！(弹药: {ammo})")
        
        # 记录每一帧
        visualizer.record_frame(state_info)
        
        # 显示进度
        if engine.state.turn % 100 == 0:
            print(f"回合 {engine.state.turn}/{max_turns} - 存活: {state_info['alive_count']}")
            # 显示双方状态
            for agent_info in state_info['agents']:
                if agent_info['health'] > 0:
                    weapon = agent_info.get('weapon', 'normal')
                    ammo_info = agent_info.get('ammo', None)
                    if weapon == 'normal':
                        ammo = '∞'
                    elif isinstance(ammo_info, dict):
                        ammo = ammo_info.get(weapon, 0)
                    else:
                        ammo = ammo_info if ammo_info is not None else 0
                    print(f"  {agent_info['name']}: 血量={agent_info['health']}, 武器={weapon}, 弹药={ammo}, 击杀={agent_info['kills']}")
        
        # 检查是否有获胜者
        winner = engine.state.get_winner(allow_score_judge=False)
        if winner:
            # 记录最后几帧
            for _ in range(20):
                state_info = engine.step()
                visualizer.record_frame(state_info)
            
            print(f"\n游戏结束！获胜者: {winner.name}")
            print(f"  击杀: {winner.kills}, 血量: {winner.health}")
            weapon = winner.weapon if hasattr(winner, 'weapon') else 'normal'
            print(f"  最终武器: {weapon}")
            break
    
    # 超时后按评分判定
    if winner is None:
        winner = engine.state.get_winner(allow_score_judge=True)
        if winner:
            visualizer.set_winner(winner.name)
            print(f"\n游戏超时！按评分判定获胜者: {winner.name}")
            print(f"  击杀: {winner.kills}, 血量: {winner.health}")
            weapon = winner.weapon if hasattr(winner, 'weapon') else 'normal'
            print(f"  最终武器: {weapon}")
    
    # 生成HTML回放文件
    print("\n正在生成网页回放文件...")
    html_file = visualizer.generate_html(output_file="weapon_effect_demo.html", 
                                         auto_play=True, fps=30)
    
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
    print("\n请在浏览器中打开查看，观察不同武器的视觉效果！")
    print("\n武器视觉效果说明：")
    print("  🔫 普通武器：小圆点，标准轨迹")
    print("  💥 霰弹枪：多个小点，散射效果")
    print("  🎯 狙击枪：细长线条，带光晕，长轨迹")
    print("  🚀 火箭筒：大圆点，带橙色尾焰效果")
    print(f"\n武器猎手找到的武器: {', '.join(weapons_found) if weapons_found else '无'}")


if __name__ == "__main__":
    main()

