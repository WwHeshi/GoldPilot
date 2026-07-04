"""AI provider configuration model."""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func

from app.database import Base


class AIConfig(Base):
    __tablename__ = "ai_configs"

    id = Column(Integer, primary_key=True, index=True)
    provider_name = Column(String(50), nullable=False, default="openai-compatible")
    base_url = Column(String(500), nullable=False, default="")
    model_name = Column(String(200), nullable=False, default="")
    api_key = Column(String(500), nullable=False, default="")
    enable_web_search = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
