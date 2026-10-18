"""
在线对战服务器
使用Flask提供Web API和界面
"""
import os
import sys
import json
import logging
import threading
import time
from pathlib import Path
from collections import defaultdict

# 观众打赏存储：match_id -> [gift, ...]
_duel_gifts: dict = defaultdict(list)
_duel_gifts_lock = threading.Lock()
# 限流：每个 match 最多 3 次打赏
MAX_GIFTS_PER_MATCH = 3

# 待处理对决：duel_id -> {player1, player2, provider, ...}
_pending_duel: dict = {}
_pending_duel_lock = threading.Lock()
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS

# 配置 logging（替换散落的 print）
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.agent_loader import AgentLoader
from game.engine import GameEngine
from visualizer.web_visualizer import WebVisualizer
from online.database import Database

app = Flask(__name__, 
            template_folder=str(project_root / 'online' / 'templates'),
            static_folder=str(project_root / 'online' / 'static'))
CORS(app)

# 初始化数据库
db = Database()

# 对战任务队列
match_queue = []
match_results = {}


def run_match(player1_name: str, player2_name: str, match_id: str, max_turns: int = 500):
    """在后台线程中运行对战"""
    try:
        # 确保使用项目根目录的绝对路径
        participants_dir = project_root / "participants"
        
        # 加载Agent
        loader = AgentLoader(participants_dir=str(participants_dir))
        all_agents = loader.create_agent_instances()
        
        agent1 = next((a for a in all_agents if a.name == player1_name), None)
        agent2 = next((a for a in all_agents if a.name == player2_name), None)
        
        if not agent1 or not agent2:
            match_results[match_id] = {
                'status': 'error',
                'message': f'找不到玩家: {player1_name} 或 {player2_name}'
            }
            return
        
        # 重置Agent状态
        agent1.reset()
        agent2.reset()
        
        # 创建可视化器
        visualizer = WebVisualizer(map_width=100, map_height=100)
        
        # 创建游戏引擎
        engine = GameEngine([agent1, agent2], map_width=100, map_height=100)
        
        # 运行游戏
        import time as time_module
        frame_interval = 2
        winner = None
        last_state_info = None
        
        # 超时保护：防止游戏卡住
        match_start_time = time_module.time()
        max_match_time = 120.0  # 最大对战时间120秒
        last_progress_time = match_start_time
        last_alive_count = len([a for a in engine.state.agents if a.health > 0])
        consecutive_no_progress = 0
        max_no_progress_turns = 100  # 连续100回合没有进展则判定为卡住
        
        while engine.state.turn < max_turns:
            # 检查总超时
            elapsed_time = time_module.time() - match_start_time
            if elapsed_time > max_match_time:
                print(f"警告: 对战 {match_id} 超过最大时间限制 ({max_match_time}秒)，强制结束")
                break
            
            # 执行一步
            step_start_time = time_module.time()
            try:
                state_info = engine.step()
                step_elapsed = time_module.time() - step_start_time
                
                # 如果单步执行时间过长，警告
                if step_elapsed > 2.0:
                    print(f"警告: 回合 {engine.state.turn} 执行时间过长 ({step_elapsed:.2f}秒)")
            except Exception as e:
                print(f"错误: 回合 {engine.state.turn} 执行出错: {e}")
                import traceback
                traceback.print_exc()
                break
            
            last_state_info = state_info
            
            # 检查是否有进展（存活人数变化或回合数增加）
            current_alive_count = state_info.get('alive_count', 0)
            if current_alive_count != last_alive_count:
                last_progress_time = time_module.time()
                consecutive_no_progress = 0
                last_alive_count = current_alive_count
            else:
                consecutive_no_progress += 1
                # 如果连续很多回合没有进展，可能卡住了
                if consecutive_no_progress >= max_no_progress_turns:
                    time_since_progress = time_module.time() - last_progress_time
                    if time_since_progress > 30.0:  # 30秒没有进展
                        print(f"警告: 对战 {match_id} 连续 {consecutive_no_progress} 回合没有进展，可能卡住，强制结束")
                        break
            
            if engine.state.turn % frame_interval == 0:
                visualizer.record_frame(state_info)
            
            winner = engine.state.get_winner(allow_score_judge=False)
            if winner:
                for _ in range(10):
                    try:
                        state_info = engine.step()
                        visualizer.record_frame(state_info)
                    except Exception as e:
                        print(f"错误: 记录最后帧时出错: {e}")
                        break
                break
        
        # 超时后按评分判定
        if winner is None:
            if last_state_info:
                if not visualizer.replay_data or visualizer.replay_data[-1]['turn'] != last_state_info['turn']:
                    visualizer.record_frame(last_state_info)
            winner = engine.state.get_winner(allow_score_judge=True)
            if winner and visualizer.replay_data:
                visualizer.set_winner(winner.name)
        
        # 保存回放
        replay_dir = project_root / "online" / "replays"
        replay_dir.mkdir(parents=True, exist_ok=True)
        replay_file = replay_dir / f"{match_id}.html"
        visualizer.generate_html(str(replay_file), auto_play=True, fps=15)
        
        # 更新数据库
        db.update_match_result(
            player1_name=player1_name,
            player2_name=player2_name,
            winner_name=winner.name if winner else None,
            player1_kills=agent1.kills,
            player2_kills=agent2.kills,
            player1_health=agent1.health,
            player2_health=agent2.health,
            replay_file=str(replay_file)
        )
        
        # 保存结果
        match_results[match_id] = {
            'status': 'completed',
            'winner': winner.name if winner else None,
            'player1': {
                'name': player1_name,
                'kills': agent1.kills,
                'health': agent1.health
            },
            'player2': {
                'name': player2_name,
                'kills': agent2.kills,
                'health': agent2.health
            },
            'replay_file': str(replay_file)
        }
        
    except Exception as e:
        match_results[match_id] = {
            'status': 'error',
            'message': str(e)
        }


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/players', methods=['GET'])
def get_players():
    """获取所有玩家列表"""
    players = db.get_all_players()
    return jsonify({'players': players})


@app.route('/api/rankings', methods=['GET'])
def get_rankings():
    """获取排名"""
    limit = request.args.get('limit', 100, type=int)
    rankings = db.get_rankings(limit=limit)
    return jsonify({'rankings': rankings})


@app.route('/api/player/<name>', methods=['GET'])
def get_player(name):
    """获取玩家信息"""
    stats = db.get_player_stats(name)
    if stats:
        return jsonify({'player': stats})
    return jsonify({'error': 'Player not found'}), 404


@app.route('/api/match/start', methods=['POST'])
def start_match():
    """开始对战"""
    data = request.json
    player1_name = data.get('player1')
    player2_name = data.get('player2')
    max_turns = data.get('max_turns', 500)  # 可选参数，默认500
    
    if not player1_name or not player2_name:
        return jsonify({'error': 'Missing player names'}), 400
    
    if player1_name == player2_name:
        return jsonify({'error': 'Cannot match player with itself'}), 400
    
    # 验证回合数范围
    try:
        max_turns = int(max_turns)
        if max_turns < 50 or max_turns > 2000:
            return jsonify({'error': 'max_turns must be between 50 and 2000'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'max_turns must be a valid integer'}), 400
    
    # 生成匹配ID
    match_id = f"{player1_name}_vs_{player2_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 在后台线程中运行对战
    thread = threading.Thread(target=run_match, args=(player1_name, player2_name, match_id, max_turns))
    thread.daemon = True
    thread.start()
    
    match_results[match_id] = {'status': 'running'}
    
    return jsonify({
        'match_id': match_id,
        'status': 'running'
    })


@app.route('/api/match/<match_id>', methods=['GET'])
def get_match_result(match_id):
    """获取对战结果"""
    if match_id not in match_results:
        return jsonify({'error': 'Match not found'}), 404
    
    result = match_results[match_id]
    return jsonify(result)


@app.route('/api/matches', methods=['GET'])
def get_matches():
    """获取对战历史"""
    player_name = request.args.get('player')
    limit = request.args.get('limit', 50, type=int)
    matches = db.get_match_history(player_name, limit)
    return jsonify({'matches': matches})


@app.route('/api/replay/<match_id>', methods=['GET'])
def get_replay(match_id):
    """获取回放文件"""
    if match_id not in match_results:
        return jsonify({'error': 'Match not found'}), 404
    
    result = match_results[match_id]
    if result.get('status') != 'completed' or 'replay_file' not in result:
        return jsonify({'error': 'Replay not available'}), 404
    
    # 处理相对路径和绝对路径
    replay_file_path = result['replay_file']
    if not Path(replay_file_path).is_absolute():
        replay_file = project_root / replay_file_path
    else:
        replay_file = Path(replay_file_path)
    
    if not replay_file.exists():
        return jsonify({'error': f'Replay file not found: {replay_file}'}), 404

    return send_file(str(replay_file))


# ============================================================
#  Prompt Duel Web API（支持多 LLM）
# ============================================================

@app.route('/duel', methods=['GET'])
def duel_form():
    """Prompt 对决表单页"""
    return render_template('duel.html')


# ---------- 观众打赏 API ----------

GIFT_TYPES = {"health", "ammo", "slow", "shield", "boost"}


@app.route('/api/duel/<duel_id>/gift', methods=['POST'])
def post_gift(duel_id):
    """观众打赏接口

    Body JSON:
    {
        "type": "health" | "ammo" | "slow" | "shield" | "boost",
        "target": "player1" | "player2",
        "user": "可选的观众昵称"
    }
    """
    data = request.get_json(silent=True) or {}
    gift_type = data.get('type', '').strip().lower()
    target = data.get('target', '').strip()
    user = (data.get('user') or '匿名观众').strip()[:32]

    # 校验
    if gift_type not in GIFT_TYPES:
        return jsonify({'ok': False, 'error': f'无效打赏类型: {gift_type}。可用: {sorted(GIFT_TYPES)}'}), 400
    if target not in ('player1', 'player2'):
        return jsonify({'ok': False, 'error': 'target 必须是 player1 或 player2'}), 400

    with _duel_gifts_lock:
        existing = _duel_gifts[duel_id]
        if len(existing) >= MAX_GIFTS_PER_MATCH:
            return jsonify({
                'ok': False,
                'error': f'本局打赏已用完（{MAX_GIFTS_PER_MATCH} 次上限）',
                'used': len(existing),
                'limit': MAX_GIFTS_PER_MATCH,
            }), 429

        gift = {
            'type': gift_type,
            'target': target,
            'user': user,
            'ts': int(time.time()),
        }
        existing.append(gift)

    return jsonify({
        'ok': True,
        'gift': gift,
        'used': len(existing),
        'limit': MAX_GIFTS_PER_MATCH,
        'remaining': MAX_GIFTS_PER_MATCH - len(existing),
    })


@app.route('/api/duel/<duel_id>/gifts', methods=['GET'])
def get_gifts(duel_id):
    """查看本局的所有打赏"""
    with _duel_gifts_lock:
        gifts = list(_duel_gifts.get(duel_id, []))
    return jsonify({
        'ok': True,
        'duel_id': duel_id,
        'gifts': gifts,
        'count': len(gifts),
    })


@app.route('/api/duel/<duel_id>/gifts', methods=['DELETE'])
def clear_gifts(duel_id):
    """清空本局打赏（开发用）"""
    with _duel_gifts_lock:
        _duel_gifts.pop(duel_id, None)
    return jsonify({'ok': True})


@app.route('/api/llm-providers', methods=['GET'])
def get_llm_providers():
    """列出支持的 LLM provider（前端表单用）"""
    try:
        from agents.prompt_agent import SUPPORTED_PROVIDERS, PROVIDER_DEFAULTS
        providers = []
        for name in SUPPORTED_PROVIDERS:
            cfg = PROVIDER_DEFAULTS.get(name, {})
            providers.append({
                "name": name,
                "default_model": cfg.get("default_model", ""),
                "api_key_env": cfg.get("api_key_env", ""),
            })
        return jsonify({"providers": providers})
    except ImportError as e:
        return jsonify({"providers": [], "error": str(e)}), 500


@app.route('/api/duel/prepare', methods=['POST'])
def prepare_duel():
    """阶段 1: 准备对决，存 prompt 到内存，生成 duel_id

    接受请求后立即返回 duel_id，前端可以随后：
    - POST /api/duel/<id>/gift  (打赏)
    - POST /api/duel/<id>/start  (真正跑对决并生成回放)
    """
    import uuid
    data = request.get_json(silent=True) or {}

    p1_data = data.get("player1") or {}
    p2_data = data.get("player2") or {}
    if not p1_data.get("prompt") or not p2_data.get("prompt"):
        return jsonify({"error": "player1.prompt 和 player2.prompt 都不能为空"}), 400

    duel_id = uuid.uuid4().hex[:12]

    with _pending_duel_lock:
        _pending_duel[duel_id] = {
            'player1': p1_data,
            'player2': p2_data,
            'provider': data.get('provider', 'openai'),
            'api_key': data.get('api_key') or None,
            'model': data.get('model') or None,
            'max_turns': int(data.get('max_turns', 100)),
            'map_size': int(data.get('map_size', 25)),
            'shotgun': bool(data.get('shotgun_duel', True)),
            'created_at': int(time.time()),
        }

    return jsonify({
        'ok': True,
        'duel_id': duel_id,
        'gift_url': f'/api/duel/{duel_id}/gift',
        'gifts_url': f'/api/duel/{duel_id}/gifts',
        'start_url': f'/api/duel/{duel_id}/start',
        'max_gifts': MAX_GIFTS_PER_MATCH,
    })


@app.route('/api/duel/<duel_id>/start', methods=['POST'])
def start_duel(duel_id):
    """阶段 2: 真正跑对决 + 生成回放（消费打赏）"""
    from tournament.prompt_duel import run_prompt_duel
    from agents.prompt_agent import create_llm_client

    with _pending_duel_lock:
        if duel_id not in _pending_duel:
            return jsonify({"error": f"duel_id {duel_id} 未准备或已过期"}), 404
        config = _pending_duel.pop(duel_id)

    p1_data = config['player1']
    p2_data = config['player2']
    player1 = _duel_player_from_dict(p1_data)
    player2 = _duel_player_from_dict(p2_data)

    provider = config['provider']
    try:
        llm_client = create_llm_client(
            provider=provider, api_key=config['api_key'], model=config['model']
        )
    except Exception as e:
        return jsonify({"error": f"LLM 初始化失败: {e}"}), 400

    max_turns = config['max_turns']
    map_size = config['map_size']
    shotgun = config['shotgun']

    try:
        result = run_prompt_duel(
            player1, player2,
            max_turns=max_turns,
            map_size=map_size,
            llm_client=llm_client,
            shotgun_duel=shotgun,
            save_replay_to=None,
        )
    except Exception as e:
        logger.error("Duel failed: %s", e, exc_info=True)
        return jsonify({"error": f"对决失败: {e}"}), 500

    # 取出本局所有打赏
    gifts = []
    with _duel_gifts_lock:
        gifts = list(_duel_gifts.pop(duel_id, []))

    # 生成 replay HTML
    replay_path = Path(project_root) / "online" / "replays" / f"duel_{duel_id}.html"
    try:
        _generate_duel_replay_html(
            player1, player2,
            llm_client=llm_client,
            max_turns=max_turns,
            map_size=map_size,
            shotgun_duel=shotgun,
            output_path=replay_path,
            gifts=gifts,
        )
    except Exception as e:
        logger.error("Replay 生成失败: %s", e, exc_info=True)
        replay_path = None

    return jsonify({
        "winner": result.winner_name,
        "player1": {"name": result.player1_name, "health": result.player1_health, "kills": result.player1_kills},
        "player2": {"name": result.player2_name, "health": result.player2_health, "kills": result.player2_kills},
        "turns": result.turns,
        "replay_url": f"/api/replay/duel_{duel_id}" if replay_path else None,
        "gifts_applied": gifts,
        "provider": provider,
    })


# 保留旧端点（向后兼容）— 立即跑对决，不走 prepare
@app.route('/api/duel', methods=['POST'])
def start_duel_legacy():
    """旧版：一步到位（不消费打赏）。仅用于向后兼容。"""
    from tournament.prompt_duel import run_prompt_duel
    from agents.prompt_agent import create_llm_client

    data = request.json or {}

    p1_data = data.get("player1") or {}
    p2_data = data.get("player2") or {}
    if not p1_data.get("prompt") or not p2_data.get("prompt"):
        return jsonify({"error": "player1.prompt 和 player2.prompt 都不能为空"}), 400

    player1 = _duel_player_from_dict(p1_data)
    player2 = _duel_player_from_dict(p2_data)

    provider = data.get("provider", "openai")
    api_key = data.get("api_key") or None
    model = data.get("model") or None
    try:
        llm_client = create_llm_client(provider=provider, api_key=api_key, model=model)
    except Exception as e:
        return jsonify({"error": f"LLM 初始化失败: {e}"}), 400

    max_turns = int(data.get("max_turns", 100))
    map_size = int(data.get("map_size", 25))
    shotgun = bool(data.get("shotgun_duel", True))

    try:
        result = run_prompt_duel(
            player1, player2,
            max_turns=max_turns,
            map_size=map_size,
            llm_client=llm_client,
            shotgun_duel=shotgun,
            save_replay_to=None,
        )
    except Exception as e:
        return jsonify({"error": f"对决失败: {e}"}), 500

    import uuid
    replay_id = uuid.uuid4().hex[:12]
    replay_path = Path(project_root) / "online" / "replays" / f"duel_{replay_id}.html"
    try:
        _generate_duel_replay_html(
            player1, player2,
            llm_client=llm_client,
            max_turns=max_turns,
            map_size=map_size,
            shotgun_duel=shotgun,
            output_path=replay_path,
        )
    except Exception:
        replay_path = None

    return jsonify({
        "winner": result.winner_name,
        "player1": {"name": result.player1_name, "health": result.player1_health, "kills": result.player1_kills},
        "player2": {"name": result.player2_name, "health": result.player2_health, "kills": result.player2_kills},
        "turns": result.turns,
        "replay_url": f"/api/replay/duel_{replay_id}" if replay_path else None,
        "provider": provider,
    })


def _duel_player_from_dict(d: dict):
    """从 dict 构造 DuelPlayer"""
    from tournament.prompt_duel import DuelPlayer
    return DuelPlayer(
        name=d.get("name") or d.get("prompt", "")[:10],
        prompt=d.get("prompt", ""),
        persona=d.get("persona", "balanced"),
        description=d.get("description", ""),
    )


def _generate_duel_replay_html(p1, p2, llm_client, max_turns, map_size,
                                shotgun_duel, output_path, gifts=None):
    """重跑一遍并生成 HTML 回放

    gifts: 可选 list of {type, target, user} — 观众打赏（每局最多 3 个）
    """
    from agents.prompt_agent import PromptAgent
    from game.engine import GameEngine

    a1 = PromptAgent(p1.name, llm_client=llm_client, persona=p1.persona)
    a1.set_strategy(p1.prompt)
    a2 = PromptAgent(p2.name, llm_client=llm_client, persona=p2.persona)
    a2.set_strategy(p2.prompt)

    if shotgun_duel:
        for a in (a1, a2):
            a.weapon = "shotgun"
            a.ammo = {"shotgun": 30, "sniper": 0, "rocket": 0}

    engine = GameEngine([a1, a2], map_size, map_size)

    # 应用观众打赏：分阶段触发（25%, 50%, 75% 进度）
    gift_events = []
    if gifts:
        for i, g in enumerate(gifts[:3]):
            apply_at = int((i + 1) * max(50, max_turns) / 4)
            gift_events.append((apply_at, g))

    from visualizer.web_visualizer import WebVisualizer
    viz = WebVisualizer(map_width=map_size, map_height=map_size,
                        canvas_width=600, canvas_height=450)

    gift_log = []

    for turn in range(max_turns):
        # 检查并 apply 打赏
        for apply_at, g in gift_events:
            if turn == apply_at and g not in gift_log:
                gift_log.append(g)
                target = a1 if g['target'] == 'player1' else a2
                _apply_gift_to_agent(target, g)

        engine.step()
        if turn % 2 == 0:
            viz.record_frame({
                'turn': turn,
                'agents': [
                    {'name': a1.name, 'health': a1.health, 'position': list(a1.position),
                     'direction': list(a1.direction), 'kills': a1.kills, 'team_id': None,
                     'weapon': a1.weapon, 'ammo': a1.ammo,
                     'shield_turns': getattr(a1, 'shield_turns', 0)},
                    {'name': a2.name, 'health': a2.health, 'position': list(a2.position),
                     'direction': list(a2.direction), 'kills': a2.kills, 'team_id': None,
                     'weapon': a2.weapon, 'ammo': a2.ammo,
                     'shield_turns': getattr(a2, 'shield_turns', 0)}
                ],
                'bullets': [], 'obstacles': [], 'supplies': [],
                'gifts_applied': list(gift_log)
            })
        if engine.state.get_winner(allow_score_judge=False):
            for _ in range(5):
                engine.step()
                viz.record_frame({
                    'turn': turn,
                    'agents': [
                        {'name': a1.name, 'health': a1.health, 'position': list(a1.position),
                         'direction': list(a1.direction), 'kills': a1.kills, 'team_id': None,
                         'weapon': a1.weapon, 'ammo': a1.ammo,
                         'shield_turns': getattr(a1, 'shield_turns', 0)},
                        {'name': a2.name, 'health': a2.health, 'position': list(a2.position),
                         'direction': list(a2.direction), 'kills': a2.kills, 'team_id': None,
                         'weapon': a2.weapon, 'ammo': a2.ammo,
                         'shield_turns': getattr(a2, 'shield_turns', 0)}
                    ],
                    'bullets': [], 'obstacles': [], 'supplies': [],
                    'gifts_applied': list(gift_log)
                })
            break

    winner = engine.state.get_winner(allow_score_judge=True)
    if winner:
        viz.set_winner(winner.name)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    viz.generate_html(str(output_path), auto_play=True, fps=12)
    return output_path


def _apply_gift_to_agent(agent, gift):
    """应用单个打赏到 agent"""
    gift_type = gift['type']
    if gift_type == 'health':
        agent.health = min(100, agent.health + 30)
    elif gift_type == 'ammo':
        for w in ('shotgun', 'sniper', 'rocket'):
            if w in agent.ammo:
                cap = 50 if w == 'shotgun' else (20 if w == 'sniper' else 10)
                agent.ammo[w] = min(cap, agent.ammo.get(w, 0) + 15)
    elif gift_type == 'slow':
        # 强制冷却 +5
        agent.shoot_cooldown = max(agent.shoot_cooldown, 5)
    elif gift_type == 'shield':
        # 标记 shield_turns（受击时减半）
        agent.shield_turns = 10
    elif gift_type == 'boost':
        # 立即开火
        agent.shoot_cooldown = 0





if __name__ == '__main__':
    # 初始化：从participants目录加载所有玩家到数据库
    loader = AgentLoader(participants_dir="participants")
    agents = loader.create_agent_instances()
    for agent in agents:
        # 假设agent路径就是participants目录下的子目录
        agent_path = f"participants/{agent.name}"
        db.add_player(agent.name, agent_path)

    print("="*60)
    print("AI竞技平台 - 在线对战服务器")
    print("="*60)
    print(f"已加载 {len(agents)} 名玩家")
    print(f"访问 http://localhost:5000 开始对战")
    print("="*60)

    # 端口和 debug 通过环境变量控制（默认 debug=False，避免生产裸奔）
    port = int(os.getenv("PORT", "5000"))
    host = os.getenv("HOST", "127.0.0.1")  # 默认绑本机，避免生产暴露
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)

