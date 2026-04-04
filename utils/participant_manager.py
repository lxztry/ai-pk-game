"""
选手管理模块
自动扫描 participants/ 目录，加载选手，识别类型
"""
import json
import importlib
import inspect
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict


class ParticipantManager:
    """选手管理器"""
    
    def __init__(self, participants_dir: str = "participants", data_file: str = "data/participants.json"):
        self.participants_dir = Path(participants_dir)
        self.data_file = Path(data_file)
        self.participants: List[Dict[str, Any]] = []
        self._agent_cache: Dict[str, type] = {}
    
    def load_from_data_file(self) -> List[Dict[str, Any]]:
        """从 data/participants.json 加载选手数据"""
        if self.data_file.exists():
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.participants = data.get('participants', [])
        return self.participants
    
    def save_to_data_file(self):
        """保存选手数据到文件"""
        data = {
            "version": "1.0",
            "last_updated": self._get_date_str(),
            "participants": self.participants,
            "type_labels": {
                "ai": "🤖 AI选手",
                "human": "👤 人类选手"
            }
        }
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def scan_participants_directory(self) -> List[Dict[str, Any]]:
        """扫描 participants/ 目录，识别所有选手"""
        discovered = []
        
        if not self.participants_dir.exists():
            print(f"目录不存在: {self.participants_dir}")
            return discovered
        
        for item in self.participants_dir.iterdir():
            if not item.is_dir() or item.name.startswith('_') or item.name.startswith('.'):
                continue
            
            agent_info = self._discover_agent(item)
            if agent_info:
                discovered.append(agent_info)
        
        return discovered
    
    def _discover_agent(self, agent_dir: Path) -> Optional[Dict[str, Any]]:
        """发现单个 Agent 的信息"""
        agent_file = agent_dir / "agent.py"
        if not agent_file.exists():
            return None
        
        try:
            # 动态导入模块
            module_name = f"participants.{agent_dir.name}.agent"
            spec = importlib.util.spec_from_file_location(module_name, agent_file)
            if not spec or not spec.loader:
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找 Agent 类
            agent_class = None
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and hasattr(obj, 'step') and obj.__module__ == module_name:
                    agent_class = obj
                    break
            
            if not agent_class:
                return None
            
            # 分析 Agent 类型
            agent_type, developer_info, model_info = self._analyze_agent_class(agent_class, agent_dir)
            
            return {
                "id": agent_dir.name,
                "name": agent_class.__name__,
                "display_name": self._get_display_name(agent_dir.name, agent_type),
                "type": agent_type,
                "developer": developer_info,
                "model_info": model_info,
                "description": self._get_description(agent_class),
                "created_at": self._get_date_str(),
                "stats": {
                    "total_matches": 0,
                    "total_wins": 0,
                    "total_kills": 0,
                    "total_deaths": 0,
                    "total_points": 0
                }
            }
            
        except Exception as e:
            print(f"Error discovering agent in {agent_dir}: {e}")
            return None
    
    def _analyze_agent_class(self, agent_class: type, agent_dir: Path) -> tuple:
        """分析 Agent 类，返回 (type, developer_info, model_info)"""
        class_name = agent_class.__name__.lower()
        dir_name = agent_dir.name.lower()
        
        # 规则判断 AI vs Human
        # 如果类名包含 human 或目录名包含 human，则是人类
        if 'human' in class_name or 'human' in dir_name:
            return 'human', 'Human Developer', 'human-coded strategy'
        
        # AI 关键词：agent, player, hunter, smart 等
        ai_keywords = ['agent', 'player', 'hunter', 'smart', 'ai', 'bot', 'auto']
        is_likely_ai = any(kw in class_name or kw in dir_name for kw in ai_keywords)
        
        if is_likely_ai:
            # 检查是否使用 LLM/Prompt
            source_file = agent_dir / "agent.py"
            if source_file.exists():
                source = source_file.read_text(encoding='utf-8')
                
                # 如果使用 OpenAI/Anthropic API 相关的prompt，则是 Prompt 派
                if any(kw in source.lower() for kw in ['openai', 'anthropic', 'prompt', 'api_key', 'gpt', 'claude', 'llm']):
                    return 'ai', 'Prompt Engineering', 'LLM-based strategy'
                
                # 如果使用特定模型相关代码
                if any(kw in source for kw in ['model', 'completion', 'chat']):
                    return 'ai', 'AI Model', 'LLM-powered'
            
            return 'ai', 'Code-based AI', 'rule-based strategy'
        
        return 'human', 'Human Developer', 'human-coded strategy'
    
    def _get_display_name(self, agent_id: str, agent_type: str) -> str:
        """获取带标签的显示名称"""
        emoji = "🤖" if agent_type == "ai" else "👤"
        name = agent_id.replace('_', ' ').title()
        return f"{emoji} {name}"
    
    def _get_description(self, agent_class: type) -> str:
        """获取 Agent 描述"""
        doc = inspect.getdoc(agent_class)
        if doc:
            # 取第一行作为描述
            return doc.split('\n')[0].strip()
        return agent_class.__name__
    
    def _get_date_str(self) -> str:
        """获取当前日期字符串"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d')
    
    def sync_participants(self) -> Dict[str, Any]:
        """同步选手数据：扫描目录 + 合并已有统计"""
        # 加载已有数据
        existing = {p['id']: p for p in self.load_from_data_file()}
        
        # 扫描目录发现新选手
        discovered = {p['id']: p for p in self.scan_participants_directory()}
        
        # 合并：保留已有统计，更新新信息
        merged = []
        all_ids = set(existing.keys()) | set(discovered.keys())
        
        for pid in all_ids:
            if pid in discovered:
                base = discovered[pid]
                # 保留已有统计
                if pid in existing:
                    base['stats'] = existing[pid].get('stats', base['stats'])
                merged.append(base)
            elif pid in existing:
                merged.append(existing[pid])
        
        self.participants = merged
        self.save_to_data_file()
        
        return {
            'total': len(merged),
            'ai_count': sum(1 for p in merged if p['type'] == 'ai'),
            'human_count': sum(1 for p in merged if p['type'] == 'human')
        }
    
    def get_participant(self, participant_id: str) -> Optional[Dict[str, Any]]:
        """获取指定选手信息"""
        if not self.participants:
            self.load_from_data_file()
        return next((p for p in self.participants if p['id'] == participant_id), None)
    
    def get_all_participants(self) -> List[Dict[str, Any]]:
        """获取所有选手"""
        if not self.participants:
            self.load_from_data_file()
        return self.participants
    
    def get_participants_by_type(self, ptype: str) -> List[Dict[str, Any]]:
        """按类型获取选手"""
        return [p for p in self.get_all_participants() if p['type'] == ptype]
    
    def get_ai_participants(self) -> List[Dict[str, Any]]:
        """获取所有 AI 选手"""
        return self.get_participants_by_type('ai')
    
    def get_human_participants(self) -> List[Dict[str, Any]]:
        """获取所有人类选手"""
        return self.get_participants_by_type('human')
    
    def create_agent_instance(self, participant_id: str):
        """根据选手ID创建 Agent 实例"""
        if participant_id in self._agent_cache:
            agent_class = self._agent_cache[participant_id]
            return agent_class(participant_id)
        
        agent_dir = self.participants_dir / participant_id
        agent_file = agent_dir / "agent.py"
        
        if not agent_file.exists():
            raise ValueError(f"Agent file not found: {agent_file}")
        
        module_name = f"participants.{participant_id}.agent"
        spec = importlib.util.spec_from_file_location(module_name, agent_file)
        if not spec or not spec.loader:
            raise ValueError(f"Cannot load agent: {participant_id}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 查找 Agent 类
        agent_class = None
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and hasattr(obj, 'step') and obj.__module__ == module_name:
                agent_class = obj
                break
        
        if not agent_class:
            raise ValueError(f"No Agent class found in {agent_file}")
        
        self._agent_cache[participant_id] = agent_class
        return agent_class(participant_id)
    
    def create_all_agent_instances(self) -> List:
        """创建所有选手的 Agent 实例"""
        instances = []
        for p in self.get_all_participants():
            try:
                agent = self.create_agent_instance(p['id'])
                instances.append(agent)
            except Exception as e:
                print(f"Warning: Cannot create agent {p['id']}: {e}")
        return instances


# 使用示例
if __name__ == "__main__":
    manager = ParticipantManager()
    result = manager.sync_participants()
    print(f"选手同步完成: {result}")
    
    for p in manager.get_all_participants():
        print(f"  - {p['display_name']} ({p['type']})")
