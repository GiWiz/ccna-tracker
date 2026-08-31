console.log("YouTube Auto-Scraper Extension Loaded!");

let currentVideoId = null;
let isProcessing = false;

function getVideoId() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('v');
}

async function scrapeLoop() {
    const vid = getVideoId();
    if (!vid) return; // Not on a video page
    
    // Only process a video once
    if (vid === currentVideoId || isProcessing) return;
    
    console.log("Starting scrape for video:", vid);
    isProcessing = true;
    currentVideoId = vid;
    
    try {
        // Step 1: Wait for description to load and expand it
        await waitForElement('div#description-inner', 10000);
        let expandBtn = document.querySelector('tp-yt-paper-button#expand');
        if (expandBtn && expandBtn.offsetParent !== null) {
            expandBtn.click();
            console.log("Clicked ...more");
        }
        
        await sleep(1000);
        
        // Step 2: Find and click the "Show transcript" button
        let clicked = false;
        let btns = document.querySelectorAll('button');
        for (let btn of btns) {
            if (btn.innerText.toLowerCase().includes('transcript') || 
                (btn.getAttribute('aria-label') && btn.getAttribute('aria-label').toLowerCase().includes('transcript'))) {
                btn.click();
                clicked = true;
                console.log("Clicked Transcript button");
                break;
            }
        }
        
        if (!clicked) {
            throw new Error("Could not find Transcript button");
        }
        
        // Step 3: Wait for transcript segments to render
        await waitForElement('.segment-text', 10000);
        let segments = document.querySelectorAll('.segment-text');
        
        if (segments.length === 0) {
            throw new Error("Segments container found but no text inside");
        }
        
        let transcriptText = Array.from(segments).map(el => el.innerText.replace(/\n/g, ' ').trim()).join(' ');
        console.log("Successfully extracted transcript! Length:", transcriptText.length);
        
        // Step 4: Send to our local Python server
        const response = await fetch('http://localhost:5000/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                video_id: vid,
                text: transcriptText
            })
        });
        
        const result = await response.json();
        
        // Step 5: Navigate to next video
        if (result.next_url) {
            console.log("Navigating to next video:", result.next_url);
            window.location.href = result.next_url;
        } else {
            alert("All done! Successfully scraped all missing transcripts.");
        }
        
    } catch (e) {
        console.error("Scraper Error:", e);
        // If it fails, let's just send the failure to the server so it can skip/log it, and move on to the next
        try {
            const response = await fetch('http://localhost:5000/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ video_id: vid, error: e.message })
            });
            const result = await response.json();
            if (result.next_url) {
                window.location.href = result.next_url;
            }
        } catch (e2) {
            console.error("Fatal: Could not reach python server.");
        }
    }
    
    isProcessing = false;
}

// Utility functions
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function waitForElement(selector, timeout) {
    return new Promise((resolve, reject) => {
        if (document.querySelector(selector)) {
            return resolve(document.querySelector(selector));
        }

        const observer = new MutationObserver(mutations => {
            if (document.querySelector(selector)) {
                observer.disconnect();
                resolve(document.querySelector(selector));
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        setTimeout(() => {
            observer.disconnect();
            reject(new Error(`Timeout waiting for ${selector}`));
        }, timeout);
    });
}

// Run the loop every 2 seconds to catch page navigations
setInterval(scrapeLoop, 2000);
