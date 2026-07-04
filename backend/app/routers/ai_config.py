"""AI configuration API."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.ai_config import AIConfigResponse, AIConfigUpdate
from app.services.ai_config_service import AIConfigService, mask_api_key

router = APIRouter()


@router.get("/ai-config", response_model=AIConfigResponse)
async def get_ai_config(db: Session = Depends(get_db)):
    service = AIConfigService(db)
    config = service.get_or_create_config()
    return AIConfigResponse(
        id=config.id,
        provider_name=config.provider_name,
        base_url=config.base_url,
        model_name=config.model_name,
        enable_web_search=bool(config.enable_web_search),
        has_api_key=bool(config.api_key),
        masked_api_key=mask_api_key(config.api_key),
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.put("/ai-config", response_model=AIConfigResponse)
async def update_ai_config(payload: AIConfigUpdate, db: Session = Depends(get_db)):
    if not payload.base_url.strip():
        raise HTTPException(status_code=400, detail="base_url is required")
    if not payload.model_name.strip():
        raise HTTPException(status_code=400, detail="model_name is required")

    service = AIConfigService(db)
    config = service.update_config(
        base_url=payload.base_url,
        model_name=payload.model_name,
        api_key=payload.api_key,
        enable_web_search=payload.enable_web_search,
    )
    return AIConfigResponse(
        id=config.id,
        provider_name=config.provider_name,
        base_url=config.base_url,
        model_name=config.model_name,
        enable_web_search=bool(config.enable_web_search),
        has_api_key=bool(config.api_key),
        masked_api_key=mask_api_key(config.api_key),
        created_at=config.created_at,
        updated_at=config.updated_at,
    )
