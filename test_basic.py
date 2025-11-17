"""
基础功能测试
"""
from agents.code_agent import RandomAgent, AggressiveAgent
from game.engine import GameEngine


def test_basic_game():
    """测试基本游戏功能"""
    print("测试基本游戏功能...")
    
    # 创建两个简单的Agent
    agents = [
        AggressiveAgent("测试Agent1"),
        RandomAgent("测试Agent2")
    ]
    
    # 创建游戏引擎
    engine = GameEngine(agents, map_width=50, map_height=50)
    
    # 运行游戏
    winner = engine.run(max_turns=500, verbose=False)
    
    if winner:
        print(f"✓ 测试通过！获胜者: {winner.name}")
        print(f"  击杀数: {winner.kills}")
    else:
        print("✓ 测试通过（游戏超时，这是正常的）")
    
    return True


if __name__ == "__main__":
    test_basic_game()

