from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.db.dependencies import get_db
from app.model import StaffRole, StaffUser
from app.schema import CreateStaffRequest, StaffLoginRequest, StaffMeResponse, StaffResponse, TokenResponse, UpdateStaffRequest

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


def get_current_staff(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> StaffUser:
    token = _extract_bearer_token(authorization)
    payload = decode_access_token(token)
    role = payload.get("role")
    if role not in {StaffRole.super_admin.value, StaffRole.admin.value, StaffRole.host.value}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required",
        )

    staff = db.get(StaffUser, int(payload["sub"]))
    if staff is None or not staff.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Staff user not found",
        )
    return staff


def require_admin(staff: StaffUser = Depends(get_current_staff)) -> StaffUser:
    if staff.role not in {StaffRole.super_admin, StaffRole.admin}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return staff


def require_super_admin(staff: StaffUser = Depends(get_current_staff)) -> StaffUser:
    if staff.role != StaffRole.super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )
    return staff


@router.post("/login", response_model=TokenResponse)
def staff_login(payload: StaffLoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    staff = db.query(StaffUser).filter(StaffUser.login == payload.login).first()
    if staff is None or not staff.is_active or not verify_password(payload.password, staff.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    return TokenResponse(
        access_token=create_access_token(str(staff.id), staff.role.value),
        role=staff.role,
    )


@router.post("/staff", status_code=status.HTTP_201_CREATED)
def create_staff(
    payload: CreateStaffRequest,
    _: StaffUser = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> dict[str, str | int]:
    staff = StaffUser(
        login=payload.login,
        name=payload.name,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(staff)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Staff user with this login already exists",
        ) from exc
    db.refresh(staff)
    return {
        "status": "created",
        "id": staff.id,
        "login": staff.login,
        "name": staff.name,
        "role": staff.role.value,
    }


@router.get("/staff", response_model=list[StaffResponse])
def list_staff(
    _: StaffUser = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> list[StaffResponse]:
    staff_users = db.query(StaffUser).order_by(StaffUser.created_at.asc(), StaffUser.id.asc()).all()
    return [
        StaffResponse(
            id=staff.id,
            login=staff.login,
            name=staff.name,
            role=staff.role,
            is_active=staff.is_active,
        )
        for staff in staff_users
    ]


@router.patch("/staff/{staff_id}", response_model=StaffResponse)
def update_staff(
    staff_id: int,
    payload: UpdateStaffRequest,
    current_staff: StaffUser = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> StaffResponse:
    staff = db.get(StaffUser, staff_id)
    if staff is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff user not found")

    if payload.name is not None:
        staff.name = payload.name
    if payload.password is not None:
        staff.password_hash = hash_password(payload.password)
    if payload.role is not None:
        if staff.id == current_staff.id and payload.role != StaffRole.super_admin:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot demote yourself from super admin")
        staff.role = payload.role
    if payload.is_active is not None:
        if staff.id == current_staff.id and payload.is_active is False:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate yourself")
        staff.is_active = payload.is_active

    if staff.role != StaffRole.super_admin:
        super_admin_exists = (
            db.query(StaffUser)
            .filter(StaffUser.role == StaffRole.super_admin, StaffUser.id != staff.id)
            .first()
        )
        if super_admin_exists is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one super admin must remain")

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Staff user with this login already exists",
        ) from exc
    db.refresh(staff)
    return StaffResponse(
        id=staff.id,
        login=staff.login,
        name=staff.name,
        role=staff.role,
        is_active=staff.is_active,
    )


@router.delete("/staff/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_staff(
    staff_id: int,
    current_staff: StaffUser = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> None:
    staff = db.get(StaffUser, staff_id)
    if staff is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff user not found")
    if staff.id == current_staff.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")
    if staff.role == StaffRole.super_admin:
        another_super_admin = (
            db.query(StaffUser)
            .filter(StaffUser.role == StaffRole.super_admin, StaffUser.id != staff.id)
            .first()
        )
        if another_super_admin is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one super admin must remain")

    db.delete(staff)
    db.commit()


@router.get("/me", response_model=StaffMeResponse)
def staff_me(staff: StaffUser = Depends(get_current_staff)) -> StaffMeResponse:
    return StaffMeResponse(
        id=staff.id,
        login=staff.login,
        name=staff.name,
        role=staff.role,
        is_active=staff.is_active,
    )
