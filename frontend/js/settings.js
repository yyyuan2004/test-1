/**
 * Settings module — model selection, theme toggle.
 */
const Settings = {
    init() {
        const backendSelect = document.getElementById('select-backend');
        const themeSelect = document.getElementById('select-theme');

        backendSelect.addEventListener('change', () => this.switchBackend(backendSelect.value));
        themeSelect.addEventListener('change', () => this.setTheme(themeSelect.value));

        // Load saved theme
        const savedTheme = localStorage.getItem('theme') || 'dark';
        themeSelect.value = savedTheme;
        this.setTheme(savedTheme);

        this.loadModelInfo();
    },

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    },

    async loadModelInfo() {
        try {
            const info = await API.get('/api/models');
            document.getElementById('select-backend').value = info.active_backend;

            const infoDiv = document.getElementById('model-info');
            infoDiv.textContent =
                `Active: ${info.active_backend}\n` +
                `OpenAI: ${info.openai_model} ${info.has_openai_key ? '(key set)' : '(no key)'}\n` +
                `Claude: ${info.anthropic_model} ${info.has_anthropic_key ? '(key set)' : '(no key)'}\n` +
                `Local: ${info.local_model_path}`;
        } catch (e) {
            document.getElementById('model-info').textContent = 'Failed to load model info';
            console.error(e);
        }
    },

    async switchBackend(backend) {
        try {
            await API.post('/api/models/switch', { backend });
            this.loadModelInfo();
        } catch (e) {
            alert('Failed to switch backend: ' + e.message);
            console.error(e);
        }
    },
};
