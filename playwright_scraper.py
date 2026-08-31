import sys
import os
import json
from playwright.sync_api import sync_playwright
import time

def scrape_transcripts():
    os.makedirs('downloaded_transcripts', exist_ok=True)
    
    with open('jeremy_playlist.json', 'r') as f:
        videos = json.load(f)['videos']
    
    existing = set(f.replace('.txt', '') for f in os.listdir('data/transcripts') if f.endswith('.txt'))
    missing = [v for v in videos if v['video_id'] not in existing]
    
    print(f"Attempting to download {len(missing)} missing transcripts via Playwright...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()
        
        success = 0
        for idx, video in enumerate(missing):
            vid = video['video_id']
            print(f"[{idx+1}/{len(missing)}] {video['title'][:40]}...", end=" ", flush=True)
            
            try:
                page.goto(f"https://www.youtube.com/watch?v={vid}")
                page.wait_for_selector('div#description-inner', timeout=15000)
                
                try:
                    page.locator('button:has-text("Reject all")').click(timeout=2000)
                except:
                    pass
                
                # Expand description
                try:
                    more_btn = page.locator('tp-yt-paper-button#expand').first
                    if more_btn.is_visible():
                        more_btn.click(timeout=2000)
                except:
                    pass
                    
                time.sleep(1)
                
                # Click Transcript button
                clicked = False
                btns = page.locator('button:has-text("transcript"), button:has-text("Transcript")').all()
                for btn in btns:
                    try:
                        btn.click(timeout=1000)
                        clicked = True
                        break # Only need to click one successfully
                    except:
                        pass
                
                if not clicked:
                    print("FAILED: Button not clickable")
                    continue
                    
                # Wait for transcript to load
                page.wait_for_selector('ytd-transcript-segment-renderer, .segment-text', timeout=15000)
                
                # Extract text
                segments = page.locator('.segment-text').all_inner_texts()
                if not segments:
                    print("FAILED: No segments found")
                    continue
                    
                full_text = " ".join(s.replace('\n', ' ').strip() for s in segments)
                
                # Save
                with open(f"downloaded_transcripts/{vid}.txt", 'w', encoding='utf-8') as f:
                    f.write(full_text)
                    
                print("SUCCESS")
                success += 1
                
            except Exception as e:
                print(f"FAILED: {type(e).__name__}")
                
            time.sleep(2) # Give youtube a breather between page loads
            
        browser.close()
        print(f"\nDone! Successfully scraped {success} transcripts via Playwright.")

if __name__ == "__main__":
    scrape_transcripts()
