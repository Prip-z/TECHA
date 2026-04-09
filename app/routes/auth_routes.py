from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.db.dependencies import get_db
from app.model import Admin
from app.schema.auth import AdminLoginRequest, AdminMeResponse, RegisterAdminRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
        )
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
        )
    return token


def get_current_admin(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Admin:
    token = _extract_bearer_token(authorization)
    payload = decode_access_token(token)
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    admin = db.get(Admin, int(payload["sub"]))
    if admin is None or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin not found",
        )
    return admin


@router.post("/login", response_model=TokenResponse)
def admin_login(payload: AdminLoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    admin = db.query(Admin).filter(Admin.login == payload.login).first()
    if admin is None or not admin.is_active or not verify_password(payload.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
        )

    return TokenResponse(
        access_token=create_access_token(str(admin.id), "admin"),
        role="admin",
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_admin(
    payload: RegisterAdminRequest,
    _: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, str | int]:
    admin = Admin(
        login=payload.login,
        name=payload.name,
        password_hash=hash_password(payload.password),
    )
    db.add(admin)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Admin with this login already exists",
        ) from exc
    db.refresh(admin)
    return {
        "status": "created",
        "id": admin.id,
        "login": admin.login,
        "name": admin.name,
    }


@router.get("/me", response_model=AdminMeResponse)
def admin_me(admin: Admin = Depends(get_current_admin)) -> AdminMeResponse:
    return AdminMeResponse(
        id=admin.id,
        login=admin.login,
        name=admin.name,
        is_active=admin.is_active,
    )
