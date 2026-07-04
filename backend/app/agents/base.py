"""LangChain Agent 基类"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from langchain_openai import ChatOpenAI

from app.database import SessionLocal
from app.services.ai_config_service import build_chat_openai


class BaseAgent(ABC):
    def __init__(self):
        self.llm = self._create_llm()
    
    def _create_llm(self) -> ChatOpenAI:
        db = SessionLocal()
        try:
            return build_chat_openai(db, temperature=0.7, max_tokens=4096)
        finally:
            db.close()
    
    @abstractmethod
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass
