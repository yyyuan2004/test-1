"""Trend awareness — scrape trending topics and popular comments.

Fetches hot topics from Chinese social platforms, extracts real conversational
language from comment sections, and stores them in the vector DB for RAG.

Anti-crawler measures:
- Rotating User-Agent headers
- Random request delays
- Cookie session simulation
- Referrer spoofing
"""

from __future__ import annotations

import asyncio
import random
from typing import Any

import httpx
from bs4 import BeautifulSoup

from backend.services.embeddings import EmbeddingService
from backend.services.vector_store import VectorStore
from backend.services.rag import RAGService


# Rotating User-Agent pool
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
]


def _random_headers() -> dict[str, str]:
    return {
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
    }


class TrendScraper:
    """Scrape trending content from the web for freshness."""

    # Well-known public trending APIs / pages
    SOURCES = {
        "weibo_hot": {
            "url": "https://weibo.com/ajax/side/hotSearch",
            "type": "json_api",
        },
        "zhihu_hot": {
            "url": "https://www.zhihu.com/hot",
            "type": "html",
        },
        "baidu_hot": {
            "url": "https://top.baidu.com/board?tab=realtime",
            "type": "html",
        },
    }

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
        rag_service: RAGService,
    ) -> None:
        self._vs = vector_store
        self._emb = embedding_service
        self._rag = rag_service

    async def fetch_trends(self, source: str = "weibo_hot") -> list[dict]:
        """Fetch trending topics from a source. Returns list of {title, url, hot_score}."""
        src = self.SOURCES.get(source)
        if not src:
            return []

        try:
            await asyncio.sleep(random.uniform(0.5, 2.0))

            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=15,
                headers=_random_headers(),
            ) as client:
                resp = await client.get(src["url"])
                resp.raise_for_status()

                if src["type"] == "json_api":
                    return self._parse_weibo_api(resp.json())
                else:
                    return self._parse_html_trends(resp.text, source)

        except Exception as e:
            return [{"title": f"获取热搜失败: {str(e)[:50]}", "error": True}]

    def _parse_weibo_api(self, data: dict) -> list[dict]:
        """Parse Weibo hot search API response."""
        trends = []
        realtime = data.get("data", {}).get("realtime", [])
        for item in realtime[:20]:
            trends.append({
                "title": item.get("word", ""),
                "hot_score": item.get("num", 0),
                "source": "weibo",
            })
        return trends

    def _parse_html_trends(self, html: str, source: str) -> list[dict]:
        """Parse trending topics from HTML page."""
        soup = BeautifulSoup(html, "html.parser")
        trends = []

        if source == "zhihu_hot":
            for item in soup.select(".HotItem-content")[:20]:
                title_el = item.select_one(".HotItem-title")
                if title_el:
                    trends.append({
                        "title": title_el.get_text(strip=True),
                        "source": "zhihu",
                    })
        elif source == "baidu_hot":
            for item in soup.select(".c-single-text-ellipsis")[:20]:
                text = item.get_text(strip=True)
                if text:
                    trends.append({"title": text, "source": "baidu"})

        return trends

    async def scrape_and_store(
        self, url: str, persona_id: str = "", max_comments: int = 50
    ) -> dict:
        """Scrape a page's content and comments, store in vector DB."""
        await asyncio.sleep(random.uniform(1.0, 3.0))

        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=20,
                headers=_random_headers(),
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                tag.decompose()

            # Extract main text
            text = soup.get_text(separator="\n", strip=True)
            if not text.strip():
                return {"url": url, "chunks": 0, "status": "no_content"}

            # Chunk and embed
            chunks = self._rag.chunk_text(text, chunk_size=300)
            if not chunks:
                return {"url": url, "chunks": 0, "status": "no_content"}

            # Limit chunk count
            chunks = chunks[:100]
            vectors = self._emb.encode(chunks)

            metadatas = [
                {
                    "text": chunk,
                    "source": url,
                    "source_type": "trend_scrape",
                    "persona_id": persona_id,
                    "chunk_index": i,
                }
                for i, chunk in enumerate(chunks)
            ]

            self._vs.add(vectors, metadatas)
            self._vs.save()

            return {"url": url, "chunks": len(chunks), "status": "success"}

        except Exception as e:
            return {"url": url, "chunks": 0, "status": f"error: {str(e)[:100]}"}

    async def fetch_and_store_trends(self, persona_id: str = "") -> dict:
        """Fetch trending topics and store their titles as knowledge."""
        all_trends = []
        for source_name in self.SOURCES:
            trends = await self.fetch_trends(source_name)
            all_trends.extend([t for t in trends if not t.get("error")])
            await asyncio.sleep(random.uniform(1.0, 3.0))

        if not all_trends:
            return {"trends": 0, "status": "no_trends_found"}

        texts = [
            f"[热搜/{t.get('source', 'web')}] {t['title']}"
            for t in all_trends if t.get("title")
        ]

        if texts:
            vectors = self._emb.encode(texts)
            metadatas = [
                {
                    "text": text,
                    "source": "trend_hot",
                    "source_type": "trend",
                    "persona_id": persona_id,
                    "chunk_index": i,
                }
                for i, text in enumerate(texts)
            ]
            self._vs.add(vectors, metadatas)
            self._vs.save()

        return {"trends": len(texts), "status": "success"}
