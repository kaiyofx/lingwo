from datetime import datetime
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field


class UserSettingsResponse(BaseModel):
    target_percent: int = Field(..., ge=0, le=100, description="Целевой процент выполнения 0–100")
    auto_save_enabled: bool = True
    auto_save_interval_sec: int = Field(..., ge=10, le=120)


class UserSettingsUpdate(BaseModel):
    target_percent: Optional[int] = Field(None, ge=0, le=100)
    auto_save_enabled: Optional[bool] = None
    auto_save_interval_sec: Optional[int] = Field(None, ge=10, le=120)


class ValidateThemeRequest(BaseModel):
    theme: str = Field(..., min_length=1, max_length=512)


class ValidateThemeResponse(BaseModel):
    valid: bool
    message: str = ""


class RandomTopicResponse(BaseModel):
    theme: str


class EssayStartRequest(BaseModel):
    theme: str = Field(..., min_length=1, max_length=512)
    type: Literal["ege", "essay"]
    theme_source: Optional[Literal["recommended", "random", "own"]] = None  # только при "own" проверяем тему


class EssaySaveRequest(BaseModel):
    text: str = Field(..., min_length=1)


class EssayEndRequest(BaseModel):
    """Текст сочинения. criteries заполняются на бэкенде после оценки."""
    text: str = Field(..., min_length=1)


class EssayListItem(BaseModel):
    """Элемент списка сочинений для GET /essays."""
    id: int
    type: str
    theme: str
    ended_at: datetime
    total_score: float
    total_score_per: Optional[float] = None
    max_score: Optional[float] = None
    criteries: Dict[str, Any] = Field(default_factory=dict, description="Критерии оценки k1–k5 (essay) или K1–K10 (ege)")


class EssayDetailResponse(BaseModel):
    """Ответ для GET /essay/{id} — сочинение с результатом оценки (для опроса после /essay/end)."""
    id: int
    user_id: str
    type: str
    theme: str
    text: str
    started_at: datetime
    ended_at: datetime
    total_score: float  # сырые баллы (сумма по критериям)
    total_score_per: Optional[float] = None  # доля от максимума 0–1
    max_score: Optional[float] = None
    criteries: Dict[str, Any] = Field(default_factory=dict)
    common_mistakes: list = Field(default_factory=list)


class EssayState(BaseModel):
    user_id: str
    type: str
    theme: str
    text: str
    started_at: datetime


class EssayEndResponse(BaseModel):
    id: int
    user_id: str
    type: str
    theme: str
    text: str
    started_at: datetime
    ended_at: datetime
    total_score: float  # сырые баллы
    total_score_per: Optional[float] = None  # доля 0–1
    max_score: Optional[float] = None
    criteries: Dict[str, Any] = Field(default_factory=dict)
    common_mistakes: list = Field(default_factory=list)