/**
 * Settings 模块 — 模型选择、主题切换、连接测试、热搜抓取
 */
const Settings = {
    init() {
        const backendSelect = document.getElementById('select-backend');
        const themeSelect = document.getElementById('select-theme');
        const testBtn = document.getElementById('btn-test-backend');
        const trendBtn = document.getElementById('btn-fetch-trends');

        backendSelect.addEventListener('change', () => this.switchBackend(backendSelect.value));
        themeSelect.addEventListener('change', () => this.setTheme(themeSelect.value));
        testBtn.addEventListener('click', () => this.testBackend());
        trendBtn.addEventListener('click', () => this.fetchTrends());

        const savedTheme = localStorage.getItem('theme') || 'dark';
        themeSelect.value = savedTheme;
        this.setTheme(savedTheme);

        this.loadModelInfo();
        this.checkStatus();
    },

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    },

    async loadModelInfo() {
        try {
            const info = await API.get('/api/models');
            document.getElementById('select-backend').value = info.active_backend;

            const BACKEND_NAMES = {
                openai: 'OpenAI',
                anthropic: 'Claude',
                deepseek: 'DeepSeek',
                qwen: '通义千问',
                zhipu: '智谱清言',
                local: '本地模型',
            };

            const lines = [`当前后端: ${BACKEND_NAMES[info.active_backend] || info.active_backend}`];

            const backends = [
                { key: 'openai', model: info.openai_model, hasKey: info.has_openai_key },
                { key: 'anthropic', model: info.anthropic_model, hasKey: info.has_anthropic_key },
                { key: 'deepseek', model: info.deepseek_model, hasKey: info.has_deepseek_key },
                { key: 'qwen', model: info.qwen_model, hasKey: info.has_qwen_key },
                { key: 'zhipu', model: info.zhipu_model, hasKey: info.has_zhipu_key },
            ];

            for (const b of backends) {
                const status = b.hasKey ? '(已配置)' : '(未配置密钥)';
                lines.push(`${BACKEND_NAMES[b.key]}: ${b.model} ${status}`);
            }
            lines.push(`本地模型: ${info.local_model_path}`);

            document.getElementById('model-info').textContent = lines.join('\n');
        } catch (e) {
            document.getElementById('model-info').textContent = '获取模型信息失败';
            console.error(e);
        }
    },

    async switchBackend(backend) {
        try {
            await API.post('/api/models/switch', { backend });
            this.loadModelInfo();
            this.checkStatus();
        } catch (e) {
            alert('切换后端失败: ' + e.message);
            console.error(e);
        }
    },

    async testBackend() {
        const backend = document.getElementById('select-backend').value;
        const resultEl = document.getElementById('test-result');
        resultEl.classList.remove('hidden');
        resultEl.className = 'upload-status loading';
        resultEl.textContent = `正在测试 ${backend} 连接...`;

        try {
            const result = await API.post(`/api/status/test/${backend}`, {});
            if (result.connected) {
                resultEl.className = 'upload-status success';
                resultEl.textContent = `连接成功！模型: ${result.model}`;
                this.setStatus('ok', '已连接');
            } else {
                resultEl.className = 'upload-status error';
                resultEl.textContent = `连接失败: ${result.error || '未知错误'}`;
                this.setStatus('error', '连接失败');
            }
        } catch (e) {
            resultEl.className = 'upload-status error';
            resultEl.textContent = `测试出错: ${e.message}`;
            this.setStatus('error', '测试出错');
        }
    },

    async checkStatus() {
        try {
            const status = await API.get('/api/status');
            if (!status.server_ok) {
                this.setStatus('error', '服务器异常');
                return;
            }

            const activeBackend = status.backends.find(b => b.name === status.active_backend);
            if (activeBackend && !activeBackend.has_key && activeBackend.name !== 'local') {
                this.setStatus('warning', `${activeBackend.display_name} 未配置密钥`);
            } else if (!status.embedding_ok) {
                this.setStatus('warning', '嵌入模型加载中...');
            } else {
                this.setStatus('ok', `就绪 | ${status.active_backend} | ${status.vector_store_count} 条向量`);
            }
        } catch (e) {
            this.setStatus('error', '无法连接服务器');
        }
    },

    setStatus(level, text) {
        const dot = document.getElementById('status-dot');
        const textEl = document.getElementById('status-text');
        dot.className = `status-dot ${level}`;
        textEl.textContent = text;
    },

    async fetchTrends() {
        const resultEl = document.getElementById('trend-result');
        resultEl.classList.remove('hidden');
        resultEl.className = 'upload-status loading';
        resultEl.textContent = '正在抓取热搜数据...';

        try {
            const result = await API.post('/api/web-learn', {
                url: 'https://weibo.com/ajax/side/hotSearch',
                persona_id: '',
            });
            resultEl.className = 'upload-status success';
            resultEl.textContent = `完成！已存储 ${result.chunks} 条热搜数据。`;
        } catch (e) {
            resultEl.className = 'upload-status error';
            resultEl.textContent = `抓取失败: ${e.message}`;
        }
    },
};
