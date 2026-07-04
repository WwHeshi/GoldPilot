"""Diagnostics API routes."""
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.data_source_diagnostics import DataSourceDiagnosticsService

router = APIRouter()


@router.get("/data-sources/status", response_model=Dict[str, Any])
def get_data_source_status(db: Session = Depends(get_db)):
    """Check whether configured data sources and local dependencies are available."""
    service = DataSourceDiagnosticsService(db)
    return service.run()
