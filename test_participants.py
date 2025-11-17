"""
测试参赛者加载功能
"""
from utils.agent_loader import AgentLoader
from game.engine import GameEngine

def main():
    print("="*80)
    print("测试参赛者Agent自动加载功能")
    print("="*80)
    print()
    
    # 加载所有参赛者Agent
    print("正在加载参赛者Agent...")
    print("-" * 80)
    loader = AgentLoader(participants_dir="participants")
    agents = loader.create_agent_instances()
    print("-" * 80)
    
    if len(agents) == 0:
        print("未找到任何参赛者Agent")
        return
    
    print(f"\n成功加载 {len(agents)} 个Agent:")
    for i, agent in enumerate(agents, 1):
        print(f"  {i}. {agent.name} ({agent.__class__.__name__})")
    
    if len(agents) < 2:
        print("\n需要至少2个Agent才能进行对战")
        return
    
    # 运行一场快速对战
    print("\n" + "="*80)
    print("开始快速对战测试...")
    print("="*80)
    
    engine = GameEngine(agents, map_width=100, map_height=100)
    winner = engine.run(max_turns=500, verbose=False)
    
    print("\n" + "="*80)
    print("对战结果:")
    print("="*80)
    for agent in agents:
        print(f"{agent.name}: 击杀 {agent.kills}, 死亡 {agent.deaths}, 最终血量 {agent.health}")
    
    if winner:
        print(f"\n获胜者: {winner.name}!")
    else:
        print("\n游戏超时，无获胜者")

if __name__ == "__main__":
    main()

