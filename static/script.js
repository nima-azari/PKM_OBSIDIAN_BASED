// Load source count on page load
window.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        document.getElementById('source-count').textContent =
            `Chatting with ${data.num_documents} sources from data/sources/`;
    } catch (error) {
        console.error('Error loading stats:', error);
        document.getElementById('source-count').textContent = 'Error loading sources';
    }
});

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

function sendSuggestion(question) {
    document.getElementById('user-input').value = question;
    sendMessage();
}

// Global sources array
let currentSources = [];

async function sendMessage() {
    const input = document.getElementById('user-input');
    const question = input.value.trim();

    if (!question) return;

    // Clear input and disable send button
    input.value = '';
    const sendBtn = document.getElementById('send-btn');
    sendBtn.disabled = true;

    // Add user message to chat
    addMessage(question, 'user');

    // Add loading indicator
    const loadingId = addLoadingMessage();

    try {
        const response = await fetch('/api/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question })
        });

        const data = await response.json();

        // Remove loading indicator
        removeLoadingMessage(loadingId);

        if (data.error) {
            addMessage(`Error: ${data.error}`, 'assistant', true);
        } else {
            // Store sources globally
            if (data.sources && data.sources.length > 0) {
                currentSources = data.sources;
                updateSourcesSidebar(data.sources);
            }

            // Process answer text to make citations clickable
            let answerText = data.answer;
            answerText = makeInTextCitationsClickable(answerText);

            // Add timing info (Debug)
            if (data.elapsed_time) {
                answerText += `\n\n_(Generated in ${data.elapsed_time.toFixed(2)}s)_`;
            }

            // Add sources at the bottom (keeping existing functionality)
            if (data.sources && data.sources.length > 0) {
                answerText += '\n\n**Sources:**\n';
                data.sources.forEach((source, i) => {
                    answerText += `${i + 1}. <a href="#" onclick="window.openSource('${source.path}'); return false;">${source.title}</a>`;
                    if (source.score !== undefined && source.score !== null) {
                        answerText += ` (relevance: ${Number(source.score).toFixed(2)})`;
                    }
                    answerText += '\n';
                });
            }

            addMessage(answerText, 'assistant');
        }
    } catch (error) {
        removeLoadingMessage(loadingId);
        addMessage(`Error: ${error.message}`, 'assistant', true);
    } finally {
        sendBtn.disabled = false;
        input.focus();
    }
}

function makeInTextCitationsClickable(text) {
    // Match citations like [1], [2], [3] etc.
    return text.replace(/\[(\d+)\]/g, (match, num) => {
        const sourceIndex = parseInt(num) - 1;
        if (currentSources[sourceIndex]) {
            return `<a href="#" class="citation-link" onclick="window.openSource('${currentSources[sourceIndex].path}'); return false;" title="${currentSources[sourceIndex].title}">[${num}]</a>`;
        }
        return match; // Return original if source not found
    });
}

function updateSourcesSidebar(sources) {
    const sourcesList = document.getElementById('sources-list');
    sourcesList.innerHTML = '';

    sources.forEach((source, index) => {
        const sourceItem = document.createElement('div');
        sourceItem.className = 'source-item';
        sourceItem.onclick = () => window.openSource(source.path);

        sourceItem.innerHTML = `
            <span class="source-item-number">${index + 1}</span>
            <span class="source-item-title">${source.title}</span>
            <span class="source-item-path">${source.path}</span>
        `;

        sourcesList.appendChild(sourceItem);
    });
}

function addMessage(text, sender, isError = false) {
    const messagesContainer = document.getElementById('chat-messages');

    // Remove welcome message if it exists
    const welcomeMsg = messagesContainer.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message ${isError ? 'error-message' : ''}`;

    const label = document.createElement('div');
    label.className = 'message-label';
    label.textContent = sender === 'user' ? 'You' : 'Assistant';

    const content = document.createElement('div');
    content.className = 'message-content';

    // Convert markdown-style bold to HTML
    let formattedText = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Convert newlines to line breaks
    formattedText = formattedText.replace(/\n/g, '<br>');

    // Note: The source links are already HTML in our constructed string, so they will pass through.
    // However, we should be careful about XSS if we were handling user input repeatedly, 
    // but here it's from our trusted API (mostly).

    content.innerHTML = formattedText;

    messageDiv.appendChild(label);
    messageDiv.appendChild(content);
    messagesContainer.appendChild(messageDiv);

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Global function to handle source clicks
window.openSource = function (path) {
    // Open source in new tab
    const url = `/api/source?path=${encodeURIComponent(path)}`;
    window.open(url, '_blank');
};

function addLoadingMessage() {
    const messagesContainer = document.getElementById('chat-messages');
    const loadingDiv = document.createElement('div');
    const loadingId = 'loading-' + Date.now();
    loadingDiv.id = loadingId;
    loadingDiv.className = 'loading-message';
    loadingDiv.innerHTML = 'Thinking<span class="loading-dots"></span>';
    messagesContainer.appendChild(loadingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return loadingId;
}

function removeLoadingMessage(loadingId) {
    const loadingDiv = document.getElementById(loadingId);
    if (loadingDiv) {
        loadingDiv.remove();
    }
}
