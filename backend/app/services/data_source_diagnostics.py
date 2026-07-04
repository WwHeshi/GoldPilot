"""Data source diagnostics for external feeds and local dependencies."""
from __future__ import annotations

import csv
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from io import StringIO
from time import perf_counter
from typing import Any, Callable, Dict, List

import feedparser
import requests
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models.gold_price import DollarIndex, GoldPrice
from app.models.news import GoldNews
from app.scheduler import scheduler
from app.services.ai_config_service import AIConfigService
from app.services.cache_manager import get_cache_status
from app.services.web_search_service import WebSearchService
from app.utils.timezone import china_now_iso


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


@dataclass
class DiagnosticResult:
    name: str
    category: str
    source: str
    status: str
    latency_ms: int
    message: str
    sample: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "source": self.source,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "message": self.message,
            "sample": self.sample,
        }


class DataSourceDiagnosticsService:
    def __init__(self, db: Session):
        self.db = db

    def run(self) -> Dict[str, Any]:
        checks: List[DiagnosticResult] = [
            self._measure("MySQL 数据库", "database", "本地 MySQL", self._check_database),
            self._measure("AI 配置", "ai", "ai_configs", self._check_ai_config),
            self._measure("Tavily Web Search", "search", "Tavily API", self._check_tavily_search),
            self._measure("Agent 缓存", "cache", "backend/cache", self._check_cache),
            self._measure("定时任务", "scheduler", "APScheduler", self._check_scheduler),
        ]

        network_checks: List[tuple[str, str, str, Callable[[], Dict[str, Any]]]] = [
            ("实时金价 - 腾讯", "market", "腾讯财经 hf_GC", self._check_tencent_gold),
            ("实时金价 - 新浪", "market", "新浪财经 hf_GC", self._check_sina_gold),
            ("实时美元指数", "market", "新浪财经 DINIW", self._check_sina_dollar_index),
            ("历史金价", "history", "新浪 GlobalFuturesService", self._check_sina_gold_history),
            ("历史美元指数", "history", "FRED DTWEXBGS", self._check_fred_dollar_index),
            ("RSS - Kitco", "news", "Kitco News", lambda: self._check_rss("https://news.kitco.com/rss/kitconewsfeed.xml")),
            ("RSS - King World News", "news", "King World News", lambda: self._check_rss("https://kingworldnews.com/feed/")),
            ("RSS - MINING.com", "news", "MINING.com", lambda: self._check_rss("https://www.mining.com/feed/")),
        ]

        ordered_network_results: Dict[int, DiagnosticResult] = {}
        with ThreadPoolExecutor(max_workers=6) as executor:
            future_map = {
                executor.submit(self._measure, name, category, source, check): index
                for index, (name, category, source, check) in enumerate(network_checks)
            }
            for future in as_completed(future_map):
                ordered_network_results[future_map[future]] = future.result()

        checks.extend(ordered_network_results[index] for index in sorted(ordered_network_results))

        summary = {
            "total": len(checks),
            "ok": sum(1 for item in checks if item.status == "ok"),
            "warning": sum(1 for item in checks if item.status == "warning"),
            "error": sum(1 for item in checks if item.status == "error"),
        }
        overall_status = "ok"
        if summary["error"]:
            overall_status = "degraded"
        elif summary["warning"]:
            overall_status = "warning"

        return {
            "overall_status": overall_status,
            "checked_at": china_now_iso(),
            "summary": summary,
            "checks": [item.to_dict() for item in checks],
        }

    def _measure(
        self,
        name: str,
        category: str,
        source: str,
        check: Callable[[], Dict[str, Any]],
    ) -> DiagnosticResult:
        start = perf_counter()
        try:
            payload = check()
            status = payload.get("status", "ok")
            message = payload.get("message", "")
            sample = payload.get("sample", {})
        except Exception as exc:
            status = "error"
            message = str(exc)
            sample = {}

        latency_ms = int((perf_counter() - start) * 1000)
        return DiagnosticResult(
            name=name,
            category=category,
            source=source,
            status=status,
            latency_ms=latency_ms,
            message=message,
            sample=sample,
        )

    def _check_database(self) -> Dict[str, Any]:
        self.db.execute(text("SELECT 1"))
        gold_count = self.db.query(func.count(GoldPrice.id)).scalar() or 0
        dollar_count = self.db.query(func.count(DollarIndex.id)).scalar() or 0
        news_count = self.db.query(func.count(GoldNews.id)).scalar() or 0
        latest_gold = self.db.query(func.max(GoldPrice.date)).scalar()
        latest_dollar = self.db.query(func.max(DollarIndex.date)).scalar()

        status = "ok" if gold_count and dollar_count else "warning"
        message = "数据库连接正常"
        if status == "warning":
            message = "数据库可连接，但历史行情数据不完整"

        return {
            "status": status,
            "message": message,
            "sample": {
                "gold_prices": gold_count,
                "latest_gold_date": latest_gold.isoformat() if latest_gold else None,
                "dollar_index": dollar_count,
                "latest_dollar_date": latest_dollar.isoformat() if latest_dollar else None,
                "gold_news": news_count,
            },
        }

    def _check_ai_config(self) -> Dict[str, Any]:
        config = AIConfigService(self.db).get_resolved_config()
        configured = bool(config.base_url and config.model_name and config.api_key)
        return {
            "status": "ok" if configured else "warning",
            "message": "AI 接口配置完整" if configured else "AI 接口未完整配置，Agent 会使用缓存或默认结果",
            "sample": {
                "provider_name": config.provider_name,
                "base_url": config.base_url,
                "model_name": config.model_name,
                "has_api_key": bool(config.api_key),
                "web_search_enabled": config.enable_web_search,
                "has_web_search_api_key": bool(config.web_search_api_key),
            },
        }

    def _check_tavily_search(self) -> Dict[str, Any]:
        result = WebSearchService(self.db).search("latest gold market news", max_results=2)
        if not result.get("enabled"):
            return {
                "status": "warning",
                "message": result.get("message", "Tavily Web Search 未启用"),
                "sample": {},
            }
        if not result.get("results"):
            return {
                "status": "warning",
                "message": result.get("message", "Tavily 未返回搜索结果"),
                "sample": {},
            }
        return {
            "status": "ok",
            "message": result.get("message", "Tavily 搜索正常"),
            "sample": {
                "first_result": result["results"][0],
            },
        }

    def _check_cache(self) -> Dict[str, Any]:
        status = get_cache_status()
        file_keys = status.get("file_cache_keys", [])
        return {
            "status": "ok",
            "message": f"缓存目录可访问，当前文件缓存 {len(file_keys)} 个",
            "sample": status,
        }

    def _check_scheduler(self) -> Dict[str, Any]:
        running = scheduler.running
        jobs = scheduler.get_jobs()
        return {
            "status": "ok" if running else "warning",
            "message": "定时任务运行中" if running else "定时任务未运行，Docker 默认配置下这是正常状态",
            "sample": {
                "running": running,
                "jobs_count": len(jobs),
                "jobs": [
                    {
                        "id": job.id,
                        "name": job.name,
                        "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                    }
                    for job in jobs
                ],
            },
        }

    def _check_tencent_gold(self) -> Dict[str, Any]:
        response = requests.get("https://qt.gtimg.cn/q=hf_GC", headers=HEADERS, timeout=5)
        response.raise_for_status()
        match = re.search(r'v_hf_GC="([^"]+)"', response.text)
        if not match:
            raise ValueError("响应格式不匹配")

        values = match.group(1).split(",")
        price = float(values[0])
        previous_close = float(values[7])
        return {
            "status": "ok",
            "message": "实时金价可获取",
            "sample": {
                "price": price,
                "previous_close": previous_close,
                "date": values[12] if len(values) > 12 else None,
            },
        }

    def _check_sina_gold(self) -> Dict[str, Any]:
        response = requests.get(
            "https://hq.sinajs.cn/list=hf_GC",
            headers={**HEADERS, "Referer": "https://finance.sina.com.cn"},
            timeout=5,
        )
        response.raise_for_status()
        response.encoding = "gb2312"
        match = re.search(r'var hq_str_hf_GC="([^"]*)"', response.text)
        if not match or not match.group(1):
            raise ValueError("响应格式不匹配")

        values = match.group(1).split(",")
        price = float(values[0])
        return {
            "status": "ok",
            "message": "新浪实时金价可获取",
            "sample": {
                "price": price,
                "high": values[4] if len(values) > 4 else None,
                "low": values[5] if len(values) > 5 else None,
                "date": values[12] if len(values) > 12 else None,
            },
        }

    def _check_sina_dollar_index(self) -> Dict[str, Any]:
        response = requests.get(
            "https://hq.sinajs.cn/list=DINIW",
            headers={**HEADERS, "Referer": "https://finance.sina.com.cn"},
            timeout=5,
        )
        response.raise_for_status()
        match = re.search(r'var hq_str_DINIW="([^"]*)"', response.text)
        if not match or not match.group(1):
            raise ValueError("响应格式不匹配")

        values = match.group(1).split(",")
        price = float(values[1])
        previous_close = float(values[8])
        return {
            "status": "ok",
            "message": "美元指数可获取",
            "sample": {
                "price": round(price, 2),
                "previous_close": round(previous_close, 2),
                "name": values[9] if len(values) > 9 else "DINIW",
            },
        }

    def _check_sina_gold_history(self) -> Dict[str, Any]:
        url = (
            "https://stock2.finance.sina.com.cn/futures/api/jsonp.php/"
            "var_GC=/GlobalFuturesService.getGlobalFuturesDailyKLine?symbol=GC"
        )
        response = requests.get(
            url,
            headers={**HEADERS, "Referer": "https://finance.sina.com.cn"},
            timeout=8,
        )
        response.raise_for_status()
        match = re.search(r"var_GC=\((\[.*?\])\);", response.text, re.DOTALL)
        if not match:
            raise ValueError("响应格式不匹配")

        rows = json.loads(match.group(1))
        if not rows:
            raise ValueError("历史金价返回为空")

        latest = rows[-1]
        return {
            "status": "ok",
            "message": f"历史金价可获取，共 {len(rows)} 条",
            "sample": {
                "date": latest.get("date"),
                "close": latest.get("close"),
            },
        }

    def _check_fred_dollar_index(self) -> Dict[str, Any]:
        response = requests.get(
            "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTWEXBGS",
            headers=HEADERS,
            timeout=8,
        )
        response.raise_for_status()
        reader = csv.DictReader(StringIO(response.text))
        latest = None
        count = 0
        for row in reader:
            value = row.get("DTWEXBGS")
            if value and value != ".":
                latest = row
                count += 1

        if not latest:
            raise ValueError("FRED CSV 没有可用数据")

        return {
            "status": "ok",
            "message": f"FRED 美元指数历史数据可获取，共 {count} 条",
            "sample": latest,
        }

    def _check_rss(self, rss_url: str) -> Dict[str, Any]:
        response = requests.get(rss_url, headers=HEADERS, timeout=6)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        if feed.bozo and not feed.entries:
            raise ValueError(str(feed.bozo_exception))
        if not feed.entries:
            raise ValueError("RSS 返回为空")

        first = feed.entries[0]
        return {
            "status": "ok",
            "message": f"RSS 可获取，共解析 {len(feed.entries)} 条",
            "sample": {
                "title": first.get("title", ""),
                "link": first.get("link", ""),
            },
        }
