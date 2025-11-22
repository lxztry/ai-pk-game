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
    <title>AI斗兽场 - 游戏回放</title>
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
    </style>
</head>
<body>
    <div class="container">
        <h1>🏟️ AI斗兽场 - 游戏回放</h1>
        <canvas id="gameCanvas" width="{self.canvas_width}" height="{self.canvas_height}"></canvas>
        <div class="controls">
            <button onclick="togglePlay()">播放/暂停</button>
            <button onclick="reset()">重置</button>
            <button onclick="speedUp()">加速</button>
            <button onclick="speedDown()">减速</button>
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
        
        const agentColors = {json.dumps(self.agent_colors)};
        const letters = "COURAGE";
        function letterForObstacle(x, y) {{
            // 基于坐标的稳定映射，确保同一障碍显示同一字母
            const h = Math.abs(Math.floor(x * 31 + y * 17)) % letters.length;
            return letters[h];
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
            // 更新时间轴与标签
            timeline.value = frameIndex;
            frameLabel.textContent = frameIndex;
            
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
            
            // 绘制子弹
            for (const bullet of frame.bullets) {{
                const pos = mapToCanvas(bullet.position[0], bullet.position[1]);
                // 颜色跟随发射者
                const ownerColor = agentColors[bullet.owner] || [255, 255, 255];
                const ownerColorStr = `rgb(${{ownerColor[0]}}, ${{ownerColor[1]}}, ${{ownerColor[2]}})`;
                ctx.fillStyle = ownerColorStr;
                ctx.beginPath();
                const kind = bullet.kind || 'normal';
                const r = kind === 'rocket' ? 4 : (kind === 'sniper' ? 2.5 : 3);
                ctx.arc(pos.x, pos.y, r, 0, Math.PI * 2);
                ctx.fill();
                
                // 子弹轨迹
                // 使用发射者颜色的半透明线条，狙击更亮
                const trailAlpha = kind === 'sniper' ? 0.6 : 0.35;
                ctx.strokeStyle = `rgba(${{ownerColor[0]}}, ${{ownerColor[1]}}, ${{ownerColor[2]}}, ${{trailAlpha}})`;
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(pos.x, pos.y);
                ctx.lineTo(pos.x - bullet.direction[0] * 10, pos.y - bullet.direction[1] * 10);
                ctx.stroke();
            }}
            
            // 绘制Agent
            for (const agent of frame.agents) {{
                if (agent.health <= 0) continue;
                
                const pos = mapToCanvas(agent.position[0], agent.position[1]);
                const color = agentColors[agent.name] || [255, 255, 255];
                const colorStr = `rgb(${{color[0]}}, ${{color[1]}}, ${{color[2]}})`;
                
                // 绘制Agent身体（圆形）
                ctx.fillStyle = colorStr;
                ctx.beginPath();
                ctx.arc(pos.x, pos.y, 12, 0, Math.PI * 2);
                ctx.fill();

                // 受击高亮（上一帧到这一帧血量下降）
                if (prev) {{
                    const pa = prev.agents.find(a => a.name === agent.name);
                    if (pa && pa.health > agent.health) {{
                        ctx.strokeStyle = 'rgba(239,68,68,0.8)'; // 红色高亮
                        ctx.lineWidth = 3;
                        ctx.beginPath();
                        ctx.arc(pos.x, pos.y, 16, 0, Math.PI * 2);
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
                ctx.moveTo(pos.x, pos.y);
                ctx.lineTo(pos.x + dir[0] * 15, pos.y + dir[1] * 15);
                ctx.stroke();
                
                // 绘制Agent名称
                ctx.fillStyle = 'white';
                ctx.font = 'bold 12px Arial';
                ctx.textAlign = 'center';
                ctx.fillText(agent.name, pos.x, pos.y - 20);
                
                // 绘制血量条
                const healthPercent = agent.health / 100;
                const barWidth = 30;
                const barHeight = 4;
                ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
                ctx.fillRect(pos.x - barWidth/2, pos.y + 18, barWidth, barHeight);
                ctx.fillStyle = healthPercent > 0.5 ? '#4ade80' : healthPercent > 0.25 ? '#fbbf24' : '#ef4444';
                ctx.fillRect(pos.x - barWidth/2, pos.y + 18, barWidth * healthPercent, barHeight);
                
                // 绘制武器/弹药简要图标
                const w = (agent.weapon || 'normal');
                if (w && w !== 'normal') {{
                    ctx.fillStyle = 'rgba(0,0,0,0.6)';
                    ctx.fillRect(pos.x - 16, pos.y - 34, 32, 12);
                    ctx.fillStyle = '#fff';
                    ctx.font = '10px Arial';
                    const ammo = (agent.ammo && agent.ammo[w]) ? agent.ammo[w] : 0;
                    ctx.fillText(w.substring(0,1).toUpperCase()+':'+ammo, pos.x, pos.y - 25);
                }}
            }}
            
            // 更新信息面板
            updateInfoPanel(frame);
            updateLegend(frame);
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
        
        function gameLoop(currentTime) {{
            if (isPlaying && currentTime - lastTime >= frameInterval) {{
                drawFrame(currentFrame);
                currentFrame++;
                lastTime = currentTime;
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

