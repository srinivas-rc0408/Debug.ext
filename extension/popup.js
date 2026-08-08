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
        let timeLeft = 15; 

        // Instantly inject the spinner and update text
        btn.innerHTML = `<span class="spinner"></span> Intercepting... (${timeLeft}s)`;
        btn.classList.add('btn-listening');
        btn.disabled = true;

        let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        chrome.runtime.sendMessage({ action: 'START_DEBUGGING', tabId: tab.id });

        const countdown = setInterval(() => {
            timeLeft--;
            btn.innerHTML = `<span class="spinner"></span> Intercepting... (${timeLeft}s)`;
            if (statusText) statusText.textContent = "Analyzing DOM and Network requests in real-time.";

            if (timeLeft <= 0) {
                clearInterval(countdown);
                btn.innerHTML = "Start Debugging (15 Sec)";
                btn.classList.remove('btn-listening');
                if (statusText) statusText.textContent = "Session complete. Routing to Dashboard...";
                btn.disabled = false;
            }
        }, 1000);
    });

    document.getElementById('dashboard-btn').addEventListener('click', () => {
        chrome.tabs.create({ url: 'http://localhost:8501' });
    });
});
