"""
AI 教练 — 分析 agent 表现，给出改进建议

输入：一场比赛的 state 序列 + decision log
输出：诊断报告

可工作模式：
1. 启发式模式（默认，无需 API）：基于决策分布、关键时刻模式
2. LLM 模式：把决策日志喂给 LLM，让它输出人类可读建议

启发式输出示例：
  - "你在 87% 的回合选择 idle，但视野里有敌人时你应该射击"
  - "你平均每个有敌人可见的回合做了 3 次无效转向"
  - "你的血量从 100 降到 30 的过程中，57% 的回合在移动而不是射击或躲避"
"""
from collections import Counter, defaultdict
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class CoachReport:
    """教练报告"""
    agent_name: str
    total_decisions: int
    action_distribution: Dict[str, int]
    enemy_visible_turns: int
    enemy_visible_shoot_rate: float  # 视野有敌时射击比例
    low_health_turns: int
    low_health_action_distribution: Dict[str, int]
    idle_turns_with_enemy: int  # 视野有敌却 idle（明显的失误）
    critical_turns: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


def analyze_decision_log(agent_name: str, decision_log: List[Dict]) -> CoachReport:
    """分析单个 agent 的决策日志（不需要 LLM，纯启发式）"""
    if not decision_log:
        return CoachReport(
            agent_name=agent_name, total_decisions=0,
            action_distribution={}, enemy_visible_turns=0,
            enemy_visible_shoot_rate=0.0, low_health_turns=0,
            low_health_action_distribution={}, idle_turns_with_enemy=0,
            recommendations=["决策日志为空，无法分析"],
        )

    actions = [d["action"] for d in decision_log]
    dist = Counter(actions)

    # 视野有敌的回合
    enemy_visible = [d for d in decision_log if d["enemies_visible"] > 0]
    if enemy_visible:
        shoot_in_enemy = sum(1 for d in enemy_visible if d["action"] == "shoot")
        idle_in_enemy = sum(1 for d in enemy_visible if d["action"] == "idle")
        shoot_rate = shoot_in_enemy / len(enemy_visible)
    else:
        shoot_rate = 0.0
        idle_in_enemy = 0

    # 低血回合（< 30）
    low_health = [d for d in decision_log if d["health"] < 30]
    low_health_dist = Counter(d["action"] for d in low_health)

    # 关键时刻：血量 < 30 且视野有敌
    critical = [
        {"turn": d.get("turn"), "health": d["health"],
         "enemies": d["enemies_visible"], "action": d["action"]}
        for d in decision_log if d["health"] < 30 and d["enemies_visible"] > 0
    ]

    # 生成建议
    recs = _generate_recommendations(
        total=len(decision_log),
        dist=dist,
        shoot_rate=shoot_rate,
        idle_in_enemy=idle_in_enemy,
        low_health_dist=low_health_dist,
    )

    return CoachReport(
        agent_name=agent_name,
        total_decisions=len(decision_log),
        action_distribution=dict(dist),
        enemy_visible_turns=len(enemy_visible),
        enemy_visible_shoot_rate=shoot_rate,
        low_health_turns=len(low_health),
        low_health_action_distribution=dict(low_health_dist),
        idle_turns_with_enemy=idle_in_enemy,
        critical_turns=critical[:5],  # 只保留前 5 个关键时刻
        recommendations=recs,
    )


def _generate_recommendations(total, dist, shoot_rate, idle_in_enemy, low_health_dist) -> List[str]:
    """根据统计数据生成建议"""
    recs = []

    # 1. 决策分布
    idle_pct = dist.get("idle", 0) / total * 100 if total else 0
    if idle_pct > 50:
        recs.append(f"⚠️  你 {idle_pct:.0f}% 的回合都在 idle — 移动太少，应该主动接近或寻找掩护")
    elif idle_pct < 10:
        recs.append(f"✓  你很少 idle，行动积极（仅 {idle_pct:.0f}%）")

    # 2. 视野有敌时的射击率
    if shoot_rate < 0.2:
        recs.append(f"⚠️  视野里有敌人时，你射击率仅 {shoot_rate*100:.0f}% — 应该积极开火")
    elif shoot_rate > 0.8:
        recs.append(f"✓  视野有敌时射击率 {shoot_rate*100:.0f}% — 积极开火")

    # 3. 视野有敌却 idle
    if idle_in_enemy > 0:
        recs.append(f"⚠️  视野里有敌人却选择了 {idle_in_enemy} 次 idle — 这是明显的失误")

    # 4. 低血行为
    if low_health_dist:
        low_idle = low_health_dist.get("idle", 0)
        low_move = sum(v for k, v in low_health_dist.items() if k.startswith("move_"))
        low_total = sum(low_health_dist.values())
        if low_idle > 0:
            recs.append(f"⚠️  低血量时 ({low_total} 回合) 仍有 {low_idle} 次 idle — 应该逃跑")
        if low_move > 0:
            recs.append(f"✓  低血量时 ({low_total} 回合) 有 {low_move} 次移动 — 知道逃跑")
        else:
            recs.append(f"⚠️  低血量时 ({low_total} 回合) 没有移动 — 应该远离敌人")

    # 5. 转向次数
    turn_count = dist.get("turn_left", 0) + dist.get("turn_right", 0)
    if turn_count > total * 0.7:
        recs.append(f"⚠️  你 {turn_count}/{total} 回合在转向 — 方向感差，建议利用移动 + 转向组合")

    if not recs:
        recs.append("✓  你的决策看起来合理，没有明显失误")

    return recs


def format_coach_report(report: CoachReport) -> str:
    """格式化为可读报告"""
    lines = [
        "=" * 60,
        f"  AI 教练报告 — {report.agent_name}",
        "=" * 60,
        "",
        f"  总决策数: {report.total_decisions}",
        f"  视野有敌回合: {report.enemy_visible_turns}",
        f"  视野有敌射击率: {report.enemy_visible_shoot_rate*100:.1f}%",
        f"  视野有敌却 idle: {report.idle_turns_with_enemy} 次",
        f"  低血回合: {report.low_health_turns}",
        "",
        "  动作分布:",
    ]

    if report.action_distribution:
        max_count = max(report.action_distribution.values())
        for action in ["move_up", "move_down", "move_left", "move_right",
                       "turn_left", "turn_right", "shoot", "idle"]:
            cnt = report.action_distribution.get(action, 0)
            if cnt == 0:
                continue
            pct = cnt / report.total_decisions * 100
            bar = "█" * int(cnt / max_count * 20) if max_count else ""
            lines.append(f"    {action:<12} {cnt:>5} ({pct:>5.1f}%) {bar}")

    lines.append("")
    lines.append("  改进建议:")
    for rec in report.recommendations:
        lines.append(f"    {rec}")

    if report.critical_turns:
        lines.append("")
        lines.append("  关键时刻（血量<30 且视野有敌）:")
        for c in report.critical_turns:
            lines.append(f"    回合 {c.get('turn', '?')}: 血{c['health']}, 敌{c['enemies']}, 动作={c['action']}")

    return "\n".join(lines)
