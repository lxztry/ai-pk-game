"""验证生成的 replay HTML 文件内容"""
import sys
from pathlib import Path

path = Path("online/replays/aggressive_player_vs_survival_player_20260927_131624.html")
html = path.read_text(encoding="utf-8")

print(f"文件: {path}")
print(f"大小: {len(html)} chars ({path.stat().st_size} bytes)")
print(f"含 <canvas>:    {'<canvas' in html}")
print(f"含 gameData:    {'gameData' in html}")
print(f"含 togglePlay:  {'togglePlay' in html}")
print(f"含 winner:      {'winner' in html}")
print(f"含 turn 数字:   {'turn' in html}")

# 提取 JSON 数据长度
import re
m = re.search(r"const gameData = (\[.*?\]);", html, re.DOTALL)
if m:
    js_len = len(m.group(1))
    print(f"gameData JSON:  {js_len:,} chars (~{js_len//1000}KB)")
    print(f"占比:           {js_len*100//len(html)}%")
