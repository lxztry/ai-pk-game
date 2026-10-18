"""
SVG 美术资源库

不依赖外部图片文件，所有素材用代码画"基础设施"——SVG 内联。
加载快、风格统一、可任意缩放。

包括：
- 角色（多种性格风格）
- 障碍物（砖块、箱子、骷髅标记）
- 武器（霰弹枪图标、狙击镜图标）
- 补给（血包心形、弹药箱）
- 子弹（彩色圆形带尾迹）
- 特效（爆炸放射线、受击闪光、击杀 ✕）
"""
from typing import Optional


# ---------- 角色渲染 ----------

def character_svg(color: str = "#f43",
                 direction_deg: float = 0,
                 weapon: str = "normal",
                 health_pct: float = 1.0,
                 size: int = 36,
                 face: str = "happy") -> str:
    """渲染一个可爱的小人

    Args:
        color: 主色（红/蓝/绿/紫）
        direction_deg: 朝向角度（0 = 右）
        weapon: normal / shotgun / sniper / rocket
        health_pct: 血量百分比（0-1）
        size: 大小像素
        face: 表情 happy / angry / scared / dead
    """
    eye_color = "#fff"
    pupil_color = "#000"
    if face == "angry":
        eye_color = "#fee"
        pupil_color = "#900"
    elif face == "scared":
        eye_color = "#cff"
        pupil_color = "#006"
    elif face == "dead":
        eye_color = "#aaa"
        pupil_color = "#555"

    # 武器颜色
    weapon_color = {
        "normal": "#888",
        "shotgun": "#f97316",
        "sniper": "#a855f7",
        "rocket": "#dc2626",
    }.get(weapon, "#888")

    cx, cy = size // 2, size // 2
    r = size // 3

    return f'''<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
  <!-- 阴影 -->
  <ellipse cx="{cx}" cy="{cy+r+2}" rx="{r}" ry="3" fill="rgba(0,0,0,0.3)"/>
  <!-- 身体 -->
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" stroke="#000" stroke-width="2"/>
  <!-- 高光 -->
  <circle cx="{cx-r//3}" cy="{cy-r//3}" r="{r//3}" fill="rgba(255,255,255,0.4)"/>
  <!-- 眼睛 -->
  <circle cx="{cx-3}" cy="{cy-2}" r="4" fill="{eye_color}"/>
  <circle cx="{cx+5}" cy="{cy-2}" r="4" fill="{eye_color}"/>
  <!-- 瞳孔（看向 direction） -->
  <circle cx="{cx-3 + int(cx*0.2*pow(-1, direction_deg>180))}" cy="{cy-2}" r="2" fill="{pupil_color}"/>
  <circle cx="{cx+5 + int(cx*0.2*pow(-1, direction_deg>180))}" cy="{cy-2}" r="2" fill="{pupil_color}"/>
  <!-- 嘴 -->
  {'<path d="M {cx-3} {cy+5} Q {cx} {cy+8} {cx+5} {cy+5}" stroke="#000" stroke-width="1.5" fill="none"/>' if face == "happy" else
   '<line x1="{cx-4}" y1="{cy+6}" x2="{cx+4}" y2="{cy+6}" stroke="#000" stroke-width="1.5"/>' if face == "angry" else
   '<circle cx="{cx}" cy="{cy+6}" r="2" fill="none" stroke="#000" stroke-width="1.5"/>' if face == "scared" else
   '<line x1="{cx-3}" y1="{cy+3}" x2="{cx+3}" y2="{cy+9}" stroke="#000" stroke-width="1.5"/>\
    <line x1="{cx-3}" y1="{cy+9}" x2="{cx+3}" y2="{cy+3}" stroke="#000" stroke-width="1.5"/>'}
  <!-- 武器 -->
  <g transform="rotate({direction_deg} {cx} {cy})">
    <rect x="{cx+r-2}" y="{cy-2}" width="6" height="4" fill="{weapon_color}" stroke="#000" stroke-width="0.5"/>
  </g>
  <!-- 血量环 -->
  <circle cx="{cx}" cy="{cy}" r="{r+3}" fill="none" stroke="#333" stroke-width="2"/>
  <circle cx="{cx}" cy="{cy}" r="{r+3}" fill="none" stroke="{health_pct_color(health_pct)}" stroke-width="2"
          stroke-dasharray="{2*3.14159*(r+3)}" stroke-dashoffset="{2*3.14159*(r+3)*(1-health_pct)}"
          transform="rotate(-90 {cx} {cy})"/>
</svg>'''


def health_pct_color(pct: float) -> str:
    """根据血量返回颜色"""
    if pct > 0.5:
        return "#22c55e"  # 绿
    elif pct > 0.25:
        return "#eab308"  # 黄
    return "#ef4444"  # 红


# ---------- 障碍物 ----------

def obstacle_svg(kind: str = "brick", size: int = 32) -> str:
    """障碍物 SVG

    Args:
        kind: brick / box / skull / crate
    """
    if kind == "brick":
        return f'''<svg width="{size}" height="{size}" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
  <rect x="1" y="1" width="30" height="30" fill="#92400e" stroke="#000" stroke-width="1.5"/>
  <rect x="1" y="1" width="30" height="10" fill="rgba(0,0,0,0.2)"/>
  <line x1="0" y1="11" x2="32" y2="11" stroke="#000" stroke-width="0.5" stroke-dasharray="3,2"/>
  <line x1="11" y1="0" x2="11" y2="11" stroke="#000" stroke-width="0.5"/>
  <line x1="21" y1="11" x2="21" y2="32" stroke="#000" stroke-width="0.5"/>
  <text x="16" y="22" font-size="8" fill="rgba(255,255,255,0.4)" text-anchor="middle">墙</text>
</svg>'''
    elif kind == "box":
        return f'''<svg width="{size}" height="{size}" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
  <rect x="1" y="1" width="30" height="30" fill="#a16207" stroke="#000" stroke-width="1.5"/>
  <path d="M 1 1 L 31 31 M 31 1 L 1 31" stroke="rgba(0,0,0,0.3)" stroke-width="1"/>
  <text x="16" y="20" font-size="14" text-anchor="middle">📦</text>
</svg>'''
    elif kind == "skull":
        return f'''<svg width="{size}" height="{size}" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
  <circle cx="16" cy="16" r="13" fill="#e5e5e5" stroke="#000" stroke-width="1.5"/>
  <circle cx="11" cy="13" r="3" fill="#000"/>
  <circle cx="21" cy="13" r="3" fill="#000"/>
  <line x1="16" y1="13" x2="16" y2="22" stroke="#000" stroke-width="2"/>
</svg>'''
    else:  # crate
        return f'''<svg width="{size}" height="{size}" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
  <rect x="1" y="1" width="30" height="30" fill="#854d0e" stroke="#000" stroke-width="1.5"/>
  <line x1="1" y1="11" x2="31" y2="11" stroke="#000" stroke-width="1"/>
  <line x1="1" y1="21" x2="31" y2="21" stroke="#000" stroke-width="1"/>
  <line x1="11" y1="1" x2="11" y2="31" stroke="#000" stroke-width="1"/>
  <line x1="21" y1="1" x2="21" y2="31" stroke="#000" stroke-width="1"/>
</svg>'''


# ---------- 子弹 ----------

def bullet_svg(kind: str = "normal", size: int = 14) -> str:
    """子弹 SVG"""
    colors = {
        "normal": "#fbbf24",
        "shotgun": "#f97316",
        "sniper": "#a855f7",
        "rocket": "#dc2626",
    }
    color = colors.get(kind, "#fbbf24")
    if kind == "rocket":
        return f'''<svg width="{size}" height="{size}" viewBox="0 0 14 14" xmlns="http://www.w3.org/2000/svg">
  <circle cx="7" cy="7" r="6" fill="{color}" stroke="#000" stroke-width="1"/>
  <path d="M 7 1 L 5 4 L 9 4 Z" fill="#fef3c7"/>
  <circle cx="5" cy="7" r="1" fill="#fff"/>
  <circle cx="9" cy="7" r="1" fill="#fff"/>
</svg>'''
    return f'''<svg width="{size}" height="{size}" viewBox="0 0 14 14" xmlns="http://www.w3.org/2000/svg">
  <circle cx="7" cy="7" r="5" fill="{color}" stroke="#000" stroke-width="1"/>
  <circle cx="5" cy="5" r="2" fill="#fff" opacity="0.6"/>
</svg>'''


# ---------- 补给 ----------

def supply_svg(kind: str = "health", size: int = 24) -> str:
    """补给 SVG: health/health/ammo/shotgun/sniper/rocket"""
    if kind == "health":
        return f'''<svg width="{size}" height="{size}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <path d="M 12 21 C 4 14 2 9 5 6 C 8 3 11 4 12 7 C 13 4 16 3 19 6 C 22 9 20 14 12 21 Z"
        fill="#ef4444" stroke="#000" stroke-width="1.5"/>
  <path d="M 12 21 Q 8 16 6 13" stroke="#fff" stroke-width="2" fill="none" opacity="0.4"/>
  <text x="12" y="14" font-size="7" text-anchor="middle" fill="#fff" font-weight="bold">+</text>
</svg>'''
    if kind.startswith("ammo"):
        return f'''<svg width="{size}" height="{size}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <rect x="3" y="6" width="18" height="14" fill="#3b82f6" stroke="#000" stroke-width="1.5"/>
  <rect x="5" y="8" width="14" height="2" fill="rgba(255,255,255,0.3)"/>
  <text x="12" y="17" font-size="9" text-anchor="middle" fill="#fff" font-weight="bold">A</text>
</svg>'''
    if kind.startswith("weapon_"):
        weapon_kind = kind.replace("weapon_", "")
        colors = {"shotgun": "#f97316", "sniper": "#a855f7", "rocket": "#dc2626"}
        labels = {"shotgun": "SG", "sniper": "SR", "rocket": "RL"}
        c = colors.get(weapon_kind, "#f97316")
        l = labels.get(weapon_kind, "?")
        return f'''<svg width="{size}" height="{size}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <rect x="3" y="6" width="18" height="14" fill="{c}" stroke="#000" stroke-width="1.5" rx="2"/>
  <rect x="5" y="8" width="14" height="2" fill="rgba(255,255,255,0.3)"/>
  <text x="12" y="17" font-size="9" text-anchor="middle" fill="#fff" font-weight="bold">{l}</text>
</svg>'''
    return ""


# ---------- 特效 ----------

def explosion_svg(size: int = 40) -> str:
    """爆炸效果"""
    return f'''<svg width="{size}" height="{size}" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
  <circle cx="20" cy="20" r="18" fill="#fbbf24" opacity="0.8"/>
  <circle cx="20" cy="20" r="12" fill="#f97316"/>
  <circle cx="20" cy="20" r="6" fill="#fef3c7"/>
  <!-- 放射线 -->
  {'<line x1="20" y1="2" x2="20" y2="8" stroke="#fbbf24" stroke-width="2"/>' if True else ''}
  {'<line x1="20" y1="32" x2="20" y2="38" stroke="#fbbf24" stroke-width="2"/>' if True else ''}
  {'<line x1="2" y1="20" x2="8" y2="20" stroke="#fbbf24" stroke-width="2"/>' if True else ''}
  {'<line x1="32" y1="20" x2="38" y2="20" stroke="#fbbf24" stroke-width="2"/>' if True else ''}
  {'<line x1="6" y1="6" x2="10" y2="10" stroke="#fbbf24" stroke-width="2"/>' if True else ''}
  {'<line x1="30" y1="30" x2="34" y2="34" stroke="#fbbf24" stroke-width="2"/>' if True else ''}
  {'<line x1="6" y1="34" x2="10" y2="30" stroke="#fbbf24" stroke-width="2"/>' if True else ''}
  {'<line x1="34" y1="6" x2="30" y2="10" stroke="#fbbf24" stroke-width="2"/>' if True else ''}
</svg>'''


def hit_flash_svg(size: int = 30) -> str:
    """受击闪光"""
    return f'''<svg width="{size}" height="{size}" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg">
  <circle cx="15" cy="15" r="12" fill="none" stroke="#fbbf24" stroke-width="2" opacity="0.8"/>
  <text x="15" y="20" font-size="14" text-anchor="middle" fill="#fbbf24" font-weight="bold">!</text>
</svg>'''


def skull_svg(size: int = 32) -> str:
    """击杀标记（骷髅）"""
    return obstacle_svg("skull", size)


# ---------- 把整套状态帧渲染成 SVG 帧 ----------

def render_frame_svg(state: dict, width: int = 600, height: int = 450,
                     map_w: int = 100, map_h: int = 100,
                     agent_colors: dict = None) -> str:
    """把一帧游戏状态渲染成完整 SVG

    Args:
        state: engine.step() 返回的字典
        width, height: 画布像素
        map_w, map_h: 地图坐标大小（用于缩放）
        agent_colors: {name: color} 字典
    """
    agent_colors = agent_colors or {}
    bg_color = "#1e293b"
    floor_color = "#334155"

    # 缩放：地图坐标 → 画布像素
    scale_x = width / map_w
    scale_y = height / map_h

    # 网格
    grid_svg = ""
    for x in range(0, map_w + 1, 10):
        px = x * scale_x
        grid_svg += f'<line x1="{px}" y1="0" x2="{px}" y2="{height}" stroke="rgba(255,255,255,0.05)" stroke-width="1"/>'
    for y in range(0, map_h + 1, 10):
        py = y * scale_y
        grid_svg += f'<line x1="0" y1="{py}" x2="{width}" y2="{py}" stroke="rgba(255,255,255,0.05)" stroke-width="1"/>'

    # 障碍物
    obstacles_svg = ""
    for obs in state.get("obstacles", []):
        rx, ry, rw, rh = obs["rect"]
        x = rx * scale_x
        y = ry * scale_y
        w = rw * scale_x
        h = rh * scale_y
        obstacles_svg += f'''<g transform="translate({x},{y})">
  <svg width="{w}" height="{h}" viewBox="0 0 32 32"><use href="#obstacle_brick"/></svg>
</g>'''

    # 补给
    supplies_svg = ""
    for s in state.get("supplies", []):
        sx = s["position"][0] * scale_x
        sy = s["position"][1] * scale_y
        kind = s["type"]
        if "weapon_shotgun" in kind: svg_id = "supply_weapon_sg"
        elif "weapon_sniper" in kind: svg_id = "supply_weapon_sr"
        elif "weapon_rocket" in kind: svg_id = "supply_weapon_rl"
        elif "ammo" in kind: svg_id = "supply_ammo"
        elif kind == "health": svg_id = "supply_health"
        else: svg_id = "supply_health"
        supplies_svg += f'<use href="#{svg_id}" x="{sx-12}" y="{sy-12}"/>'

    # 子弹
    bullets_svg = ""
    for b in state.get("bullets", []):
        bx = b["position"][0] * scale_x
        by = b["position"][1] * scale_y
        kind = b.get("kind", "normal")
        svg_id = f"bullet_{kind}"
        # 方向尾迹
        dir_x = b.get("direction", [1, 0])[0]
        dir_y = b.get("direction", [1, 0])[1]
        trail_x = bx - dir_x * 12
        trail_y = by - dir_y * 12
        bullets_svg += f'''
  <line x1="{trail_x}" y1="{trail_y}" x2="{bx}" y2="{by}" stroke="rgba(255,255,255,0.4)" stroke-width="2"/>
  <use href="#{svg_id}" x="{bx-7}" y="{by-7}"/>'''

    # Agent
    agents_svg = ""
    for a in state.get("agents", []):
        if a.get("health", 0) <= 0:
            continue
        ax = a["position"][0] * scale_x
        ay = a["position"][1] * scale_y
        dir_x = a["direction"][0]
        dir_y = a["direction"][1]
        import math
        deg = math.degrees(math.atan2(dir_y, dir_x))
        color = agent_colors.get(a["name"], "#3b82f6")
        weapon = a.get("weapon", "normal")
        hp_pct = a.get("health", 100) / 100
        # 表情根据血量
        face = "happy" if hp_pct > 0.5 else ("angry" if hp_pct > 0.25 else "scared")
        size = 36
        agents_svg += f'<g transform="translate({ax-size/2},{ay-size/2})">'
        agents_svg += f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
        agents_svg += character_inner_svg(color, deg, weapon, hp_pct, face)
        agents_svg += '</svg></g>'

    return f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
<defs>
  {character_defs()}
  {obstacle_defs()}
  {supply_defs()}
  {bullet_defs()}
</defs>
<rect width="{width}" height="{height}" fill="{bg_color}"/>
<rect width="{width}" height="{height}" fill="{floor_color}" opacity="0.3"/>
{grid_svg}
{obstacles_svg}
{supplies_svg}
{bullets_svg}
{agents_svg}
</svg>'''


def character_inner_svg(color: str, deg: float, weapon: str, hp_pct: float, face: str) -> str:
    """角色内层 SVG（无外层 svg 标签，便于复用）"""
    eye_color = "#fff"
    pupil_color = "#000"
    if face == "angry":
        eye_color = "#fee"; pupil_color = "#900"
    elif face == "scared":
        eye_color = "#cff"; pupil_color = "#006"
    elif face == "dead":
        eye_color = "#aaa"; pupil_color = "#555"
    weapon_color = {
        "normal": "#888", "shotgun": "#f97316",
        "sniper": "#a855f7", "rocket": "#dc2626",
    }.get(weapon, "#888")
    cx, cy, r = 18, 18, 12
    pupil_offset = -2 if deg > 90 or deg < -90 else 2
    hp_color = health_pct_color(hp_pct)
    return f'''
<ellipse cx="{cx}" cy="{cy+r+2}" ry="3" fill="rgba(0,0,0,0.3)" rx="{r}"/>
<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" stroke="#000" stroke-width="2"/>
<circle cx="{cx-r//3}" cy="{cy-r//3}" r="{r//3}" fill="rgba(255,255,255,0.4)"/>
<circle cx="{cx-3}" cy="{cy-2}" r="4" fill="{eye_color}"/>
<circle cx="{cx+5}" cy="{cy-2}" r="4" fill="{eye_color}"/>
<circle cx="{cx-3+pupil_offset}" cy="{cy-2}" r="2" fill="{pupil_color}"/>
<circle cx="{cx+5+pupil_offset}" cy="{cy-2}" r="2" fill="{pupil_color}"/>
<g transform="rotate({deg} {cx} {cy})">
  <rect x="{cx+r-2}" y="{cy-2}" width="6" height="4" fill="{weapon_color}" stroke="#000" stroke-width="0.5"/>
</g>
<circle cx="{cx}" cy="{cy}" r="{r+3}" fill="none" stroke="#333" stroke-width="2"/>
<circle cx="{cx}" cy="{cy}" r="{r+3}" fill="none" stroke="{hp_color}" stroke-width="2"
  stroke-dasharray="{(2*3.14159*(r+3)):.2f}" stroke-dashoffset="{(2*3.14159*(r+3)*(1-hp_pct)):.2f}"
  transform="rotate(-90 {cx} {cy})"/>'''


def character_defs() -> str:
    return ""


def obstacle_defs() -> str:
    return f'''<symbol id="obstacle_brick" viewBox="0 0 32 32">
<rect x="1" y="1" width="30" height="30" fill="#92400e" stroke="#000" stroke-width="1.5"/>
<rect x="1" y="1" width="30" height="10" fill="rgba(0,0,0,0.3)"/>
<line x1="0" y1="11" x2="32" y2="11" stroke="#000" stroke-width="0.5" stroke-dasharray="3,2"/>
<line x1="11" y1="0" x2="11" y2="11" stroke="#000" stroke-width="0.5"/>
<line x1="21" y1="11" x2="21" y2="32" stroke="#000" stroke-width="0.5"/>
<text x="16" y="22" font-size="8" fill="rgba(255,255,255,0.5)" text-anchor="middle">墙</text>
</symbol>'''


def supply_defs() -> str:
    return f'''<symbol id="supply_health" viewBox="0 0 24 24">
<path d="M 12 21 C 4 14 2 12 5 9 C 8 6 11 7 12 10 C 13 7 16 6 19 9 C 22 12 20 14 12 21 Z"
  fill="#ef4444" stroke="#000" stroke-width="1.5"/>
<text x="12" y="14" font-size="8" text-anchor="middle" fill="#fff" font-weight="bold">+</text>
</symbol>
<symbol id="supply_ammo" viewBox="0 0 24 24">
<rect x="3" y="6" width="18" height="14" fill="#3b82f6" stroke="#000" stroke-width="1.5"/>
<text x="12" y="17" font-size="9" text-anchor="middle" fill="#fff" font-weight="bold">A</text>
</symbol>
<symbol id="supply_weapon_sg" viewBox="0 0 24 24">
<rect x="3" y="6" width="18" height="14" fill="#f97316" stroke="#000" stroke-width="1.5" rx="2"/>
<text x="12" y="17" font-size="8" text-anchor="middle" fill="#fff" font-weight="bold">SG</text>
</symbol>
<symbol id="supply_weapon_sr" viewBox="0 0 24 24">
<rect x="3" y="6" width="18" height="14" fill="#a855f7" stroke="#000" stroke-width="1.5" rx="2"/>
<text x="12" y="17" font-size="8" text-anchor="middle" fill="#fff" font-weight="bold">SR</text>
</symbol>
<symbol id="supply_weapon_rl" viewBox="0 0 24 24">
<rect x="3" y="6" width="18" height="14" fill="#dc2626" stroke="#000" stroke-width="1.5" rx="2"/>
<text x="12" y="17" font-size="8" text-anchor="middle" fill="#fff" font-weight="bold">RL</text>
</symbol>'''


def bullet_defs() -> str:
    return f'''<symbol id="bullet_normal" viewBox="0 0 14 14">
<circle cx="7" cy="7" r="5" fill="#fbbf24" stroke="#000" stroke-width="1"/>
<circle cx="5" cy="5" r="2" fill="#fff" opacity="0.6"/>
</symbol>
<symbol id="bullet_shotgun" viewBox="0 0 14 14">
<circle cx="7" cy="7" r="5" fill="#f97316" stroke="#000" stroke-width="1"/>
<circle cx="5" cy="5" r="2" fill="#fff" opacity="0.6"/>
</symbol>
<symbol id="bullet_sniper" viewBox="0 0 14 14">
<circle cx="7" cy="7" r="5" fill="#a855f7" stroke="#000" stroke-width="1"/>
<circle cx="5" cy="5" r="2" fill="#fff" opacity="0.6"/>
</symbol>
<symbol id="bullet_rocket" viewBox="0 0 14 14">
<circle cx="7" cy="7" r="6" fill="#dc2626" stroke="#000" stroke-width="1"/>
<path d="M 7 1 L 5 4 L 9 4 Z" fill="#fef3c7"/>
</symbol>'''


# ---------- HTML 回放生成（用 SVG 替代 canvas） ----------

def generate_svg_replay_html(state_frames: list, output_file: str,
                              map_w: int = 100, map_h: int = 100,
                              width: int = 600, height: int = 600,
                              title: str = "AI 对决回放",
                              fps: int = 6,
                              commentary: list = None) -> str:
    """生成完整的 SVG 回放 HTML（不依赖 canvas）

    每帧支持字段：
    - agents: list of {name, health, position, direction, weapon, ammo, kills}
    - bullets: list of {kind, position, direction, owner}
    - obstacles: list of {rect: [x, y, w, h]}
    - supplies: list of {position, type}
    - explosions: list of {position, intensity} (受击爆炸)

    commentary: 可选 list of {turn, text, importance} — 实时解说气泡
    """
    import json
    if commentary is None:
        commentary = []
    states_json = json.dumps(state_frames)
    commentary_json = json.dumps(commentary)

    # 静态资源
    resources_svg = f'''<svg width="0" height="0" style="position:absolute">
<defs>
{obstacle_defs()}
{supply_defs()}
{bullet_defs()}
</defs>
</svg>'''

    html = f'''<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  font-family:'Microsoft YaHei',Arial,sans-serif;
  background:linear-gradient(135deg,#1e293b 0%,#0f172a 100%);
  color:white; min-height:100vh; padding:20px;
  display:flex; flex-direction:column; align-items:center;
}}
.container {{ background:rgba(255,255,255,0.05); border-radius:16px;
  padding:20px; backdrop-filter:blur(10px); }}
h1 {{ text-align:center; margin-bottom:12px;
  text-shadow:2px 2px 4px rgba(0,0,0,0.5); }}
#stage {{ width:{width}px; height:{height}px;
  border:3px solid rgba(255,255,255,0.2); border-radius:12px;
  background:#1e293b; box-shadow:0 8px 24px rgba(0,0,0,0.5); }}
.controls {{ margin-top:16px; text-align:center; }}
button {{
  background:rgba(255,255,255,0.15); border:1px solid rgba(255,255,255,0.3);
  color:white; padding:8px 16px; border-radius:6px;
  margin:3px; cursor:pointer; font-size:14px;
}}
button:hover {{ background:rgba(255,255,255,0.3); }}
.info {{ margin-top:12px; display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
.card {{ background:rgba(255,255,255,0.08); padding:10px 14px; border-radius:8px; }}
.hp {{ background:rgba(0,0,0,0.4); height:12px; border-radius:6px; overflow:hidden; margin-top:4px; }}
.hpfill {{ height:100%; background:linear-gradient(90deg,#22c55e,#16a34a); }}

/* 实时解说面板 */
.comm-panel {{
  margin-top:12px;
  background:rgba(0,0,0,0.5);
  border:1px solid rgba(251,191,36,0.4);
  border-radius:10px;
  padding:10px 16px;
  min-height:60px;
  max-width:600px;
  width:100%;
}}
.comm-title {{
  font-size:13px;
  color:#fbbf24;
  font-weight:bold;
  margin-bottom:6px;
  letter-spacing:1px;
}}
.comm-empty {{ color:rgba(255,255,255,0.4); font-style:italic; font-size:12px; padding:6px 0; }}
.comm-line {{
  padding:4px 8px;
  margin:3px 0;
  font-size:13px;
  line-height:1.4;
  background:rgba(255,255,255,0.04);
  border-radius:0 4px 4px 0;
}}
.comm-turn {{ color:rgba(255,255,255,0.5); font-size:11px; margin-right:6px; }}
.comm-text {{ color:rgba(255,255,255,0.92); font-family:'Microsoft YaHei',sans-serif; }}

/* 飞过大气泡 */
.commentary-bubble {{
  animation: slideIn 0.6s ease-out;
}}
@keyframes slideIn {{
  from {{ transform:translate({int(width/2 - 200)}px, -30px); opacity:0; }}
  to {{ transform:translate({int(width/2 - 200)}px, 20px); opacity:0.95; }}
}}
</style>
</head>
<body>
<div class="container">
<h1>🏟️ {title}</h1>
<div id="stage"></div>
<div class="controls">
<button onclick="togglePlay()">⏯ 播放/暂停</button>
<button onclick="reset()">🔄 重置</button>
<button onclick="speedUp()">⏩ 加速</button>
<button onclick="speedDown()">⏪ 减速</button>
<button onclick="toggleSound()">🔊 音效: <span id="soundStatus">关</span></button>
<span style="margin-left:12px;">速度: <span id="speedDisplay">{fps}</span> FPS</span>
<div style="margin-top:8px;">
<input id="timeline" type="range" min="0" value="0" step="1" style="width:600px;" />
<span id="frameLabel">0</span>/<span id="frameTotal">0</span>
</div>
</div>
<div class="info" id="info"></div>
<div id="commentary"></div>
</div>
{resources_svg}
<script>
const states = {states_json};
const commentary = {commentary_json};
const canvasW = {width}, canvasH = {height};
const mapW = {map_w}, mapH = {map_h};
const agentColors = {{}};

// 分配颜色
const colorList = ["#a855f7","#ec4899","#22d3ee","#facc15","#84cc16","#fb923c"];
states.forEach(f => {{
  f.agents.forEach((a, i) => {{
    if (!agentColors[a.name]) agentColors[a.name] = colorList[Object.keys(agentColors).length % colorList.length];
  }});
}});

let currentFrame = 0, isPlaying = true, fps = {fps};
// URL 参数 ?pause=1 停止自动播放（用于截图）
if (new URLSearchParams(window.location.search).get('pause') === '1') isPlaying = false;
let lastTime = 0;

const stage = document.getElementById('stage');
const timeline = document.getElementById('timeline');
const frameLabel = document.getElementById('frameLabel');
const frameTotal = document.getElementById('frameTotal');
const info = document.getElementById('info');

frameTotal.textContent = states.length - 1;
timeline.max = states.length - 1;

function renderFrame(frameIdx) {{
  if (frameIdx >= states.length) return;
  const f = states[frameIdx];
  const currentFrame = frameIdx;  // 给角色动画用
  // 统一缩放（地图不形变）+ 居中留白
  const scale = Math.min(canvasW / mapW, canvasH / mapH);
  const contentW = mapW * scale;
  const contentH = mapH * scale;
  const offsetX = (canvasW - contentW) / 2;
  const offsetY = (canvasH - contentH) / 2;
  const scaleX = scale, scaleY = scale;

  let svg = `<svg width="${{canvasW}}" height="${{canvasH}}" viewBox="0 0 ${{canvasW}} ${{canvasH}}" xmlns="http://www.w3.org/2000/svg">`;
  svg += `<rect width="${{canvasW}}" height="${{canvasH}}" fill="#1e293b"/>`;
  svg += `<rect width="${{canvasW}}" height="${{canvasH}}" fill="#334155" opacity="0.3"/>`;

  // 网格（用统一 scale 避免形变）
  for (let x = 0; x <= mapW; x += 10) {{
    const px = offsetX + x*scale;
    svg += `<line x1="${{px}}" y1="${{offsetY}}" x2="${{px}}" y2="${{offsetY+contentH}}" stroke="rgba(255,255,255,0.05)" stroke-width="1"/>`;
  }}
  for (let y = 0; y <= mapH; y += 10) {{
    const py = offsetY + y*scale;
    svg += `<line x1="${{offsetX}}" y1="${{py}}" x2="${{offsetX+contentW}}" y2="${{py}}" stroke="rgba(255,255,255,0.05)" stroke-width="1"/>`;
  }}

  // 障碍物
  (f.obstacles || []).forEach(obs => {{
    const [rx, ry, rw, rh] = obs.rect;
    const x = offsetX + rx * scaleX, y = offsetY + ry * scaleY, w = rw * scaleX, h = rh * scaleY;
    svg += `<g transform="translate(${{x}},${{y}})">`;
    svg += `<svg width="${{w}}" height="${{h}}" viewBox="0 0 32 32">`;
    svg += `<use href="#obstacle_brick" width="32" height="32"/>`;  // 关键：width/height
    svg += `</svg></g>`;
  }});

  // 补给
  (f.supplies || []).forEach(s => {{
    const sx = offsetX + s.position[0] * scaleX - 8;
    const sy = offsetY + s.position[1] * scaleY - 8;
    let kind = s.type;
    let svgId = 'supply_health';
    if (kind.includes('weapon_shotgun')) svgId = 'supply_weapon_sg';
    else if (kind.includes('weapon_sniper')) svgId = 'supply_weapon_sr';
    else if (kind.includes('weapon_rocket')) svgId = 'supply_weapon_rl';
    else if (kind.startsWith('ammo')) svgId = 'supply_ammo';
    // 关键：必须加 width/height，否则浏览器拉伸填满父容器
    svg += `<use href="#${{svgId}}" x="${{sx-2}}" y="${{sy-2}}" width="20" height="20"/>`;
  }});

  // 子弹
  (f.bullets || []).forEach(b => {{
    const bx = offsetX + b.position[0] * scaleX;
    const by = offsetY + b.position[1] * scaleY;
    const [dx, dy] = b.direction || [1, 0];
    const tx = bx - dx * 8, ty = by - dy * 8;
    // 尾迹
    svg += `<line x1="${{tx}}" y1="${{ty}}" x2="${{bx}}" y2="${{by}}" stroke="rgba(255,255,255,0.5)" stroke-width="1.5"/>`;
    // 关键：必须加 width/height
    svg += `<use href="#bullet_${{b.kind || 'normal'}}" x="${{bx-5}}" y="${{by-5}}" width="10" height="10"/>`;
  }});

  // 爆炸 / 受击效果（缩小到合理范围）
  (f.explosions || []).forEach(e => {{
    const ex = offsetX + e.position[0] * scaleX;
    const ey = offsetY + e.position[1] * scaleY;
    const r = 10;
    svg += `<circle cx="${{ex}}" cy="${{ey}}" r="${{r}}" fill="#fbbf24" opacity="0.7"/>`;
    svg += `<circle cx="${{ex}}" cy="${{ey}}" r="${{r*0.6}}" fill="#f97316" opacity="0.9"/>`;
    svg += `<circle cx="${{ex}}" cy="${{ey}}" r="${{r*0.3}}" fill="#fef3c7"/>`;
    // 放射线
    for (let i = 0; i < 6; i++) {{
      const a = (Math.PI * 2 * i) / 6;
      const x1 = ex + Math.cos(a) * r * 0.5;
      const y1 = ey + Math.sin(a) * r * 0.5;
      const x2 = ex + Math.cos(a) * r * 1.3;
      const y2 = ey + Math.sin(a) * r * 1.3;
      svg += `<line x1="${{x1}}" y1="${{y1}}" x2="${{x2}}" y2="${{y2}}" stroke="#fbbf24" stroke-width="1.5" stroke-linecap="round"/>`;
    }}
    // 受击感叹号（8px）
    svg += `<text x="${{ex}}" y="${{ey+3}}" font-size="9" text-anchor="middle" fill="#000" font-weight="bold">!</text>`;
  }});

  // Agent
  f.agents.forEach(a => {{
    const ax = offsetX + a.position[0] * scaleX;
    const ay = offsetY + a.position[1] * scaleY;
    const [dx, dy] = a.direction || [1, 0];
    const deg = Math.atan2(dy, dx) * 180 / Math.PI;
    const color = agentColors[a.name] || '#3b82f6';
    const weapon = a.weapon || 'normal';
    const hp = Math.max(0, a.health) / 100;
    const face = hp > 0.5 ? 'happy' : (hp > 0.25 ? 'angry' : 'scared');
    const cx = 18, cy = 18, r = 12;
    const pupilOff = (deg > 90 || deg < -90) ? -2 : 2;
    const hpColor = hp > 0.5 ? '#22c55e' : (hp > 0.25 ? '#eab308' : '#ef4444');
    const weaponColor = {{normal:'#888',shotgun:'#f97316',sniper:'#a855f7',rocket:'#dc2626'}}[weapon];

    svg += `<g transform="translate(${{ax-12}},${{ay-12}})">`;
    svg += `<ellipse cx="12" cy="22" ry="2" rx="8" fill="rgba(0,0,0,0.4)"/>`;

    // 死亡：渲染骷髅
    if (a.health <= 0) {{
      svg += `<circle cx="12" cy="11" r="8" fill="#fff" stroke="#000" stroke-width="2"/>`;
      svg += `<path d="M 5 8 Q 12 4 19 8" stroke="#000" stroke-width="1" fill="none"/>`;
      svg += `<circle cx="9" cy="10" r="3" fill="#000"/>`;
      svg += `<circle cx="15" cy="10" r="3" fill="#000"/>`;
      svg += `<polygon points="12,11 10,14 14,14" fill="#000"/>`;
      svg += `<line x1="8.5" y1="15" x2="8.5" y2="19" stroke="#000" stroke-width="1"/>`;
      svg += `<line x1="11" y1="15" x2="11" y2="19" stroke="#000" stroke-width="1"/>`;
      svg += `<line x1="13" y1="15" x2="13" y2="19" stroke="#000" stroke-width="1"/>`;
      svg += `<line x1="15.5" y1="15" x2="15.5" y2="19" stroke="#000" stroke-width="1"/>`;
      svg += `<text x="12" y="9" font-size="8" text-anchor="middle" fill="#dc2626" font-weight="bold">✕</text>`;
      svg += `</g>`;
      return;
    }}

    // 走动动画：交替脚位置
    const walking = Math.abs(dx) + Math.abs(dy) > 0.01;
    const legPhase = walking ? Math.floor(currentFrame / 4) % 2 : 0;
    const legY = legPhase ? 21 : 22;
    const legOff = legPhase ? 0.8 : -0.8;
    svg += `<ellipse cx="${{9+legOff}}" cy="${{legY}}" rx="2" ry="1.2" fill="#333"/>`;
    svg += `<ellipse cx="${{15-legOff}}" cy="${{legY}}" rx="2" ry="1.2" fill="#333"/>`;

    svg += `<circle cx="12" cy="12" r="8" fill="${{color}}" stroke="#000" stroke-width="1.5"/>`;
    svg += `<circle cx="9" cy="9" r="2.5" fill="rgba(255,255,255,0.4)"/>`;
    // 表情：scared / angry / happy 三种
    if (face === 'scared') {{
      // X 眼
      svg += `<line x1="7" y1="8" x2="11" y2="12" stroke="#000" stroke-width="1"/>`;
      svg += `<line x1="11" y1="8" x2="7" y2="12" stroke="#000" stroke-width="1"/>`;
      svg += `<line x1="13" y1="8" x2="17" y2="12" stroke="#000" stroke-width="1"/>`;
      svg += `<line x1="17" y1="8" x2="13" y2="12" stroke="#000" stroke-width="1"/>`;
      // O 嘴
      svg += `<ellipse cx="12" cy="16" rx="2" ry="2.5" fill="#000"/>`;
    }} else if (face === 'angry') {{
      // V 眉
      svg += `<line x1="6" y1="9" x2="10" y2="11" stroke="#000" stroke-width="1.2"/>`;
      svg += `<line x1="18" y1="9" x2="14" y2="11" stroke="#000" stroke-width="1.2"/>`;
      svg += `<circle cx="9" cy="10" r="1.2" fill="#000"/>`;
      svg += `<circle cx="15" cy="10" r="1.2" fill="#000"/>`;
      // 直线嘴
      svg += `<line x1="9" y1="16" x2="15" y2="16" stroke="#000" stroke-width="1.2"/>`;
    }} else {{
      // happy
      svg += `<circle cx="9" cy="10" r="1.5" fill="#fff"/>`;
      svg += `<circle cx="15" cy="10" r="1.5" fill="#fff"/>`;
      svg += `<circle cx="${{9+pupilOff}}" cy="10" r="0.8" fill="#000"/>`;
      svg += `<circle cx="${{15+pupilOff}}" cy="10" r="0.8" fill="#000"/>`;
      // 微笑
      svg += `<path d="M 9 15 Q 12 17 15 15" stroke="#000" stroke-width="1" fill="none"/>`;
    }}
    // 武器（朝朝向）
    svg += `<g transform="rotate(${{deg}} 12 12)"><rect x="18" y="10.5" width="4" height="3" fill="${{weaponColor}}" stroke="#000" stroke-width="0.4"/></g>`;
    // 血量环
    const circ = 2 * Math.PI * 11;
    svg += `<circle cx="12" cy="12" r="11" fill="none" stroke="#333" stroke-width="1.5"/>`;
    svg += `<circle cx="12" cy="12" r="11" fill="none" stroke="${{hpColor}}" stroke-width="1.5" stroke-dasharray="${{circ}}" stroke-dashoffset="${{circ*(1-hp)}}" transform="rotate(-90 12 12)"/>`;
    svg += `</g>`;
  }});

  svg += `</svg>`;
  stage.innerHTML = svg;

  // 信息面板
  let infoHtml = '';
  f.agents.forEach(a => {{
    const color = agentColors[a.name] || '#3b82f6';
    const hp = Math.max(0, a.health);
    infoHtml += `<div class="card" style="border-left:4px solid ${{color}}">
      <b>${{a.name}}</b> · 血 ${{hp}}/100 · 击杀 ${{a.kills || 0}}
      <div class="hp"><div class="hpfill" style="width:${{hp}}%"></div></div>
      ${{a.weapon && a.weapon !== 'normal' ? '<small>武器:' + a.weapon + '</small>' : ''}}
    </div>`;
  }});
  info.innerHTML = infoHtml;

  // 实时解说气泡（最近 1 个 importance>=3 事件）
  const recentComm = commentary.filter(c => c.turn <= frameIdx && c.turn > frameIdx - 5);
  // 找最近一个 importance>=3 的事件作为"飞过"气泡（最近 5 帧内）
  const flyIn = recentComm.filter(c => c.importance >= 3).pop();
  if (flyIn) {{
    // 气泡放在画布底部（不挡角色，避开 z-index 风险）
    svg += `<g class="commentary-bubble" transform="translate(${{canvasW/2 - 200}}, ${{canvasH - 80}})">
      <rect x="0" y="0" width="400" height="60" rx="10" fill="#fbbf24" stroke="#000" stroke-width="2" opacity="0.98"/>
      <text x="20" y="38" font-size="20" font-weight="bold" fill="#000" font-family="Microsoft YaHei, sans-serif">${{flyIn.text.replace(/[<>&]/g, c => ({{'<':'&lt;','>':'&gt;','&':'&amp;'}}[c]))}}</text>
    </g>`;
  }}

  // 解说面板：画布下方显示最近 3 条
  let panelHtml = '<div class="comm-panel">';
  panelHtml += '<div class="comm-title">📺 实时解说</div>';
  // 取最近的 3 条（按 turn 升序）
  const displayComm = commentary.filter(c => c.turn <= frameIdx).slice(-3);
  if (displayComm.length === 0) {{
    panelHtml += '<div class="comm-empty">（等待精彩时刻...）</div>';
  }} else {{
    displayComm.forEach(c => {{
      const color = c.importance >= 3 ? '#fbbf24' : (c.importance >= 2 ? '#94a3b8' : '#475569');
      panelHtml += `<div class="comm-line" style="border-left:3px solid ${{color}}">
        <span class="comm-turn">[回合 ${{c.turn}}]</span>
        <span class="comm-text">${{c.text}}</span>
      </div>`;
    }});
  }}
  panelHtml += '</div>';
  // 用 innerHTML 设置（panel 在 stage 外的 div）
  const commPanel = document.getElementById('commentary');
  if (commPanel) commPanel.innerHTML = panelHtml;

  timeline.value = frameIdx;
  frameLabel.textContent = frameIdx;
}}

function gameLoop(t) {{
  if (isPlaying && t - lastTime > 1000/fps) {{
    currentFrame = (currentFrame + 1) % states.length;
    renderFrame(currentFrame);
    lastTime = t;
  }}
  requestAnimationFrame(gameLoop);
}}

function togglePlay() {{ isPlaying = !isPlaying; }}
function reset() {{ currentFrame = 0; renderFrame(0); isPlaying = true; lastTime = 0; }}
function speedUp() {{ fps = Math.min(fps + 5, 60); document.getElementById('speedDisplay').textContent = fps; }}
function speedDown() {{ fps = Math.max(fps - 5, 5); document.getElementById('speedDisplay').textContent = fps; }}

// ====== Web Audio 8-bit 音效 ======
let audioCtx = null;
let soundEnabled = false;
function ensureAudio() {{
  if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
}}
function toggleSound() {{
  soundEnabled = !soundEnabled;
  document.getElementById('soundStatus').textContent = soundEnabled ? '开' : '关';
  if (soundEnabled) {{ ensureAudio(); audioCtx.resume(); playSound('pickup'); }}
}}
function playSound(kind) {{
  if (!soundEnabled || !audioCtx) return;
  const now = audioCtx.currentTime;
  if (kind === 'shoot') {{
    // 短促方波（800Hz）
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'square';
    osc.frequency.setValueAtTime(800, now);
    osc.frequency.exponentialRampToValueAtTime(400, now + 0.08);
    gain.gain.setValueAtTime(0.1, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
    osc.connect(gain).connect(audioCtx.destination);
    osc.start(now);
    osc.stop(now + 0.08);
  }} else if (kind === 'explode') {{
    // 低频 + 噪声（爆炸）
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(120, now);
    osc.frequency.exponentialRampToValueAtTime(40, now + 0.2);
    gain.gain.setValueAtTime(0.15, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
    osc.connect(gain).connect(audioCtx.destination);
    osc.start(now);
    osc.stop(now + 0.2);
  }} else if (kind === 'pickup') {{
    // 上升音（拾取）
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'square';
    osc.frequency.setValueAtTime(400, now);
    osc.frequency.exponentialRampToValueAtTime(800, now + 0.15);
    gain.gain.setValueAtTime(0.08, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);
    osc.connect(gain).connect(audioCtx.destination);
    osc.start(now);
    osc.stop(now + 0.15);
  }}
}}
// 监听帧变化触发音效
let lastFrameIdx = -1;
let lastBulletCount = 0;
let lastExplosionCount = 0;
const origRenderFrame = renderFrame;
renderFrame = function(frameIdx) {{
  origRenderFrame(frameIdx);
  if (frameIdx !== lastFrameIdx && soundEnabled) {{
    const cur = states[frameIdx];
    if (cur) {{
      const bc = cur.bullets ? cur.bullets.length : 0;
      const ec = cur.explosions ? cur.explosions.length : 0;
      if (bc > lastBulletCount) playSound('shoot');
      if (ec > lastExplosionCount) playSound('explode');
      lastBulletCount = bc;
      lastExplosionCount = ec;
    }}
  }}
  lastFrameIdx = frameIdx;
}};
timeline.oninput = () => {{ currentFrame = parseInt(timeline.value); renderFrame(currentFrame); }};

renderFrame(0);
requestAnimationFrame(gameLoop);
</script>
</body></html>'''

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    return output_file