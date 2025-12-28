"""
在线对战服务器
使用Flask提供Web API和界面
"""
import os
import sys
import json
import threading
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS

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
    
    app.run(host='0.0.0.0', port=5000, debug=True)

