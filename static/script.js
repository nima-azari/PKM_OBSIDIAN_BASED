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
            // Format answer with sources
            let answerText = data.answer;
            
            if (data.sources && data.sources.length > 0) {
                answerText += '\n\n**Sources:**\n';
                data.sources.forEach((source, i) => {
                    answerText += `${i + 1}. ${source.title} (relevance: ${source.score.toFixed(2)})\n`;
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
    const formattedText = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    content.innerHTML = formattedText;
    
    messageDiv.appendChild(label);
    messageDiv.appendChild(content);
    messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

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
