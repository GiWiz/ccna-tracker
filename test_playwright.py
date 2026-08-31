import sys
from playwright.sync_api import sync_playwright

def get_transcript(vid):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()
        
        page.goto(f"https://www.youtube.com/watch?v={vid}")
        page.wait_for_selector('div#description-inner', timeout=10000)
        
        # Click ...more
        try:
            more_btn = page.locator('tp-yt-paper-button#expand').first
            if more_btn.is_visible():
                more_btn.click()
        except:
            pass
            
        page.wait_for_timeout(2000)
        
        # Dump description inner text to see if the button is there
        desc_html = page.locator('ytd-text-inline-expander').first.inner_html()
        with open('desc_dump.html', 'w', encoding='utf-8') as f:
            f.write(desc_html)
            
        # Let's also dump all buttons that have the word transcript
        btns = page.locator('button:has-text("transcript"), button:has-text("Transcript")').all()
        print(f"Found {len(btns)} buttons with 'transcript'")
        for btn in btns:
            try:
                print(btn.get_attribute('aria-label') or btn.inner_text())
                btn.click(timeout=1000)
            except:
                pass
                
        # Wait for segments
        try:
            page.wait_for_selector('ytd-transcript-segment-renderer', timeout=5000)
            segments = page.locator('ytd-transcript-segment-renderer .segment-text').all_inner_texts()
            text = " ".join(s.replace('\n', ' ').strip() for s in segments)
            print(f"Success! Got {len(segments)} segments. First 100 chars:")
            print(text[:100])
        except Exception as e:
            print("Failed to read segments")
            
        browser.close()

if __name__ == "__main__":
    get_transcript("1cuMzWBrEYs")
