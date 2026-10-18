"""读取 v4 三模式数据 + 模板 → 生成新 HTML（真实帧驱动 + 模式切换 + 补给 + 武器库）"""
import json, sys

with open('outputs/team_v4_modes.json', encoding='utf-8') as f:
    all_modes = json.load(f)

# 读 v3 模板（CSS + body）
with open('outputs/team_3v3_v3.html', encoding='utf-8') as f:
    tmpl = f.read()

script_start = tmpl.find('<script>')
script_end = tmpl.rfind('</script>') + len('</script>')
head_body = tmpl[:script_start]

# 构造新 script
modes_data_json = json.dumps(all_modes, ensure_ascii=False)
mode_keys = list(all_modes.keys())

new_script = f'''<script>
const ALL_MODES = {modes_data_json};
const MODE_KEYS = {json.dumps(mode_keys)};
let currentMode = '3v3';
let FRAMES = ALL_MODES[currentMode].frames;
let HERO_META = ALL_MODES[currentMode].meta;
let TOTAL = FRAMES.length;
let FINAL_BLUE = ALL_MODES[currentMode].final_blue;
let FINAL_RED = ALL_MODES[currentMode].final_red;
let TOWER_DESTROYED = ALL_MODES[currentMode].tower_destroyed;
// URL 参数支持 ?mode=1v1 / 3v3 / 5v5（必须在变量声明后）
const urlMode = new URLSearchParams(window.location.search).get('mode');
if (urlMode && ALL_MODES[urlMode]) {{
  currentMode = urlMode;
  FRAMES = ALL_MODES[urlMode].frames;
  HERO_META = ALL_MODES[urlMode].meta;
  TOTAL = FRAMES.length;
  FINAL_BLUE = ALL_MODES[urlMode].final_blue;
  FINAL_RED = ALL_MODES[urlMode].final_red;
  TOWER_DESTROYED = ALL_MODES[urlMode].tower_destroyed;
  // 同步 UI
  setTimeout(() => switchMode(urlMode), 0);
}}

// 地图: 40x25 格子, 渲染到 800x500 (每格 20px)
const CELL = 20;
const MAP_W = 800;
const MAP_H = 500;
function toPx(x, y) {{
  return [x * CELL + CELL/2, y * CELL + CELL/2];
}}

// ===== 武器库 =====
const WEAPONS = {{
  shotgun:  {{name:'散弹', icon:'🔫', color:'#f59e0b'}},
  laser:    {{name:'激光', icon:'🔴', color:'#ef4444'}},
  cannon:   {{name:'大炮', icon:'💣', color:'#94a3b8'}},
  fireball: {{name:'火球', icon:'🔥', color:'#ea580c'}},
  ice:      {{name:'冰冻', icon:'❄️', color:'#06b6d4'}},
  heal:     {{name:'治疗', icon:'✚', color:'#34d399'}},
}};

// ===== 补给类型 =====
const SUPPLY_INFO = {{
  ammo:   {{name:'弹药包', icon:'📦', color:'#fbbf24'}},
  health: {{name:'血包',   icon:'💊', color:'#34d399'}},
  shield: {{name:'护盾',   icon:'🛡', color:'#60a5fa'}},
  damage: {{name:'攻击 buff', icon:'⚔', color:'#ef4444'}},
}};

let currentFrame = 0;
let isPlaying = true;
let speed = 1;
let interval = null;
let lastWinRate = 50;
let winRate = 50;
let N_BLUE = HERO_META.filter(h => h.side === 'blue').length;
let N_HEROES = HERO_META.length;

function getFrame() {{ return FRAMES[currentFrame] || FRAMES[0]; }}

function switchMode(mode) {{
  currentMode = mode;
  FRAMES = ALL_MODES[mode].frames;
  HERO_META = ALL_MODES[mode].meta;
  TOTAL = FRAMES.length;
  FINAL_BLUE = ALL_MODES[mode].final_blue;
  FINAL_RED = ALL_MODES[mode].final_red;
  TOWER_DESTROYED = ALL_MODES[mode].tower_destroyed;
  N_BLUE = HERO_META.filter(h => h.side === 'blue').length;
  N_HEROES = HERO_META.length;
  currentFrame = 0;
  document.querySelectorAll('.mode-chip').forEach(b => b.classList.remove('active'));
  document.getElementById('mode-' + mode).classList.add('active');
  document.getElementById('mode-desc').textContent = ALL_MODES[mode].description;
  // 更新左栏标签
  document.getElementById('lane-info').textContent = ALL_MODES[mode].description;
  renderAll();
}}

function renderHeroes() {{
  const blueList = document.getElementById('blue-hero-list');
  const redList = document.getElementById('red-hero-list');
  const f = getFrame();
  let blueH = '', redH = '';
  for (let i = 0; i < HERO_META.length; i++) {{
    const m = HERO_META[i];
    const hp = f.healths[i];
    const ammo = f.ammos ? f.ammos[i] : m.max_ammo;
    const shield = f.shields ? f.shields[i] : 0;
    const kills = f.kills[i];
    const deaths = f.deaths[i];
    const pct = Math.max(0, Math.min(100, (hp / m.max_hp) * 100));
    const ammoPct = Math.max(0, Math.min(100, (ammo / m.max_ammo) * 100));
    const dead = hp <= 0;
    const cls = m.side === 'blue' ? 'blue-card' : 'red-card';
    const sideColor = m.side === 'blue' ? '#3b82f6' : '#ef4444';
    const html = `<div class="hero-card ${{cls}} ${{dead?'dead':''}}">
      <div class="hero-portrait ${{m.color}}">${{m.icon}}</div>
      <div class="hero-info">
        <div class="hero-title">
          <span class="hero-name">${{m.name}}</span>
          <span class="weapon-tag" style="background:${{m.weapon_color}}22;color:${{m.weapon_color}};">${{m.weapon_icon}}${{m.weapon_name}}</span>
        </div>
        <div class="hp-track ${{m.side==='blue'?'hp-blue':'hp-red'}}"><span style="width:${{pct}}%"></span></div>
        ${{shield > 0 ? `<div class="shield-track"><span style="width:${{Math.min(100, shield*3.33)}}%"></span></div>` : ''}}
        <div class="ammo-track" title="弹药"><div class="ammo-fill" style="width:${{ammoPct}}%"></div><span class="ammo-label">${{Math.round(ammo)}}/${{m.max_ammo}}</span></div>
        <div class="hero-stats">
          <span class="kills">杀 ${{kills}}</span>
          <span class="deaths">死 ${{deaths}}</span>
          <span>·</span>
          <span>${{m.lane.toUpperCase()}}路</span>
        </div>
      </div>
    </div>`;
    if (m.side === 'blue') blueH += html; else redH += html;
  }}
  blueList.innerHTML = blueH;
  redList.innerHTML = redH;
}}

function renderBattle() {{
  const svg = document.getElementById('battle-svg');
  const f = getFrame();
  let html = '';
  // ===== 地图背景（王者峡谷风：深色 + 网格 + 装饰）=====
  html += '<defs>';
  html += '<pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(34,211,238,.05)" stroke-width="1"/></pattern>';
  html += '<radialGradient id="blueBase"><stop offset="0%" stop-color="#3b82f6" stop-opacity=".3"/><stop offset="100%" stop-color="#3b82f6" stop-opacity="0"/></radialGradient>';
  html += '<radialGradient id="redBase"><stop offset="0%" stop-color="#ef4444" stop-opacity=".3"/><stop offset="100%" stop-color="#ef4444" stop-opacity="0"/></radialGradient>';
  html += '<linearGradient id="bgGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#0a1428"/><stop offset="50%" stop-color="#0d1b30"/><stop offset="100%" stop-color="#0a1428"/></linearGradient>';
  html += '<pattern id="bush" width="14" height="14" patternUnits="userSpaceOnUse"><circle cx="3" cy="4" r="3" fill="rgba(34,197,94,.25)"/><circle cx="9" cy="8" r="4" fill="rgba(22,163,74,.2)"/><circle cx="5" cy="11" r="2" fill="rgba(34,197,94,.3)"/></pattern>';
  html += '<pattern id="river" width="30" height="14" patternUnits="userSpaceOnUse"><path d="M 0 7 Q 7 2 14 7 T 30 7" fill="none" stroke="rgba(34,211,238,.4)" stroke-width="1.5"/><path d="M 0 11 Q 7 6 14 11 T 30 11" fill="none" stroke="rgba(34,211,238,.25)" stroke-width="1"/></pattern>';
  html += '<radialGradient id="supplyGlow"><stop offset="0%" stop-color="#fbbf24" stop-opacity=".8"/><stop offset="100%" stop-color="#fbbf24" stop-opacity="0"/></radialGradient>';
  html += '</defs>';
  // 背景底色
  html += `<rect width="${{MAP_W}}" height="${{MAP_H}}" fill="url(#bgGrad)"/>`;
  // 网格
  html += `<rect width="${{MAP_W}}" height="${{MAP_H}}" fill="url(#grid)"/>`;
  // 3 路（用不同阴影区分）
  html += `<rect x="0" y="0" width="${{MAP_W}}" height="83" fill="rgba(34,211,238,.04)"/>`;  // 上路蓝
  html += `<rect x="0" y="83" width="${{MAP_W}}" height="167" fill="rgba(251,100,112,.04)"/>`;  // 中路红
  html += `<rect x="0" y="250" width="${{MAP_W}}" height="167" fill="rgba(167,139,250,.04)"/>`;  // 下路紫
  // 河道
  html += `<rect x="380" y="0" width="40" height="${{MAP_H}}" fill="url(#river)" opacity="0.7"/>`;
  // 3 路分隔线
  html += `<line x1="0" y1="83" x2="${{MAP_W}}" y2="83" stroke="rgba(34,211,238,.25)" stroke-width="1.5" stroke-dasharray="3,5"/>`;
  html += `<line x1="0" y1="250" x2="${{MAP_W}}" y2="250" stroke="rgba(251,100,112,.25)" stroke-width="1.5" stroke-dasharray="3,5"/>`;
  html += `<line x1="0" y1="417" x2="${{MAP_W}}" y2="417" stroke="rgba(167,139,250,.25)" stroke-width="1.5" stroke-dasharray="3,5"/>`;
  // 路标签
  html += `<text x="12" y="50" fill="#22d3ee" font-size="13" font-weight="700" opacity="0.7">▲ 上路</text>`;
  html += `<text x="12" y="262" fill="#fb6470" font-size="13" font-weight="700" opacity="0.7">● 中路</text>`;
  html += `<text x="12" y="430" fill="#a78bfa" font-size="13" font-weight="700" opacity="0.7">▼ 下路</text>`;
  // 基地光晕
  html += `<rect x="0" y="220" width="80" height="60" fill="url(#blueBase)"/>`;
  html += `<rect x="${{MAP_W-80}}" y="220" width="80" height="60" fill="url(#redBase)"/>`;
  // 草丛（6 个，密集叶子）
  const bushes = [{{x: 14, y: 6}}, {{x: 14, y: 18}}, {{x: 25, y: 6}}, {{x: 25, y: 18}}, {{x: 35, y: 7}}, {{x: 35, y: 17}}];
  bushes.forEach(b => {{
    const [px, py] = toPx(b.x, b.y);
    html += `<ellipse cx="${{px-12}}" cy="${{py+2}}" rx="18" ry="14" fill="#15803d" opacity="0.7"/>`;
    html += `<ellipse cx="${{px+8}}" cy="${{py-3}}" rx="16" ry="13" fill="#22c55e" opacity="0.8"/>`;
    html += `<ellipse cx="${{px}}" cy="${{py+5}}" rx="20" ry="15" fill="#16a34a" opacity="0.7"/>`;
    html += `<text x="${{px}}" y="${{py+3}}" text-anchor="middle" fill="#bbf7d0" font-size="10" font-weight="900">🌿</text>`;
  }});
  // 野怪点（4 个，真实生物）
  const monsters = [
    {{x: 12, y: 12, color:'#22c55e', emoji:'🐺', label:'蓝野'}},
    {{x: 12, y: 5, color:'#a855f7', emoji:'🗿', label:'蓝 buff'}},
    {{x: 27, y: 12, color:'#ef4444', emoji:'🐉', label:'红野'}},
    {{x: 27, y: 19, color:'#a855f7', emoji:'🗿', label:'红 buff'}},
  ];
  monsters.forEach(m => {{
    const [px, py] = toPx(m.x, m.y);
    html += `<circle cx="${{px}}" cy="${{py}}" r="20" fill="${{m.color}}" opacity="0.18"/>`;
    html += `<circle cx="${{px}}" cy="${{py}}" r="14" fill="none" stroke="${{m.color}}" stroke-width="2" stroke-dasharray="3,3" opacity="0.8"><animateTransform attributeName="transform" type="rotate" from="0 ${{px}} ${{py}}" to="360 ${{px}} ${{py}}" dur="6s" repeatCount="indefinite"/></circle>`;
    html += `<text x="${{px}}" y="${{py+6}}" text-anchor="middle" font-size="18">${{m.emoji}}</text>`;
    html += `<text x="${{px}}" y="${{py+22}}" text-anchor="middle" fill="${{m.color}}" font-size="8" font-weight="700">${{m.label}}</text>`;
  }});
  // 主宰点
  html += `<circle cx="400" cy="250" r="32" fill="rgba(242,199,92,.15)" stroke="rgba(242,199,92,.5)" stroke-width="2" stroke-dasharray="4,3"><animateTransform attributeName="transform" type="rotate" from="0 400 250" to="360 400 250" dur="10s" repeatCount="indefinite"/></circle>`;
  html += `<text x="400" y="246" text-anchor="middle" fill="#f2c75c" font-size="12" font-weight="900">👑</text>`;
  html += `<text x="400" y="262" text-anchor="middle" fill="#f2c75c" font-size="9" font-weight="700">暗影主宰</text>`;
  // 防御塔（塔楼形象）
  const towers = [
    {{side:'blue',lane:0,x:8,y:4}},{{side:'blue',lane:1,x:8,y:12}},{{side:'blue',lane:2,x:8,y:20}},
    {{side:'red',lane:0,x:31,y:4}},{{side:'red',lane:1,x:31,y:12}},{{side:'red',lane:2,x:31,y:20}},
  ];
  const aliveCount = f.tower_alive;
  towers.forEach((t, i) => {{
    const [px, py] = toPx(t.x, t.y);
    const color = t.side === 'blue' ? '#3b82f6' : '#ef4444';
    let destroyed = false;
    if (aliveCount < 6 && i >= aliveCount) destroyed = true;
    const opacity = destroyed ? 0.25 : 1;
    html += `<g opacity="${{opacity}}">`;
    if (!destroyed) {{
      html += `<rect x="${{px-15}}" y="${{py+5}}" width="30" height="14" fill="${{color}}" opacity="0.5" stroke="${{color}}" stroke-width="1.5"/>`;
      html += `<rect x="${{px-10}}" y="${{py-10}}" width="20" height="20" fill="${{color}}" opacity="0.7" stroke="#000" stroke-width="1.5"/>`;
      html += `<rect x="${{px-5}}" y="${{py-5}}" width="3" height="5" fill="#fff" opacity="0.8"/>`;
      html += `<rect x="${{px+2}}" y="${{py-5}}" width="3" height="5" fill="#fff" opacity="0.8"/>`;
      html += `<rect x="${{px-5}}" y="${{py+3}}" width="3" height="5" fill="#fff" opacity="0.8"/>`;
      html += `<rect x="${{px+2}}" y="${{py+3}}" width="3" height="5" fill="#fff" opacity="0.8"/>`;
      html += `<polygon points="${{px-12}},${{py-10}} ${{px+12}},${{py-10}} ${{px}},${{py-22}}" fill="${{color}}" stroke="#000" stroke-width="1.5"/>`;
      html += `<line x1="${{px}}" y1="${{py-22}}" x2="${{px}}" y2="${{py-32}}" stroke="#000" stroke-width="1.5"/>`;
      const flagColor = t.side === 'blue' ? '#1d4ed8' : '#7f1d1d';
      html += `<polygon points="${{px}},${{py-32}} ${{px+10}},${{py-29}} ${{px}},${{py-26}}" fill="${{flagColor}}"/>`;
    }} else {{
      html += `<rect x="${{px-12}}" y="${{py+5}}" width="24" height="10" fill="${{color}}" opacity="0.2" stroke="${{color}}" stroke-width="1" stroke-dasharray="2,2"/>`;
      html += `<rect x="${{px-8}}" y="${{py-2}}" width="16" height="10" fill="none" stroke="${{color}}" stroke-width="1" stroke-dasharray="2,2"/>`;
      html += `<text x="${{px}}" y="${{py+2}}" text-anchor="middle" fill="#ef4444" font-size="10" font-weight="900">废</text>`;
      html += `<text x="${{px+12}}" y="${{py-8}}" text-anchor="middle" fill="#ef4444" font-size="14" font-weight="900">✕</text>`;
    }}
    html += `</g>`;
  }});
  // 基地（古堡）
  const [bx, by] = toPx(2, 12);
  const [rx, ry] = toPx(38, 12);
  html += `<g>`;
  html += `<rect x="${{bx-32}}" y="${{by-20}}" width="64" height="40" fill="#1e3a8a" opacity="0.6" stroke="#3b82f6" stroke-width="2"/>`;
  html += `<rect x="${{bx-32}}" y="${{by-26}}" width="64" height="6" fill="#3b82f6" stroke="#1e3a8a" stroke-width="1"/>`;
  html += `<rect x="${{bx-8}}" y="${{by-2}}" width="16" height="22" fill="#000" stroke="#fbbf24" stroke-width="1.5"/>`;
  html += `<text x="${{bx}}" y="${{by+13}}" text-anchor="middle" fill="#fbbf24" font-size="9" font-weight="900">门</text>`;
  html += `<rect x="${{bx-30}}" y="${{by-32}}" width="10" height="12" fill="#1e3a8a" stroke="#3b82f6" stroke-width="1.5"/>`;
  html += `<rect x="${{bx+20}}" y="${{by-32}}" width="10" height="12" fill="#1e3a8a" stroke="#3b82f6" stroke-width="1.5"/>`;
  html += `<polygon points="${{bx-30}},${{by-32}} ${{bx-20}},${{by-32}} ${{bx-25}},${{by-38}}" fill="#3b82f6"/>`;
  html += `<polygon points="${{bx+20}},${{by-32}} ${{bx+30}},${{by-32}} ${{bx+25}},${{by-38}}" fill="#3b82f6"/>`;
  html += `<rect x="${{bx-30}}" y="${{by+22}}" width="60" height="6" fill="#000" stroke="#3b82f6" stroke-width="1"/>`;
  const blueHPPct = Math.max(0, f.base_hp[0] / 1000);
  html += `<rect x="${{bx-30}}" y="${{by+22}}" width="${{60 * blueHPPct}}" height="6" fill="#3b82f6"/>`;
  html += `<text x="${{bx}}" y="${{by+34}}" text-anchor="middle" fill="#93c5fd" font-size="9" font-weight="700">${{f.base_hp[0]}}/1000</text>`;
  html += `</g>`;
  html += `<g>`;
  html += `<rect x="${{rx-32}}" y="${{ry-20}}" width="64" height="40" fill="#7f1d1d" opacity="0.6" stroke="#ef4444" stroke-width="2"/>`;
  html += `<rect x="${{rx-32}}" y="${{ry-26}}" width="64" height="6" fill="#ef4444" stroke="#7f1d1d" stroke-width="1"/>`;
  html += `<rect x="${{rx-8}}" y="${{ry-2}}" width="16" height="22" fill="#000" stroke="#fbbf24" stroke-width="1.5"/>`;
  html += `<text x="${{rx}}" y="${{ry+13}}" text-anchor="middle" fill="#fbbf24" font-size="9" font-weight="900">门</text>`;
  html += `<rect x="${{rx-30}}" y="${{ry-32}}" width="10" height="12" fill="#7f1d1d" stroke="#ef4444" stroke-width="1.5"/>`;
  html += `<rect x="${{rx+20}}" y="${{ry-32}}" width="10" height="12" fill="#7f1d1d" stroke="#ef4444" stroke-width="1.5"/>`;
  html += `<polygon points="${{rx-30}},${{ry-32}} ${{rx-20}},${{ry-32}} ${{rx-25}},${{ry-38}}" fill="#ef4444"/>`;
  html += `<polygon points="${{rx+20}},${{ry-32}} ${{rx+30}},${{ry-32}} ${{rx+25}},${{ry-38}}" fill="#ef4444"/>`;
  html += `<rect x="${{rx-30}}" y="${{ry+22}}" width="60" height="6" fill="#000" stroke="#ef4444" stroke-width="1"/>`;
  const redHPPct = Math.max(0, f.base_hp[1] / 1000);
  html += `<rect x="${{rx-30}}" y="${{ry+22}}" width="${{60 * redHPPct}}" height="6" fill="#ef4444"/>`;
  html += `<text x="${{rx}}" y="${{ry+34}}" text-anchor="middle" fill="#fca5a5" font-size="9" font-weight="700">${{f.base_hp[1]}}/1000</text>`;
  html += `</g>`;
  // ===== 补给显示 =====
  for (const sup of (f.supplies || [])) {{
    const [px, py] = toPx(sup.position[0], sup.position[1]);
    const info = SUPPLY_INFO[sup.type] || {{name:'?', icon:'?', color:'#fff'}};
    // 脉冲圈
    html += `<circle cx="${{px}}" cy="${{py}}" r="22" fill="url(#supplyGlow)" opacity="0.6"><animate attributeName="r" from="20" to="32" dur="1.2s" repeatCount="indefinite"/><animate attributeName="opacity" from="0.7" to="0.2" dur="1.2s" repeatCount="indefinite"/></circle>`;
    // 圆背景
    html += `<circle cx="${{px}}" cy="${{py}}" r="14" fill="${{info.color}}" opacity="0.3" stroke="${{info.color}}" stroke-width="2"/>`;
    // 图标
    html += `<text x="${{px}}" y="${{py+6}}" text-anchor="middle" font-size="18">${{info.icon}}</text>`;
    // 名称
    html += `<text x="${{px}}" y="${{py+28}}" text-anchor="middle" fill="${{info.color}}" font-size="9" font-weight="700">${{info.name}}</text>`;
  }}
  // ===== 技能动画 =====
  for (const sk of (f.active_skills || [])) {{
    if (!sk.pos || sk.hero_idx < 0) continue;
    const [spx, spy] = toPx(sk.pos[0], sk.pos[1]);
    const stype = sk.type;
    if (stype === 'taunt') {{
      html += `<circle cx="${{spx}}" cy="${{spy}}" r="50" fill="none" stroke="#fbbf24" stroke-width="3" opacity="0.8"><animate attributeName="r" from="10" to="90" dur="0.8s" repeatCount="1"/><animate attributeName="opacity" from="1" to="0" dur="0.8s" repeatCount="1"/></circle>`;
      html += `<text x="${{spx}}" y="${{spy-50}}" text-anchor="middle" fill="#fbbf24" font-size="14" font-weight="900">🔥嘲讽!</text>`;
    }} else if (stype === 'dash') {{
      html += `<line x1="${{spx-40}}" y1="${{spy}}" x2="${{spx+40}}" y2="${{spy}}" stroke="#ec4899" stroke-width="6" opacity="0.8" stroke-linecap="round"><animate attributeName="opacity" from="1" to="0" dur="0.4s" repeatCount="1"/></line>`;
      html += `<text x="${{spx}}" y="${{spy-30}}" text-anchor="middle" fill="#ec4899" font-size="13" font-weight="900">⚡突进!</text>`;
    }} else if (stype === 'piercing') {{
      html += `<path d="M ${{spx}} ${{spy}} L ${{spx+120}} ${{spy-30}} L ${{spx+120}} ${{spy+30}} Z" fill="#10b981" opacity="0.4"/>`;
      html += `<line x1="${{spx}}" y1="${{spy}}" x2="${{spx+140}}" y2="${{spy}}" stroke="#10b981" stroke-width="3"><animate attributeName="opacity" from="1" to="0" dur="0.5s" repeatCount="1"/></line>`;
      html += `<text x="${{spx+70}}" y="${{spy-15}}" text-anchor="middle" fill="#10b981" font-size="13" font-weight="900">🏹穿透箭!</text>`;
    }} else if (stype === 'heal') {{
      for (let k = 0; k < 5; k++) {{
        const ox = (k - 2) * 8;
        html += `<circle cx="${{spx+ox}}" cy="${{spy+10}}" r="3" fill="#34d399"><animate attributeName="cy" from="${{spy+10}}" to="${{spy-30}}" dur="0.8s" repeatCount="1"/><animate attributeName="opacity" from="1" to="0" dur="0.8s" repeatCount="1"/></circle>`;
      }}
      html += `<text x="${{spx}}" y="${{spy-25}}" text-anchor="middle" fill="#34d399" font-size="14" font-weight="900">✚+治疗!</text>`;
    }} else if (stype === 'fireball') {{
      html += `<circle cx="${{spx}}" cy="${{spy}}" r="35" fill="#ea580c" opacity="0.3"><animate attributeName="r" from="5" to="50" dur="0.6s" repeatCount="1"/><animate attributeName="opacity" from="1" to="0" dur="0.6s" repeatCount="1"/></circle>`;
      html += `<text x="${{spx}}" y="${{spy+5}}" text-anchor="middle" font-size="22">🔥</text>`;
    }}
  }}
  // ===== 武器攻击动画 =====
  for (const at of (f.active_attacks || [])) {{
    if (at.attacker_idx < 0 || !at.attacker_pos) continue;
    const [p1x, p1y] = toPx(at.attacker_pos[0], at.attacker_pos[1]);
    const [p2x, p2y] = toPx(at.target_pos[0], at.target_pos[1]);
    const weapon = at.weapon;
    const isCrit = at.is_crit;
    if (weapon === 'cannon' || weapon === 'tank' || (weapon === 'shotgun' === false && weapon === 'tank')) {{
      // 大炮/坦克：白色剑光
      const angle = Math.atan2(p2y - p1y, p2x - p1x);
      const arcAngle = angle + Math.PI/4;
      const arcR = 28;
      const ax1 = p2x - Math.cos(arcAngle) * arcR;
      const ay1 = p2y - Math.sin(arcAngle) * arcR;
      const ax2 = p2x + Math.cos(arcAngle) * arcR;
      const ay2 = p2y + Math.sin(arcAngle) * arcR;
      html += `<line x1="${{p1x}}" y1="${{p1y}}" x2="${{p2x}}" y2="${{p2y}}" stroke="#fef3c7" stroke-width="6" opacity="0.6"><animate attributeName="opacity" from="1" to="0" dur="0.4s" repeatCount="1"/></line>`;
      html += `<line x1="${{p1x}}" y1="${{p1y}}" x2="${{p2x}}" y2="${{p2y}}" stroke="#ffffff" stroke-width="3" opacity="0.9"><animate attributeName="opacity" from="1" to="0" dur="0.3s" repeatCount="1"/></line>`;
      html += `<path d="M ${{ax1}} ${{ay1}} A 28 28 0 0 1 ${{ax2}} ${{ay2}}" fill="none" stroke="#fbbf24" stroke-width="3" opacity="0.9"><animateTransform attributeName="transform" type="rotate" from="0 ${{p2x}} ${{p2y}}" to="180 ${{p2x}} ${{p2y}}" dur="0.4s" repeatCount="1"/></path>`;
      html += `<circle cx="${{p2x}}" cy="${{p2y}}" r="6" fill="#fef3c7"><animate attributeName="r" from="6" to="24" dur="0.4s" repeatCount="1"/><animate attributeName="opacity" from="1" to="0" dur="0.4s" repeatCount="1"/></circle>`;
      html += `<circle cx="${{p2x}}" cy="${{p2y}}" r="10" fill="none" stroke="#fbbf24" stroke-width="2"><animate attributeName="r" from="4" to="30" dur="0.5s" repeatCount="1"/><animate attributeName="opacity" from="1" to="0" dur="0.5s" repeatCount="1"/></circle>`;
    }} else if (weapon === 'shotgun' || weapon === 'assassin') {{
      // 散弹：5 发扇形
      const angle = Math.atan2(p2y - p1y, p2x - p1x);
      for (let p = 0; p < 5; p++) {{
        const spread = (p - 2) * 0.18;
        const a = angle + spread;
        const tx = p1x + Math.cos(a) * 60;
        const ty = p1y + Math.sin(a) * 60;
        html += `<line x1="${{p1x}}" y1="${{p1y}}" x2="${{tx}}" y2="${{ty}}" stroke="#f59e0b" stroke-width="2" opacity="0.85"><animate attributeName="opacity" from="1" to="0" dur="0.2s" repeatCount="1"/></line>`;
        html += `<circle cx="${{tx}}" cy="${{ty}}" r="3" fill="#fde68a"><animate attributeName="r" from="3" to="6" dur="0.2s" repeatCount="1"/></circle>`;
      }}
      // 残影
      for (let trail = 1; trail <= 3; trail++) {{
        const ox = -Math.cos(angle) * trail * 10;
        const oy = -Math.sin(angle) * trail * 10;
        html += `<circle cx="${{p2x+ox}}" cy="${{p2y+oy}}" r="6" fill="#f59e0b" opacity="${{0.5 - trail * 0.15}}"><animate attributeName="opacity" from="${{0.5 - trail*0.15}}" to="0" dur="0.3s" repeatCount="1"/></circle>`;
      }}
      html += `<circle cx="${{p2x}}" cy="${{p2y}}" r="5" fill="#fbcfe8"><animate attributeName="r" from="3" to="18" dur="0.3s" repeatCount="1"/><animate attributeName="opacity" from="1" to="0" dur="0.3s" repeatCount="1"/></circle>`;
    }} else if (weapon === 'laser' || weapon === 'marksman') {{
      // 激光：长程单发穿透
      const angle = Math.atan2(p2y - p1y, p2x - p1x);
      // 延长到 1.5 倍距离表示穿透
      const ex = p2x + Math.cos(angle) * 80;
      const ey = p2y + Math.sin(angle) * 80;
      html += `<line x1="${{p1x}}" y1="${{p1y}}" x2="${{ex}}" y2="${{ey}}" stroke="#fef2f2" stroke-width="8" opacity="0.5"><animate attributeName="opacity" from="0.7" to="0" dur="0.3s" repeatCount="1"/></line>`;
      html += `<line x1="${{p1x}}" y1="${{p1y}}" x2="${{ex}}" y2="${{ey}}" stroke="#ef4444" stroke-width="3"><animate attributeName="opacity" from="1" to="0" dur="0.2s" repeatCount="1"/></line>`;
      // 中心高亮
      html += `<line x1="${{p1x}}" y1="${{p1y}}" x2="${{ex}}" y2="${{ey}}" stroke="#fff" stroke-width="1"><animate attributeName="opacity" from="1" to="0" dur="0.15s" repeatCount="1"/></line>`;
      // 落点爆炸
      html += `<circle cx="${{p2x}}" cy="${{p2y}}" r="6" fill="none" stroke="#ef4444" stroke-width="2"><animate attributeName="r" from="4" to="20" dur="0.3s" repeatCount="1"/><animate attributeName="opacity" from="1" to="0" dur="0.3s" repeatCount="1"/></circle>`;
    }} else if (weapon === 'fireball' || weapon === 'mage') {{
      // 火球：3 层 + 飞溅粒子
      const mx = (p1x + p2x) / 2;
      const my = (p1y + p2y) / 2;
      html += `<circle cx="${{mx}}" cy="${{my}}" r="14" fill="#fde68a" opacity="0.8"><animate attributeName="r" from="8" to="20" dur="0.5s" repeatCount="1"/><animate attributeName="opacity" from="0.9" to="0" dur="0.5s" repeatCount="1"/></circle>`;
      html += `<circle cx="${{mx}}" cy="${{my}}" r="10" fill="#fb923c" opacity="1"><animate attributeName="r" from="6" to="18" dur="0.5s" repeatCount="1"/><animate attributeName="opacity" from="1" to="0" dur="0.5s" repeatCount="1"/></circle>`;
      html += `<circle cx="${{p2x}}" cy="${{p2y}}" r="22" fill="none" stroke="#fb923c" stroke-width="3"><animate attributeName="r" from="10" to="35" dur="0.5s" repeatCount="1"/><animate attributeName="opacity" from="1" to="0" dur="0.5s" repeatCount="1"/></circle>`;
      for (let k = 0; k < 6; k++) {{
        const pa = (k / 6) * Math.PI * 2;
        html += `<circle cx="${{p2x + Math.cos(pa)*5}}" cy="${{p2y + Math.sin(pa)*5}}" r="2" fill="#fb923c"><animate attributeName="cx" from="${{p2x + Math.cos(pa)*5}}" to="${{p2x + Math.cos(pa)*20}}" dur="0.4s" repeatCount="1"/><animate attributeName="opacity" from="1" to="0" dur="0.4s" repeatCount="1"/></circle>`;
      }}
    }} else if (weapon === 'heal' || weapon === 'support') {{
      // 治疗：金色光束 + 上升粒子
      html += `<line x1="${{p1x}}" y1="${{p1y}}" x2="${{p2x}}" y2="${{p2y}}" stroke="#fef3c7" stroke-width="6" opacity="0.5"><animate attributeName="opacity" from="0.6" to="0" dur="0.5s" repeatCount="1"/></line>`;
      html += `<line x1="${{p1x}}" y1="${{p1y}}" x2="${{p2x}}" y2="${{p2y}}" stroke="#34d399" stroke-width="3" stroke-dasharray="6,3"><animate attributeName="stroke-dashoffset" from="0" to="-18" dur="0.3s" repeatCount="1"/></line>`;
      for (let k = 0; k < 6; k++) {{
        const ox = (k - 2.5) * 5;
        html += `<circle cx="${{p2x+ox}}" cy="${{p2y+8}}" r="2.5" fill="#fde047"><animate attributeName="cy" from="${{p2y+8}}" to="${{p2y-25}}" dur="0.8s" repeatCount="1"/><animate attributeName="opacity" from="1" to="0" dur="0.8s" repeatCount="1"/></circle>`;
      }}
      html += `<circle cx="${{p2x}}" cy="${{p2y}}" r="14" fill="none" stroke="#34d399" stroke-width="2" opacity="0.8"><animate attributeName="r" from="8" to="22" dur="0.5s" repeatCount="1"/><animate attributeName="opacity" from="0.9" to="0" dur="0.5s" repeatCount="1"/></circle>`;
    }} else {{
      // 默认：白色连线
      html += `<line x1="${{p1x}}" y1="${{p1y}}" x2="${{p2x}}" y2="${{p2y}}" stroke="#fbbf24" stroke-width="3" opacity="0.9" stroke-linecap="round"><animate attributeName="opacity" from="1" to="0" dur="0.3s" repeatCount="1"/></line>`;
    }}
    // 伤害数字（所有武器通用）
    const dmgColor = isCrit ? '#fbbf24' : (weapon === 'heal' || weapon === 'support' ? '#34d399' : '#ffffff');
    const dmgText = isCrit ? ('暴击 -' + at.damage) : (weapon === 'heal' || weapon === 'support' ? ('+' + at.damage + 'HP') : ('-' + at.damage));
    html += `<text x="${{p2x+12}}" y="${{p2y-12}}" fill="${{dmgColor}}" font-size="${{isCrit ? 16 : 13}}" font-weight="900" stroke="#000" stroke-width="1" paint-order="stroke"><animate attributeName="y" from="${{p2y-12}}" to="${{p2y-32}}" dur="0.6s" repeatCount="1"/><animate attributeName="opacity" from="1" to="0" dur="0.6s" repeatCount="1"/>${{dmgText}}</text>`;
  }}
  // ===== 拾取动画 =====
  for (const pk of (f.pickups || [])) {{
    const [px, py] = toPx(pk.pos[0], pk.pos[1]);
    const info = SUPPLY_INFO[pk.type] || {{}};
    html += `<text x="${{px}}" y="${{py-15}}" text-anchor="middle" fill="${{info.color || '#fff'}}" font-size="16" font-weight="900"><animate attributeName="y" from="${{py-15}}" to="${{py-50}}" dur="0.8s" repeatCount="1"/><animate attributeName="opacity" from="1" to="0" dur="0.8s" repeatCount="1"/>${{info.icon}} ${{pk.hero}} 拾取!</text>`;
  }}
  // ===== 英雄（带护盾圈/buff）=====
  HERO_META.forEach((m, i) => {{
    const [px, py] = toPx(f.positions[i][0], f.positions[i][1]);
    const isDead = f.healths[i] <= 0;
    const color = isDead ? '#475569' : m.color;
    const sideColor = m.side === 'blue' ? '#3b82f6' : '#ef4444';
    const sideColorDark = m.side === 'blue' ? '#1e3a8a' : '#7f1d1d';
    const sideLight = m.side === 'blue' ? '#60a5fa' : '#fca5a5';
    const opacity = isDead ? 0.4 : 1;
    const hp = f.healths[i];
    const hpPct = Math.max(0, hp / m.max_hp);
    const shield = f.shields ? f.shields[i] : 0;
    const buffList = (f.buffs && f.buffs[i] || '').split('|').filter(Boolean);
    html += `<g opacity="${{opacity}}">`;
    if (!isDead) {{
      // 阵营大光环
      html += `<circle cx="${{px}}" cy="${{py}}" r="32" fill="${{sideColor}}" opacity="0.12"/>`;
      html += `<circle cx="${{px}}" cy="${{py}}" r="26" fill="none" stroke="${{sideColor}}" stroke-width="1.5" stroke-dasharray="2,4" opacity="0.6"><animateTransform attributeName="transform" type="rotate" from="0 ${{px}} ${{py}}" to="360 ${{px}} ${{py}}" dur="3s" repeatCount="indefinite"/></circle>`;
      // 护盾圈
      if (shield > 0) {{
        html += `<circle cx="${{px}}" cy="${{py}}" r="24" fill="none" stroke="#60a5fa" stroke-width="3" opacity="0.8"><animate attributeName="opacity" values="0.4;0.9;0.4" dur="1s" repeatCount="indefinite"/></circle>`;
        html += `<text x="${{px+22}}" y="${{py-22}}" text-anchor="middle" font-size="14">🛡</text>`;
      }}
      // 攻击 buff
      if (buffList.includes('damage_buff')) {{
        html += `<circle cx="${{px}}" cy="${{py}}" r="28" fill="none" stroke="#ef4444" stroke-width="2" stroke-dasharray="5,3" opacity="0.7"><animateTransform attributeName="transform" type="rotate" from="0 ${{px}} ${{py}}" to="-360 ${{px}} ${{py}}" dur="1.5s" repeatCount="indefinite"/></circle>`;
        html += `<text x="${{px-22}}" y="${{py-22}}" text-anchor="middle" font-size="14">⚔</text>`;
      }}
    }}
    // HP 弧
    if (!isDead) {{
      html += `<circle cx="${{px}}" cy="${{py}}" r="22" fill="none" stroke="rgba(0,0,0,.6)" stroke-width="4"/>`;
      const angle = hpPct * 2 * Math.PI;
      html += `<circle cx="${{px}}" cy="${{py}}" r="22" fill="none" stroke="${{sideColor}}" stroke-width="4" stroke-dasharray="${{angle * 22 / Math.PI}} 200" transform="rotate(-90 ${{px}} ${{py}})" stroke-linecap="round"/>`;
      if (hpPct < 0.3) {{
        html += `<circle cx="${{px}}" cy="${{py}}" r="22" fill="none" stroke="#ef4444" stroke-width="2" opacity="0.8"><animate attributeName="opacity" values="0.4;1;0.4" dur="0.6s" repeatCount="indefinite"/></circle>`;
      }}
    }}
    html += `<circle cx="${{px}}" cy="${{py}}" r="18" fill="${{color}}" opacity="0.25"/>`;
    html += `<defs><radialGradient id="hero${{i}}"><stop offset="0%" stop-color="${{sideLight}}"/><stop offset="100%" stop-color="${{color}}"/></radialGradient></defs>`;
    html += `<circle cx="${{px}}" cy="${{py}}" r="14" fill="url(#hero${{i}})" stroke="${{sideColorDark}}" stroke-width="2.5"/>`;
    html += `<text x="${{px}}" y="${{py+5}}" text-anchor="middle" fill="#fff" font-size="13" font-weight="900" stroke="#000" stroke-width="0.5">${{m.icon}}</text>`;
    // 阵营徽章
    html += `<polygon points="${{px-5}},${{py-12}} ${{px+5}},${{py-12}} ${{px}},${{py-16}}" fill="${{sideColor}}"/>`;
    // 名字
    html += `<text x="${{px}}" y="${{py+38}}" text-anchor="middle" fill="#fff" font-size="10" font-weight="900" stroke="#000" stroke-width="2" paint-order="stroke">${{m.name}}</text>`;
    if (!isDead) {{
      const hpColor = hpPct < 0.3 ? '#ef4444' : '#fff';
      html += `<text x="${{px}}" y="${{py-22}}" text-anchor="middle" fill="${{hpColor}}" font-size="10" font-weight="900" stroke="#000" stroke-width="2" paint-order="stroke">${{Math.round(hp)}}</text>`;
    }}
    if (isDead) html += `<text x="${{px+14}}" y="${{py-10}}" fill="#475569" font-size="14">💀</text>`;
    html += `</g>`;
  }});
  // 帧水印
  html += `<text x="${{MAP_W-10}}" y="${{MAP_H-10}}" text-anchor="end" fill="#75829a" font-size="10">${{currentMode}} · 真实引擎 · T+${{currentFrame}}/${{TOTAL}}</text>`;
  svg.innerHTML = html;
}}

function renderEvents() {{
  const el = document.getElementById('event-stream');
  const all = [];
  for (let i = 0; i <= currentFrame; i++) {{
    for (const e of (FRAMES[i]?.events || [])) all.push({{...e, t: i}});
  }}
  const recent = all.slice(-12).reverse();
  if (!recent.length) {{
    el.innerHTML = '<div style="color:#75829a;font-size:11px;text-align:center;padding:10px;">等待事件...</div>';
    return;
  }}
  el.innerHTML = recent.map(e => {{
    const streak = e.streak >= 2 ? `<span class="event-streak">${{e.label || ''}}</span>` : '';
    const kCls = e.side === 'blue' ? 'event-killer' : 'event-victim';
    const vCls = e.side === 'blue' ? 'event-victim' : 'event-killer';
    let verb = '⚔击杀了';
    if (e.type === 'tower_destroyed') verb = '⚡摧毁了';
    else if (e.type === 'supply_pickup') {{
      const info = SUPPLY_INFO[e.victim] || {{}};
      return `<div class="event-line">
        <span class="event-time">T+${{e.t}}s</span>
        <span style="color:${{info.color || '#fff'}}">${{info.icon || '📦'}} ${{e.killer}} 拾取 ${{info.name || e.victim}}</span>
      </div>`;
    }}
    return `<div class="event-line">
      <span class="event-time">T+${{e.t}}s</span>
      <span class="${{kCls}}">${{verb}} ${{e.killer}}</span>
      ${{e.victim && e.type !== 'supply_pickup' ? `<span class="event-arrow">→</span><span class="${{vCls}}">💀 ${{e.victim}}</span>` : ''}}
      ${{streak}}
    </div>`;
  }}).join('');
}}

function renderCommentary() {{
  const el = document.getElementById('commentary-list');
  const all = [];
  for (let i = 0; i <= currentFrame; i++) {{
    for (const e of (FRAMES[i]?.events || [])) all.push({{...e, t: i}});
    for (const s of (FRAMES[i]?.streaks || [])) all.push({{t:i, type:'streak_announce', killer:s.hero, label:s.label, side:s.side, streak:s.count}});
  }}
  const recent = all.slice(-6);
  if (!recent.length) {{
    el.innerHTML = '<div style="color:#75829a;font-style:italic;">（等待精彩时刻...）</div>';
    return;
  }}
  el.innerHTML = recent.map(e => {{
    let text = '';
    if (e.type === 'streak_announce' && e.streak >= 3) text = `🔥 ${{e.killer}} ${{e.label || 'LEGENDARY!'}}!`;
    else if (e.type === 'streak_announce' && e.streak === 2) text = `⚡ ${{e.killer}} ${{e.label || 'DOUBLE KILL!'}}!`;
    else if (e.type === 'kill') text = `🗡 ${{e.killer}} 击杀了 ${{e.victim}}`;
    else if (e.type === 'tower_destroyed') text = `🏰 防御塔被摧毁！`;
    else if (e.type === 'supply_pickup') text = `📦 ${{e.killer}} 拾取了 ${{e.victim}}`;
    return `<div style="color:#e9f0ff;margin:2px 0;">${{text}}</div>`;
  }}).join('');
}}

function renderScore() {{
  const f = getFrame();
  document.getElementById('score-blue').textContent = f.blue_kills;
  document.getElementById('score-red').textContent = f.red_kills;
  document.getElementById('kill-summary').textContent = `${{f.blue_kills}}/${{f.red_kills}}`;
  document.getElementById('tower-stat').textContent = `${{f.tower_alive}}/6`;
  let maxStreak = 0;
  for (let i = 0; i <= currentFrame; i++) {{
    for (const s of (FRAMES[i]?.streaks || [])) if (s.count > maxStreak) maxStreak = s.count;
  }}
  document.getElementById('streak-stat').textContent = maxStreak;
  document.getElementById('current-frame').textContent = currentFrame;
  document.getElementById('total-frames').textContent = TOTAL;
  const killRate = f.blue_kills / (f.blue_kills + f.red_kills + 0.001);
  winRate = Math.round(50 + (killRate - 0.5) * 30 + (f.tower_alive - 3) * 5);
  winRate = Math.max(5, Math.min(95, winRate));
  document.getElementById('win-rate').textContent = winRate + '%';
  const delta = winRate - lastWinRate;
  document.getElementById('win-delta').textContent = (delta >= 0 ? '+' : '') + delta + '%';
  document.getElementById('win-delta').style.color = delta >= 0 ? '#39daa0' : '#fb6470';
  document.getElementById('win-bar').style.width = winRate + '%';
  lastWinRate = winRate;
}}

function showFlyBubble(text) {{
  const host = document.getElementById('fly-bubble-host');
  const div = document.createElement('div');
  div.className = 'fly-bubble';
  div.textContent = text;
  host.appendChild(div);
  setTimeout(() => div.remove(), 2500);
}}

function renderAll() {{
  renderHeroes();
  renderBattle();
  renderEvents();
  renderCommentary();
  renderScore();
  const f = getFrame();
  for (const s of (f.streaks || [])) {{
    if (s.count >= 2 && s.label) showFlyBubble(s.label);
  }}
}}

function setSpeed(s) {{
  speed = s;
  document.querySelectorAll('.speed-btn').forEach(b => b.classList.remove('active'));
  if (s === 0.5) document.getElementById('sp-05').classList.add('active');
  if (s === 1) document.getElementById('sp-1').classList.add('active');
  if (s === 2) document.getElementById('sp-2').classList.add('active');
  if (interval) {{
    clearInterval(interval);
    if (isPlaying) interval = setInterval(tick, 250 / speed);
  }}
}}

function togglePause() {{
  isPlaying = !isPlaying;
  document.getElementById('btn-pause').textContent = isPlaying ? '⏸' : '▶';
  if (interval) clearInterval(interval);
  if (isPlaying) interval = setInterval(tick, 250 / speed);
}}

function tick() {{
  currentFrame++;
  if (currentFrame >= TOTAL) currentFrame = 0;
  renderAll();
}}

// 启动
renderAll();
interval = setInterval(tick, 250);
</script>'''

new_html = head_body + new_script
with open('outputs/team_3v3_v3.html', 'w', encoding='utf-8') as f:
    f.write(new_html)
print(f'OK 写入 {len(new_html)/1024:.1f} KB')