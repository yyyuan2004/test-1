/**
 * Ingest module — file upload and chat log processing.
 */
const Ingest = {
    selectedFiles: [],

    init() {
        const uploadBtn = document.getElementById('btn-upload');
        const browseBtn = document.getElementById('btn-browse');
        const fileInput = document.getElementById('upload-file');
        const submitBtn = document.getElementById('btn-upload-submit');
        const zone = document.getElementById('upload-zone');

        uploadBtn.addEventListener('click', () => this.showModal());
        browseBtn.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => this.onFilesSelected(e.target.files));
        submitBtn.addEventListener('click', () => this.submit());

        // Drag and drop
        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('drag-over');
        });
        zone.addEventListener('dragleave', () => {
            zone.classList.remove('drag-over');
        });
        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('drag-over');
            this.onFilesSelected(e.dataTransfer.files);
        });
        zone.addEventListener('click', (e) => {
            if (e.target === zone || e.target.tagName === 'P' || e.target.tagName === 'SVG') {
                fileInput.click();
            }
        });

        // Modal close handlers
        this.setupModalClose('modal-upload');
    },

    showModal() {
        const modal = document.getElementById('modal-upload');
        modal.classList.remove('hidden');
        this.selectedFiles = [];
        document.getElementById('upload-file').value = '';
        document.getElementById('upload-persona-name').value = '';
        document.getElementById('upload-target-speaker').value = '';
        document.getElementById('upload-status').classList.add('hidden');
        document.getElementById('btn-upload-submit').disabled = true;

        // Populate persona selector
        this.populatePersonaSelect();
    },

    async populatePersonaSelect() {
        const select = document.getElementById('upload-persona-select');
        select.innerHTML = '<option value="">Create new persona</option>';
        try {
            const personas = await API.get('/api/personas');
            for (const p of personas) {
                const opt = document.createElement('option');
                opt.value = p.id;
                opt.textContent = p.name;
                select.appendChild(opt);
            }
        } catch (e) {
            console.error('Failed to load personas:', e);
        }
    },

    onFilesSelected(files) {
        this.selectedFiles = Array.from(files);
        const submitBtn = document.getElementById('btn-upload-submit');
        submitBtn.disabled = this.selectedFiles.length === 0;

        const status = document.getElementById('upload-status');
        if (this.selectedFiles.length > 0) {
            status.classList.remove('hidden');
            status.className = 'upload-status success';
            status.textContent = `Selected ${this.selectedFiles.length} file(s): ${this.selectedFiles.map(f => f.name).join(', ')}`;
        }
    },

    async submit() {
        if (this.selectedFiles.length === 0) return;

        const personaName = document.getElementById('upload-persona-name').value.trim();
        const targetSpeaker = document.getElementById('upload-target-speaker').value.trim();
        const personaId = document.getElementById('upload-persona-select').value;
        const status = document.getElementById('upload-status');
        const submitBtn = document.getElementById('btn-upload-submit');

        submitBtn.disabled = true;
        status.classList.remove('hidden');
        status.className = 'upload-status loading';
        status.textContent = 'Uploading and analyzing... This may take a moment.';

        let lastResult = null;

        for (const file of this.selectedFiles) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('persona_name', personaName);
            formData.append('target_speaker', targetSpeaker);
            if (personaId || (lastResult && lastResult.persona_id)) {
                formData.append('persona_id', personaId || lastResult.persona_id);
            }

            try {
                lastResult = await API.upload('/api/ingest', formData);
            } catch (e) {
                status.className = 'upload-status error';
                status.textContent = `Error processing ${file.name}: ${e.message}`;
                submitBtn.disabled = false;
                return;
            }
        }

        status.className = 'upload-status success';
        status.textContent = `Done! Analyzed ${lastResult.messages_parsed} messages, stored ${lastResult.chunks_stored} chunks. Persona: ${lastResult.persona_name}`;

        // Refresh persona list
        Persona.loadList();
        App.loadConversations();

        setTimeout(() => {
            document.getElementById('modal-upload').classList.add('hidden');
        }, 2000);
    },

    setupModalClose(modalId) {
        const modal = document.getElementById(modalId);
        modal.querySelector('.modal-overlay').addEventListener('click', () => {
            modal.classList.add('hidden');
        });
        modal.querySelector('.modal-close').addEventListener('click', () => {
            modal.classList.add('hidden');
        });
        const cancelBtn = modal.querySelector('.modal-cancel');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                modal.classList.add('hidden');
            });
        }
    },
};
