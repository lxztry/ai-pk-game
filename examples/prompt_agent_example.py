"""
Prompt Agent示例
注意：需要设置 OPENAI_API_KEY 环境变量
"""
import os
from agents.prompt_agent import PromptAgent
from agents.code_agent import AggressiveAgent, DefensiveAgent
from game.engine import GameEngine


def main():
    """运行Prompt Agent对战示例"""
    print("AI竞技平台 - Prompt Agent示例\n")
    
    # 检查API Key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("错误: 需要设置 OPENAI_API_KEY 环境变量")
        print("例如: export OPENAI_API_KEY='your-api-key'")
        return
    
    # 创建Prompt Agent
    try:
        prompt_agent = PromptAgent("Prompt大师", api_key=api_key, model="gpt-4o-mini")
    except Exception as e:
        print(f"创建Prompt Agent失败: {e}")
        return
    
    # 创建代码Agent作为对手
    code_agents = [
        AggressiveAgent("激进者"),
        DefensiveAgent("防御者")
    ]
    
    # 创建游戏
    agents = [prompt_agent] + code_agents
    engine = GameEngine(agents, map_width=100, map_height=100)
    
    print("游戏开始！Prompt Agent vs 代码Agent\n")
    
    # 运行游戏
    winner = engine.run(max_turns=2000, verbose=True)
    
    if winner:
        print(f"\n获胜者: {winner.name}")
        print(f"击杀数: {winner.kills}")
    else:
        print("\n游戏超时")


if __name__ == "__main__":
    main()

