# PersonaMirror — Personal AI Chatbot

A cross-platform AI chatbot that learns a person's speaking style from chat logs, creating a digital "mirror" of their personality.

## Features

- **Persona Learning**: Upload chat logs (WeChat, WhatsApp, plain text) and the AI extracts speaking patterns, tone, vocabulary, and style
- **Multi-Backend LLM**: Supports OpenAI API, Anthropic Claude API, and local models (llama-cpp-python)
- **RAG-Powered**: Uses vector search to retrieve relevant chat examples for style-accurate responses
- **Web Learning**: Feed URLs to expand the persona's knowledge base
- **Modern UI**: Clean, responsive web interface with dark/light themes
- **Cross-Platform**: Runs on Windows and macOS

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env`:
```
OPENAI_API_KEY=sk-your-key-here
# or
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 3. Run

```bash
python run.py
```

The app will open at `http://127.0.0.1:8765`.

## Usage

1. **Create a Persona**: Click "Upload Chat Logs" in the Personas tab. Upload a chat export file and specify whose style to learn.
2. **Start Chatting**: Click a persona to start a new conversation. The AI will respond in that person's style.
3. **Web Learning**: Add web content to expand the knowledge base via "Learn from Web".
4. **Customize**: Edit persona details (tone, style, topics) in the persona detail view.

## Chat Log Formats

- **WeChat**: Plain text export (`2024-01-01 12:00 Name\nmessage`) or HTML backup
- **WhatsApp**: Standard export (`[DD/MM/YYYY, HH:MM:SS] Name: message`)
- **Plain Text**: Generic `Name: message` format, or raw text

## Local Model Setup

To use a local model instead of API:

1. Download a GGUF model file (e.g., from HuggingFace)
2. Place it in `data/models/`
3. Update `.env`:
   ```
   DEFAULT_LLM_BACKEND=local
   LOCAL_MODEL_PATH=data/models/your-model.gguf
   ```

## Project Structure

```
├── run.py                  # Entry point
├── config/settings.py      # All configuration
├── backend/
│   ├── app.py              # FastAPI application
│   ├── routers/            # API endpoints
│   ├── services/           # Business logic
│   │   ├── llm_router.py   # Multi-backend LLM
│   │   ├── rag.py          # Retrieval-augmented generation
│   │   ├── chat_service.py # Chat orchestration
│   │   └── ...
│   ├── ingestion/          # Chat log parsers
│   └── models/             # Data models
├── frontend/               # Web UI
│   ├── index.html
│   ├── css/style.css
│   └── js/
└── data/                   # Runtime data (gitignored)
```

## Tech Stack

- **Backend**: Python, FastAPI, uvicorn
- **LLM**: OpenAI API, Anthropic API, llama-cpp-python
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Vector Store**: FAISS
- **Frontend**: Vanilla HTML/CSS/JS (no build step)
- **Database**: SQLite (aiosqlite)
