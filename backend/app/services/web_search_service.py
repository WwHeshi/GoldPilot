"""Web search provider integration for Agent grounding."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import requests
from sqlalchemy.orm import Session

from app.services.ai_config_service import AIConfigService


TAVILY_SEARCH_URL = "https://api.tavily.com/search"


@dataclass
class WebSearchResult:
    title: str
    url: str
    content: str
    score: float | None = None
    published_date: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "content": self.content,
            "score": self.score,
            "published_date": self.published_date,
        }


class WebSearchService:
    def __init__(self, db: Session):
        self.db = db

    def search(self, query: str, *, max_results: int = 6) -> Dict[str, Any]:
        config = AIConfigService(self.db).get_resolved_config()
        if not config.enable_web_search:
            return {
                "enabled": False,
                "provider": "tavily",
                "results": [],
                "message": "Tavily Web Search 未启用",
            }

        if not config.web_search_api_key:
            return {
                "enabled": True,
                "provider": "tavily",
                "results": [],
                "message": "Tavily API Key 未配置",
            }

        payload = {
            "query": query,
            "search_depth": "basic",
            "max_results": max_results,
            "include_answer": False,
            "include_raw_content": False,
        }
        response = requests.post(
            TAVILY_SEARCH_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {config.web_search_api_key}",
                "Content-Type": "application/json",
            },
            timeout=12,
        )
        response.raise_for_status()
        data = response.json()

        results = [
            WebSearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                content=item.get("content", ""),
                score=item.get("score"),
                published_date=item.get("published_date"),
            ).to_dict()
            for item in data.get("results", [])
        ]

        return {
            "enabled": True,
            "provider": "tavily",
            "results": results,
            "message": f"Tavily 返回 {len(results)} 条结果",
        }


def format_search_results(search_result: Dict[str, Any], *, max_chars: int = 4000) -> str:
    results: List[Dict[str, Any]] = search_result.get("results", [])
    if not results:
        return search_result.get("message", "无搜索结果")

    lines: List[str] = []
    total = 0
    for index, item in enumerate(results, start=1):
        block = (
            f"[{index}] {item.get('title', '')}\n"
            f"URL: {item.get('url', '')}\n"
            f"Published: {item.get('published_date') or 'unknown'}\n"
            f"Content: {item.get('content', '')}\n"
        )
        if total + len(block) > max_chars:
            break
        lines.append(block)
        total += len(block)

    return "\n".join(lines)
