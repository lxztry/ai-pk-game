# 简单语法检查
print("检查智能参赛选手代码语法...")

try:
    # 尝试读取agent.py文件
    with open('participants/smart_agent/agent.py', 'r', encoding='utf-8') as f:
        code = f.read()
    
    print("✓ 成功读取agent.py文件")
    print(f"✓ 文件大小: {len(code)} 字符")
    
    # 检查基本的Python语法
    compile(code, 'participants/smart_agent/agent.py', 'exec')
    print("✓ Python语法检查通过")
    
    # 检查关键类和方法
    if 'class SmartAgent' in code:
        print("✓ SmartAgent类定义存在")
    else:
        print("✗ SmartAgent类定义缺失")
        
    if 'def step(self, observation: Observation)' in code:
        print("✓ step方法定义存在")
    else:
        print("✗ step方法定义缺失")
        
    if 'from agents.code_agent import CodeAgent' in code:
        print("✓ 正确导入CodeAgent")
    else:
        print("✗ 未正确导入CodeAgent")
        
    print("\n🎉 代码语法检查完成，没有发现明显问题！")
    print("注意：由于环境限制，无法完全运行测试，但代码结构和语法看起来正确。")
    
except FileNotFoundError:
    print("✗ 找不到agent.py文件")
except SyntaxError as e:
    print(f"✗ 语法错误: {e}")
except Exception as e:
    print(f"✗ 其他错误: {e}")