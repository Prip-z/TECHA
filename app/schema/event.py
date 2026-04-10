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


class EventRosterItem(BaseModel):
    id: int
    player_id: int
    name: str
    nick: str
    phone: str | None
    social_link: str | None
    games_played: int
    paid_amount: float


class EventGameItem(BaseModel):
    game_id: int
    game_number: int
    table_id: int
    table_name: str
    host_staff_id: int
    host_name: str
    status: str
    result: str | None
