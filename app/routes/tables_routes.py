from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.model import StaffUser, Table
from app.routes.auth_routes import get_current_staff, require_admin
from app.schema import TableCreateRequest, TableResponse

router = APIRouter(prefix="/tables", tags=["Tables"])


@router.get("", response_model=list[TableResponse])
def list_tables(
    _: StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> list[TableResponse]:
    tables = db.query(Table).order_by(Table.name.asc(), Table.id.asc()).all()
    return [TableResponse.model_validate(table) for table in tables]


@router.post("", response_model=TableResponse, status_code=status.HTTP_201_CREATED)
def create_table(
    payload: TableCreateRequest,
    _: StaffUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> TableResponse:
    table = Table(name=payload.name)
    db.add(table)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Table name already exists") from exc
    db.refresh(table)
    return TableResponse.model_validate(table)


@router.put("/{table_id}", response_model=TableResponse)
def update_table(
    table_id: int,
    payload: TableCreateRequest,
    _: StaffUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> TableResponse:
    table = db.get(Table, table_id)
    if table is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")
    table.name = payload.name
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Table name already exists") from exc
    db.refresh(table)
    return TableResponse.model_validate(table)


@router.delete("/{table_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_table(
    table_id: int,
    _: StaffUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    table = db.get(Table, table_id)
    if table is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")
    db.delete(table)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Table cannot be deleted while it is used in games",
        ) from exc
