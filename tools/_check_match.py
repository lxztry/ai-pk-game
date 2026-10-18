import sys
sys.path.insert(0, '.')
from game.team_state import TeamGameState
from game.team_engine import TeamEngine
from agents.team_agents import TankAI, AssassinAI, MarksmanAI, SupportAI, MageAI
b = [TankAI('b0','tank','blue','mid'), AssassinAI('b1','assassin','blue','top'), MarksmanAI('b2','marksman','blue','bot')]
r = [TankAI('r0','tank','red','top'), SupportAI('r1','support','red','mid'), MageAI('r2','mage','red','bot')]
b[0].position = (5,12); b[1].position = (5,5); b[2].position = (5,19)
r[0].position = (35,5); r[1].position = (35,12); r[2].position = (35,19)
s = TeamGameState(b, r)
eng = TeamEngine(s)
for t in range(30):
    eng.step()
# 检查 27 turn
recent = [e for e in s.events if e.get('turn') == 27]
print('events at turn 27:', len(recent))
for e in recent:
    print(' ', e)
print('state.turn:', s.turn)
print('all event turns (sorted unique):', sorted(set(e.get('turn') for e in s.events))[:10])