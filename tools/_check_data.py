import json
with open('outputs/team_3v3_v3_data.json', encoding='utf-8') as f:
    d = json.load(f)
for fr in d['frames']:
    if fr['events']:
        print('frame t=', fr['t'], 'events:', json.dumps(fr['events'], ensure_ascii=False))
        break
else:
    print('NO frames have events!')
print('total events in JSON:', sum(len(f['events']) for f in d['frames']))
print('total active_attacks:', sum(len(f['active_attacks']) for f in d['frames']))
print('total active_skills:', sum(len(f['active_skills']) for f in d['frames']))