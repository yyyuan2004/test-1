/**
 * Chat module — handles message display and streaming.
 */
const Chat = {
    currentConversationId: null,
    currentPersonaId: '',
    isStreaming: false,

    init() {
        const input = document.getElementById('chat-input');
        const sendBtn = document.getElementById('btn-send');

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.send();
            }
        });

        input.addEventListener('input', () => {
            // Auto-resize textarea
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 150) + 'px';
        });

        sendBtn.addEventListener('click', () => this.send());
    },

    show() {
        document.getElementById('welcome-screen').classList.add('hidden');
        document.getElementById('chat-view').classList.remove('hidden');
    },

    showWelcome() {
        document.getElementById('welcome-screen').classList.remove('hidden');
        document.getElementById('chat-view').classList.add('hidden');
        this.currentConversationId = null;
    },

    async loadConversation(conversationId, personaId, title) {
        this.currentConversationId = conversationId;
        this.currentPersonaId = personaId || '';
        this.show();

        // Update header
        const nameEl = document.getElementById('chat-persona-name');
        const badgeEl = document.getElementById('chat-persona-badge');
        nameEl.textContent = title || 'New Chat';

        if (personaId) {
            badgeEl.classList.remove('hidden');
            badgeEl.textContent = 'Persona';
        } else {
            badgeEl.classList.add('hidden');
        }

        // Load messages
        const container = document.getElementById('chat-messages');
        container.innerHTML = '';

        try {
            const messages = await API.get(`/api/conversations/${conversationId}/messages`);
            for (const msg of messages) {
                this.appendMessage(msg.role, msg.content);
            }
            this.scrollToBottom();
        } catch (e) {
            console.error('Failed to load messages:', e);
        }

        // Focus input
        document.getElementById('chat-input').focus();
    },

    async startNewChat(personaId, personaName) {
        this.currentConversationId = null;
        this.currentPersonaId = personaId || '';
        this.show();

        const nameEl = document.getElementById('chat-persona-name');
        const badgeEl = document.getElementById('chat-persona-badge');
        nameEl.textContent = personaName || 'New Chat';

        if (personaId) {
            badgeEl.classList.remove('hidden');
            badgeEl.textContent = personaName || 'Persona';
        } else {
            badgeEl.classList.add('hidden');
        }

        document.getElementById('chat-messages').innerHTML = '';
        document.getElementById('chat-input').focus();
    },

    appendMessage(role, content) {
        const container = document.getElementById('chat-messages');
        const div = document.createElement('div');
        div.className = `message message-${role}`;

        const avatarText = role === 'user' ? 'U' : 'AI';
        div.innerHTML = `
            <div class="message-avatar">${avatarText}</div>
            <div class="message-bubble">${this.escapeHtml(content)}</div>
        `;

        container.appendChild(div);
        return div;
    },

    appendStreamingMessage() {
        const container = document.getElementById('chat-messages');
        const div = document.createElement('div');
        div.className = 'message message-assistant message-typing';
        div.id = 'streaming-message';
        div.innerHTML = `
            <div class="message-avatar">AI</div>
            <div class="message-bubble"></div>
        `;
        container.appendChild(div);
        return div;
    },

    updateStreamingMessage(token) {
        const msg = document.getElementById('streaming-message');
        if (!msg) return;
        const bubble = msg.querySelector('.message-bubble');
        bubble.textContent += token;
        this.scrollToBottom();
    },

    finalizeStreamingMessage() {
        const msg = document.getElementById('streaming-message');
        if (!msg) return;
        msg.classList.remove('message-typing');
        msg.removeAttribute('id');
    },

    async send() {
        if (this.isStreaming) return;

        const input = document.getElementById('chat-input');
        const text = input.value.trim();
        if (!text) return;

        input.value = '';
        input.style.height = 'auto';

        // Show user message
        this.appendMessage('user', text);
        this.scrollToBottom();

        // Show streaming placeholder
        this.appendStreamingMessage();
        this.scrollToBottom();

        this.isStreaming = true;
        this.updateSendButton();

        await API.streamPost('/api/chat', {
            message: text,
            conversation_id: this.currentConversationId || '',
            persona_id: this.currentPersonaId,
        }, {
            onStart: (data) => {
                if (data.conversation_id && !this.currentConversationId) {
                    this.currentConversationId = data.conversation_id;
                    // Refresh sidebar conversation list
                    App.loadConversations();
                }
            },
            onToken: (token) => {
                this.updateStreamingMessage(token);
            },
            onDone: () => {
                this.finalizeStreamingMessage();
                this.isStreaming = false;
                this.updateSendButton();
                App.loadConversations();
            },
            onError: (err) => {
                this.finalizeStreamingMessage();
                const msg = document.getElementById('streaming-message');
                if (msg) {
                    const bubble = msg.querySelector('.message-bubble');
                    bubble.textContent = `Error: ${err.message}`;
                    bubble.style.color = 'var(--danger)';
                    msg.removeAttribute('id');
                }
                this.isStreaming = false;
                this.updateSendButton();
            },
        });
    },

    updateSendButton() {
        const btn = document.getElementById('btn-send');
        btn.disabled = this.isStreaming;
    },

    scrollToBottom() {
        const container = document.getElementById('chat-messages');
        container.scrollTop = container.scrollHeight;
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
};
