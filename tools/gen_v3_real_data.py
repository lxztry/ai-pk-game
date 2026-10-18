"""用真实 NvN 引擎生成 v4 HTML —— 多模式（1v1/3v3/5v5）+ 补给系统"""
import sys, random, json, os
sys.path.insert(0, '.')
from game.team_state import TeamGameState, Supply
from game.team_engine import TeamEngine
from agents.team_agents import TankAI, AssassinAI, MarksmanAI, SupportAI, MageAI
from game.weapons import ROLE_WEAPON, WEAPONS, SUPPLY_TYPES

ICON_MAP = {'tank':'盾','assassin':'刺','marksman':'射','support':'辅','mage':'法'}
# 阵营配色：蓝方亮饱和，红方深暗调
BLUE_COLOR = {'tank':'#f59e0b', 'assassin':'#a855f7', 'marksman':'#10b981', 'support':'#ec4899', 'mage':'#06b6d4'}
RED_COLOR  = {'tank':'#ef4444', 'assassin':'#9333ea', 'marksman':'#dc2626', 'support':'#f97316', 'mage':'#fb7185'}
ROLE_CLASS = {'tank': TankAI, 'assassin': AssassinAI, 'marksman': MarksmanAI, 'support': SupportAI, 'mage': MageAI}

# 选手数量配置
MODES = {
    '1v1': {
        'blue_heroes': [{'name':'蓝焰战士', 'role':'tank', 'lane':'mid'}],
        'red_heroes':  [{'name':'赤焰战士', 'role':'tank', 'lane':'mid'}],
        'description': '经典单挑，看谁先倒下',
    },
    '3v3': {
        'blue_heroes': [
            {'name':'蓝焰坦克', 'role':'tank',     'lane':'mid'},
            {'name':'疾风刺客', 'role':'assassin', 'lane':'top'},
            {'name':'穿云射手', 'role':'marksman', 'lane':'bot'},
        ],
        'red_heroes': [
            {'name':'铁壁',     'role':'tank',     'lane':'top'},
            {'name':'圣女',     'role':'support',  'lane':'mid'},
            {'name':'烈焰法师', 'role':'mage',     'lane':'bot'},
        ],
        'description': '3v3 团队战，5 角色混搭',
    },
    '5v5': {
        'blue_heroes': [
            {'name':'蓝焰坦克', 'role':'tank',     'lane':'top'},
            {'name':'疾风刺客', 'role':'assassin', 'lane':'mid'},
            {'name':'穿云射手', 'role':'marksman', 'lane':'bot'},
            {'name':'碧波辅助', 'role':'support',  'lane':'top'},
            {'name':'冰霜法师', 'role':'mage',     'lane':'mid'},
        ],
        'red_heroes': [
            {'name':'铁壁',     'role':'tank',     'lane':'bot'},
            {'name':'暗影刺客', 'role':'assassin', 'lane':'mid'},
            {'name':'烈焰射手', 'role':'marksman', 'lane':'top'},
            {'name':'圣女',     'role':'support',  'lane':'bot'},
            {'name':'烈焰法师', 'role':'mage',     'lane':'mid'},
        ],
        'description': '5v5 大乱斗，全 5 角色',
    },
}

# 补给点位置（固定 4 个，分散在地图）
SUPPLY_POSITIONS = [
    (15, 8), (15, 16), (25, 8), (25, 16),
]
SUPPLY_CYCLE = ['ammo', 'health', 'shield', 'damage', 'ammo', 'health', 'shield', 'damage']

def make_hero(spec, side, idx):
    cls = ROLE_CLASS[spec['role']]
    h = cls(spec['name'], spec['role'], side, spec['lane'])
    return h

def init_positions(heroes, side):
    """分散初始位置"""
    y_positions = [5, 12, 19, 8, 16]
    x_start = 5 if side == 'blue' else 35
    for i, h in enumerate(heroes):
        y = y_positions[i] if i < len(y_positions) else 12
        x = x_start if i == 0 else (x_start - 2 if side == 'blue' else x_start + 2)
        h.position = (x, y)

def run_mode(mode_name, spec, max_turns=300, seed=42):
    """跑一场指定模式"""
    random.seed(seed)
    blue = [make_hero(s, 'blue', i) for i, s in enumerate(spec['blue_heroes'])]
    red  = [make_hero(s, 'red',  i) for i, s in enumerate(spec['red_heroes'])]
    init_positions(blue, 'blue')
    init_positions(red, 'red')
    s = TeamGameState(blue, red)
    engine = TeamEngine(s)
    if mode_name == '1v1':
        for t in s.blue_towers + s.red_towers:
            t.hp = t.max_hp = 30
            t.attack = 5
    n = len(blue) + len(red)
    hero_names = [h.name for h in blue + red]
    hero_roles = [h.role for h in blue + red]
    hero_sides = [h.side for h in blue + red]
    hero_weapons = [h.weapon_type for h in blue + red]
    frames = []
    hero_meta = []
    for h in blue + red:
        cm = BLUE_COLOR if h.side == 'blue' else RED_COLOR
        wt = h.weapon_type
        wd = WEAPONS.get(wt, {})
        hero_meta.append({
            'name': h.name, 'role': h.role, 'side': h.side,
            'lane': h.lane, 'max_hp': h.max_health, 'max_ammo': h.max_ammo,
            'icon': ICON_MAP.get(h.role, '?'),
            'color': cm.get(h.role, '#888'),
            'weapon_type': wt,
            'weapon_name': wd.get('name', wt),
            'weapon_icon': wd.get('icon', '⚔'),
            'weapon_color': wd.get('color', '#fff'),
        })
    tower_alive_0 = sum(1 for t in s.blue_towers + s.red_towers if not t.destroyed)
    frames.append({
        't': 0, 'positions': [list(h.position) for h in blue + red],
        'healths': [h.health for h in blue + red],
        'ammos': [getattr(h, 'ammo', 30) for h in blue + red],
        'shields': [getattr(h, 'shield', 0) for h in blue + red],
        'kills': [h.stats['kills'] for h in blue + red],
        'deaths': [h.deaths for h in blue + red],
        'blue_kills': s.score['blue'], 'red_kills': s.score['red'],
        'tower_alive': tower_alive_0,
        'base_hp': [s.blue_base.hp, s.red_base.hp],
        'events': [], 'active_attacks': [], 'active_skills': [], 'streaks': [], 'buffs': {},
        'supplies': [], 'pickups': [],
    })
    prev_healths = [h.health for h in blue + red]
    prev_attacker_pos = [None] * n
    supply_idx = 0
    last_supply_spawn = 0
    for turn in range(1, max_turns + 1):
        engine.step()
        if not engine.running:
            break
        event_turn = turn - 1
        recent = [e for e in s.events if e.get('turn') == event_turn]
        pickups_this_turn = []
        if turn - last_supply_spawn >= 30:
            last_supply_spawn = turn
            pos = SUPPLY_POSITIONS[supply_idx % len(SUPPLY_POSITIONS)]
            supply_idx += 1
            stype = SUPPLY_CYCLE[supply_idx % len(SUPPLY_CYCLE)]
            sup = Supply(supply_type=stype, position=pos, spawned_at=turn, expires_at=turn + 100)
            s.supplies.append(sup)
            s.log_event('supply_spawn', type=stype, position=list(pos), turn=turn)
        active_supplies = []
        for sup in s.supplies:
            if sup.consumed or turn > sup.expires_at:
                continue
            consumed = False
            for h in blue + red:
                if h.health <= 0:
                    continue
                dx = h.position[0] - sup.position[0]
                dy = h.position[1] - sup.position[1]
                d = (dx * dx + dy * dy) ** 0.5
                if d < 2.5:
                    sup.consumed = True
                    consumed = True
                    pickups_this_turn.append({'type': sup.supply_type, 'hero': h.name, 'side': h.side, 'pos': list(sup.position)})
                    if sup.supply_type == 'ammo':
                        h.ammo = min(h.max_ammo, h.ammo + 30)
                    elif sup.supply_type == 'health':
                        h.health = min(h.max_health, h.health + 50)
                    elif sup.supply_type == 'shield':
                        h.shield = 30
                        h.shield_until = turn + 25
                    elif sup.supply_type == 'damage':
                        h.damage_buff_until = turn + 25
                    s.log_event('supply_pickup', type=sup.supply_type, hero=h.name, turn=turn)
                    break
            if not consumed:
                active_supplies.append({
                    'type': sup.supply_type,
                    'position': list(sup.position),
                    'remaining': sup.expires_at - turn,
                })
        cur_healths = [h.health for h in blue + red]
        cur_positions = [list(h.position) for h in blue + red]
        cur_ammos = [getattr(h, 'ammo', 30) for h in blue + red]
        cur_shields = [getattr(h, 'shield', 0) for h in blue + red]
        active_attacks = []
        for i, (prev, cur) in enumerate(zip(prev_healths, cur_healths)):
            if cur < prev and cur >= 0:
                target_side = hero_sides[i]
                target_pos = cur_positions[i]
                best_attacker = -1
                best_d = 999
                for j in range(n):
                    if hero_sides[j] == target_side: continue
                    if cur_healths[j] <= 0: continue
                    if prev_attacker_pos[j] is None: continue
                    dx = prev_attacker_pos[j][0] - target_pos[0]
                    dy = prev_attacker_pos[j][1] - target_pos[1]
                    d = (dx * dx + dy * dy) ** 0.5
                    if d < best_d:
                        best_d = d
                        best_attacker = j
                weapon = hero_weapons[best_attacker] if best_attacker >= 0 else 'tower'
                is_crit = (prev - cur) > 25
                active_attacks.append({
                    'target_idx': i, 'target': hero_names[i],
                    'attacker_idx': best_attacker,
                    'attacker': hero_names[best_attacker] if best_attacker >= 0 else 'tower',
                    'attacker_pos': prev_attacker_pos[best_attacker] if best_attacker >= 0 and prev_attacker_pos[best_attacker] else target_pos,
                    'target_pos': target_pos,
                    'weapon': weapon,
                    'damage': prev - cur,
                    'is_tower': False,
                    'is_crit': is_crit,
                })
        for j in range(n):
            if cur_healths[j] > 0:
                prev_attacker_pos[j] = cur_positions[j]
        prev_healths = cur_healths
        active_skills = []
        for e in recent:
            et = e.get('type', '')
            if et.startswith('skill_'):
                hero_idx = next((i for i, hn in enumerate(hero_names) if hn == e.get('hero')), -1)
                skill_pos = cur_positions[hero_idx] if hero_idx >= 0 else None
                active_skills.append({
                    'hero': e.get('hero'), 'hero_idx': hero_idx,
                    'type': et[6:],
                    'pos': skill_pos,
                    'targets': e.get('targets', e.get('target', '')),
                    'hit': e.get('hit', 1),
                    'dmg': e.get('dmg', 0),
                    'amount': e.get('amount', 0),
                })
        tower_alive = sum(1 for t in s.blue_towers + s.red_towers if not t.destroyed)
        streaks = []
        for e in recent:
            if e.get('type') == 'kill' and e.get('streak', 0) >= 2:
                streaks.append({'hero': e.get('killer'), 'count': e.get('streak'),
                                'label': e.get('label', ''), 'side': e.get('side', '')})
        buffs = {}
        for j, h in enumerate(blue + red):
            if h.health <= 0: continue
            if hasattr(h, 'taunt_until') and h.taunt_until > 0:
                buffs[j] = 'taunting'
            elif hasattr(h, 'taunted_by') and h.taunted_by:
                buffs[j] = 'taunted'
            if hasattr(h, 'shield_until') and h.shield_until > turn:
                buffs[j] = (buffs.get(j, '') + '|shield').strip('|')
            if hasattr(h, 'damage_buff_until') and h.damage_buff_until > turn:
                buffs[j] = (buffs.get(j, '') + '|damage_buff').strip('|')
        frames.append({
            't': turn, 'positions': cur_positions,
            'healths': cur_healths, 'ammos': cur_ammos, 'shields': cur_shields,
            'kills': [h.stats['kills'] for h in blue + red],
            'deaths': [h.deaths for h in blue + red],
            'blue_kills': s.score['blue'], 'red_kills': s.score['red'],
            'tower_alive': tower_alive,
            'base_hp': [s.blue_base.hp, s.red_base.hp],
            'events': [{
                't': turn, 'type': e.get('type'),
                'killer': e.get('killer', ''), 'victim': e.get('victim', ''),
                'streak': e.get('streak', 0), 'label': e.get('label', ''),
                'side': e.get('side', ''),
            } for e in recent if e.get('type') in ('kill', 'tower_destroyed', 'streak', 'supply_pickup')],
            'active_attacks': active_attacks,
            'active_skills': active_skills,
            'streaks': streaks,
            'buffs': buffs,
            'supplies': active_supplies,
            'pickups': pickups_this_turn,
        })
    print(f"[{mode_name}] {len(frames)} 帧, 蓝{s.score['blue']}:红{s.score['red']}, 攻击:{sum(len(f['active_attacks']) for f in frames)}, 技能:{sum(len(f['active_skills']) for f in frames)}, 补给:{supply_idx}")
    return {
        'mode': mode_name,
        'description': spec['description'],
        'meta': hero_meta,
        'frames': frames,
        'final_blue': s.score['blue'],
        'final_red': s.score['red'],
        'tower_destroyed': sum(1 for t in s.blue_towers + s.red_towers if t.destroyed),
    }

# 跑三种模式
results = {}
for mode_name, spec in MODES.items():
    results[mode_name] = run_mode(mode_name, spec, max_turns=300)

# 保存
out_path = 'outputs/team_v4_modes.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False)
print(f"OK 写入 {os.path.getsize(out_path)/1024:.1f} KB")