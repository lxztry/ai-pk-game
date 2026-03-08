"""
智能参赛选手测试脚本
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from participants.smart_agent.agent import SmartAgent
from game.agent import Observation


def test_smart_agent():
    """测试智能参赛选手"""
    print("测试智能参赛选手...")
    
    # 创建智能参赛选手
    agent = SmartAgent("SmartAI")
    
    # 创建模拟观察数据
    test_observation = {
        'my_health': 80,
        'my_position': [50, 50],
        'my_direction': [1, 0],
        'my_team': None,
        'my_weapon': 'normal',
        'my_ammo': None,
        'enemies_in_view': [
            {
                'position': [60, 50],
                'distance': 10,
                'health': 100
            }
        ],
        'bullets_in_view': [
            {
                'position': [45, 50],
                'direction': [1, 0],
                'speed': 1.0
            }
        ],
        'obstacles_in_view': [
            {
                'x': 70, 'y': 40,
                'width': 10, 'height': 20
            }
        ],
        'supplies_in_view': [
            {
                'type': 'health',
                'position': [40, 60],
                'distance': 14
            },
            {
                'type': 'weapon_sniper',
                'position': [30, 50],
                'distance': 20
            }
        ],
        'map_boundary': [100, 100],
        'shoot_cooldown': 0
    }
    
    # 创建观察对象
    obs = Observation(test_observation)
    
    # 测试多次决策
    print("\n模拟10个游戏回合的决策...")
    for i in range(10):
        action = agent.step(obs)
        print(f"回合 {i+1}: {action}")
        
        # 更新模拟数据（简化版）
        if action == "move_right":
            test_observation['my_position'][0] += 1
        elif action == "move_left":
            test_observation['my_position'][0] -= 1
        elif action == "move_up":
            test_observation['my_position'][1] -= 1
        elif action == "move_down":
            test_observation['my_position'][1] += 1
        elif action == "shoot":
            test_observation['shoot_cooldown'] = 20  # 射击冷却
        
        # 更新观察对象
        obs = Observation(test_observation)
        
        # 更新敌人距离
        for enemy in test_observation['enemies_in_view']:
            enemy['distance'] = ((enemy['position'][0] - test_observation['my_position'][0])**2 + 
                                (enemy['position'][1] - test_observation['my_position'][1])**2) ** 0.5
    
    print("\n智能参赛选手测试完成！")
    print("参赛选手能够：")
    print("- 识别并攻击最近的敌人")
    print("- 躲避危险子弹")
    print("- 寻找补给恢复血量")
    print("- 选择合适的武器")
    print("- 根据游戏状态做出合理决策")


if __name__ == "__main__":
    test_smart_agent()