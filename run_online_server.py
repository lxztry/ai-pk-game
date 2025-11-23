"""
启动在线对战服务器
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from online.server import app, db
from utils.agent_loader import AgentLoader

if __name__ == '__main__':
    # 初始化：从participants目录加载所有玩家到数据库
    print("正在加载玩家...")
    participants_dir = project_root / "participants"
    loader = AgentLoader(participants_dir=str(participants_dir))
    agents = loader.create_agent_instances()
    
    for agent in agents:
        agent_path = f"participants/{agent.name}"
        if db.add_player(agent.name, agent_path):
            print(f"✓ 已添加玩家: {agent.name}")
        else:
            print(f"ℹ 玩家已存在: {agent.name}")
    
    print("\n" + "="*60)
    print("AI竞技平台 - 在线对战服务器")
    print("="*60)
    print(f"已加载 {len(agents)} 名玩家")
    print(f"访问 http://localhost:5000 开始对战")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

