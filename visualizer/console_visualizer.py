"""
命令行可视化工具
"""
import os
import sys
import time
from typing import List, Dict, Any, Optional
from colorama import init, Fore, Back, Style

init(autoreset=True)

# 设置Windows控制台编码为UTF-8（如果可能）
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass  # 如果无法设置，使用默认编码


class ConsoleVisualizer:
    """命令行可视化器"""
    
    def __init__(self, map_width: int = 100, map_height: int = 100, 
                 display_width: int = 60, display_height: int = 30):
        self.map_width = map_width
        self.map_height = map_height
        self.display_width = display_width
        self.display_height = display_height
        self.colors = [
            Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE,
            Fore.MAGENTA, Fore.CYAN, Fore.WHITE
        ]
        self.agent_colors = {}
        self.color_index = 0
    
    def _get_agent_color(self, agent_name: str) -> str:
        """获取Agent的颜色"""
        if agent_name not in self.agent_colors:
            self.agent_colors[agent_name] = self.colors[self.color_index % len(self.colors)]
            self.color_index += 1
        return self.agent_colors[agent_name]
    
    def _map_to_display(self, x: float, y: float) -> tuple:
        """将地图坐标转换为显示坐标"""
        display_x = int((x / self.map_width) * self.display_width)
        display_y = int((y / self.map_height) * self.display_height)
        display_x = max(0, min(display_x, self.display_width - 1))
        display_y = max(0, min(display_y, self.display_height - 1))
        return (display_x, display_y)
    
    def render(self, state_info: Dict[str, Any], clear: bool = True):
        """渲染游戏状态"""
        if clear:
            os.system('cls' if os.name == 'nt' else 'clear')
        
        # 创建显示缓冲区
        display = [[' ' for _ in range(self.display_width)] 
                   for _ in range(self.display_height)]
        
        # 绘制边界（使用ASCII字符以兼容Windows控制台）
        for i in range(self.display_height):
            display[i][0] = '|'
            display[i][self.display_width - 1] = '|'
        for j in range(self.display_width):
            display[0][j] = '-'
            display[self.display_height - 1][j] = '-'
        display[0][0] = '+'
        display[0][self.display_width - 1] = '+'
        display[self.display_height - 1][0] = '+'
        display[self.display_height - 1][self.display_width - 1] = '+'
        
        # 绘制子弹（不同武器使用不同字符）
        for bullet in state_info['bullets']:
            x, y = self._map_to_display(bullet['position'][0], bullet['position'][1])
            if 0 < x < self.display_width - 1 and 0 < y < self.display_height - 1:
                kind = bullet.get('kind', 'normal')
                # 不同武器使用不同字符
                if kind == 'shotgun':
                    # 霰弹枪：使用多个点
                    for offset in [-1, 0, 1]:
                        if 0 < x + offset < self.display_width - 1:
                            display[y][x + offset] = '.'
                elif kind == 'sniper':
                    # 狙击枪：使用竖线
                    display[y][x] = '|'
                elif kind == 'rocket':
                    # 火箭筒：使用大字符
                    display[y][x] = 'O'
                else:
                    # 普通子弹：使用星号
                    display[y][x] = '*'
        
        # 绘制Agent
        for agent_info in state_info['agents']:
            if agent_info['health'] <= 0:
                continue
            
            x, y = self._map_to_display(
                agent_info['position'][0],
                agent_info['position'][1]
            )
            
            if 0 < x < self.display_width - 1 and 0 < y < self.display_height - 1:
                # 使用首字母作为标识
                char = agent_info['name'][0].upper()
                display[y][x] = char
        
        # 打印显示
        print(f"\n回合: {state_info['turn']} | 存活: {state_info['alive_count']}")
        print("-" * (self.display_width + 2))
        
        for row in display:
            print('|' + ''.join(row) + '|')
        
        print("-" * (self.display_width + 2))
        
        # 打印Agent状态
        print("\nAgent状态:")
        for agent_info in state_info['agents']:
            if agent_info['health'] > 0:
                color = self._get_agent_color(agent_info['name'])
                print(f"{color}{agent_info['name']:<15} "
                      f"血量: {agent_info['health']:>3}  "
                      f"击杀: {agent_info['kills']:>2}  "
                      f"位置: ({agent_info['position'][0]:>5.1f}, {agent_info['position'][1]:>5.1f})")
        
        if state_info['winner']:
            print(f"\n{Fore.YELLOW}[WIN] 获胜者: {state_info['winner']} [WIN]")
    
    def render_replay(self, replay_data: List[Dict[str, Any]], delay: float = 0.1):
        """回放游戏"""
        for state in replay_data:
            self.render(state, clear=True)
            time.sleep(delay)
    
    def print_match_result(self, agent1_name: str, agent2_name: str, winner: Optional[str]):
        """打印比赛结果"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{agent1_name} vs {agent2_name}")
        if winner:
            print(f"{Fore.YELLOW}获胜者: {winner}")
        else:
            print(f"{Fore.RED}平局")
        print(f"{Fore.CYAN}{'='*60}\n")

