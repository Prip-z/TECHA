from pydantic import BaseModel, ConfigDict


class TableResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class TableCreateRequest(BaseModel):
    name: str
