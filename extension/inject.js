(function() {
    if (window.__debugExtInjected) return;
    window.__debugExtInjected = true;

    // --- ISOLATED WORLD (Message Forwarder) ---
    if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.sendMessage) {
        const messageHandler = (event) => {
            if (event.source !== window || !event.data || event.data.source !== 'debug-ext-interceptor') return;
            
            const payload = {
                ...event.data,
                domContext: {
                    viewport: `${window.innerWidth}x${window.innerHeight}`,
                    title: document.title
                }
            };
            chrome.runtime.sendMessage({ action: 'PROCESS_ERROR', payload: payload });
        };
        window.addEventListener('message', messageHandler);

        chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
            if (msg.action === 'SLEEP') {
                window.postMessage({ source: 'debug-ext-sleep' }, '*');
                window.removeEventListener('message', messageHandler);
                window.__debugExtInjected = false;
            }
        });
        return; // Stop execution in isolated world
    }

    // --- MAIN WORLD (Interceptor) ---

    // Short-term memory for deduplication
    const recentErrors = new Set();
    const DEDUPE_TIME_MS = 5000;

    function dispatchError(type, payload) {
        const errorSignature = type + '_' + JSON.stringify(payload).substring(0, 150);
        if (recentErrors.has(errorSignature)) return;
        
        recentErrors.add(errorSignature);
        setTimeout(() => { recentErrors.delete(errorSignature); }, DEDUPE_TIME_MS);

        window.postMessage({
            source: 'debug-ext-interceptor',
            type: type,
            payload: payload,
            timestamp: new Date().toISOString(),
            url: window.location.href
        }, '*');
    }

    // Handlers
    const onError = function(event) {
        dispatchError('UNCAUGHT_EXCEPTION', {
            message: event.message,
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno,
            stack: event.error ? event.error.stack : null
        });
    };

    const onUnhandledRejection = function(event) {
        dispatchError('UNHANDLED_REJECTION', {
            reason: event.reason ? (event.reason.stack || event.reason.toString()) : 'Unhandled Promise Rejection'
        });
    };

    // Intercept Fetch
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        try {
            const response = await originalFetch.apply(this, args);
            if (!response.ok) {
                const clone = response.clone();
                let bodyText = '';
                try { bodyText = await clone.text(); } catch(e) {}
                dispatchError('NETWORK_FETCH_ERROR', {
                    requestUrl: typeof args[0] === 'string' ? args[0] : args[0].url,
                    status: response.status,
                    statusText: response.statusText,
                    responseBody: bodyText.substring(0, 500)
                });
            }
            return response;
        } catch (err) {
            dispatchError('NETWORK_FETCH_FAILURE', {
                requestUrl: typeof args[0] === 'string' ? args[0] : args[0].url,
                error: err.toString()
            });
            throw err;
        }
    };

    // Intercept Console Error
    const originalConsoleError = console.error;
    console.error = function(...args) {
        const errorString = args.map(arg => typeof arg === 'object' ? JSON.stringify(arg) : String(arg)).join(' ');
        if (!errorString.includes('Backend connection error')) {
            dispatchError('CONSOLE_ERROR', { details: errorString });
        }
        originalConsoleError.apply(this, args);
    };

    // Sleep Handler
    const onSleepMessage = function(event) {
        if (event.source === window && event.data && event.data.source === 'debug-ext-sleep') {
            // Restore originals
            window.fetch = originalFetch;
            console.error = originalConsoleError;
            
            // Remove listeners
            window.removeEventListener('error', onError);
            window.removeEventListener('unhandledrejection', onUnhandledRejection);
            window.removeEventListener('message', onSleepMessage);
            
            window.__debugExtInjected = false;
        }
    };

    // Attach listeners in the capture phase (true) to intercept errors before frameworks swallow them
    window.addEventListener('error', onError, true);
    window.addEventListener('unhandledrejection', onUnhandledRejection, true);
    window.addEventListener('message', onSleepMessage);
})();
