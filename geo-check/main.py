"""
Сервис для Traefik ForwardAuth: разрешает доступ только из указанных стран.
Ожидает заголовок CF-IPCountry (Cloudflare) или X-Country-Code.
По умолчанию разрешена только Россия (RU). При отсутствии заголовка
поведение задаётся GEO_ALLOW_UNKNOWN (0 = запретить, 1 = разрешить для разработки).
"""
import os
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

APP = FastAPI(title="Geo Check", version="0.1.0")

ALLOWED = set(os.environ.get("GEO_ALLOWED_COUNTRIES", "RU").upper().replace(" ", "").split(","))
ALLOW_UNKNOWN = os.environ.get("GEO_ALLOW_UNKNOWN", "0").strip() in ("1", "true", "yes")


@APP.get("/")
@APP.post("/")
@APP.get("/{_:path}")
@APP.post("/{_:path}")
async def check(request: Request):
    country = (
        request.headers.get("cf-ipcountry")
        or request.headers.get("CF-IPCountry")
        or request.headers.get("x-country-code")
        or request.headers.get("X-Country-Code")
        or ""
    ).upper().strip() or None

    if country is None:
        if ALLOW_UNKNOWN:
            return PlainTextResponse("OK", status_code=200)
        return PlainTextResponse("Forbidden: country unknown", status_code=403)

    if country in ALLOWED:
        return PlainTextResponse("OK", status_code=200)
    return PlainTextResponse("Forbidden: access only from allowed countries", status_code=403)
