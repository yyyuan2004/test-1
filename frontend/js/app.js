/**
 * App — main controller, initializes everything.
 */
const App = {
    init() {
        Chat.init();
        Ingest.init();
        Persona.init();
        Settings.init();

        this.initTabs();
        this.initNewChat();
        this.loadConversations();
    },

    initTabs() {
        const tabs = document.querySelectorAll('.nav-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // Deactivate all tabs and panels
                tabs.forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.sidebar-panel').forEach(p => p.classList.remove('active'));

                // Activate clicked tab
                tab.classList.add('active');
                const panelId = `panel-${tab.dataset.tab}`;
                document.getElementById(panelId).classList.add('active');
            });
        });
    },

    initNewChat() {
        document.getElementById('btn-new-chat').addEventListener('click', () => {
            Chat.startNewChat('', '');
        });
    },

    async loadConversations() {
        const container = document.getElementById('conversation-list');
        try {
            const conversations = await API.get('/api/conversations');
            if (conversations.length === 0) {
                container.innerHTML = '<div class="empty-state">No conversations yet</div>';
                return;
            }

            container.innerHTML = '';
            for (const c of conversations) {
                const card = document.createElement('div');
                card.className = 'item-card';
                if (c.id === Chat.currentConversationId) {
                    card.classList.add('active');
                }

                const date = c.updated_at ? new Date(c.updated_at).toLocaleDateString() : '';

                card.innerHTML = `
                    <div class="item-card-content">
                        <div class="item-card-title">${this.escapeHtml(c.title)}</div>
                        <div class="item-card-subtitle">${date}</div>
                    </div>
                    <div class="item-card-actions">
                        <button title="Delete" data-action="delete">&times;</button>
                    </div>
                `;

                card.addEventListener('click', () => {
                    Chat.loadConversation(c.id, c.persona_id, c.title);
                    // Update active state
                    container.querySelectorAll('.item-card').forEach(el => el.classList.remove('active'));
                    card.classList.add('active');
                });

                card.querySelector('[data-action="delete"]').addEventListener('click', async (e) => {
                    e.stopPropagation();
                    if (confirm('Delete this conversation?')) {
                        await API.del(`/api/conversations/${c.id}`);
                        if (Chat.currentConversationId === c.id) {
                            Chat.showWelcome();
                        }
                        this.loadConversations();
                    }
                });

                container.appendChild(card);
            }
        } catch (e) {
            container.innerHTML = '<div class="empty-state">Failed to load conversations</div>';
            console.error(e);
        }
    },

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
};

// Start the app
document.addEventListener('DOMContentLoaded', () => App.init());
