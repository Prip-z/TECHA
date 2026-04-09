from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.model import EventType


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: datetime
    type: EventType
    price_per_game: float


class EventListResponse(BaseModel):
    items: list[EventResponse]
    total: int


class EventCreateRequest(BaseModel):
    name: str
    date: datetime
    type: EventType
    price_per_game: float


class EventAddPlayer(BaseModel):
    player_id: int


class EventPlayerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    player_id: int
    games_played: int
    paid_amount: float
