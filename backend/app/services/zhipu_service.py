"""OpenAI-compatible AI service for optional web-search style calls."""
import json
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.ai_config_service import AIConfigService, build_openai_client


class ZhipuService:
    """Backward-compatible service name, now driven by generic OpenAI-compatible config."""

    def _get_config(self):
        db = SessionLocal()
        try:
            return AIConfigService(db).get_resolved_config()
        finally:
            db.close()

    def _create_client(self):
        config = self._get_config()
        return build_openai_client(config), config

    def _extract_json(self, content: str) -> Dict[str, Any]:
        if "```json" in content:
            content = content.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in content:
            content = content.split("```", 1)[1].split("```", 1)[0]

        try:
            return json.loads(content.strip())
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(content[start:end])
            raise

    def search_institution_predictions(self) -> Dict[str, Any]:
        prompt = """Search for the latest gold forecasts from Goldman Sachs, UBS, Morgan Stanley, and Citi.

Return valid JSON only:
{
  "institutions": [
    {
      "name": "Goldman Sachs",
      "logo": "GS",
      "rating": "bullish",
      "target_price": 5400,
      "timeframe": "end of 2026",
      "reasoning": "one-sentence summary",
      "key_points": ["point1", "point2", "point3", "point4"]
    }
  ],
  "analysis_summary": "short summary",
  "search_time": "YYYY-MM-DD HH:MM:SS"
}

Rules:
1. rating must be bullish, bearish, or neutral.
2. target_price must be numeric.
3. Include all four institutions when possible.
4. If search is unavailable, infer cautiously from the latest known context and say so in reasoning.
"""
        try:
            client, config = self._create_client()
            request_kwargs = {
                "model": config.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 4096,
            }
            if config.enable_web_search:
                request_kwargs["tools"] = [{
                    "type": "web_search",
                    "web_search": {
                        "enable": True,
                        "search_result": True,
                    },
                }]

            response = client.chat.completions.create(**request_kwargs)
            content = response.choices[0].message.content or ""
            result = self._extract_json(content)
            result.setdefault("search_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            return result
        except Exception as e:
            return {
                "institutions": [],
                "analysis_summary": f"AI request failed: {str(e)}",
                "search_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

    def search_gold_news(self, query: str = "gold price market news") -> str:
        try:
            client, config = self._create_client()
            request_kwargs = {
                "model": config.model_name,
                "messages": [{
                    "role": "user",
                    "content": f"Summarize the latest news about: {query}",
                }],
                "temperature": 0.5,
                "max_tokens": 2048,
            }
            if config.enable_web_search:
                request_kwargs["tools"] = [{
                    "type": "web_search",
                    "web_search": {
                        "enable": True,
                        "search_result": True,
                    },
                }]
            response = client.chat.completions.create(**request_kwargs)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"AI request failed: {str(e)}"

    def search_json(self, prompt: str) -> Dict[str, Any]:
        try:
            client, config = self._create_client()
            request_kwargs = {
                "model": config.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 4096,
            }
            if config.enable_web_search:
                request_kwargs["tools"] = [{
                    "type": "web_search",
                    "web_search": {
                        "enable": True,
                        "search_result": True,
                    },
                }]

            response = client.chat.completions.create(**request_kwargs)
            content = response.choices[0].message.content or ""
            return self._extract_json(content)
        except Exception as e:
            return {
                "error": str(e),
                "raw_content": "",
            }


_zhipu_service: Optional[ZhipuService] = None


def get_zhipu_service() -> ZhipuService:
    global _zhipu_service
    if _zhipu_service is None:
        _zhipu_service = ZhipuService()
    return _zhipu_service
