from pydantic import BaseModel, ConfigDict


class PlayerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    nick: str
    phone: str | None
    social_link: str | None


class PlayerListResponse(BaseModel):
    items: list[PlayerResponse]
    total: int

class PlayerCreateRequest(BaseModel):
    name: str
    nick: str
    phone: str | None
    social_link: str | None

