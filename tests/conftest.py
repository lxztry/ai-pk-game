"""
全局 pytest fixtures

约定：
- tmp_path 是 pytest 内置的，每次测试自动清理
- 所有测试不依赖真实 participants 目录
- 每个测试都重置 random.seed（防止 _initialize_positions 等污染）
"""
import random
import sys
from pathlib import Path

# 确保项目根目录在 sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest


@pytest.fixture(autouse=True)
def _reset_random():
    """每个测试前重置 random seed，避免 _initialize_positions 等随机化函数污染测试间状态"""
    random.seed(42)
    yield
    # 测试后不强制重置，让下一个 fixture 调用再重置


@pytest.fixture
def project_root():
    """项目根目录"""
    return PROJECT_ROOT


@pytest.fixture
def sample_obs():
    """构造一个标准的 Observation"""
    from game.agent import Observation
    return Observation({
        "my_health": 100,
        "my_position": [50, 50],
        "my_direction": [1, 0],
        "my_team": None,
        "my_weapon": "normal",
        "my_ammo": None,
        "enemies_in_view": [],
        "bullets_in_view": [],
        "obstacles_in_view": [],
        "supplies_in_view": [],
        "map_boundary": [100, 100],
        "shoot_cooldown": 0,
    })


@pytest.fixture
def sample_state_info():
    """构造一帧游戏状态（用于回放记录器测试）"""
    return {
        "turn": 0,
        "alive_count": 2,
        "winner": None,
        "winning_team": None,
        "agents": [
            {
                "name": "A",
                "health": 100,
                "position": [25, 50],
                "direction": [1, 0],
                "kills": 0,
                "team_id": None,
                "weapon": "normal",
                "ammo": {"shotgun": 0, "sniper": 0, "rocket": 0},
            },
            {
                "name": "B",
                "health": 100,
                "position": [75, 50],
                "direction": [-1, 0],
                "kills": 0,
                "team_id": None,
                "weapon": "normal",
                "ammo": {"shotgun": 0, "sniper": 0, "rocket": 0},
            },
        ],
        "bullets": [],
        "obstacles": [],
        "supplies": [],
    }
