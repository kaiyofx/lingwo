import os
from pydantic import BaseModel
from jose import jwt, jwk, exceptions
from typing import Dict, Any
import asyncio
import httpx
from fastapi import HTTPException

JWKS_URL: str = os.environ.get("JWKS_URL", "http://localhost:8000/.well-known/jwks.json")


class Claims(BaseModel):
    exp: int
    iat: int
    jti: str
    user_id: str
    role: int
    email: str
    username: str
    token: str | None = None


_decoding_key_lock = asyncio.Lock()
_decoding_key_cache = None


async def get_decoding_key_rs256():
    """
    Асинхронно загружает и кэширует ключ JWKS.
    Гарантированно выполнится только один раз.
    """
    print(f"⏳ Fetching JWKS from: {JWKS_URL} (Первая и единственная загрузка)")

    global _decoding_key_cache
    if _decoding_key_cache is not None:
        return _decoding_key_cache

    async with _decoding_key_lock:
        if _decoding_key_cache is not None:
            return _decoding_key_cache

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(JWKS_URL)
                response.raise_for_status()

                jwks = response.json()
                jwk_data = next(
                    (
                        key
                        for key in jwks.get("keys", [])
                        if key.get("alg") == "RS256" and key.get("kty") == "RSA"
                    ),
                    None,
                )

                if jwk_data is None:
                    raise ValueError("Критическая ошибка: ключ RS256 не найден в JWKS.")

                public_key = jwk.construct(jwk_data)

                print("✅ JWT public key успешно загружен и возвращен.")
                _decoding_key_cache = public_key
                return public_key

        except Exception as e:
            print(f"🚨 КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить ключ JWKS: {e}")
            raise SystemExit(1)


async def decode_token_async(token_str: str) -> Claims:
    """Декодирует и валидирует токен, используя асинхронно полученный ключ."""

    decoding_key = await get_decoding_key_rs256()

    try:
        token_data: Dict[str, Any] = jwt.decode(
            token_str,
            decoding_key,
            algorithms=["RS256"],
            options={"verify_signature": True},
        )

        claims = Claims(**token_data)
        claims.token = token_str
        return claims

    except exceptions.JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Недействительный токен: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Внутренняя ошибка сервера при обработке токена",
        )
