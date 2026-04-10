from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.model import GameResult, GameStatus, ParticipantRole


class GameResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    game_id: int
    event_id: int
    table_id: int
    host_staff_id: int
    game_number: int
    status: GameStatus
    result: GameResult | None
    protests: str | None
    started_at: datetime | None
    finished_at: datetime | None


class GameCreateRequest(BaseModel):
    event_id: int
    table_id: int


class GameParticipantCreateRequest(BaseModel):
    player_id: int
    seat_number: int = Field(ge=1, le=10)


class GameParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    game_id: int
    player_id: int
    seat_number: int
    fouls: int
    score: float
    extra_score: float
    role: ParticipantRole
    is_alive: bool


class GameParticipantDetailResponse(BaseModel):
    id: int
    game_id: int
    player_id: int
    name: str
    nick: str
    seat_number: int
    fouls: int
    score: float
    extra_score: float
    role: ParticipantRole
    is_alive: bool


class GameParticipantUpdateRequest(BaseModel):
    seat_number: int | None = None
    fouls: int | None = Field(default=None, ge=0, le=4)
    score: float | None = None
    extra_score: float | None = None
    role: ParticipantRole | None = None
    is_alive: bool | None = None


class GameFinishRequest(BaseModel):
    confirm_word: str
    result: GameResult
    protests: str | None = None


class VoteDraftRequest(BaseModel):
    round: int
    nominations: list[int] = []
    votes: dict[str, int | str] = {}
    isTie: bool = False
    isRevote: bool = False
    liftApplied: bool = False


class ShotDraftRequest(BaseModel):
    round: int
    shooterSeat: int | None = None
    targetSeat: int | str | None = None


class TestamentDraftRequest(BaseModel):
    sourceSeat: int | None = None
    targetSeats: list[int] = []


class NightDraftRequest(BaseModel):
    round: int
    killedSeat: int | None = None
    notes: str = ""


class GameDraftExportRequest(BaseModel):
    stage: GameStatus | None = None
    roundNumber: int | None = None
    phase: str | None = None
    winner: GameResult | None = None
    protests: str | None = None
    votes: list[VoteDraftRequest] = []
    shots: list[ShotDraftRequest] = []
    testament: TestamentDraftRequest = TestamentDraftRequest()
    nights: list[NightDraftRequest] = []
