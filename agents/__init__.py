"""
示例Agent实现
"""

from .prompt_agent import PromptAgent
from .code_agent import CodeAgent, RandomAgent, AggressiveAgent, DefensiveAgent

__all__ = ['PromptAgent', 'CodeAgent', 'RandomAgent', 'AggressiveAgent', 'DefensiveAgent']

