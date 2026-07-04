"""Schemas for AI configuration."""
from datetime import datetime
from pydantic import BaseModel, Field


class AIConfigBase(BaseModel):
    base_url: str
    model_name: str
    enable_web_search: bool = False


class AIConfigUpdate(AIConfigBase):
    api_key: str = Field(default="", description="Leave empty to keep the existing key")
    web_search_api_key: str = Field(default="", description="Leave empty to keep the existing Tavily key")


class AIConfigTestRequest(AIConfigUpdate):
    pass


class AIConfigTestResponse(BaseModel):
    success: bool
    status: str
    message: str
    latency_ms: int | None = None
    base_url: str
    model_name: str
    response_preview: str | None = None


class AIConfigResponse(AIConfigBase):
    id: int
    has_api_key: bool
    masked_api_key: str
    has_web_search_api_key: bool
    masked_web_search_api_key: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
