"""AI configuration API."""
from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.ai_config import AIConfigResponse, AIConfigTestRequest, AIConfigTestResponse, AIConfigUpdate
from app.services.ai_config_service import (
    AIConfigService,
    ResolvedAIConfig,
    build_openai_client,
    mask_api_key,
)

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
        has_web_search_api_key=bool(config.web_search_api_key),
        masked_web_search_api_key=mask_api_key(config.web_search_api_key),
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
        web_search_api_key=payload.web_search_api_key,
    )
    return AIConfigResponse(
        id=config.id,
        provider_name=config.provider_name,
        base_url=config.base_url,
        model_name=config.model_name,
        enable_web_search=bool(config.enable_web_search),
        has_api_key=bool(config.api_key),
        masked_api_key=mask_api_key(config.api_key),
        has_web_search_api_key=bool(config.web_search_api_key),
        masked_web_search_api_key=mask_api_key(config.web_search_api_key),
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.post("/ai-config/test", response_model=AIConfigTestResponse)
async def test_ai_config(payload: AIConfigTestRequest, db: Session = Depends(get_db)):
    if not payload.base_url.strip():
        raise HTTPException(status_code=400, detail="base_url is required")
    if not payload.model_name.strip():
        raise HTTPException(status_code=400, detail="model_name is required")

    service = AIConfigService(db)
    saved_config = service.get_resolved_config()
    api_key = payload.api_key.strip() or saved_config.api_key
    base_url = payload.base_url.strip()
    model_name = payload.model_name.strip()

    if not api_key:
        return AIConfigTestResponse(
            success=False,
            status="missing_api_key",
            message="请填写 API Key，或先保存一个可用的 API Key",
            base_url=base_url,
            model_name=model_name,
        )

    test_config = ResolvedAIConfig(
        provider_name=saved_config.provider_name,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        enable_web_search=False,
        web_search_api_key="",
    )

    start = perf_counter()
    try:
        client = build_openai_client(test_config).with_options(timeout=15)
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": "Reply with exactly: OK",
                }
            ],
            temperature=0,
            max_tokens=8,
        )
        latency_ms = int((perf_counter() - start) * 1000)
        content = response.choices[0].message.content or ""
        return AIConfigTestResponse(
            success=True,
            status="ok",
            message="AI 接口连通性正常",
            latency_ms=latency_ms,
            base_url=base_url,
            model_name=model_name,
            response_preview=content[:120],
        )
    except Exception as exc:
        latency_ms = int((perf_counter() - start) * 1000)
        return AIConfigTestResponse(
            success=False,
            status="request_failed",
            message=str(exc),
            latency_ms=latency_ms,
            base_url=base_url,
            model_name=model_name,
        )
