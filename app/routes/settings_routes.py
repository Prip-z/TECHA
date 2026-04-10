from fastapi import APIRouter, Depends
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.model import AppSetting, StaffUser
from app.routes.auth_routes import get_current_staff, require_admin
from app.schema import AppSettingResponse, UpdateAppSettingsRequest

router = APIRouter(prefix="/settings", tags=["Settings"])

DEFAULT_PRICE_KEY = "default_price_per_game"
DEFAULT_PRICE_FALLBACK = 2500.0


def get_default_price_per_game(db: Session) -> float:
    try:
        row = db.query(AppSetting).filter(AppSetting.key == DEFAULT_PRICE_KEY).first()
    except ProgrammingError:
        db.rollback()
        return DEFAULT_PRICE_FALLBACK
    if row is None:
        return DEFAULT_PRICE_FALLBACK
    try:
        return float(row.value)
    except ValueError:
        return DEFAULT_PRICE_FALLBACK


@router.get("", response_model=AppSettingResponse)
def get_settings(
    _: StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> AppSettingResponse:
    return AppSettingResponse(default_price_per_game=get_default_price_per_game(db))


@router.put("", response_model=AppSettingResponse)
def update_settings(
    payload: UpdateAppSettingsRequest,
    _: StaffUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AppSettingResponse:
    try:
        row = db.query(AppSetting).filter(AppSetting.key == DEFAULT_PRICE_KEY).first()
    except ProgrammingError:
        db.rollback()
        return AppSettingResponse(default_price_per_game=DEFAULT_PRICE_FALLBACK)
    if row is None:
        row = AppSetting(key=DEFAULT_PRICE_KEY, value=str(payload.default_price_per_game))
        db.add(row)
    else:
        row.value = str(payload.default_price_per_game)
    db.commit()
    return AppSettingResponse(default_price_per_game=payload.default_price_per_game)
