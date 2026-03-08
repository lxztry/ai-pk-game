"""
简单测试脚本 - 验证智能参赛选手
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_import():
    """测试导入"""
    try:
        from participants.smart_agent.agent import SmartAgent
        print("✓ 成功导入SmartAgent")
        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_creation():
    """测试创建实例"""
    try:
        from participants.smart_agent.agent import SmartAgent
        agent = SmartAgent("TestSmartAgent")
        print("✓ 成功创建SmartAgent实例")
        return True
    except Exception as e:
        print(f"✗ 创建实例失败: {e}")
        return False

def test_basic_step():
    """测试基本决策"""
    try:
        from participants.smart_agent.agent import SmartAgent
        from game.agent import Observation
        
        agent = SmartAgent("TestSmartAgent")
        
        # 创建简单的观察数据
        test_data = {
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
        
        obs = Observation(test_data)
        action = agent.step(obs)
        
        print(f"✓ 成功生成决策: {action}")
        print(f"  可用动作类型: {type(action)}")
        print(f"  动作值: {repr(action)}")
        
        # 检查动作是否有效
        valid_actions = ["move_up", "move_down", "move_left", "move_right", 
                       "turn_left", "turn_right", "shoot", "idle"]
        if action in valid_actions:
            print(f"✓ 动作有效: {action}")
            return True
        else:
            print(f"✗ 无效动作: {action}")
            return False
            
    except Exception as e:
        print(f"✗ 基本决策测试失败: {e}")
        return False

def main():
    print("智能参赛选手测试")
    print("=" * 50)
    
    tests = [
        ("导入测试", test_import),
        ("创建实例测试", test_creation),
        ("基本决策测试", test_basic_step)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
        print("-" * 30)
    
    print(f"\n测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！智能参赛选手准备就绪。")
        return True
    else:
        print("❌ 部分测试失败，请检查实现。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)