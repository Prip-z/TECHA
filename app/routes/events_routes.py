from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.model import Event, EventPlayer, EventType, Game, StaffUser, Table, Player, StaffUser as StaffAccount
from app.routes.auth_routes import get_current_staff
from app.routes.sync_routes import broadcast_sync_event
from app.schema import EventAddPlayer, EventCreateRequest, EventGameItem, EventListResponse, EventPlayerResponse, EventResponse, EventRosterItem
from app.services.export_service import build_event_export
from io import BytesIO

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("", response_model=EventListResponse)
def list_events(
    mode: str = Query(default="all", pattern="^(all|dashboard)$"),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> EventListResponse:
    base_query = db.query(Event)

    if mode == "dashboard":
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        recent = (
            base_query.filter(Event.date < now)
            .order_by(Event.date.desc())
            .limit(3)
            .all()
        )
        upcoming = (
            base_query.filter(Event.date >= now)
            .order_by(Event.date.asc())
            .limit(3)
            .all()
        )
        items = list(reversed(recent)) + upcoming
        return EventListResponse(
            items=[EventResponse.model_validate(event) for event in items],
            total=len(items),
        )

    total_count = base_query.count()
    events = base_query.order_by(Event.date.desc(), Event.id.desc()).offset(offset).limit(limit).all()
    return EventListResponse(
        items=[EventResponse.model_validate(event) for event in events],
        total=total_count,
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=EventResponse)
def create_event(
    payload: EventCreateRequest,
    background_tasks: BackgroundTasks,
    _: StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> EventResponse:
    date = db.query(Event).filter(
        Event.date == payload.date,
    ).first()
    if date:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Event is already exist")
    event = Event(
        name=payload.name,
        date=payload.date,
        type=payload.type,
        price_per_game=0 if payload.type == EventType.tournament else payload.price_per_game,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    background_tasks.add_task(
        broadcast_sync_event,
        "dashboard",
        "event_updated",
        {"eventId": event.id, "reason": "event_created"},
    )
    return EventResponse.model_validate(event)


@router.put("/{event_id}", status_code=status.HTTP_200_OK, response_model=EventResponse)
def put_event(
    event_id: int,
    payload: EventCreateRequest,
    background_tasks: BackgroundTasks,
    _: StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> EventResponse:
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    event.name = payload.name
    event.date = payload.date
    event.type = payload.type
    event.price_per_game = 0 if payload.type == EventType.tournament else payload.price_per_game
    db.commit()
    db.refresh(event)
    background_tasks.add_task(
        broadcast_sync_event,
        "dashboard",
        "event_updated",
        {"eventId": event.id, "reason": "event_updated"},
    )
    background_tasks.add_task(
        broadcast_sync_event,
        f"event-{event.id}",
        "event_updated",
        {"eventId": event.id, "reason": "event_updated"},
    )
    return EventResponse.model_validate(event)


@router.post("/{event_id}/players", status_code=status.HTTP_201_CREATED, response_model=EventPlayerResponse)
def add_player(
    event_id: int,
    payload: EventAddPlayer,
    background_tasks: BackgroundTasks,
    _: StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> EventPlayerResponse:
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    existing = db.query(EventPlayer).filter(
        EventPlayer.event_id == event_id,
        EventPlayer.player_id == payload.player_id,
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Player already registered for this event")

    registration = EventPlayer(event_id=event_id, player_id=payload.player_id)
    db.add(registration)
    db.commit()
    db.refresh(registration)
    background_tasks.add_task(
        broadcast_sync_event,
        f"event-{event_id}",
        "event_updated",
        {"eventId": event_id, "reason": "player_added", "playerId": payload.player_id},
    )
    return EventPlayerResponse.model_validate(registration)


@router.get("/{event_id}/players", response_model=list[EventRosterItem])
def list_event_players(
    event_id: int,
    _: StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> list[EventRosterItem]:
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    rows = (
        db.query(EventPlayer, Player)
        .join(Player, Player.id == EventPlayer.player_id)
        .filter(EventPlayer.event_id == event_id)
        .order_by(Player.nick.asc(), Player.id.asc())
        .all()
    )
    return [
        EventRosterItem(
            id=registration.id,
            player_id=player.id,
            name=player.name,
            nick=player.nick,
            phone=player.phone,
            social_link=player.social_link,
            games_played=registration.games_played,
            paid_amount=registration.paid_amount,
        )
        for registration, player in rows
    ]


@router.get("/{event_id}/games", response_model=list[EventGameItem])
def list_event_games(
    event_id: int,
    _: StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> list[EventGameItem]:
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    rows = (
        db.query(Game, Table, StaffAccount)
        .join(Table, Table.id == Game.table_id)
        .join(StaffAccount, StaffAccount.id == Game.host_staff_id)
        .filter(Game.event_id == event_id)
        .order_by(Game.game_number.asc(), Game.game_id.asc())
        .all()
    )
    return [
        EventGameItem(
            game_id=game.game_id,
            game_number=game.game_number,
            table_id=table.id,
            table_name=table.name,
            host_staff_id=host.id,
            host_name=host.name,
            status=game.status.value,
            result=game.result.value if game.result else None,
        )
        for game, table, host in rows
    ]


@router.delete("/{event_id}/players/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player(
    event_id: int,
    player_id: int,
    background_tasks: BackgroundTasks,
    _: StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> None:
    registration = db.query(EventPlayer).filter(
        EventPlayer.event_id == event_id,
        EventPlayer.player_id == player_id,
    ).first()
    if registration is None:
        raise HTTPException(status_code=404, detail="Player is not registered for this event")
    if registration.games_played > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Player cannot be removed from the event after playing games",
        )

    db.delete(registration)
    db.commit()
    background_tasks.add_task(
        broadcast_sync_event,
        f"event-{event_id}",
        "event_updated",
        {"eventId": event_id, "reason": "player_removed", "playerId": player_id},
    )


@router.get("/{event_id}/export")
def export_event(
    event_id: int,
    _: StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    filename, content = build_event_export(db, event)
    return StreamingResponse(
        BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
