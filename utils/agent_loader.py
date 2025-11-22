"""
Agent自动加载器
自动发现并加载participants目录下的所有Agent
"""
import os
import importlib
import importlib.util
import sys
from pathlib import Path
from typing import List, Dict, Any
from game.agent import Agent


class AgentLoader:
    """Agent加载器"""
    
    def __init__(self, participants_dir: str = "participants"):
        """
        初始化Agent加载器
        
        Args:
            participants_dir: 参赛者目录路径
        """
        self.participants_dir = Path(participants_dir)
        self.loaded_agents: Dict[str, Any] = {}
    
    def discover_agents(self) -> List[Dict[str, Any]]:
        """
        发现所有参赛者的Agent
        
        Returns:
            包含Agent信息的列表，每个元素包含：
            - name: 参赛者名称（目录名）
            - agent_class: Agent类
            - path: Agent文件路径
        """
        agents = []
        
        if not self.participants_dir.exists():
            print(f"警告: 参赛者目录 {self.participants_dir} 不存在")
            return agents
        
        # 遍历所有子目录
        for player_dir in self.participants_dir.iterdir():
            if not player_dir.is_dir():
                continue
            
            # 跳过特殊目录
            if player_dir.name.startswith('_') or player_dir.name.startswith('.'):
                continue
            
            player_name = player_dir.name
            agent_file = player_dir / "agent.py"
            
            if not agent_file.exists():
                print(f"警告: {player_name} 目录下没有找到 agent.py")
                continue
            
            # 尝试加载Agent
            try:
                agent_class = self._load_agent_from_file(agent_file, player_name)
                if agent_class:
                    agents.append({
                        'name': player_name,
                        'agent_class': agent_class,
                        'path': str(agent_file)
                    })
                    print(f"[OK] 已加载: {player_name}")
            except Exception as e:
                print(f"[ERROR] 加载 {player_name} 失败: {e}")
        
        return agents
    
    def _load_agent_from_file(self, agent_file: Path, player_name: str):
        """
        从文件加载Agent类
        
        Args:
            agent_file: Agent文件路径
            player_name: 参赛者名称
            
        Returns:
            Agent类，如果加载失败返回None
        """
        # 构建模块路径
        module_path = f"participants.{player_name}.agent"
        
        # 将文件所在目录添加到sys.path（如果需要）
        parent_dir = str(agent_file.parent.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        # 动态导入模块
        try:
            # 如果模块已经加载，先移除
            if module_path in sys.modules:
                del sys.modules[module_path]
            
            spec = importlib.util.spec_from_file_location(module_path, agent_file)
            if spec is None or spec.loader is None:
                raise ImportError(f"无法创建模块规范: {module_path}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找Agent类（优先查找名为Agent的类，否则查找继承自Agent的类）
            agent_class = None
            
            # 首先查找名为Agent的类
            if hasattr(module, 'Agent'):
                agent_class = getattr(module, 'Agent')
            else:
                # 查找所有继承自Agent的类
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, Agent) and 
                        attr != Agent):
                        agent_class = attr
                        break
            
            if agent_class is None:
                raise ValueError(f"在 {agent_file} 中未找到Agent类")
            
            return agent_class
            
        except Exception as e:
            raise Exception(f"加载模块失败: {e}")
    
    def create_agent_instances(self, agent_name_prefix: str = "") -> List[Agent]:
        """
        创建所有Agent的实例
        
        Args:
            agent_name_prefix: Agent名称前缀（可选）
            
        Returns:
            Agent实例列表
        """
        agents_info = self.discover_agents()
        instances = []
        
        for info in agents_info:
            try:
                agent_class = info['agent_class']
                player_name = info['name']
                
                # 创建Agent实例
                # 尝试使用不同的初始化方式
                if agent_name_prefix:
                    agent_name = f"{agent_name_prefix}{player_name}"
                else:
                    agent_name = player_name
                
                # 尝试创建实例
                try:
                    # 先尝试无参数初始化
                    instance = agent_class(agent_name)
                except TypeError:
                    # 如果失败，尝试只传name参数
                    try:
                        instance = agent_class(name=agent_name)
                    except TypeError:
                        # 如果还失败，使用默认名称
                        instance = agent_class(player_name)
                
                instances.append(instance)
                self.loaded_agents[player_name] = instance
                
            except Exception as e:
                print(f"✗ 创建 {info['name']} 的实例失败: {e}")
        
        return instances

