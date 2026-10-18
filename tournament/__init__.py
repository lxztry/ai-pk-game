"""
比赛系统
"""

from .tournament import Tournament, RoundRobinTournament, EliminationTournament
from .group_tournament import GroupTournament
from .prompt_duel import run_prompt_duel, format_duel_report, DuelPlayer, DuelResult

__all__ = [
    'Tournament', 'RoundRobinTournament', 'EliminationTournament', 'GroupTournament',
    'run_prompt_duel', 'format_duel_report', 'DuelPlayer', 'DuelResult',
]

