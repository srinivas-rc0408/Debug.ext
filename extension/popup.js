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

    document.getElementById('start-btn').addEventListener('click', () => {
        chrome.runtime.sendMessage({ action: 'ACTIVATE_INTERCEPTOR' });
        document.getElementById('status-badge').textContent = 'Active';
        document.getElementById('status-badge').style.background = '#10B981';
        document.getElementById('start-btn').textContent = 'Listening... (2 Min)';
        document.getElementById('start-btn').disabled = true;
    });

    document.getElementById('dashboard-btn').addEventListener('click', () => {
        chrome.tabs.create({ url: 'http://localhost:8501' });
    });
});
