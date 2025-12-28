"""
网页版可视化工具 - 生成HTML文件并实时显示游戏
"""
import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path


class WebVisualizer:
    """网页版可视化器 - 生成HTML文件"""
    
    def __init__(self, map_width: int = 100, map_height: int = 100, 
                 canvas_width: int = 800, canvas_height: int = 600):
        self.map_width = map_width
        self.map_height = map_height
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.replay_data = []
        self.agent_colors = {}
        self.color_index = 0
        
        # Agent颜色列表（RGB）
        self.colors = [
            (255, 0, 0),      # 红色
            (0, 255, 0),      # 绿色
            (0, 0, 255),      # 蓝色
            (255, 255, 0),    # 黄色
            (255, 0, 255),    # 品红
            (0, 255, 255),    # 青色
            (255, 165, 0),    # 橙色
            (128, 0, 128),    # 紫色
        ]
    
    def _get_agent_color(self, agent_name: str) -> tuple:
        """获取Agent的颜色"""
        if agent_name not in self.agent_colors:
            self.agent_colors[agent_name] = self.colors[self.color_index % len(self.colors)]
            self.color_index += 1
        return self.agent_colors[agent_name]
    
    def record_frame(self, state_info: Dict[str, Any]):
        """记录一帧游戏状态"""
        # 确保为出现的所有Agent分配稳定颜色
        try:
            agents = state_info.get('agents', [])
            for a in agents:
                name = a.get('name')
                if name:
                    self._get_agent_color(name)
        except Exception:
            pass
        self.replay_data.append(state_info.copy())
    
    def set_winner(self, winner_name: Optional[str]):
        """
        设置获胜者信息（用于超时后按评分判定的情况）
        只更新最后一帧的获胜者信息，不会影响游戏进行中的帧
        """
        if winner_name and self.replay_data:
            # 只更新最后一帧的获胜者信息
            self.replay_data[-1]['winner'] = winner_name
    
    def _map_to_canvas(self, x: float, y: float) -> tuple:
        """将地图坐标转换为画布坐标"""
        canvas_x = int((x / self.map_width) * self.canvas_width)
        canvas_y = int((y / self.map_height) * self.canvas_height)
        return (canvas_x, canvas_y)
    
    def generate_html(self, output_file: str = "game_replay.html", 
                     auto_play: bool = True, fps: int = 10):
        """生成HTML回放文件"""
        # 保障颜色映射：如果有缺失，根据回放数据补全
        if not self.agent_colors:
            try:
                for frame in self.replay_data:
                    for a in frame.get('agents', []):
                        name = a.get('name')
                        if name:
                            self._get_agent_color(name)
            except Exception:
                pass
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI竞技平台 - 游戏回放</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .container {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}
        h1 {{
            text-align: center;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        }}
        #gameCanvas {{
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 10px;
            background: #1a1a2e;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
            display: block;
            margin: 0 auto;
        }}
        .controls {{
            margin-top: 20px;
            text-align: center;
        }}
        button {{
            background: rgba(255, 255, 255, 0.2);
            border: 2px solid rgba(255, 255, 255, 0.3);
            color: white;
            padding: 10px 20px;
            margin: 5px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.3s;
        }}
        button:hover {{
            background: rgba(255, 255, 255, 0.3);
            transform: scale(1.05);
        }}
        .info-panel {{
            margin-top: 20px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .info-card {{
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
            border-left: 4px solid;
        }}
        .info-card h3 {{
            margin: 0 0 10px 0;
            font-size: 18px;
        }}
        .info-card p {{
            margin: 5px 0;
            font-size: 14px;
        }}
        .health-bar {{
            width: 100%;
            height: 20px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            overflow: hidden;
            margin-top: 5px;
        }}
        .health-fill {{
            height: 100%;
            background: linear-gradient(90deg, #ff6b6b, #ee5a6f);
            transition: width 0.3s;
        }}
        .canvas-wrapper {{
            position: relative;
            display: inline-block;
        }}
        #minimap {{
            position: absolute;
            top: 10px;
            right: 10px;
            width: 150px;
            height: 150px;
            background: rgba(0, 0, 0, 0.7);
            border: 2px solid rgba(255, 255, 255, 0.5);
            border-radius: 5px;
            z-index: 10;
            display: none;
        }}
        .toggle-btn {{
            position: absolute;
            top: 10px;
            left: 10px;
            z-index: 10;
            background: rgba(255, 255, 255, 0.2);
            border: 2px solid rgba(255, 255, 255, 0.3);
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏟️ AI竞技平台 - 游戏回放（增强版）</h1>
        <div class="canvas-wrapper">
            <canvas id="gameCanvas" width="{self.canvas_width}" height="{self.canvas_height}"></canvas>
            <canvas id="minimap" width="150" height="150" style="display: none;"></canvas>
            <button class="toggle-btn" onclick="toggleMinimap()">小地图</button>
        </div>
        <div class="controls">
            <button onclick="togglePlay()">播放/暂停</button>
            <button onclick="reset()">重置</button>
            <button onclick="speedUp()">加速</button>
            <button onclick="speedDown()">减速</button>
            <button onclick="toggleTrails()">轨迹: <span id="trailStatus">关闭</span></button>
            <span style="margin-left: 20px;">速度: <span id="speedDisplay">{fps}</span> FPS</span>
            <div style="margin-top:10px;">
                <input id="timeline" type="range" min="0" value="0" step="1" style="width: 600px;" />
                <span id="frameLabel">0</span>/<span id="frameTotal">0</span>
            </div>
        </div>
        <div class="info-panel" id="infoPanel"></div>
        <div id="legend" class="info-panel" style="margin-top:10px;"></div>
    </div>

    <script>
        const gameData = {json.dumps(self.replay_data)};
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');
        const mapWidth = {self.map_width};
        const mapHeight = {self.map_height};
        const canvasWidth = {self.canvas_width};
        const canvasHeight = {self.canvas_height};
        
        let currentFrame = 0;
        let isPlaying = {str(auto_play).lower()};
        let fps = {fps};
        let frameInterval = 1000 / fps;
        let lastTime = 0;
        let animationProgress = 0; // 平滑动画进度 (0-1)
        let showTrails = false; // 是否显示移动轨迹
        let agentTrails = {{}}; // Agent移动轨迹记录
        const TRAIL_LENGTH = 20; // 轨迹长度（帧数）
        
        // 特效系统
        class EffectSystem {{
            constructor() {{
                this.effects = [];
            }}
            
            addExplosion(x, y, color = [255, 100, 0]) {{
                this.effects.push({{
                    type: 'explosion',
                    x, y, color,
                    frame: 0,
                    maxFrames: 15
                }});
            }}
            
            addHitFlash(x, y) {{
                this.effects.push({{
                    type: 'hit',
                    x, y,
                    frame: 0,
                    maxFrames: 5
                }});
            }}
            
            addPickup(x, y, type) {{
                this.effects.push({{
                    type: 'pickup',
                    x, y, itemType: type,
                    frame: 0,
                    maxFrames: 10
                }});
            }}
            
            update() {{
                this.effects = this.effects.filter(e => e.frame < e.maxFrames);
                this.effects.forEach(e => e.frame++);
            }}
            
            render(ctx) {{
                this.effects.forEach(effect => {{
                    const progress = effect.frame / effect.maxFrames;
                    const alpha = 1 - progress;
                    
                    if (effect.type === 'explosion') {{
                        // 爆炸效果：扩散的圆圈
                        const radius = effect.frame * 4;
                        const gradient = ctx.createRadialGradient(
                            effect.x, effect.y, 0,
                            effect.x, effect.y, radius
                        );
                        gradient.addColorStop(0, `rgba(${{effect.color[0]}}, ${{effect.color[1]}}, ${{effect.color[2]}}, ${{alpha * 0.8}})`);
                        gradient.addColorStop(0.5, `rgba(255, 200, 0, ${{alpha * 0.5}})`);
                        gradient.addColorStop(1, `rgba(${{effect.color[0]}}, ${{effect.color[1]}}, ${{effect.color[2]}}, 0)`);
                        ctx.fillStyle = gradient;
                        ctx.beginPath();
                        ctx.arc(effect.x, effect.y, radius, 0, Math.PI * 2);
                        ctx.fill();
                        
                        // 粒子效果
                        for (let i = 0; i < 8; i++) {{
                            const angle = (Math.PI * 2 * i) / 8;
                            const dist = effect.frame * 3;
                            const px = effect.x + Math.cos(angle) * dist;
                            const py = effect.y + Math.sin(angle) * dist;
                            ctx.fillStyle = `rgba(255, 255, 255, ${{alpha}})`;
                            ctx.beginPath();
                            ctx.arc(px, py, 2, 0, Math.PI * 2);
                            ctx.fill();
                        }}
                    }} else if (effect.type === 'hit') {{
                        // 受击闪烁：白色闪光
                        ctx.strokeStyle = `rgba(255, 255, 255, ${{alpha * 0.9}}`;
                        ctx.lineWidth = 4;
                        ctx.beginPath();
                        ctx.arc(effect.x, effect.y, 18 + effect.frame, 0, Math.PI * 2);
                        ctx.stroke();
                    }} else if (effect.type === 'pickup') {{
                        // 拾取光效：旋转的光环
                        const radius = 10 + effect.frame * 2;
                        ctx.strokeStyle = `rgba(100, 255, 100, ${{alpha}}`;
                        ctx.lineWidth = 2;
                        ctx.beginPath();
                        ctx.arc(effect.x, effect.y, radius, 0, Math.PI * 2);
                        ctx.stroke();
                        
                        // 中心闪光
                        ctx.fillStyle = `rgba(255, 255, 255, ${{alpha}}`;
                        ctx.beginPath();
                        ctx.arc(effect.x, effect.y, 3, 0, Math.PI * 2);
                        ctx.fill();
                    }}
                }});
            }}
        }}
        
        const effectSystem = new EffectSystem();
        
        const agentColors = {json.dumps(self.agent_colors)};
        const letters = "COURAGE";
        function letterForObstacle(x, y) {{
            // 基于坐标的稳定映射，确保同一障碍显示同一字母
            const h = Math.abs(Math.floor(x * 31 + y * 17)) % letters.length;
            return letters[h];
        }}
        
        // 平滑插值函数
        function lerp(start, end, t) {{
            return start + (end - start) * t;
        }}
        
        function interpolatePosition(prevPos, nextPos, t) {{
            return {{
                x: lerp(prevPos[0], nextPos[0], t),
                y: lerp(prevPos[1], nextPos[1], t)
            }};
        }}

        // 初始化时间轴范围
        const timeline = document.getElementById('timeline');
        const frameLabel = document.getElementById('frameLabel');
        const frameTotal = document.getElementById('frameTotal');
        frameTotal.textContent = Math.max(0, gameData.length - 1);
        timeline.max = Math.max(0, gameData.length - 1);
        timeline.oninput = function(e) {{
            const v = parseInt(e.target.value);
            currentFrame = Math.min(Math.max(0, v), gameData.length - 1);
            isPlaying = false;
            drawFrame(currentFrame);
        }};

        // 键盘快捷键：空格播放/暂停，左右箭头逐帧
        window.addEventListener('keydown', (e) => {{
            if (e.code === 'Space') {{
                e.preventDefault();
                togglePlay();
            }} else if (e.code === 'ArrowRight') {{
                isPlaying = false;
                currentFrame = Math.min(currentFrame + 1, gameData.length - 1);
                drawFrame(currentFrame);
            }} else if (e.code === 'ArrowLeft') {{
                isPlaying = false;
                currentFrame = Math.max(currentFrame - 1, 0);
                drawFrame(currentFrame);
            }}
        }});

        function updateLegend(frame) {{
            const legend = document.getElementById('legend');
            legend.innerHTML = '';
            const container = document.createElement('div');
            container.className = 'info-card';
            container.style.borderLeftColor = '#94a3b8';
            const list = document.createElement('div');
            for (const a of frame.agents) {{
                const color = agentColors[a.name] || [255,255,255];
                const colorStr = `rgb(${{color[0]}}, ${{color[1]}}, ${{color[2]}})`;
                const row = document.createElement('div');
                row.style.display = 'flex';
                row.style.alignItems = 'center';
                row.style.gap = '8px';
                row.style.margin = '4px 0';
                const swatch = document.createElement('span');
                swatch.style.display = 'inline-block';
                swatch.style.width = '14px';
                swatch.style.height = '14px';
                swatch.style.background = colorStr;
                swatch.style.border = '1px solid rgba(255,255,255,0.6)';
                swatch.style.borderRadius = '3px';
                const label = document.createElement('span');
                label.textContent = a.name;
                row.appendChild(swatch);
                row.appendChild(label);
                list.appendChild(row);
            }}
            container.appendChild(list);
            legend.appendChild(container);
        }}
        
        function mapToCanvas(x, y) {{
            return {{
                x: (x / mapWidth) * canvasWidth,
                y: (y / mapHeight) * canvasHeight
            }};
        }}
        
        function drawFrame(frameIndex) {{
            if (frameIndex >= gameData.length) {{
                isPlaying = false;
                return;
            }}
            
            const frame = gameData[frameIndex];
            const prev = frameIndex > 0 ? gameData[frameIndex - 1] : null;
            const next = frameIndex < gameData.length - 1 ? gameData[frameIndex + 1] : null;
            
            // 更新时间轴与标签
            timeline.value = frameIndex;
            frameLabel.textContent = frameIndex;
            
            // 计算平滑动画插值进度
            if (isPlaying && next) {{
                animationProgress += 0.15; // 动画速度
                if (animationProgress >= 1) {{
                    animationProgress = 0;
                }}
            }} else {{
                animationProgress = 0;
            }}
            
            // 检测击杀和受击事件
            if (prev) {{
                const prevAgents = new Map(prev.agents.map(a => [a.name, a]));
                frame.agents.forEach(agent => {{
                    const prevAgent = prevAgents.get(agent.name);
                    if (prevAgent) {{
                        // 检测击杀（从存活到死亡）
                        if (prevAgent.health > 0 && agent.health <= 0) {{
                            const pos = mapToCanvas(agent.position[0], agent.position[1]);
                            effectSystem.addExplosion(pos.x, pos.y);
                        }}
                        // 检测受击（血量下降）
                        else if (prevAgent.health > agent.health && agent.health > 0) {{
                            const pos = mapToCanvas(agent.position[0], agent.position[1]);
                            effectSystem.addHitFlash(pos.x, pos.y);
                        }}
                    }}
                }});
            }}
            
            // 更新轨迹记录
            if (showTrails) {{
                frame.agents.forEach(agent => {{
                    if (agent.health > 0) {{
                        if (!agentTrails[agent.name]) {{
                            agentTrails[agent.name] = [];
                        }}
                        agentTrails[agent.name].push([agent.position[0], agent.position[1]]);
                        if (agentTrails[agent.name].length > TRAIL_LENGTH) {{
                            agentTrails[agent.name].shift();
                        }}
                    }} else {{
                        // Agent死亡时清除轨迹
                        delete agentTrails[agent.name];
                    }}
                }});
            }}
            
            // 更新特效系统
            effectSystem.update();
            
            // 清空画布
            ctx.fillStyle = '#1a1a2e';
            ctx.fillRect(0, 0, canvasWidth, canvasHeight);
            
            // 绘制网格
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
            ctx.lineWidth = 1;
            const gridSize = 20;
            for (let x = 0; x < canvasWidth; x += gridSize) {{
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, canvasHeight);
                ctx.stroke();
            }}
            for (let y = 0; y < canvasHeight; y += gridSize) {{
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(canvasWidth, y);
                ctx.stroke();
            }}
            
            // 绘制障碍物（墙体矩形）
            if (frame.obstacles) {{
                ctx.fillStyle = 'rgba(200,200,200,0.8)';
                ctx.strokeStyle = 'rgba(255,255,255,0.4)';
                ctx.lineWidth = 2;
                for (const obs of frame.obstacles) {{
                    const r = obs.rect; // [x, y, w, h] in map coords
                    const p1 = mapToCanvas(r[0], r[1]);
                    const p2 = mapToCanvas(r[0] + r[2], r[1] + r[3]);
                    const rw = p2.x - p1.x;
                    const rh = p2.y - p1.y;
                    ctx.beginPath();
                    ctx.rect(p1.x, p1.y, rw, rh);
                    ctx.fill();
                    ctx.stroke();
                }}
            }}
            
            // 绘制补给
            if (frame.supplies) {{
                for (const s of frame.supplies) {{
                    const pos = mapToCanvas(s.position[0], s.position[1]);
                    let color = '#4ade80';
                    if (s.type.startsWith('ammo')) color = '#60a5fa';
                    if (s.type.startsWith('weapon')) color = '#f472b6';
                    ctx.fillStyle = color;
                    ctx.strokeStyle = 'white';
                    ctx.lineWidth = 1.5;
                    ctx.beginPath();
                    ctx.rect(pos.x - 6, pos.y - 6, 12, 12);
                    ctx.fill();
                    ctx.stroke();
                }}
            }}
            
            // 绘制子弹（不同武器有不同效果）
            for (const bullet of frame.bullets) {{
                const pos = mapToCanvas(bullet.position[0], bullet.position[1]);
                const ownerColor = agentColors[bullet.owner] || [255, 255, 255];
                const ownerColorStr = `rgb(${{ownerColor[0]}}, ${{ownerColor[1]}}, ${{ownerColor[2]}})`;
                const kind = bullet.kind || 'normal';
                const dir = bullet.direction;
                
                if (kind === 'normal') {{
                    // 普通子弹：小圆点，增强轨迹
                    // 发光效果
                    const glowGradient = ctx.createRadialGradient(pos.x, pos.y, 0, pos.x, pos.y, 6);
                    glowGradient.addColorStop(0, `rgba(${{ownerColor[0]}}, ${{ownerColor[1]}}, ${{ownerColor[2]}}, 0.8)`);
                    glowGradient.addColorStop(1, `rgba(${{ownerColor[0]}}, ${{ownerColor[1]}}, ${{ownerColor[2]}}, 0)`);
                    ctx.fillStyle = glowGradient;
                    ctx.beginPath();
                    ctx.arc(pos.x, pos.y, 6, 0, Math.PI * 2);
                    ctx.fill();
                    
                    // 子弹主体
                    ctx.fillStyle = ownerColorStr;
                    ctx.beginPath();
                    ctx.arc(pos.x, pos.y, 3, 0, Math.PI * 2);
                    ctx.fill();
                    
                    // 增强轨迹（更长更明显）
                    const trailLength = 15;
                    ctx.strokeStyle = `rgba(${{ownerColor[0]}}, ${{ownerColor[1]}}, ${{ownerColor[2]}}, 0.5)`;
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.moveTo(pos.x, pos.y);
                    ctx.lineTo(pos.x - dir[0] * trailLength, pos.y - dir[1] * trailLength);
                    ctx.stroke();
                }} else if (kind === 'shotgun') {{
                    // 霰弹枪：多个小点，散射效果
                    ctx.fillStyle = ownerColorStr;
                    for (let i = 0; i < 3; i++) {{
                        const offset = (i - 1) * 2;
                        const offsetX = -dir[1] * offset;
                        const offsetY = dir[0] * offset;
                        ctx.beginPath();
                        ctx.arc(pos.x + offsetX, pos.y + offsetY, 2.5, 0, Math.PI * 2);
                        ctx.fill();
                    }}
                    
                    // 轨迹（多条）
                    ctx.strokeStyle = `rgba(${{ownerColor[0]}}, ${{ownerColor[1]}}, ${{ownerColor[2]}}, 0.4)`;
                    ctx.lineWidth = 1;
                    for (let i = 0; i < 3; i++) {{
                        const offset = (i - 1) * 2;
                        const offsetX = -dir[1] * offset;
                        const offsetY = dir[0] * offset;
                        ctx.beginPath();
                        ctx.moveTo(pos.x + offsetX, pos.y + offsetY);
                        ctx.lineTo(pos.x + offsetX - dir[0] * 6, pos.y + offsetY - dir[1] * 6);
                        ctx.stroke();
                    }}
                }} else if (kind === 'sniper') {{
                    // 狙击枪：细长线条，高亮轨迹，带光晕
                    // 光晕效果
                    const gradient = ctx.createRadialGradient(pos.x, pos.y, 0, pos.x, pos.y, 8);
                    gradient.addColorStop(0, `rgba(${{ownerColor[0]}}, ${{ownerColor[1]}}, ${{ownerColor[2]}}, 0.6)`);
                    gradient.addColorStop(1, `rgba(${{ownerColor[0]}}, ${{ownerColor[1]}}, ${{ownerColor[2]}}, 0)`);
                    ctx.fillStyle = gradient;
                    ctx.beginPath();
                    ctx.arc(pos.x, pos.y, 8, 0, Math.PI * 2);
                    ctx.fill();
                    
                    // 细长子弹（沿方向延伸）
                    ctx.strokeStyle = ownerColorStr;
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.moveTo(pos.x - dir[0] * 6, pos.y - dir[1] * 6);
                    ctx.lineTo(pos.x + dir[0] * 6, pos.y + dir[1] * 6);
                    ctx.stroke();
                    
                    // 中心亮点
                    ctx.fillStyle = '#ffffff';
                    ctx.beginPath();
                    ctx.arc(pos.x, pos.y, 1.5, 0, Math.PI * 2);
                    ctx.fill();
                    
                    // 长轨迹
                    ctx.strokeStyle = `rgba(${{ownerColor[0]}}, ${{ownerColor[1]}}, ${{ownerColor[2]}}, 0.7)`;
                    ctx.lineWidth = 1.5;
                    ctx.beginPath();
                    ctx.moveTo(pos.x, pos.y);
                    ctx.lineTo(pos.x - dir[0] * 20, pos.y - dir[1] * 20);
                    ctx.stroke();
                }} else if (kind === 'rocket') {{
                    // 火箭筒：大圆点，带尾焰效果
                    // 尾焰（渐变）
                    const tailLength = 12;
                    const tailStart = {{
                        x: pos.x - dir[0] * tailLength,
                        y: pos.y - dir[1] * tailLength
                    }};
                    const tailGradient = ctx.createLinearGradient(
                        tailStart.x, tailStart.y, pos.x, pos.y
                    );
                    tailGradient.addColorStop(0, `rgba(${{ownerColor[0]}}, ${{ownerColor[1]}}, ${{ownerColor[2]}}, 0)`);
                    tailGradient.addColorStop(0.5, `rgba(255, 165, 0, 0.6)`);
                    tailGradient.addColorStop(1, `rgba(255, 100, 0, 0.8)`);
                    
                    ctx.strokeStyle = tailGradient;
                    ctx.lineWidth = 4;
                    ctx.beginPath();
                    ctx.moveTo(tailStart.x, tailStart.y);
                    ctx.lineTo(pos.x, pos.y);
                    ctx.stroke();
                    
                    // 火箭主体（大圆点）
                    ctx.fillStyle = ownerColorStr;
                    ctx.beginPath();
                    ctx.arc(pos.x, pos.y, 5, 0, Math.PI * 2);
                    ctx.fill();
                    
                    // 外圈高亮
                    ctx.strokeStyle = '#ffaa00';
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.arc(pos.x, pos.y, 5, 0, Math.PI * 2);
                    ctx.stroke();
                    
                    // 中心亮点
                    ctx.fillStyle = '#ffffff';
                    ctx.beginPath();
                    ctx.arc(pos.x, pos.y, 2, 0, Math.PI * 2);
                    ctx.fill();
                }}
            }}
            
            // 绘制移动轨迹
            if (showTrails) {{
                for (const [agentName, trail] of Object.entries(agentTrails)) {{
                    if (trail.length < 2) continue;
                    const color = agentColors[agentName] || [255, 255, 255];
                    ctx.strokeStyle = `rgba(${{color[0]}}, ${{color[1]}}, ${{color[2]}}, 0.3)`;
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    for (let i = 0; i < trail.length - 1; i++) {{
                        const p1 = mapToCanvas(trail[i][0], trail[i][1]);
                        const p2 = mapToCanvas(trail[i + 1][0], trail[i + 1][1]);
                        if (i === 0) {{
                            ctx.moveTo(p1.x, p1.y);
                        }}
                        ctx.lineTo(p2.x, p2.y);
                    }}
                    ctx.stroke();
                }}
            }}
            
            // 绘制Agent
            for (const agent of frame.agents) {{
                if (agent.health <= 0) continue;
                
                // 平滑插值位置
                let displayPos;
                if (next && animationProgress > 0) {{
                    const nextAgent = next.agents.find(a => a.name === agent.name);
                    if (nextAgent && nextAgent.health > 0) {{
                        const interpPos = interpolatePosition(
                            agent.position,
                            nextAgent.position,
                            animationProgress
                        );
                        displayPos = mapToCanvas(interpPos.x, interpPos.y);
                    }} else {{
                        displayPos = mapToCanvas(agent.position[0], agent.position[1]);
                    }}
                }} else {{
                    displayPos = mapToCanvas(agent.position[0], agent.position[1]);
                }}
                
                const color = agentColors[agent.name] || [255, 255, 255];
                const colorStr = `rgb(${{color[0]}}, ${{color[1]}}, ${{color[2]}})`;
                
                // 绘制Agent身体（圆形）
                ctx.fillStyle = colorStr;
                ctx.beginPath();
                ctx.arc(displayPos.x, displayPos.y, 12, 0, Math.PI * 2);
                ctx.fill();

                // 受击高亮（上一帧到这一帧血量下降）
                if (prev) {{
                    const pa = prev.agents.find(a => a.name === agent.name);
                    if (pa && pa.health > agent.health) {{
                        ctx.strokeStyle = 'rgba(239,68,68,0.8)'; // 红色高亮
                        ctx.lineWidth = 3;
                        ctx.beginPath();
                        ctx.arc(displayPos.x, displayPos.y, 16, 0, Math.PI * 2);
                        ctx.stroke();
                    }}
                }}
                
                // 绘制边框
                ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
                ctx.lineWidth = 2;
                ctx.stroke();
                
                // 绘制方向指示
                const dir = agent.direction;
                ctx.strokeStyle = 'white';
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.moveTo(displayPos.x, displayPos.y);
                ctx.lineTo(displayPos.x + dir[0] * 15, displayPos.y + dir[1] * 15);
                ctx.stroke();
                
                // 绘制Agent名称
                ctx.fillStyle = 'white';
                ctx.font = 'bold 12px Arial';
                ctx.textAlign = 'center';
                ctx.fillText(agent.name, displayPos.x, displayPos.y - 20);
                
                // 绘制血量条
                const healthPercent = agent.health / 100;
                const barWidth = 30;
                const barHeight = 4;
                ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
                ctx.fillRect(displayPos.x - barWidth/2, displayPos.y + 18, barWidth, barHeight);
                ctx.fillStyle = healthPercent > 0.5 ? '#4ade80' : healthPercent > 0.25 ? '#fbbf24' : '#ef4444';
                ctx.fillRect(displayPos.x - barWidth/2, displayPos.y + 18, barWidth * healthPercent, barHeight);
                
                // 绘制武器/弹药简要图标
                const w = (agent.weapon || 'normal');
                if (w && w !== 'normal') {{
                    ctx.fillStyle = 'rgba(0,0,0,0.6)';
                    ctx.fillRect(displayPos.x - 16, displayPos.y - 34, 32, 12);
                    ctx.fillStyle = '#fff';
                    ctx.font = '10px Arial';
                    const ammo = (agent.ammo && agent.ammo[w]) ? agent.ammo[w] : 0;
                    ctx.fillText(w.substring(0,1).toUpperCase()+':'+ammo, displayPos.x, displayPos.y - 25);
                }}
            }}
            
            // 渲染特效
            effectSystem.render(ctx);
            
            // 更新信息面板
            updateInfoPanel(frame);
            updateLegend(frame);
            
            // 绘制小地图
            drawMinimap(frame);
        }}
        
        function updateInfoPanel(frame) {{
            const panel = document.getElementById('infoPanel');
            panel.innerHTML = '';
            
            // 回合信息
            const roundCard = document.createElement('div');
            roundCard.className = 'info-card';
            roundCard.style.borderLeftColor = '#3b82f6';
            roundCard.innerHTML = `
                <h3>回合信息</h3>
                <p>回合: ${{frame.turn}}</p>
                <p>存活: ${{frame.alive_count}}</p>
                ${{frame.winner ? `<p style="color: #fbbf24; font-weight: bold;">获胜者: ${{frame.winner}}</p>` : ''}}
            `;
            panel.appendChild(roundCard);
            
            // Agent信息
            for (const agent of frame.agents) {{
                if (agent.health <= 0) continue;
                const color = agentColors[agent.name] || [255, 255, 255];
                const colorStr = `rgb(${{color[0]}}, ${{color[1]}}, ${{color[2]}})`;
                
                const agentCard = document.createElement('div');
                agentCard.className = 'info-card';
                agentCard.style.borderLeftColor = colorStr;
                agentCard.innerHTML = `
                    <h3>${{agent.name}}</h3>
                    <p>队伍: ${{agent.team_id !== null && agent.team_id !== undefined ? agent.team_id : '-'}}</p>
                    <p>血量: ${{agent.health}}/100</p>
                    <div class="health-bar">
                        <div class="health-fill" style="width: ${{agent.health}}%"></div>
                    </div>
                    <p>击杀: ${{agent.kills}}</p>
                    <p>位置: (${{agent.position[0].toFixed(1)}}, ${{agent.position[1].toFixed(1)}})</p>
                    <p>武器: ${{agent.weapon || 'normal'}}</p>
                    ${{agent.weapon && agent.weapon !== 'normal' ? `<p>弹药: ${{agent.ammo && agent.ammo[agent.weapon] !== undefined ? agent.ammo[agent.weapon] : 0}}</p>` : ''}}
                `;
                panel.appendChild(agentCard);
            }}
        }}
        
        function togglePlay() {{
            isPlaying = !isPlaying;
        }}
        
        function reset() {{
            currentFrame = 0;
            animationProgress = 0;
            agentTrails = {{}};
            effectSystem.effects = [];
            isPlaying = true;
            drawFrame(currentFrame);
        }}
        
        function speedUp() {{
            fps = Math.min(fps + 5, 60);
            frameInterval = 1000 / fps;
            document.getElementById('speedDisplay').textContent = fps;
        }}
        
        function speedDown() {{
            fps = Math.max(fps - 5, 5);
            frameInterval = 1000 / fps;
            document.getElementById('speedDisplay').textContent = fps;
        }}
        
        function toggleTrails() {{
            showTrails = !showTrails;
            document.getElementById('trailStatus').textContent = showTrails ? '开启' : '关闭';
            if (!showTrails) {{
                agentTrails = {{}};
            }}
        }}
        
        function toggleMinimap() {{
            const minimap = document.getElementById('minimap');
            minimap.style.display = minimap.style.display === 'none' ? 'block' : 'none';
        }}
        
        function drawMinimap(frame) {{
            const minimap = document.getElementById('minimap');
            if (minimap.style.display === 'none') return;
            
            const minimapCtx = minimap.getContext('2d');
            const minimapSize = 150;
            const scale = minimapSize / Math.max(mapWidth, mapHeight);
            
            // 清空
            minimapCtx.fillStyle = 'rgba(0, 0, 0, 0.8)';
            minimapCtx.fillRect(0, 0, minimapSize, minimapSize);
            
            // 绘制障碍物
            if (frame.obstacles) {{
                minimapCtx.fillStyle = 'rgba(200, 200, 200, 0.6)';
                for (const obs of frame.obstacles) {{
                    const r = obs.rect;
                    minimapCtx.fillRect(r[0] * scale, r[1] * scale, r[2] * scale, r[3] * scale);
                }}
            }}
            
            // 绘制Agent
            for (const agent of frame.agents) {{
                if (agent.health <= 0) continue;
                const color = agentColors[agent.name] || [255, 255, 255];
                minimapCtx.fillStyle = `rgb(${{color[0]}}, ${{color[1]}}, ${{color[2]}})`;
                minimapCtx.beginPath();
                minimapCtx.arc(
                    agent.position[0] * scale,
                    agent.position[1] * scale,
                    3, 0, Math.PI * 2
                );
                minimapCtx.fill();
            }}
            
            // 绘制子弹
            minimapCtx.fillStyle = 'rgba(255, 255, 255, 0.8)';
            for (const bullet of frame.bullets) {{
                minimapCtx.beginPath();
                minimapCtx.arc(
                    bullet.position[0] * scale,
                    bullet.position[1] * scale,
                    1, 0, Math.PI * 2
                );
                minimapCtx.fill();
            }}
        }}
        
        function gameLoop(currentTime) {{
            // 即使不播放也要重绘（用于平滑动画和特效）
            if (isPlaying && currentTime - lastTime >= frameInterval) {{
                drawFrame(currentFrame);
                currentFrame++;
                lastTime = currentTime;
                animationProgress = 0; // 重置动画进度
            }} else if (!isPlaying) {{
                // 暂停时也要重绘（用于特效动画）
                drawFrame(currentFrame);
            }}
            requestAnimationFrame(gameLoop);
        }}
        
        // 初始化
        drawFrame(0);
        requestAnimationFrame(gameLoop);
    </script>
</body>
</html>
"""
        
        # 确保输出目录存在
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入HTML文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_file
    
    def render_replay(self, output_file: str = "game_replay.html", 
                     auto_play: bool = True, fps: int = 10):
        """生成并打开回放文件"""
        html_file = self.generate_html(output_file, auto_play, fps)
        print(f"已生成回放文件: {html_file}")
        print(f"请在浏览器中打开查看: file://{os.path.abspath(html_file)}")
        return html_file

