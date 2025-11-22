"""
Prompt派Agent - 通过LLM生成决策
"""
import os
from typing import Optional
from game.agent import Agent, Observation

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class PromptAgent(Agent):
    """通过Prompt调用LLM生成决策的Agent"""
    
    def __init__(self, name: str, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        super().__init__(name)
        self.model = model
        
        if not OPENAI_AVAILABLE:
            raise ImportError("需要安装 openai 库: pip install openai")
        
        # 如果没有提供api_key，尝试从环境变量获取
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        
        if api_key is None:
            raise ValueError("需要提供 OpenAI API Key 或设置 OPENAI_API_KEY 环境变量")
        
        self.client = OpenAI(api_key=api_key)
        self.prompt_template = self._default_prompt_template()
    
    def _default_prompt_template(self) -> str:
        """默认Prompt模板"""
        return """你是一个顶级的战斗特工AI。你的目标是生存并击败所有敌人。

当前游戏状态：
- 你的生命值：{my_health}
- 你的位置：({my_position[0]:.1f}, {my_position[1]:.1f})
- 你的方向：({my_direction[0]:.2f}, {my_direction[1]:.2f})
- 射击冷却：{shoot_cooldown} 回合
- 地图大小：{map_boundary[0]} x {map_boundary[1]}

视野内的敌人：
{enemies_info}

视野内的子弹：
{bullets_info}

你可以执行的动作：
- "move_up": 向上移动
- "move_down": 向下移动
- "move_left": 向左移动
- "move_right": 向右移动
- "turn_left": 向左转向
- "turn_right": 向右转向
- "shoot": 射击（需要冷却时间为0）
- "idle": 不执行任何动作

策略建议：
1. 如果生命值低（<30），优先躲避和移动，远离敌人和子弹
2. 如果敌人正在瞄准你或距离很近，快速移动或转向躲避
3. 如果敌人在你的正前方且距离适中（10-20），优先射击
4. 尽量利用地图边界作为掩护
5. 注意射击冷却时间，不要浪费射击机会
6. 优先攻击血量低的敌人

请根据当前状态，分析最优策略，只返回一个动作字符串，不要有任何其他解释。
你的决策是："""
    
    def step(self, observation: Observation) -> str:
        """通过LLM生成决策"""
        # 格式化敌人信息
        if observation.enemies_in_view:
            enemies_info = "\n".join([
                f"  - {e['name']}: 位置({e['position'][0]:.1f}, {e['position'][1]:.1f}), "
                f"血量{e['health']}, 距离{e['distance']:.1f}"
                for e in observation.enemies_in_view
            ])
        else:
            enemies_info = "  无"
        
        # 格式化子弹信息
        if observation.bullets_in_view:
            bullets_info = "\n".join([
                f"  - 位置({b['position'][0]:.1f}, {b['position'][1]:.1f}), 距离{b['distance']:.1f}"
                for b in observation.bullets_in_view
            ])
        else:
            bullets_info = "  无"
        
        # 构建Prompt
        prompt = self.prompt_template.format(
            my_health=observation.my_health,
            my_position=observation.my_position,
            my_direction=observation.my_direction,
            shoot_cooldown=observation.shoot_cooldown,
            map_boundary=observation.map_boundary,
            enemies_info=enemies_info,
            bullets_info=bullets_info
        )
        
        try:
            # 调用LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个战斗AI，只返回动作指令，不要有任何解释。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=10
            )
            
            action = response.choices[0].message.content.strip().lower()
            
            # 验证动作有效性
            valid_actions = [
                "move_up", "move_down", "move_left", "move_right",
                "turn_left", "turn_right", "shoot", "idle"
            ]
            
            # 如果返回的动作不在有效列表中，尝试提取
            if action not in valid_actions:
                for valid_action in valid_actions:
                    if valid_action in action:
                        action = valid_action
                        break
                else:
                    # 如果无法匹配，返回idle
                    action = "idle"
            
            return action
            
        except Exception as e:
            print(f"PromptAgent {self.name} LLM调用失败: {e}")
            return "idle"
    
    def set_prompt_template(self, template: str):
        """设置自定义Prompt模板"""
        self.prompt_template = template

