import sys
sys.path.insert(0, ".")

print("Python version:", sys.version)
print("Testing imports...")

try:
    from utils.database import Database
    print("✓ Database OK")
except Exception as e:
    print(f"✗ Database Error: {e}")
    import traceback
    traceback.print_exc()

try:
    from utils.participant_manager import ParticipantManager
    print("✓ ParticipantManager OK")
except Exception as e:
    print(f"✗ ParticipantManager Error: {e}")
    import traceback
    traceback.print_exc()

try:
    from tournament.scheduler import MatchScheduler
    print("✓ MatchScheduler OK")
except Exception as e:
    print(f"✗ MatchScheduler Error: {e}")
    import traceback
    traceback.print_exc()

try:
    from tournament.ranking import RankingManager
    print("✓ RankingManager OK")
except Exception as e:
    print(f"✗ RankingManager Error: {e}")
    import traceback
    traceback.print_exc()

print("\nAll tests completed!")
