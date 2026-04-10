from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.dependencies import get_db
from app.db.session import ping_database
from app.model import SystemCheck

router = APIRouter(tags=["System"])


@router.get("/")
async def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "environment": settings.app_env,
        "docs": "/docs",
        "health": "/api/health/live",
    }


@router.get("/api/health/live")
async def health_live() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/api/health/ready")
async def health_ready() -> dict[str, str]:
    try:
        ping_database()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        ) from exc

    return {
        "status": "ready",
        "database": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/api/health/db")
async def health_db(db: Session = Depends(get_db)) -> dict[str, str | int | None]:
    try:
        row = db.query(SystemCheck).filter(SystemCheck.name == "migration_check").first()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database query failed",
        ) from exc

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Migration check row not found",
        )

    return {
        "status": "ok",
        "table": "system_checks",
        "row_id": row.id,
        "name": row.name,
        "db_status": row.status,
    }
