import json
import csv

pending_labs = set()
try:
    with open(r"C:\Users\swrav\.gemini\antigravity-ide\brain\beffb45c-4358-4cc5-ac87-97c70f1f958b\scratch\pending_boson.json", 'r', encoding='utf-8') as f:
        pending_labs = set(json.load(f))
except Exception as e:
    print(e)

boson_metadata = {}
with open('data/cleaned/boson_labs_cleaned.csv', 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        title = row['Lab_Title'].strip()
        lab_id = row['Lab_ID'].strip()
        boson_metadata[lab_id] = title

with open('data/cleaned/topic_mapping.csv', 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        day = int(row['Day'])
        if day < 26 and row['Boson_Lab_IDs']:
            ids = [x.strip() for x in row['Boson_Lab_IDs'].split(';')]
            for i in ids:
                if i in boson_metadata:
                    title = boson_metadata[i]
                    if title in pending_labs:
                        print(f"MATCH! Day {day}: {title}")
                    else:
                        print(f"No match for Day {day}: {title} (Pending list check)")
