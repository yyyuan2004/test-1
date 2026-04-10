/**
 * Persona module — view, edit, and manage persona profiles.
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

        // Modal close handlers
        Ingest.setupModalClose('modal-web-learn');
        Ingest.setupModalClose('modal-persona-detail');

        this.loadList();
    },

    async loadList() {
        const container = document.getElementById('persona-list');
        try {
            const personas = await API.get('/api/personas');
            if (personas.length === 0) {
                container.innerHTML = '<div class="empty-state">No personas created yet.<br>Upload chat logs to get started.</div>';
                return;
            }

            container.innerHTML = '';
            for (const p of personas) {
                const card = document.createElement('div');
                card.className = 'item-card';
                card.innerHTML = `
                    <div class="item-card-content">
                        <div class="item-card-title">${this.escapeHtml(p.name)}</div>
                        <div class="item-card-subtitle">${p.total_messages_analyzed} msgs | ${p.tone || 'No analysis yet'}</div>
                    </div>
                    <div class="item-card-actions">
                        <button title="Chat" data-action="chat" data-id="${p.id}" data-name="${this.escapeHtml(p.name)}">&#9993;</button>
                        <button title="Details" data-action="detail" data-id="${p.id}">&#9998;</button>
                        <button title="Delete" data-action="delete" data-id="${p.id}">&times;</button>
                    </div>
                `;

                card.querySelector('[data-action="chat"]').addEventListener('click', (e) => {
                    e.stopPropagation();
                    Chat.startNewChat(p.id, p.name);
                    // Switch to chats tab
                    document.querySelector('.nav-tab[data-tab="chats"]').click();
                });

                card.querySelector('[data-action="detail"]').addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.showDetail(p.id);
                });

                card.querySelector('[data-action="delete"]').addEventListener('click', async (e) => {
                    e.stopPropagation();
                    if (confirm(`Delete persona "${p.name}"?`)) {
                        await API.del(`/api/personas/${p.id}`);
                        this.loadList();
                    }
                });

                // Click card to start chat
                card.addEventListener('click', () => {
                    Chat.startNewChat(p.id, p.name);
                    document.querySelector('.nav-tab[data-tab="chats"]').click();
                });

                container.appendChild(card);
            }
        } catch (e) {
            container.innerHTML = `<div class="empty-state">Error loading personas</div>`;
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
                        <label>Name</label>
                        <input class="value setting-input" id="pd-name" value="${this.escapeHtml(p.name)}">
                    </div>
                    <div class="persona-field">
                        <label>Tone</label>
                        <input class="value setting-input" id="pd-tone" value="${this.escapeHtml(p.tone)}">
                    </div>
                    <div class="persona-field">
                        <label>Formality</label>
                        <input class="value setting-input" id="pd-formality" value="${this.escapeHtml(p.formality_level)}">
                    </div>
                    <div class="persona-field">
                        <label>Humor Style</label>
                        <input class="value setting-input" id="pd-humor" value="${this.escapeHtml(p.humor_style)}">
                    </div>
                </div>
                <div class="persona-field">
                    <label>Style Description</label>
                    <textarea class="value setting-input" id="pd-style" rows="3">${this.escapeHtml(p.style_description)}</textarea>
                </div>
                <div class="persona-field">
                    <label>Topics of Interest</label>
                    <input class="value setting-input" id="pd-topics" value="${(p.topics_of_interest || []).join(', ')}">
                </div>
                <div class="persona-field">
                    <label>Common Phrases</label>
                    <div class="persona-tags">${(p.common_phrases || []).map(ph => `<span class="persona-tag">${this.escapeHtml(ph)}</span>`).join('')}</div>
                </div>
                <div class="persona-field">
                    <label>Emojis</label>
                    <div class="persona-tags">${(p.emoji_usage || []).map(e => `<span class="persona-tag">${e}</span>`).join('')}</div>
                </div>
                <div class="persona-detail-grid">
                    <div class="persona-field">
                        <label>Messages Analyzed</label>
                        <div class="value">${p.total_messages_analyzed}</div>
                    </div>
                    <div class="persona-field">
                        <label>Avg Message Length</label>
                        <div class="value">${Math.round(p.avg_message_length)} chars</div>
                    </div>
                </div>
            `;

            modal.classList.remove('hidden');
        } catch (e) {
            console.error('Failed to load persona detail:', e);
        }
    },

    async savePersonaDetail() {
        if (!this.currentDetailId) return;

        const topicsRaw = document.getElementById('pd-topics').value;
        const topics = topicsRaw.split(',').map(t => t.trim()).filter(Boolean);

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
            console.error('Failed to save persona:', e);
            alert('Failed to save persona: ' + e.message);
        }
    },

    async showWebLearnModal() {
        const modal = document.getElementById('modal-web-learn');
        document.getElementById('web-learn-url').value = '';
        document.getElementById('web-learn-status').classList.add('hidden');

        // Populate persona selector
        const select = document.getElementById('web-learn-persona-select');
        select.innerHTML = '<option value="">No persona (general knowledge)</option>';
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
        status.textContent = 'Fetching and processing...';

        try {
            const result = await API.post('/api/web-learn', { url, persona_id: personaId });
            status.className = 'upload-status success';
            status.textContent = `Done! Processed ${result.chunks} chunks from the page.`;
            setTimeout(() => {
                document.getElementById('modal-web-learn').classList.add('hidden');
            }, 2000);
        } catch (e) {
            status.className = 'upload-status error';
            status.textContent = `Error: ${e.message}`;
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
