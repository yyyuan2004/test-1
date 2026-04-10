/**
 * Persona 模块 — 人格的查看、编辑与管理
 */
const Persona = {
    currentDetailId: null,

    init() {
        const webLearnBtn = document.getElementById('btn-web-learn');
        const webLearnSubmit = document.getElementById('btn-web-learn-submit');
        const personaSave = document.getElementById('btn-persona-save');

        webLearnBtn.addEventListener('click', () => this.showWebLearnModal());
        webLearnSubmit.addEventListener('click', () => this.submitWebLearn());
        personaSave.addEventListener('click', () => this.savePersonaDetail());

        Ingest.setupModalClose('modal-web-learn');
        Ingest.setupModalClose('modal-persona-detail');

        this.loadList();
    },

    async loadList() {
        const container = document.getElementById('persona-list');
        try {
            const personas = await API.get('/api/personas');
            if (personas.length === 0) {
                container.innerHTML = '<div class="empty-state">尚未创建人格。<br>上传聊天记录即可开始。</div>';
                return;
            }

            container.innerHTML = '';
            for (const p of personas) {
                const card = document.createElement('div');
                card.className = 'item-card';
                card.innerHTML = `
                    <div class="item-card-content">
                        <div class="item-card-title">${this.escapeHtml(p.name)}</div>
                        <div class="item-card-subtitle">${p.total_messages_analyzed} 条消息 | ${p.tone || '尚未分析'}</div>
                    </div>
                    <div class="item-card-actions">
                        <button title="开始对话" data-action="chat" data-id="${p.id}" data-name="${this.escapeHtml(p.name)}">&#9993;</button>
                        <button title="查看详情" data-action="detail" data-id="${p.id}">&#9998;</button>
                        <button title="删除" data-action="delete" data-id="${p.id}">&times;</button>
                    </div>
                `;

                card.querySelector('[data-action="chat"]').addEventListener('click', (e) => {
                    e.stopPropagation();
                    Chat.startNewChat(p.id, p.name);
                    document.querySelector('.nav-tab[data-tab="chats"]').click();
                });

                card.querySelector('[data-action="detail"]').addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.showDetail(p.id);
                });

                card.querySelector('[data-action="delete"]').addEventListener('click', async (e) => {
                    e.stopPropagation();
                    if (confirm(`确定要删除人格 "${p.name}" 吗？`)) {
                        await API.del(`/api/personas/${p.id}`);
                        this.loadList();
                    }
                });

                card.addEventListener('click', () => {
                    Chat.startNewChat(p.id, p.name);
                    document.querySelector('.nav-tab[data-tab="chats"]').click();
                });

                container.appendChild(card);
            }
        } catch (e) {
            container.innerHTML = '<div class="empty-state">加载人格列表失败</div>';
            console.error(e);
        }
    },

    async showDetail(personaId) {
        this.currentDetailId = personaId;
        const modal = document.getElementById('modal-persona-detail');
        const body = document.getElementById('persona-detail-body');

        try {
            const p = await API.get(`/api/personas/${personaId}`);
            document.getElementById('persona-detail-title').textContent = p.name;

            body.innerHTML = `
                <div class="persona-detail-grid">
                    <div class="persona-field">
                        <label>名称</label>
                        <input class="value setting-input" id="pd-name" value="${this.escapeHtml(p.name)}">
                    </div>
                    <div class="persona-field">
                        <label>语气</label>
                        <input class="value setting-input" id="pd-tone" value="${this.escapeHtml(p.tone)}">
                    </div>
                    <div class="persona-field">
                        <label>正式程度</label>
                        <input class="value setting-input" id="pd-formality" value="${this.escapeHtml(p.formality_level)}">
                    </div>
                    <div class="persona-field">
                        <label>幽默风格</label>
                        <input class="value setting-input" id="pd-humor" value="${this.escapeHtml(p.humor_style)}">
                    </div>
                </div>
                <div class="persona-field">
                    <label>说话风格描述</label>
                    <textarea class="value setting-input" id="pd-style" rows="3">${this.escapeHtml(p.style_description)}</textarea>
                </div>
                <div class="persona-field">
                    <label>感兴趣的话题</label>
                    <input class="value setting-input" id="pd-topics" value="${(p.topics_of_interest || []).join('、')}">
                </div>
                <div class="persona-field">
                    <label>常用词句</label>
                    <div class="persona-tags">${(p.common_phrases || []).map(ph => `<span class="persona-tag">${this.escapeHtml(ph)}</span>`).join('')}</div>
                </div>
                <div class="persona-field">
                    <label>常用表情</label>
                    <div class="persona-tags">${(p.emoji_usage || []).map(e => `<span class="persona-tag">${e}</span>`).join('')}</div>
                </div>
                <div class="persona-detail-grid">
                    <div class="persona-field">
                        <label>已分析消息数</label>
                        <div class="value">${p.total_messages_analyzed}</div>
                    </div>
                    <div class="persona-field">
                        <label>平均消息长度</label>
                        <div class="value">${Math.round(p.avg_message_length)} 字</div>
                    </div>
                </div>
            `;

            modal.classList.remove('hidden');
        } catch (e) {
            console.error('加载人格详情失败:', e);
        }
    },

    async savePersonaDetail() {
        if (!this.currentDetailId) return;

        const topicsRaw = document.getElementById('pd-topics').value;
        const topics = topicsRaw.split(/[,、]/).map(t => t.trim()).filter(Boolean);

        const update = {
            name: document.getElementById('pd-name').value.trim(),
            tone: document.getElementById('pd-tone').value.trim(),
            formality_level: document.getElementById('pd-formality').value.trim(),
            humor_style: document.getElementById('pd-humor').value.trim(),
            style_description: document.getElementById('pd-style').value.trim(),
            topics_of_interest: topics,
        };

        try {
            await API.put(`/api/personas/${this.currentDetailId}`, update);
            document.getElementById('modal-persona-detail').classList.add('hidden');
            this.loadList();
        } catch (e) {
            console.error('保存人格失败:', e);
            alert('保存失败: ' + e.message);
        }
    },

    async showWebLearnModal() {
        const modal = document.getElementById('modal-web-learn');
        document.getElementById('web-learn-url').value = '';
        document.getElementById('web-learn-status').classList.add('hidden');

        const select = document.getElementById('web-learn-persona-select');
        select.innerHTML = '<option value="">不关联人格（通用知识）</option>';
        try {
            const personas = await API.get('/api/personas');
            for (const p of personas) {
                const opt = document.createElement('option');
                opt.value = p.id;
                opt.textContent = p.name;
                select.appendChild(opt);
            }
        } catch (e) {
            console.error(e);
        }

        modal.classList.remove('hidden');
    },

    async submitWebLearn() {
        const url = document.getElementById('web-learn-url').value.trim();
        if (!url) return;

        const personaId = document.getElementById('web-learn-persona-select').value;
        const status = document.getElementById('web-learn-status');
        const submitBtn = document.getElementById('btn-web-learn-submit');

        submitBtn.disabled = true;
        status.classList.remove('hidden');
        status.className = 'upload-status loading';
        status.textContent = '正在获取并处理网页内容...';

        try {
            const result = await API.post('/api/web-learn', { url, persona_id: personaId });
            status.className = 'upload-status success';
            status.textContent = `完成！已处理 ${result.chunks} 个文本块。`;
            setTimeout(() => {
                document.getElementById('modal-web-learn').classList.add('hidden');
            }, 2000);
        } catch (e) {
            status.className = 'upload-status error';
            status.textContent = `错误: ${e.message}`;
        } finally {
            submitBtn.disabled = false;
        }
    },

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
};
