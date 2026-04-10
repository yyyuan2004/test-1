/**
 * API wrapper — all backend calls go through here.
 */
const API = {
    base: '',

    async get(path) {
        const res = await fetch(this.base + path);
        if (!res.ok) throw new Error(`GET ${path}: ${res.status}`);
        return res.json();
    },

    async post(path, body) {
        const res = await fetch(this.base + path, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!res.ok) throw new Error(`POST ${path}: ${res.status}`);
        return res.json();
    },

    async put(path, body) {
        const res = await fetch(this.base + path, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!res.ok) throw new Error(`PUT ${path}: ${res.status}`);
        return res.json();
    },

    async del(path) {
        const res = await fetch(this.base + path, { method: 'DELETE' });
        if (!res.ok) throw new Error(`DELETE ${path}: ${res.status}`);
        return res.json();
    },

    async upload(path, formData) {
        const res = await fetch(this.base + path, {
            method: 'POST',
            body: formData,
        });
        if (!res.ok) throw new Error(`UPLOAD ${path}: ${res.status}`);
        return res.json();
    },

    /**
     * Stream SSE from a POST endpoint.
     * @param {string} path
     * @param {object} body
     * @param {function} onToken  called with each token string
     * @param {function} onDone   called when stream ends
     * @param {function} onError  called on error
     */
    async streamPost(path, body, { onStart, onToken, onDone, onError }) {
        try {
            const res = await fetch(this.base + path, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });

            if (!res.ok) {
                onError && onError(new Error(`${res.status} ${res.statusText}`));
                return;
            }

            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (!line.startsWith('data: ')) continue;
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.type === 'start') {
                            onStart && onStart(data);
                        } else if (data.type === 'token') {
                            onToken && onToken(data.content);
                        } else if (data.type === 'done') {
                            onDone && onDone();
                        } else if (data.type === 'error') {
                            onError && onError(new Error(data.message));
                        }
                    } catch (e) {
                        // skip malformed lines
                    }
                }
            }
        } catch (err) {
            onError && onError(err);
        }
    },
};
