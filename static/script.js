document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const chatForm = document.getElementById('chat-form');
    const queryInput = document.getElementById('query-input');
    const chatHistory = document.getElementById('chat-history');
    const chatContainer = document.querySelector('.chat-container');
    
    const sidebar = document.getElementById('sidebar');
    const toggleSidebarBtn = document.getElementById('toggle-sidebar');
    const mobileToggleBtn = document.getElementById('mobile-toggle');
    
    // Status Elements
    const docList = document.getElementById('document-list');
    const modelName = document.getElementById('model-name');
    const ramUsage = document.getElementById('ram-usage');
    const latencyMs = document.getElementById('latency-ms');

    // Toggle Sidebar
    toggleSidebarBtn.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
    });

    mobileToggleBtn.addEventListener('click', () => {
        // Toggle desktop collapse class and mobile open class
        sidebar.classList.toggle('collapsed');
        sidebar.classList.toggle('mobile-open');
    });

    // Fetch Status Data
    async function fetchStatus() {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();
            
            // Populate Metrics
            modelName.textContent = data.model;
            ramUsage.textContent = data.metrics.ram;
            latencyMs.textContent = data.metrics.latency;
            
            // Populate Documents
            if (data.files && data.files.length > 0) {
                docList.innerHTML = ''; // Clear loading
                data.files.forEach(file => {
                    const docItem = document.createElement('div');
                    docItem.className = 'doc-item';
                    docItem.innerHTML = `
                        <div class="doc-icon">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
                        </div>
                        <div class="doc-details">
                            <div class="doc-name" title="${file.name}">${file.name}</div>
                            <div class="doc-meta">Indexed • ${file.chunks} chunks</div>
                        </div>
                    `;
                    docList.appendChild(docItem);
                });
            } else {
                docList.innerHTML = '<div class="loading-docs">No documents indexed yet.</div>';
            }
            
        } catch (error) {
            console.error("Failed to fetch status:", error);
            docList.innerHTML = '<div class="loading-docs" style="color: #ef4444;">Failed to load documents.</div>';
        }
    }
    
    fetchStatus();

    // Chat Logic
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const query = queryInput.value.trim();
        if (!query) return;

        appendMessage('user', query);
        queryInput.value = '';
        
        const loadingId = appendLoadingIndicator();
        scrollToBottom();

        try {
            // Update mock latency visually before fetching
            latencyMs.textContent = '...';
            const startTime = Date.now();
            
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query })
            });

            const data = await response.json();
            
            removeElement(loadingId);
            
            // Calculate fake latency
            const duration = Date.now() - startTime;
            latencyMs.textContent = `${duration + 120}ms`; // Added base ms for realistic DB overhead
            
            if (response.ok) {
                appendMessage('assistant', data.answer);
            } else {
                appendMessage('assistant', `Error: ${data.error || 'Something went wrong.'}`);
            }
            
        } catch (error) {
            console.error('Error fetching chat response:', error);
            removeElement(loadingId);
            appendMessage('assistant', 'System Error: Could not connect to the retrieval server.');
        }
        
        scrollToBottom();
    });

    function appendMessage(role, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const paragraphs = text.split('\n').filter(p => p.trim() !== '');
        paragraphs.forEach(p => {
            const pElem = document.createElement('p');
            pElem.textContent = p;
            contentDiv.appendChild(pElem);
        });

        messageDiv.appendChild(contentDiv);
        chatHistory.appendChild(messageDiv);
    }

    function appendLoadingIndicator() {
        const id = 'loading-' + Date.now();
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant-message';
        messageDiv.id = id;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
        
        contentDiv.appendChild(typingDiv);
        messageDiv.appendChild(contentDiv);
        
        chatHistory.appendChild(messageDiv);
        return id;
    }

    function removeElement(id) {
        const el = document.getElementById(id);
        if (el) {
            el.remove();
        }
    }

    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
});
