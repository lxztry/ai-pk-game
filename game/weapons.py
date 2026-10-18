"""武器系统：12 种武器，每种有不同动画/效果参数。

weapon_type → 视觉参数 + 效果类型
- 单发伤害
- 是否多发（散弹）
- 是否持续（激光/火焰）
- 是否有 AOE（大炮）
- 是否控制（冰冻/晕眩）
"""
# role → 默认 weapon
ROLE_WEAPON = {
    'tank':     'cannon',    # 大炮：重击慢速
    'assassin': 'shotgun',   # 散弹：多发扇形
    'marksman': 'laser',     # 激光：长程单发穿透
    'support':  'heal',      # 治疗：加血
    'mage':     'fireball',  # 火球：AOE
}

# 武器视觉参数
WEAPONS = {
    'shotgun':  {'name':'散弹', 'color':'#f59e0b', 'pellets': 5, 'spread': 0.6, 'icon':'🔫'},
    'laser':    {'name':'激光', 'color':'#ef4444', 'beam': True, 'icon':'🔴'},
    'cannon':   {'name':'大炮', 'color':'#94a3b8', 'aoe': 1.5, 'icon':'💣'},
    'fireball': {'name':'火球', 'color':'#ea580c', 'aoe': 1.2, 'icon':'🔥'},
    'ice':      {'name':'冰冻', 'color':'#06b6d4', 'freeze': True, 'icon':'❄️'},
    'lightning':{'name':'电击', 'color':'#facc15', 'chain': True, 'icon':'⚡'},
    'stun':     {'name':'晕眩', 'color':'#a855f7', 'stun': True, 'icon':'💫'},
    'heal':     {'name':'治疗', 'color':'#34d399', 'heal': True, 'icon':'✚'},
    'poison':   {'name':'剧毒', 'color':'#84cc16', 'dot': True, 'icon':'☠️'},
    'knockback':{'name':'击退', 'color':'#fb923c', 'knockback': True, 'icon':'💥'},
    'shield':   {'name':'护盾', 'color':'#60a5fa', 'shield': True, 'icon':'🛡'},
    'charge':   {'name':'冲锋', 'color':'#c084fc', 'charge': True, 'icon':'⚔'},
}

# 补给类型
SUPPLY_TYPES = {
    'ammo':   {'name':'弹药包', 'icon':'📦', 'color':'#fbbf24', 'effect':'+30 弹药'},
    'health': {'name':'血包', 'icon':'💊', 'color':'#34d399', 'effect':'+50 HP'},
    'shield': {'name':'护盾', 'icon':'🛡', 'color':'#60a5fa', 'effect':'+30% 护盾 5秒'},
    'damage': {'name':'攻击buff', 'icon':'⚔', 'color':'#ef4444', 'effect':'+20% 攻击 5秒'},
}