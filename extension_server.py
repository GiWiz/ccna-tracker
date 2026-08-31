import json
import os
import webbrowser
from flask import Flask, request, jsonify

app = Flask(__name__)

# Add CORS headers so the extension can talk to us
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'POST'
    return response

missing_videos = []
current_index = 0

import re

def format_filename(title):
    match = re.search(r'Day (\d+)', title, re.IGNORECASE)
    day_str = ''
    if match:
        day_str = f'Day_{int(match.group(1)):02d}_'
    clean = re.sub(r'[^a-zA-Z0-9\-]', '_', title)
    clean = re.sub(r'_+', '_', clean).strip('_')
    return f'{day_str}{clean}.txt'

@app.route('/submit', methods=['POST', 'OPTIONS'])
def submit():
    global current_index
    if request.method == 'OPTIONS':
        return jsonify({})
        
    data = request.json
    vid = data.get('video_id')
    
    if 'error' in data:
        print(f"[\u274c] Extension reported error for {vid}: {data['error']}")
    else:
        text = data.get('text', '')
        
        # Find the title for this video_id
        title = "Unknown_Video"
        for v in missing_videos:
            if v['video_id'] == vid:
                title = v['title']
                break
                
        filename = format_filename(title)
        
        with open(f"data/transcripts/{filename}", 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"[\u2714] Successfully saved {filename} (Length: {len(text)})")
        
    current_index += 1
    
    if current_index < len(missing_videos):
        next_vid = missing_videos[current_index]['video_id']
        return jsonify({"next_url": f"https://www.youtube.com/watch?v={next_vid}"})
    else:
        return jsonify({"next_url": None})

def main():
    global missing_videos
    os.makedirs('data/transcripts', exist_ok=True)
    
    try:
        with open('jeremy_playlist.json', 'r') as f:
            missing_videos = json.load(f)['videos']
    except Exception as e:
        print("Could not load jeremy_playlist.json", e)
        return
        
    if not missing_videos:
        print("No videos loaded!")
        return
        
    print(f"Loaded {len(missing_videos)} videos to scrape.")
    print("Starting local server on port 5000...")
    
    # Open the first video to kick off the chain!
    first_url = f"https://www.youtube.com/watch?v={missing_videos[0]['video_id']}"
    print(f"Opening first video in your default browser: {first_url}")
    webbrowser.open(first_url)
    
    # Disable flask output to keep console clean
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    app.run(port=5000)

if __name__ == '__main__':
    main()
