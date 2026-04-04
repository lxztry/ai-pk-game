import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from participants.smart_agent.agent import SmartAgent
    from game.agent import Observation
    
    print("✓ 成功导入SmartAgent")
    
    # 创建智能参赛选手
    agent = SmartAgent("测试选手")
    print("✓ 成功创建SmartAgent实例")
    
    # 创建简单观察数据
    test_observation = {
        'my_health': 80,
        'my_position': [50, 50],
        'my_direction': [1, 0],
        'my_team': None,
        'my_weapon': 'normal',
        'my_ammo': None,
        'enemies_in_view': [],
        'bullets_in_view': [],
        'obstacles_in_view': [],
        'supplies_in_view': [],
        'map_boundary': [100, 100],
        'shoot_cooldown': 0
    }
    
    obs = Observation(test_observation)
    action = agent.step(obs)
    
    print(f"✓ 成功生成决策: {action}")
    
    # 验证决策格式
    valid_actions = ["move_up", "move_down", "move_left", "move_right", 
                   "turn_left", "turn_right", "shoot", "idle"]
    
    if action in valid_actions:
        print(f"✓ 决策格式正确: {action}")
        print("🎉 所有测试通过！")
        exit_code = 0
    else:
        print(f"✗ 决策格式错误: {action}")
        exit_code = 1
        
except Exception as e:
    print(f"✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    exit_code = 1

sys.exit(exit_code)