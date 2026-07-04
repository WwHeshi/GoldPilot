"""Schemas for AI configuration."""
from datetime import datetime
from pydantic import BaseModel, Field


class AIConfigBase(BaseModel):
    base_url: str
    model_name: str
    enable_web_search: bool = False


class AIConfigUpdate(AIConfigBase):
    api_key: str = Field(default="", description="Leave empty to keep the existing key")


class AIConfigResponse(AIConfigBase):
    id: int
    has_api_key: bool
    masked_api_key: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
