#!/usr/bin/env python3
"""Entry point for Personal AI Chatbot."""

import sys
import webbrowser
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    import uvicorn
    from config.settings import get_settings

    settings = get_settings()
    print(f"\n{'='*50}")
    print(f"  PersonaMirror - Personal AI Chatbot")
    print(f"  http://{settings.host}:{settings.port}")
    print(f"{'='*50}\n")

    try:
        webbrowser.open(f"http://{settings.host}:{settings.port}")
    except Exception:
        pass

    uvicorn.run(
        "backend.app:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
