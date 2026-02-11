import asyncio
import logging
import os
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

if __name__ == "__main__" and __package__ is None:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[1]))

from contextlib import asynccontextmanager
from chromadb import Settings, HttpClient  # type: ignore
from dotenv import load_dotenv
import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import AsyncSessionLocal, get_session, init_db
from api.essay_eval import evaluate_essay_sync, validate_theme_sync
from api.jwt_auth import Claims, decode_token_async
from api.models import Essay, UserSettings
from api.rate_limit import check_model_rate_limit
from api.redis_client import redis_client
from api.schemas import (
    EssayDetailResponse,
    EssayEndRequest,
    EssayEndResponse,
    EssayListItem,
    EssaySaveRequest,
    EssayStartRequest,
    EssayState,
    RandomTopicResponse,
    UserSettingsResponse,
    UserSettingsUpdate,
    ValidateThemeRequest,
    ValidateThemeResponse,
)

load_dotenv()

CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "4200"))
THEMES_PATH = os.getenv("THEMES_PATH")
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8001"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    try:
        await redis_client.ping()
    except Exception as exc:
        raise RuntimeError(f"Redis недоступен: {exc}") from exc
    yield


APP = FastAPI(title="Lingwo API", version="0.1.0", lifespan=lifespan)
security = HTTPBearer(
    scheme_name="JWT Bearer Token",
    description="Введите JWT-токен в формате 'Bearer <token>'",
)

APP.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_cached_themes: Optional[List[str]] = None


async def get_current_user(
    auth: HTTPAuthorizationCredentials = Security(security),
) -> Claims:
    try:
        claims = await decode_token_async(auth.credentials)
        return claims
    except Exception:
        raise HTTPException(
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_model_rate_limit(claim: Claims = Depends(get_current_user)) -> None:
    """Зависимость: проверка лимита запросов к модели (тема + оценка), 429 при превышении."""
    if claim and claim.user_id:
        await check_model_rate_limit(claim.user_id)


def _get_themes_path() -> Path:
    if THEMES_PATH:
        return Path(THEMES_PATH)
    repo_root = Path(__file__).resolve().parents[1]
    return repo_root / "chroma" / "all_themes.txt"


def _load_all_themes() -> List[str]:
    global _cached_themes
    if _cached_themes is not None:
        return _cached_themes

    themes_file = _get_themes_path()
    if not themes_file.exists():
        raise FileNotFoundError(f"Темы не найдены: {themes_file}")

    themes: List[str] = []
    with themes_file.open("r", encoding="utf8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            if "." in line:
                line = line[line.index(".") + 1 :].strip()
            if line:
                themes.append(line)

    if not themes:
        raise ValueError("Список тем пуст.")

    _cached_themes = themes
    return themes


def _get_chroma_collection():
    client = HttpClient(
        host=CHROMA_HOST,
        port=CHROMA_PORT,
        settings=Settings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection(name="themes")


def _random_theme_from_sections(sections: List[str]) -> str:
    collection = _get_chroma_collection()
    result = collection.query(query_texts=sections, n_results=60)
    docs = result.get("documents", [])
    flat_docs = [doc for group in docs for doc in group if doc]
    if not flat_docs:
        return random.choice(_load_all_themes())
    return random.choice(flat_docs)


def _redis_key(user_id: str) -> str:
    return f"essay:active:{user_id}"


@APP.get("/health")
async def health():
    return {"status": "OK"}


@APP.get("/settings", response_model=UserSettingsResponse)
async def get_settings(
    claim: Claims = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if claim is None or claim.token is None:
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"})

    result = await session.execute(select(UserSettings).where(UserSettings.user_id == claim.user_id))
    row = result.scalar_one_or_none()
    if not row:
        return UserSettingsResponse(target_percent=70, auto_save_enabled=True, auto_save_interval_sec=30)
    return UserSettingsResponse(
        target_percent=row.target_percent,
        auto_save_enabled=row.auto_save_enabled,
        auto_save_interval_sec=row.auto_save_interval_sec,
    )


@APP.patch("/settings", response_model=UserSettingsResponse)
async def patch_settings(
    payload: UserSettingsUpdate,
    claim: Claims = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if claim is None or claim.token is None:
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"})

    result = await session.execute(select(UserSettings).where(UserSettings.user_id == claim.user_id))
    row = result.scalar_one_or_none()
    if not row:
        row = UserSettings(
            user_id=claim.user_id,
            target_percent=70,
            auto_save_enabled=True,
            auto_save_interval_sec=30,
        )
        session.add(row)
    if payload.target_percent is not None:
        row.target_percent = payload.target_percent
    if payload.auto_save_enabled is not None:
        row.auto_save_enabled = payload.auto_save_enabled
    if payload.auto_save_interval_sec is not None:
        row.auto_save_interval_sec = payload.auto_save_interval_sec
    await session.commit()
    await session.refresh(row)
    return UserSettingsResponse(
        target_percent=row.target_percent,
        auto_save_enabled=row.auto_save_enabled,
        auto_save_interval_sec=row.auto_save_interval_sec,
    )


@APP.get("/random_topic", response_model=RandomTopicResponse)
async def random_topic(
    sections: Optional[str] = Query(
        default=None,
        description="Разделы через | (до 3), например: Человек|Война|Духовный мир",
    ),
    claim: Claims = Depends(get_current_user),
):
    if claim is None or claim.token is None:
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"})

    if sections:
        section_list = [s.strip() for s in sections.split("|") if s.strip()]
        if len(section_list) > 3:
            raise HTTPException(status_code=400, detail="Допустимо не более 3 разделов.")
        theme = _random_theme_from_sections(section_list)
    else:
        theme = random.choice(_load_all_themes())

    return RandomTopicResponse(theme=theme)


@APP.post("/essay/start", response_model=EssayState)
@APP.post("/start_essay", response_model=EssayState)
async def start_essay(
    payload: EssayStartRequest,
    _: None = Depends(require_model_rate_limit),
    claim: Claims = Depends(get_current_user),
):
    if claim is None or claim.token is None:
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"})

    # Проверка темы для «своей» темы; не проверяем только при явных recommended/random.
    # Если theme_source не передан (None) — тоже проверяем, иначе повторная отправка могла бы пройти без проверки.
    if payload.theme_source not in ("recommended", "random"):
        try:
            result = await asyncio.to_thread(validate_theme_sync, payload.theme.strip())
            if not result.get("valid", True):
                raise HTTPException(
                    status_code=400,
                    detail=result.get("message", "Тема не прошла проверку."),
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("start_essay validate_theme: %s", e)
            raise HTTPException(status_code=500, detail="Не удалось проверить тему.")

    existing = await redis_client.get(_redis_key(claim.user_id))
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Активное сочинение уже существует.",
        )

    state = EssayState(
        user_id=claim.user_id,
        type=payload.type,
        theme=payload.theme,
        text="",
        started_at=datetime.now(timezone.utc),
    )
    await redis_client.set(_redis_key(claim.user_id), state.model_dump_json())
    return state


@APP.post("/essay/clear")
async def clear_essay(
    claim: Claims = Depends(get_current_user),
):
    """Завершить без результатов: удалить активное сочинение из Redis."""
    if claim is None or claim.token is None:
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"})
    await redis_client.delete(_redis_key(claim.user_id))
    return {"ok": True}


@APP.post("/essay/validate_theme", response_model=ValidateThemeResponse)
async def validate_theme(
    payload: ValidateThemeRequest,
    _: None = Depends(require_model_rate_limit),
    claim: Claims = Depends(get_current_user),
):
    """Проверка темы сочинения: осмысленная формулировка (ИИ)."""
    if claim is None or claim.token is None:
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"})
    try:
        result = await asyncio.to_thread(validate_theme_sync, payload.theme.strip())
        return ValidateThemeResponse(valid=result["valid"], message=result.get("message", ""))
    except Exception as e:
        logger.exception("validate_theme: %s", e)
        raise HTTPException(status_code=500, detail="Не удалось проверить тему.")


@APP.get("/essay", response_model=EssayState)
@APP.get("/essay/save", response_model=EssayState)
async def get_current_essay(
    claim: Claims = Depends(get_current_user),
):
    if claim is None or claim.token is None:
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"})

    data = await redis_client.get(_redis_key(claim.user_id))
    if not data:
        raise HTTPException(status_code=404, detail="Активное сочинение не найдено.")
    return EssayState.model_validate_json(data)


@APP.post("/essay/save", response_model=EssayState)
@APP.post("/save_essay", response_model=EssayState)
async def save_essay(
    payload: EssaySaveRequest,
    claim: Claims = Depends(get_current_user),
):
    if claim is None or claim.token is None:
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"})

    data = await redis_client.get(_redis_key(claim.user_id))
    if not data:
        raise HTTPException(status_code=404, detail="Активное сочинение не найдено.")

    state = EssayState.model_validate_json(data)
    state.text = payload.text
    await redis_client.set(_redis_key(claim.user_id), state.model_dump_json())
    return state


logger = logging.getLogger(__name__)


async def _evaluate_essay_task(essay_id: int) -> None:
    """Фоновая задача: оценить сочинение локальной моделью и обновить запись в БД."""
    async with AsyncSessionLocal() as session:
        essay = await session.get(Essay, essay_id)
        if not essay:
            logger.warning("essay_eval: сочинение %s не найдено", essay_id)
            return
        theme, text, essay_type = essay.theme, essay.text, (essay.essay_type or "essay")
    logger.info("essay_eval: старт оценки сочинения %s (type=%s, theme=%s, len=%s)", essay_id, essay_type, theme[:50], len(text))
    try:
        result = await asyncio.to_thread(evaluate_essay_sync, theme, text, essay_type)
    except Exception as e:
        logger.exception("essay_eval: ошибка оценки сочинения %s: %s", essay_id, e)
        return
    logger.info("essay_eval: оценка готова для %s, total_score=%s", essay_id, result.get("total_score"))
    async with AsyncSessionLocal() as session:
        essay = await session.get(Essay, essay_id)
        if not essay:
            logger.warning("essay_eval: сочинение %s не найдено при сохранении", essay_id)
            return
        essay.criteries = result["criteries"]
        essay.common_mistakes = result["common_mistakes"]
        essay.max_score = result["max_score"]
        essay.total_score = result["total_score"]
        essay.total_score_per = result.get("total_score_per")
        session.add(essay)
        await session.commit()
    logger.info("essay_eval: сочинение %s сохранено", essay_id)


@APP.post("/essay/end", response_model=EssayEndResponse)
@APP.post("/end_essay", response_model=EssayEndResponse)
async def end_essay(
    payload: EssayEndRequest,
    background_tasks: BackgroundTasks,
    _: None = Depends(require_model_rate_limit),
    claim: Claims = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if claim is None or claim.token is None:
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"})

    data = await redis_client.get(_redis_key(claim.user_id))
    if not data:
        raise HTTPException(status_code=404, detail="Активное сочинение не найдено.")

    state = EssayState.model_validate_json(data)
    state.text = payload.text
    ended_at = datetime.now(timezone.utc)

    essay = Essay(
        user_id=state.user_id,
        essay_type=state.type,
        theme=state.theme,
        text=state.text,
        started_at=state.started_at,
        ended_at=ended_at,
        total_score=0.0,
        total_score_per=None,
        max_score=None,
        criteries={},
        common_mistakes=[],
    )
    session.add(essay)
    await session.commit()
    await session.refresh(essay)

    await redis_client.delete(_redis_key(claim.user_id))

    background_tasks.add_task(_evaluate_essay_task, essay.id)

    return EssayEndResponse(
        id=essay.id,
        user_id=essay.user_id,
        type=essay.essay_type,
        theme=essay.theme,
        text=essay.text,
        started_at=essay.started_at,
        ended_at=essay.ended_at,
        total_score=essay.total_score,
        total_score_per=essay.total_score_per,
        max_score=essay.max_score,
        criteries=essay.criteries or {},
        common_mistakes=essay.common_mistakes or [],
    )


@APP.get("/essays")
async def list_essays(
    claim: Claims = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(100, ge=1, le=200),
    search: Optional[str] = Query(None, description="Поиск по теме или тексту сочинения"),
    type_filter: Optional[str] = Query(None, description="Тип: essay или ege"),
    order: str = Query("date", description="Сортировка: date, score, theme"),
) -> list[dict]:
    """Список сочинений текущего пользователя. Поле excerpt — первые 150 символов текста."""
    if claim is None or claim.token is None:
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"})

    q = select(Essay).where(Essay.user_id == claim.user_id)
    if type_filter in ("essay", "ege"):
        q = q.where(Essay.essay_type == type_filter)
    if order == "score":
        q = q.order_by(Essay.total_score.desc().nulls_last(), Essay.ended_at.desc())
    elif order == "theme":
        q = q.order_by(Essay.theme.asc(), Essay.ended_at.desc())
    else:
        q = q.order_by(Essay.ended_at.desc())
    q = q.limit(limit * 2 if search else limit)
    result = await session.execute(q)
    rows = result.scalars().all()

    out: list[dict] = []
    for e in rows:
        text = (e.text or "")[:150]
        if search:
            search_lower = search.strip().lower()
            if search_lower and search_lower not in (e.theme or "").lower() and search_lower not in (e.text or "").lower():
                continue
        raw_crit = getattr(e, "criteries", None)
        if raw_crit is None:
            criteries: dict = {}
        elif isinstance(raw_crit, dict):
            criteries = raw_crit
        else:
            criteries = dict(raw_crit) if raw_crit else {}
        out.append({
            "id": e.id,
            "type": e.essay_type,
            "theme": e.theme,
            "ended_at": e.ended_at,
            "total_score": e.total_score,
            "total_score_per": e.total_score_per,
            "max_score": e.max_score,
            "criteries": criteries,
            "excerpt": text,
        })
        if len(out) >= limit:
            break
    return out


@APP.delete("/essay/{essay_id}")
async def delete_essay(
    essay_id: int,
    claim: Claims = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Удалить сочинение текущего пользователя."""
    if claim is None or claim.token is None:
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"})

    result = await session.execute(select(Essay).where(Essay.id == essay_id, Essay.user_id == claim.user_id))
    essay = result.scalar_one_or_none()
    if not essay:
        raise HTTPException(status_code=404, detail="Сочинение не найдено.")
    await session.delete(essay)
    await session.commit()
    return {"ok": True}


@APP.get("/essay/{essay_id}", response_model=EssayDetailResponse)
async def get_essay(
    essay_id: int,
    claim: Claims = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Получить сочинение по id (для опроса результата оценки после POST /essay/end)."""
    if claim is None or claim.token is None:
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"})

    result = await session.execute(select(Essay).where(Essay.id == essay_id, Essay.user_id == claim.user_id))
    essay = result.scalar_one_or_none()
    if not essay:
        raise HTTPException(status_code=404, detail="Сочинение не найдено.")

    return EssayDetailResponse(
        id=essay.id,
        user_id=essay.user_id,
        type=essay.essay_type,
        theme=essay.theme,
        text=essay.text,
        started_at=essay.started_at,
        ended_at=essay.ended_at,
        total_score=essay.total_score,
        total_score_per=essay.total_score_per,
        max_score=essay.max_score,
        criteries=essay.criteries or {},
        common_mistakes=essay.common_mistakes or [],
    )


if __name__ == "__main__":
    uvicorn.run("api.main:APP", host=API_HOST, port=API_PORT, reload=False)
