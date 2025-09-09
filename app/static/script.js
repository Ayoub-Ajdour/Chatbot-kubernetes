// app/static/script.js
const chatContainer = document.getElementById('chat-container');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const clusterSelect = document.getElementById('cluster-select');
const historyBtn = document.getElementById('history-btn');
const historyPopup = document.getElementById('history-popup');
const closePopup = document.getElementById('close-popup');
const commandHistory = document.getElementById('command-history');
const sessionId = `local-session-${Date.now()}`;
let commandHistoryArray = [];

async function getToken() {
    const response = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'test_user' })
    });
    const data = await response.json();
    return data.token;
}

function addMessage(content, isUser = false, isCommandOutput = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;

    let formattedContent = content.replace(/`([^`]+)`/g, '<code>$1</code>');

    if (isCommandOutput) {
        messageDiv.innerHTML = `<div class="command-output">${formattedContent}</div>`;
    } else {
        messageDiv.innerHTML = formattedContent.replace(/\n/g, '<br>');
    }
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return messageDiv; // Retourne l'élément pour le streaming
}

function addCommandSuggestion(response) {
    const suggestionDiv = document.createElement('div');
    suggestionDiv.className = 'bot-message command-suggestion';
    suggestionDiv.dataset.originalQuery = response.original_query;

    let formattedResponse = response.response.replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\n/g, '<br>');

    suggestionDiv.innerHTML = `
        <div>${formattedResponse}</div>
        <div class="confirm-buttons">
            <button class="confirm-btn bg-green-600 text-white" data-action="confirm" data-value="yes">Yes</button>
            <button class="confirm-btn bg-red-600 text-white" data-action="confirm" data-value="no">No</button>
            <button class="confirm-btn bg-blue-600 text-white" data-action="regenerate">Regenerate</button>
        </div>
    `;
    chatContainer.appendChild(suggestionDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function addTypingAnimation() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-animation bot-message';
    typingDiv.innerHTML = '🤖 is typing <span>.</span><span>.</span><span>.</span>';
    typingDiv.id = 'typing-animation';
    chatContainer.appendChild(typingDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return typingDiv;
}

function removeTypingAnimation() {
    const typingDiv = document.getElementById('typing-animation');
    if (typingDiv) typingDiv.remove();
}

function addToHistory(command) {
    commandHistoryArray.unshift(command);
    if (commandHistoryArray.length > 10) commandHistoryArray.pop();
    commandHistory.innerHTML = commandHistoryArray.map(cmd => `<div class="p-1 border-b border-gray-700">${cmd}</div>`).join('');
}

async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    addMessage(message, true);
    userInput.value = '';
    const typing = addTypingAnimation();
    const token = await getToken();

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify({ message: message, session_id: sessionId, cluster: clusterSelect.value, stream: true })
        });

        removeTypingAnimation();

        // Gère les réponses JSON (commandes, erreurs)
        if (response.headers.get("Content-Type").includes("application/json")) {
            const data = await response.json();
            if (data.action === 'pending_confirmation') {
                addCommandSuggestion(data);
            } else {
                addMessage(data.response, false, data.action === 'executed');
            }
            return;
        }

        // Gère les réponses en streaming (text/event-stream)
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let botMessageDiv = addMessage("", false); // Crée un conteneur vide pour la réponse
        let fullResponse = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const textChunk = decoder.decode(value, { stream: true });
            const eventLines = textChunk.split('\n\n').filter(line => line.startsWith('data:'));
            
            for (const line of eventLines) {
                const jsonData = line.substring(5);
                try {
                    const data = JSON.parse(jsonData);
                    if (data.chunk) {
                        fullResponse += data.chunk;
                        botMessageDiv.innerHTML = fullResponse.replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\n/g, '<br>');
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                    }
                } catch (e) {
                    console.error("Error parsing stream data:", e, jsonData);
                }
            }
        }
    } catch (error) {
        removeTypingAnimation();
        addMessage('Error: Could not connect to the server.', false);
        console.error("Fetch error:", error);
    }
}

chatContainer.addEventListener('click', async (e) => {
    const target = e.target;
    const action = target.dataset.action;
    if (!action) return;

    const suggestionBox = target.closest('.command-suggestion');
    if (!suggestionBox) return;

    const typing = addTypingAnimation();
    const token = await getToken();
    suggestionBox.remove();

    if (action === 'confirm') {
        const confirmValue = target.dataset.value;
        try {
            const response = await fetch('/confirm', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ confirm: confirmValue, session_id: sessionId })
            });
            const data = await response.json();
            removeTypingAnimation();
            addMessage(data.response, false, data.action === 'executed');
            if (data.action === 'executed') {
                const commandText = data.response.match(/`([^`]+)`/);
                if(commandText) addToHistory(commandText[1]);
            }
        } catch (error) {
            removeTypingAnimation();
            addMessage('Error: Could not process confirmation.', false);
        }
    } else if (action === 'regenerate') {
        const originalQuery = suggestionBox.dataset.originalQuery;
        try {
            const response = await fetch('/regenerate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ original_query: originalQuery, session_id: sessionId, cluster: clusterSelect.value })
            });
            const data = await response.json();
            removeTypingAnimation();
            if (data.action === 'pending_confirmation') {
                addCommandSuggestion(data);
            } else {
                addMessage(data.response, false);
            }
        } catch (error) {
            removeTypingAnimation();
            addMessage('Error: Could not regenerate command.', false);
        }
    }
});

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMessage(); });
historyBtn.addEventListener('click', () => historyPopup.classList.toggle('hidden'));
closePopup.addEventListener('click', () => historyPopup.classList.toggle('hidden'));

addMessage('🤖 Welcome to the CodeP Chatbot! Select a cluster and ask about Kubernetes or type a command.');
