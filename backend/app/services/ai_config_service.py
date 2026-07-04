"""Service for persisted AI configuration and OpenAI-compatible clients."""
from __future__ import annotations

from dataclasses import dataclass

from openai import OpenAI
from sqlalchemy.orm import Session

from app.models.ai_config import AIConfig


DEFAULT_PROVIDER_NAME = "openai-compatible"


@dataclass
class ResolvedAIConfig:
    provider_name: str
    base_url: str
    model_name: str
    api_key: str
    enable_web_search: bool

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key)


def mask_api_key(api_key: str) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}"


class AIConfigService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_config(self) -> AIConfig:
        config = self.db.query(AIConfig).order_by(AIConfig.id.asc()).first()
        if config:
            return config

        config = AIConfig(
            provider_name=DEFAULT_PROVIDER_NAME,
            base_url="",
            model_name="",
            api_key="",
            enable_web_search=False,
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def get_resolved_config(self) -> ResolvedAIConfig:
        config = self.get_or_create_config()
        return ResolvedAIConfig(
            provider_name=config.provider_name or DEFAULT_PROVIDER_NAME,
            base_url=config.base_url or "",
            model_name=config.model_name or "",
            api_key=config.api_key or "",
            enable_web_search=bool(config.enable_web_search),
        )

    def update_config(
        self,
        *,
        base_url: str,
        model_name: str,
        api_key: str,
        enable_web_search: bool,
    ) -> AIConfig:
        config = self.get_or_create_config()
        config.provider_name = DEFAULT_PROVIDER_NAME
        config.base_url = base_url.strip()
        config.model_name = model_name.strip()
        config.enable_web_search = bool(enable_web_search)
        if api_key.strip():
            config.api_key = api_key.strip()
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config


def build_openai_client(config: ResolvedAIConfig) -> OpenAI:
    return OpenAI(
        api_key=config.api_key,
        base_url=config.base_url,
    )


def build_chat_openai(db: Session, *, temperature: float = 0.7, max_tokens: int = 4096):
    from langchain_openai import ChatOpenAI

    config = AIConfigService(db).get_resolved_config()
    return ChatOpenAI(
        model=config.model_name,
        api_key=config.api_key,
        base_url=config.base_url,
        temperature=temperature,
        max_tokens=max_tokens,
    )
