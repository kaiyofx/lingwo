"""
Сервис для Traefik ForwardAuth: доступ только из указанных стран.
Страна определяется по IP через GeoIP (MaxMind GeoLite2).
Клиентский IP берётся из X-Forwarded-For (первый в цепочке) или X-Real-IP.
"""
import os
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import geoip2.database

APP = FastAPI(title="Geo Check", version="0.1.0")

ALLOWED = set(os.environ.get("GEO_ALLOWED_COUNTRIES", "RU").upper().replace(" ", "").split(","))
ALLOW_UNKNOWN = os.environ.get("GEO_ALLOW_UNKNOWN", "0").strip() in ("1", "true", "yes")
DB_PATH = os.environ.get("GEOIP_DB_PATH", "/app/GeoLite2-Country.mmdb")

_reader = None


def _get_reader():
    global _reader
    if _reader is None:
        if not os.path.isfile(DB_PATH):
            raise FileNotFoundError(
                f"GeoIP database not found: {DB_PATH}. "
                "Download GeoLite2-Country.mmdb (e.g. from MaxMind) and mount it or set GEOIP_DB_PATH."
            )
        _reader = geoip2.database.Reader(DB_PATH)
    return _reader


def _country_by_ip(ip: str) -> str | None:
    if not ip or ip.strip() in ("", "unknown"):
        return None
    ip = ip.strip().split(",")[0].strip()
    try:
        r = _get_reader().country(ip)
        return (r.country.iso_code or "").upper() or None
    except (geoip2.errors.AddressNotFoundError, ValueError):
        return None
    except Exception:
        return None


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for") or request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.strip().split(",")[0].strip()
    return request.headers.get("x-real-ip") or request.headers.get("X-Real-IP") or request.client.host if request.client else None


@APP.get("/")
@APP.post("/")
@APP.get("/{_:path}")
@APP.post("/{_:path}")
async def check(request: Request):
    ip = _client_ip(request)
    if not ip:
        if ALLOW_UNKNOWN:
            return PlainTextResponse("OK", status_code=200)
        return PlainTextResponse("Forbidden: client IP unknown", status_code=403)

    country = _country_by_ip(ip)
    if country is None:
        if ALLOW_UNKNOWN:
            return PlainTextResponse("OK", status_code=200)
        return PlainTextResponse("Forbidden: country unknown", status_code=403)

    if country in ALLOWED:
        return PlainTextResponse("OK", status_code=200)
    return PlainTextResponse("Forbidden: access only from allowed countries", status_code=403)
