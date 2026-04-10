/**
 * App — 主控制器，初始化所有模块
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
                tabs.forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.sidebar-panel').forEach(p => p.classList.remove('active'));

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
                container.innerHTML = '<div class="empty-state">暂无对话记录</div>';
                return;
            }

            container.innerHTML = '';
            for (const c of conversations) {
                const card = document.createElement('div');
                card.className = 'item-card';
                if (c.id === Chat.currentConversationId) {
                    card.classList.add('active');
                }

                const date = c.updated_at ? new Date(c.updated_at).toLocaleDateString('zh-CN') : '';

                card.innerHTML = `
                    <div class="item-card-content">
                        <div class="item-card-title">${this.escapeHtml(c.title)}</div>
                        <div class="item-card-subtitle">${date}</div>
                    </div>
                    <div class="item-card-actions">
                        <button title="删除" data-action="delete">&times;</button>
                    </div>
                `;

                card.addEventListener('click', () => {
                    Chat.loadConversation(c.id, c.persona_id, c.title);
                    container.querySelectorAll('.item-card').forEach(el => el.classList.remove('active'));
                    card.classList.add('active');
                });

                card.querySelector('[data-action="delete"]').addEventListener('click', async (e) => {
                    e.stopPropagation();
                    if (confirm('确定要删除这个对话吗？')) {
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
            container.innerHTML = '<div class="empty-state">加载对话列表失败</div>';
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

// 启动应用
document.addEventListener('DOMContentLoaded', () => App.init());
