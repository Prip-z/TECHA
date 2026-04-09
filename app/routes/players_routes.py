from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.model import Player, StaffUser
from app.routes.auth_routes import get_current_staff
from app.schema import PlayerCreateRequest, PlayerListResponse, PlayerResponse

router = APIRouter(prefix="/players", tags=["Players"])


@router.get("", response_model=PlayerListResponse)
def list_players(
    search: str | None = Query(default=None, min_length=1),
    _: StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> PlayerListResponse:
    query = db.query(Player)

    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Player.name.ilike(pattern),
                Player.nick.ilike(pattern),
            )
        )

    players = query.order_by(Player.nick.asc(), Player.id.asc()).all()
    return PlayerListResponse(
        items=[PlayerResponse.model_validate(player) for player in players],
        total=len(players),
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PlayerResponse)
def create_player(
    payload: PlayerCreateRequest,
    _: StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> PlayerResponse:
    player = Player(
        name=payload.name,
        nick=payload.nick,
        phone=payload.phone,
        social_link=payload.social_link,
    )
    db.add(player)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Player with this nick already exists",
        ) from exc

    db.refresh(player)
    return PlayerResponse.model_validate(player)


@router.put("/{player_id}", status_code=status.HTTP_200_OK, response_model=PlayerResponse)
def put_player(
    player_id: int,
    payload: PlayerCreateRequest,
    _: StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> PlayerResponse:
    player = db.get(Player, player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    player.name = payload.name
    player.nick = payload.nick
    player.phone = payload.phone
    player.social_link = payload.social_link
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Player with this nick already exists",
        ) from exc
    db.refresh(player)
    return PlayerResponse.model_validate(player)
