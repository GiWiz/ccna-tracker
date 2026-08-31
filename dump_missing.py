import json

raw_json = 'data/raw/jeremy_playlist.json'
with open(raw_json, 'r', encoding='utf-8') as f:
    data = json.load(f)

videos = [v for v in data['videos'] if v['duration'] != 'N/A']

kw_index = 'data/transcripts/keyword_index.json'
try:
    with open(kw_index, 'r', encoding='utf-8') as f:
        kd = json.load(f)
    existing_ids = list(kd.keys())
except:
    existing_ids = []

missing = [v for v in videos if v['video_id'] not in existing_ids]

print('missing_data = [')
for m in missing:
    safe_title = m['title'].replace("'", "")
    print(f"    {{'id': '{m['video_id']}', 'title': '{safe_title}'}},")
print(']')
