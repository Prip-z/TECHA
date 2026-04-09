from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.model import Event, EventPlayer, EventType, StaffUser
from app.routes.auth_routes import get_current_staff
from app.schema import EventAddPlayer, EventCreateRequest, EventListResponse, EventPlayerResponse, EventResponse
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
    _: StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
) -> EventResponse:
    event = Event(
        name=payload.name,
        date=payload.date,
        type=payload.type,
        price_per_game=0 if payload.type == EventType.tournament else payload.price_per_game,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return EventResponse.model_validate(event)


@router.put("/{event_id}", status_code=status.HTTP_200_OK, response_model=EventResponse)
def put_event(
    event_id: int,
    payload: EventCreateRequest,
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
    return EventResponse.model_validate(event)


@router.post("/{event_id}/players", status_code=status.HTTP_201_CREATED, response_model=EventPlayerResponse)
def add_player(
    event_id: int,
    payload: EventAddPlayer,
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
    return EventPlayerResponse.model_validate(registration)


@router.delete("/{event_id}/players/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player(
    event_id: int,
    player_id: int,
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
