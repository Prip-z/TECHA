from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.model import Event, EventPlayer
from app.schema import EventListResponse, EventResponse, EventCreateRequest, EventAddPlayer, EventPlayerResponse

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=EventListResponse)
def list_events(
    limit: int = Query(default=10, ge=1, le=100), 
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> EventListResponse:
    query = db.query(Event)
    total_count = query.count()
    events = db.query(Event).offset(offset).limit(limit).all()
    
    return EventListResponse(
        items=[EventResponse.model_validate(event) for event in events],
        total=total_count
    )

@router.post("", status_code=status.HTTP_201_CREATED, response_model=EventResponse)
def create_event(payload: EventCreateRequest,db: Session = Depends(get_db)) -> EventResponse:
    event = Event(name = payload.name, date = payload.date, type = payload.type, price_per_game = payload.price_per_game)
    db.add(event)
    db.commit()

    db.refresh(event)
    return event

@router.put("/{event_id}", status_code=status.HTTP_200_OK, response_model=EventResponse)
def put_event(event_id: int, payload: EventCreateRequest, db: Session = Depends(get_db)) -> EventResponse:
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    event.name = payload.name
    event.date= payload.date
    event.type = payload.type
    event.price_per_game = payload.price_per_game
    db.commit()
    db.refresh(event)
    return event


@router.post("/{event_id}/players", status_code=status.HTTP_201_CREATED, response_model=EventAddPlayer)
def add_player(event_id: int, payload: EventAddPlayer, db: Session = Depends(get_db)) -> EventPlayerResponse:
    existing = db.query(EventPlayer).filter(
        EventPlayer.event_id == event_id,
        EventPlayer.player_id == payload.player_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Player already registered for this event")

    new_registration = EventPlayer(
        event_id=event_id, 
        player_id=payload.player_id
    )
    db.add(new_registration)
    db.commit()
    db.refresh(new_registration)
    
    return new_registration

@router.delete("/{event_id}/players/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player(event_id: int, player_id:int, db: Session = Depends(get_db)):
    registration = db.query(EventPlayer).filter(EventPlayer.event_id == event_id, EventPlayer.player_id == player_id).first()

    if not registration:
        raise HTTPException(status_code=404, detail="Nekogo udalyat")
    
    db.delete(registration)
    db.commit

    return None