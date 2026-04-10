from pydantic import BaseModel


class AppSettingResponse(BaseModel):
    default_price_per_game: float


class UpdateAppSettingsRequest(BaseModel):
    default_price_per_game: float
