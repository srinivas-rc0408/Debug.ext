document.addEventListener('DOMContentLoaded', () => {
    chrome.action.setBadgeText({ text: '' });
    
    chrome.storage.local.get(['latestAnalysis'], (result) => {
        const container = document.getElementById('content');
        if (result.latestAnalysis) {
            const data = result.latestAnalysis;
            container.innerHTML = `
                <div class="card">
                    <div class="tags">
                        <span class="tag priority-${data.priority}">${data.priority}</span>
                        <span class="tag severity-${data.severity}">${data.severity}</span>
                    </div>
                    <h3>${data.bug_summary || 'Error Detected'}</h3>
                    <p><strong>Root Cause:</strong> ${data.probable_root_cause}</p>
                    <div class="code-box">
                        <pre><code>${data.suggested_fix?.code_snippet || 'No code fix generated'}</code></pre>
                    </div>
                </div>
            `;
        }
    });

    document.getElementById('start-btn').addEventListener('click', async () => {
        const btn = document.getElementById('start-btn');
        const statusText = document.getElementById('status-text');

        // 1. Instantly update the UI to look active and pro
        btn.textContent = "🟢 Intercepting... (10s)";
        btn.classList.add('btn-listening'); // Applies the green gradient from your CSS
        if (statusText) statusText.textContent = "Monitoring active tab for runtime errors.";
        btn.disabled = true;

        // 2. Send the activation message to background.js
        let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        chrome.runtime.sendMessage({ action: 'START_DEBUGGING', tabId: tab.id });

        // 3. Reset the UI automatically when the 10 seconds are up
        setTimeout(() => {
            btn.textContent = "Start Debugging (10 Sec)";
            btn.classList.remove('btn-listening');
            if (statusText) statusText.textContent = "Auto-sleep engaged. Ready to restart.";
            btn.disabled = false;
        }, 10000); // 10 seconds
    });

    document.getElementById('dashboard-btn').addEventListener('click', () => {
        chrome.tabs.create({ url: 'http://localhost:8501' });
    });
});
