let lastAlertTime = 0;
const COOLDOWN_MS = 40000; // 40 seconds
let isRouting = false; // State lock to prevent opening multiple tabs

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    // ==========================================
    // 1. START DEBUGGING & AUTO-SLEEP TIMER
    // ==========================================
    if (request.action === 'START_DEBUGGING') {
        isRouting = false; // Reset the lock for the new session
        
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0]) {
                const tabId = tabs[0].id;
                
                // Inject into MAIN world (to intercept fetch)
                chrome.scripting.executeScript({
                    target: { tabId: tabId },
                    world: 'MAIN',
                    files: ['inject.js']
                }, () => {
                    // Inject into ISOLATED world (to forward messages to background)
                    chrome.scripting.executeScript({
                        target: { tabId: tabId },
                        world: 'ISOLATED',
                        files: ['inject.js']
                    }, () => {
                        chrome.action.setBadgeText({ text: 'ON' });
                        chrome.action.setBadgeBackgroundColor({ color: '#10B981' });

                        // 🟢 THE 15-SECOND AUTONOMOUS TIMER
                        setTimeout(() => {
                            chrome.tabs.sendMessage(tabId, { action: 'SLEEP' }).catch(() => {});
                            chrome.action.setBadgeText({ text: 'SLEEP' });
                            chrome.action.setBadgeBackgroundColor({ color: '#64748B' });
                            
                            // PRO FIX: Force open the dashboard if an error didn't already trigger it
                            if (!isRouting) {
                                isRouting = true;
                                chrome.tabs.create({ url: "http://localhost:8501" });
                            }
                        }, 15000); // 15 seconds
                    });
                });
            }
        });
        return;
    }

    // ==========================================
    // 2. ERROR CAUGHT & AI PROCESSING
    // ==========================================
    if (request.action === 'PROCESS_ERROR') {
        const now = Date.now();
        
        // Check if we are in the 40-second cooldown period
        if (now - lastAlertTime < COOLDOWN_MS) {
            console.log(`[Debug.ext] Throttled: Error caught but system is in cooldown for ${Math.round((COOLDOWN_MS - (now - lastAlertTime))/1000)}s.`);
            return; 
        }

        // Update cooldown timer
        lastAlertTime = now;
        const errorData = request.payload;

        // Create a SINGLETON Notification (using a static ID prevents stacking)
        const notificationId = 'debug-ext-master-alert';
        
        // Clear it first to ensure the pop-up animation replays smoothly
        chrome.notifications.clear(notificationId, () => {
            chrome.notifications.create(notificationId, {
                type: 'basic',
                iconUrl: 'icons/icon128.png',
                title: 'Debug.ext — AI Triggered',
                message: `Captured ${errorData.type} on ${new URL(errorData.url).hostname}.\nAnalyzing root cause...`,
                priority: 2
            });
        });

        // Send to FastAPI Gateway
        fetch('http://localhost:8000/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                raw_report: JSON.stringify(errorData, null, 2),
                url: errorData.url,
                source: 'extension'
            })
        })
        .then(res => res.json())
        .then(data => {
            // Store analysis and update the extension badge
            chrome.storage.local.set({ latestAnalysis: data });
            // 1. SILENTLY UPDATE EXTENSION STATE
            chrome.action.setBadgeText({ text: '1' });
            chrome.action.setBadgeBackgroundColor({ color: '#EF4444' });
            chrome.notifications.update(notificationId, { 
                message: `Analysis Complete! Priority: ${data.priority}` 
            });
            
            // 2. STRICT BARRIER: ONLY OPEN DASHBOARD NOW
            if (!isRouting) {
                isRouting = true;
                chrome.tabs.create({ url: "http://localhost:8501" });
            }
        })
        .catch(err => console.error('Backend connection error:', err));
    }
});
