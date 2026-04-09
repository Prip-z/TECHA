from pydantic import BaseModel, ConfigDict
from app.model.game import GameStatus, GameResult

class GameResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    event_id: int
    table_id: int
    game_number: int
    status: GameStatus
    result: GameResult

class GameCreate(BaseModel):
    event_id: int
    table_id: int

class GamePlayerResponse(BaseModel):
    id: int
    game_id: int
    player_id: int

