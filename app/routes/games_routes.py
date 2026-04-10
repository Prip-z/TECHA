from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.model import Event, EventPlayer, EventType, Game, GameParticipant, GameStatus, ParticipantRole, Player, StaffRole, StaffUser, Table
from app.routes.auth_routes import get_current_staff
from app.routes.sync_routes import broadcast_sync_event
from app.schema import (
    GameDraftExportRequest,
    GameCreateRequest,
    GameFinishRequest,
    GameParticipantDetailResponse,
    GameParticipantCreateRequest,
    GameParticipantResponse,
    GameParticipantUpdateRequest,
    GameResponse,
)
from app.services.export_service import build_game_export
from io import BytesIO

router = APIRouter(prefix="/games", tags=["Games"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=GameResponse)
def create_game(
    payload: GameCreateRequest,
    background_tasks: BackgroundTasks,
    staff: StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> GameResponse:
    event = db.get(Event, payload.event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    table = db.get(Table, payload.table_id)
    if table is None:
        raise HTTPException(status_code=404, detail="Table not found")

    current_games_count = db.query(Game).filter(Game.event_id == payload.event_id).count()
    game = Game(
        event_id=payload.event_id,
        table_id=payload.table_id,
        host_staff_id=staff.id,
        game_number=current_games_count + 1,
        status=GameStatus.preparation,
    )
    db.add(game)
    db.commit()
    db.refresh(game)
    background_tasks.add_task(
        broadcast_sync_event,
        f"event-{payload.event_id}",
        "event_updated",
        {"eventId": payload.event_id, "reason": "game_created", "gameId": game.game_id},
    )
    return GameResponse.model_validate(game)


@router.get("/{game_id}", status_code=status.HTTP_200_OK, response_model=GameResponse)
def get_game(
    game_id: int,
    _: StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> GameResponse:
    game = db.get(Game, game_id)
    if game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return GameResponse.model_validate(game)


@router.get("/{game_id}/participants", response_model=list[GameParticipantDetailResponse])
def list_game_participants(
    game_id: int,
    _: StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> list[GameParticipantDetailResponse]:
    game = db.get(Game, game_id)
    if game is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    rows = (
        db.query(GameParticipant, Player)
        .join(Player, Player.id == GameParticipant.player_id)
        .filter(GameParticipant.game_id == game_id)
        .order_by(GameParticipant.seat_number.asc(), GameParticipant.id.asc())
        .all()
    )
    return [
        GameParticipantDetailResponse(
            id=participant.id,
            game_id=participant.game_id,
            player_id=player.id,
            name=player.name,
            nick=player.nick,
            seat_number=participant.seat_number,
            fouls=participant.fouls,
            score=participant.score,
            extra_score=participant.extra_score,
            role=participant.role,
            is_alive=participant.is_alive,
        )
        for participant, player in rows
    ]


@router.post("/{game_id}/participants", status_code=status.HTTP_201_CREATED, response_model=GameParticipantResponse)
def add_player_to_game(
    game_id: int,
    payload: GameParticipantCreateRequest,
    background_tasks: BackgroundTasks,
    _: StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> GameParticipantResponse:
    game = db.get(Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.status != GameStatus.preparation:
        raise HTTPException(status_code=400, detail="Participants can only be changed before the game starts")

    event_registration = db.query(EventPlayer).filter(
        EventPlayer.event_id == game.event_id,
        EventPlayer.player_id == payload.player_id,
    ).first()
    if event_registration is None:
        raise HTTPException(status_code=400, detail="Player must be added to the event before joining a game")

    existing = db.query(GameParticipant).filter(
        GameParticipant.game_id == game_id,
        GameParticipant.player_id == payload.player_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Player already added to this game")

    participant = GameParticipant(
        game_id=game_id,
        player_id=payload.player_id,
        seat_number=payload.seat_number,
        role=ParticipantRole.civilian,
        is_alive=True,
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)
    background_tasks.add_task(
        broadcast_sync_event,
        f"game-{game_id}",
        "game_updated",
        {"gameId": game_id, "reason": "participant_added", "participantId": participant.id},
    )
    return GameParticipantResponse.model_validate(participant)


@router.put("/{game_id}/participants/{participant_id}", response_model=GameParticipantResponse)
def update_player_in_game(
    game_id: int,
    participant_id: int,
    payload: GameParticipantUpdateRequest,
    background_tasks: BackgroundTasks,
    staff: StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> GameParticipantResponse:
    participant = db.get(GameParticipant, participant_id)
    if participant is None or participant.game_id != game_id:
        raise HTTPException(status_code=404, detail="Participant not found in this game")
    game = db.get(Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    if payload.seat_number is not None:
        if game.status != GameStatus.preparation:
            raise HTTPException(status_code=400, detail="Seats can only be changed before the game starts")
        seat_taken = db.query(GameParticipant).filter(
            GameParticipant.game_id == game_id,
            GameParticipant.seat_number == payload.seat_number,
            GameParticipant.id != participant_id,
        ).first()
        if seat_taken:
            raise HTTPException(status_code=409, detail="Seat number already taken")
        participant.seat_number = payload.seat_number
    if payload.fouls is not None:
        if game.status == GameStatus.finished and staff.role != StaffRole.admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin can edit fouls after the game is finished",
            )
        participant.fouls = payload.fouls
        if participant.fouls >= 4:
            participant.is_alive = False
            participant.extra_score = -0.7
    if payload.score is not None:
        participant.score = payload.score
    if payload.extra_score is not None:
        participant.extra_score = payload.extra_score
    if payload.role is not None:
        if game.status != GameStatus.finished:
            raise HTTPException(status_code=400, detail="Roles can only be edited after the game is finished")
        participant.role = payload.role
    if payload.is_alive is not None:
        participant.is_alive = payload.is_alive

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Failed to update participant") from exc
    db.refresh(participant)
    background_tasks.add_task(
        broadcast_sync_event,
        f"game-{game_id}",
        "game_updated",
        {"gameId": game_id, "reason": "participant_updated", "participantId": participant_id},
    )
    return GameParticipantResponse.model_validate(participant)


@router.delete("/{game_id}/participants/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_player_from_game(
    game_id: int,
    participant_id: int,
    background_tasks: BackgroundTasks,
    _: StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> None:
    participant = db.get(GameParticipant, participant_id)
    if participant is None or participant.game_id != game_id:
        raise HTTPException(status_code=404, detail="Participant not found in this game")
    game = db.get(Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.status != GameStatus.preparation:
        raise HTTPException(status_code=400, detail="Participants can only be removed before the game starts")
    db.delete(participant)
    db.commit()
    background_tasks.add_task(
        broadcast_sync_event,
        f"game-{game_id}",
        "game_updated",
        {"gameId": game_id, "reason": "participant_removed", "participantId": participant_id},
    )


@router.post("/{game_id}/start", response_model=GameResponse)
def start_game(
    game_id: int,
    background_tasks: BackgroundTasks,
    _: StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> GameResponse:
    game = db.get(Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.status != GameStatus.preparation:
        raise HTTPException(status_code=400, detail="Game is already started")

    participants = db.query(GameParticipant).filter(GameParticipant.game_id == game_id).all()
    if not participants:
        raise HTTPException(status_code=400, detail="Game must have at least one participant to start")

    seats = [participant.seat_number for participant in participants]
    if any(seat < 1 or seat > 10 for seat in seats):
        raise HTTPException(status_code=400, detail="All participants must have a seat number from 1 to 10")
    if len(set(seats)) != len(seats):
        raise HTTPException(status_code=409, detail="Seat numbers must be unique inside one game")

    event = db.get(Event, game.event_id)
    registrations = db.query(EventPlayer).filter(EventPlayer.event_id == game.event_id).all()
    registrations_by_player_id = {registration.player_id: registration for registration in registrations}
    for participant in participants:
        registration = registrations_by_player_id.get(participant.player_id)
        if registration is None:
            raise HTTPException(status_code=400, detail="Every participant must belong to the event")
        registration.games_played += 1
        if event is not None and event.type == EventType.tournament:
            registration.paid_amount = 0
        elif event is not None:
            registration.paid_amount = round(registration.games_played * event.price_per_game, 2)

    game.status = GameStatus.voting
    game.started_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(game)
    background_tasks.add_task(
        broadcast_sync_event,
        f"game-{game_id}",
        "game_updated",
        {"gameId": game_id, "reason": "game_started"},
    )
    background_tasks.add_task(
        broadcast_sync_event,
        f"event-{game.event_id}",
        "event_updated",
        {"eventId": game.event_id, "reason": "game_started", "gameId": game_id},
    )
    return GameResponse.model_validate(game)


@router.post("/{game_id}/finish", response_model=GameResponse)
def finish_game(
    game_id: int,
    payload: GameFinishRequest,
    background_tasks: BackgroundTasks,
    staff: StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> GameResponse:
    game = db.get(Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    if staff.role not in {StaffRole.admin, StaffRole.super_admin}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can finish the game")
    if game.status == GameStatus.finished:
        raise HTTPException(status_code=400, detail="Game is already finished")
    if payload.confirm_word.strip().lower() != "\u0437\u0430\u0432\u0435\u0440\u0448\u0438\u0442\u044c":
        raise HTTPException(status_code=400, detail="Finish confirmation word is invalid")

    game.status = GameStatus.finished
    game.result = payload.result
    game.protests = payload.protests
    game.finished_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(game)
    background_tasks.add_task(
        broadcast_sync_event,
        f"game-{game_id}",
        "game_updated",
        {"gameId": game_id, "reason": "game_finished"},
    )
    background_tasks.add_task(
        broadcast_sync_event,
        f"event-{game.event_id}",
        "event_updated",
        {"eventId": game.event_id, "reason": "game_finished", "gameId": game_id},
    )
    return GameResponse.model_validate(game)


@router.get("/{game_id}/export")
def export_game(
    game_id: int,
    _: StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    game = db.get(Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    filename, content = build_game_export(db, game)
    return StreamingResponse(
        BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{game_id}/export")
def export_game_from_draft(
    game_id: int,
    payload: GameDraftExportRequest,
    _: StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    game = db.get(Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    filename, content = build_game_export(db, game, payload)
    return StreamingResponse(
        BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
