"""
Оценка сочинения через Pollinations API (по умолчанию gemini-fast).
Тип essay: итоговое сочинение (k1–k5, зачет/незачет = 0 или 1, макс 5). Тип ege: ЕГЭ задание 27 (K1–K10, макс 22).
Возвращает criteries, common_mistakes, max_score, total_score (сырые баллы), total_score_per (0–1).
"""
import json
import logging
import os
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

POLLINATIONS_BASE_URL = os.getenv("POLLINATIONS_BASE_URL", "https://gen.pollinations.ai").rstrip("/")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")
POLLINATIONS_MODEL = os.getenv("POLLINATIONS_MODEL", "gemini-fast")

# Итоговое сочинение: по каждому критерию только «зачет» (1) или «незачет» (0), макс 5 баллов
PROMPT_ESSAY = """Ты — эксперт по проверке итоговых сочинений. По каждому из 5 критериев выставляется только «зачет» или «незачет». В JSON для каждого критерия укажи score: 1 (зачет) или 0 (незачет).

Критерии:
k1 — Соответствие теме. «Незачет» только если сочинение не по теме, нет ответа на вопрос или нет цели высказывания. Иначе «зачет».
k2 — Аргументация. Привлечение литературного материала. «Незачет» если нет аргументации, нет опоры на литературу, существенно искажён текст или примеры не подкрепляют аргументы. Иначе «зачет».
k3 — Композиция и логика рассуждения. «Незачет» если грубые логические нарушения мешают пониманию или нет тезисно-доказательной части. Иначе «зачет».
k4 — Качество письменной речи. «Незачет» если низкое качество речи существенно затрудняет понимание. Иначе «зачет».
k5 — Грамотность. «Незачет» если на 100 слов в среднем более 5 ошибок (орфография, пунктуация, грамматика). Иначе «зачет».

Для зачета за работу в целом нужны зачет по k1 и k2 и плюс зачет хотя бы по одному из k3 или k4. Критерий k5 учитывается отдельно.

Выяви ошибки по четырём типам (указывай строго эти латинские ключи):
- punctuation — пунктуация (запятые, точки, тире и т.п.)
- spelling — орфография (неправильное написание слова)
- grammar — грамматика (род, число, падеж, спряжение и т.п.)
- style — речевые ошибки (повторы, неудачное слово, нарушение норм)

Для каждого типа укажи массив fragments: точные цитаты из текста сочинения — подстроки, в которых допущена ошибка. Копируй фрагменты буквально из текста (слово или короткую фразу). Не придумывай индексы — только fragments.

Используй только для входа только текст сочинения, никаких других данных. Сам ничего не добавляй. В полях comment пиши кратко, в одну строку; внутри JSON не используй переносы строк в строках.

Ответь ТОЛЬКО валидным JSON без markdown. У каждого критерия score — только 0 или 1:
{{"criteries": {{"k1": {{"score": 0 или 1, "comment": "...", "found_in_text": []}}, "k2": {{"score": 0 или 1, "comment": "...", "suggestions": []}}, "k3": {{"score": 0 или 1, "comment": "..."}}, "k4": {{"score": 0 или 1, "comment": "..."}}, "k5": {{"score": 0 или 1, "comment": "..."}}}}, "common_mistakes": [{{"type": "punctuation", "count": N, "fragments": ["цитата из текста"]}}, {{"type": "spelling", "count": N, "fragments": ["слово с ошибкой"]}}, {{"type": "grammar", "count": N, "fragments": ["фраза с ошибкой"]}}, {{"type": "style", "count": N, "fragments": []}}]}}

Тема: {theme}

Текст сочинения:
{text}
"""

# ЕГЭ задание 27: K1–K10, макс 22 балла
EGE_MAX_BY_CRITERION = {"k1": 1, "k2": 3, "k3": 2, "k4": 1, "k5": 2, "k6": 1, "k7": 3, "k8": 3, "k9": 3, "k10": 3}
EGE_MAX_SCORE = sum(EGE_MAX_BY_CRITERION.values())

PROMPT_EGE = """Ты — эксперт по проверке сочинений ЕГЭ (задание 27). Оцени сочинение по критериям К1–К10. Баллы по каждому критерию — целое число в указанных пределах.

Критерии и макс. баллы:
К1 — Отражение позиции автора по проблеме исходного текста (0–1).
К2 — Комментарий к позиции автора: 2 примера-иллюстрации, пояснения, смысловая связь (0–3).
К3 — Собственное отношение к позиции автора, обоснование, пример-аргумент (0–2).
К4 — Фактическая точность речи (0–1).
К5 — Логичность речи (0–2).
К6 — Соблюдение этических норм (0–1).
К7 — Орфография (0–3).
К8 — Пунктуация (0–3).
К9 — Грамматика (0–3).
К10 — Речевые нормы (0–3).
Максимум за сочинение — 22 балла.

Выяви ошибки по четырём типам (указывай строго эти латинские ключи):
- punctuation — пунктуация; spelling — орфография; grammar — грамматика; style — речевые ошибки.

Для каждого типа укажи массив fragments: точные цитаты из текста — подстроки с ошибкой. Копируй буквально из текста. Не придумывай индексы — только fragments.

Используй только для входа только текст сочинения, никаких других данных. Сам ничего не добавляй. В полях comment пиши кратко, в одну строку; внутри JSON не используй переносы строк в строках.

Ответь ТОЛЬКО валидным JSON без markdown, в формате:
{{"criteries": {{"k1": {{"score": N, "comment": "..."}}, ... "k10": {{"score": N, "comment": "..."}}}}, "common_mistakes": [{{"type": "punctuation", "count": N, "fragments": ["цитата"]}}, {{"type": "spelling", "count": N, "fragments": ["слово"]}}, {{"type": "grammar", "count": N, "fragments": []}}, {{"type": "style", "count": N, "fragments": []}}]}}

Тема/проблема: {theme}

Текст сочинения:
{text}
"""

ESSAY_MAX_SCORE = 5.0  # 5 критериев, по каждому 0 или 1 (зачет/незачет)

# Проверка темы сочинения: осмысленная формулировка (итоговое сочинение или ЕГЭ)
PROMPT_VALIDATE_THEME = """Проверь, является ли следующая строка осмысленной темой сочинения (итоговое сочинение или ЕГЭ по русскому языку).
Тема должна быть формулировкой проблемы или вопроса, по которому можно написать сочинение. Не допускаются: бессмысленный текст, случайный набор слов, оскорбления, реклама.
Ответь ТОЛЬКО валидным JSON без markdown: {{"valid": true или false, "message": "краткая причина, если valid false"}}

Тема: {theme}
"""


def _chat_completion(prompt: str, max_tokens: int = 1024, temperature: float = 0.3) -> dict[str, Any]:
    """Вызов Pollinations API /v1/chat/completions. Возвращает ответ в формате OpenAI (choices[].message.content)."""
    if not POLLINATIONS_API_KEY:
        raise ValueError("POLLINATIONS_API_KEY не задан. Получите ключ на https://enter.pollinations.ai")
    url = f"{POLLINATIONS_BASE_URL}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": POLLINATIONS_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()


def _extract_json(text: str) -> dict[str, Any]:
    """Достаёт первый полный JSON-объект из ответа модели. При обрыве ответа пробует доставить закрывающие скобки."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1).strip()
    first = text.find("{")
    if first == -1:
        raise json.JSONDecodeError("No JSON object found", text, 0)

    depth = 0
    in_string = False
    escape = False
    for i in range(first, len(text)):
        c = text[i]
        if escape:
            escape = False
            continue
        if in_string:
            if c == "\\":
                escape = True
            elif c == '"':
                in_string = False
            continue
        if c == '"':
            in_string = True
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[first : i + 1])

    chunk = text[first:]
    for repaired in (chunk, chunk.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")):
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            pass
    for attempt in range(40):
        try:
            return json.loads(chunk)
        except json.JSONDecodeError:
            pass
        s = chunk.rstrip()
        if s.endswith("}") or s.endswith("]"):
            break
        if s.endswith('"'):
            chunk += '"'
        elif s.endswith(","):
            chunk += "null}"
        else:
            chunk += "]}"
    last = text.rfind("}")
    if last != -1 and last > first:
        try:
            return json.loads(text[first : last + 1])
        except json.JSONDecodeError:
            pass
    raise json.JSONDecodeError("No valid JSON object found", text, first)


def _get_response_text(out: dict[str, Any]) -> str:
    """Достаёт текст ответа из ответа API (OpenAI-формат: choices[].message.content или .text)."""
    choices = out.get("choices") or []
    if not choices:
        return ""
    first = choices[0]
    if isinstance(first, dict):
        text = first.get("text") or first.get("content")
        if text is not None:
            return (text if isinstance(text, str) else str(text)).strip()
        msg = first.get("message")
        if isinstance(msg, dict):
            content = msg.get("content")
            if content is not None:
                return (content if isinstance(content, str) else str(content)).strip()
    return ""


# Нормализация типа ошибки: русские и варианты -> канонические ключи фронта
MISTAKE_TYPE_ALIASES: dict[str, str] = {
    "punctuation": "punctuation",
    "пунктуация": "punctuation",
    "punct": "punctuation",
    "spelling": "spelling",
    "орфография": "spelling",
    "spell": "spelling",
    "грамматика": "grammar",
    "grammar": "grammar",
    "style": "style",
    "речевая": "style",
    "речь": "style",
    "речевые": "style",
}


def _normalize_mistake_type(raw_type: str) -> str:
    """Приводит тип ошибки к одному из: punctuation, spelling, grammar, style."""
    key = (raw_type or "").strip().lower()
    return MISTAKE_TYPE_ALIASES.get(key) or "style"


def _fragments_to_ranges(text: str, fragments: list[Any]) -> list[list[int]]:
    """
    Ищет каждую строку из fragments в text и возвращает список [start, end] (end исключающий).
    Повторяющиеся вхождения одного фрагмента учитываются. Сначала поиск точный, при неудаче — без учёта регистра.
    """
    if not text or not isinstance(fragments, list):
        return []
    result: list[list[int]] = []
    for f in fragments:
        if not isinstance(f, str):
            continue
        fragment = f.strip()
        if not fragment or len(fragment) > 2000:
            continue
        start = 0
        while True:
            pos = text.find(fragment, start)
            if pos == -1:
                pos = text.lower().find(fragment.lower(), start)
            if pos == -1:
                break
            result.append([pos, pos + len(fragment)])
            start = pos + 1
    return result


def _clamp_and_merge_ranges(ranges: list[list[Any]], text_len: int) -> list[list[int]]:
    """
    Приводит диапазоны к длине текста: обрезка по границам [0, text_len],
    отсечение невалидных (start >= end), сортировка и слияние перекрывающихся.
    Индексы в формате [start, end), end исключающий.
    """
    if text_len <= 0:
        return []
    out: list[list[int]] = []
    for r in ranges:
        if not isinstance(r, (list, tuple)) or len(r) != 2:
            continue
        try:
            start, end = int(r[0]), int(r[1])
        except (TypeError, ValueError):
            continue
        if start > end:
            start, end = end, start
        start = max(0, min(start, text_len))
        end = max(0, min(end, text_len))
        if start < end:
            out.append([start, end])
    if not out:
        return []
    out.sort(key=lambda x: (x[0], x[1]))
    merged: list[list[int]] = [out[0][:]]
    for start, end in out[1:]:
        last = merged[-1]
        if start <= last[1]:
            last[1] = max(last[1], end)
        else:
            merged.append([start, end])
    return merged


def _resolve_ranges_from_fragments(common_mistakes: list[dict[str, Any]], text: str) -> list[dict[str, Any]]:
    """Если в элементе есть fragments — вычисляет ranges поиском по text; удаляет ключ fragments из выхода."""
    out: list[dict[str, Any]] = []
    for m in common_mistakes:
        if not isinstance(m, dict):
            continue
        m = dict(m)
        fragments = m.pop("fragments", None)
        if isinstance(fragments, list) and fragments:
            computed = _fragments_to_ranges(text, fragments)
            m["ranges"] = _clamp_and_merge_ranges(computed, len(text))
        elif "ranges" not in m or not m["ranges"]:
            m.setdefault("ranges", [])
        out.append(m)
    return out


def _apply_ranges_to_text(common_mistakes: list[dict[str, Any]], text_len: int) -> list[dict[str, Any]]:
    """Для каждого элемента common_mistakes перезаписывает ranges с привязкой к text_len."""
    result = []
    for m in common_mistakes:
        if not isinstance(m, dict):
            continue
        ranges_raw = m.get("ranges") or []
        if not isinstance(ranges_raw, list):
            ranges_raw = []
        clamped = _clamp_and_merge_ranges(ranges_raw, text_len)
        result.append({**m, "ranges": clamped})
    return result


def _normalize_result_essay(raw: dict[str, Any]) -> dict[str, Any]:
    """Приводит ответ модели к формату: criteries (k1–k5), по каждому score только 0 или 1 (зачет/незачет)."""
    criteries = raw.get("criteries") or raw.get("criteria") or {}
    result_criteries = {}
    for i in range(1, 6):
        key = f"k{i}"
        val = criteries.get(key) or criteries.get(str(i))
        if isinstance(val, dict):
            s = val.get("score")
            score = 1 if (s is not None and int(s) >= 1) else 0  # только 0 или 1
            result_criteries[key] = {
                "score": score,
                "comment": str(val.get("comment", "")),
                "found_in_text": val.get("found_in_text") if isinstance(val.get("found_in_text"), list) else [],
                "suggestions": val.get("suggestions") if isinstance(val.get("suggestions"), list) else [],
            }
        else:
            result_criteries[key] = {"score": 0, "comment": "", "found_in_text": [], "suggestions": []}

    mistakes = raw.get("common_mistakes") or raw.get("mistakes") or []
    if not isinstance(mistakes, list):
        mistakes = []
    normalized_mistakes = []
    for m in mistakes:
        if isinstance(m, dict) and "type" in m:
            raw_type = str(m.get("type", ""))
            mistake_type = _normalize_mistake_type(raw_type)
            count = int(m["count"]) if m.get("count") is not None else 0
            ranges = m.get("ranges") or []
            fragments = m.get("fragments") or []
            if not isinstance(ranges, list):
                ranges = []
            if not isinstance(fragments, list):
                fragments = []
            valid_ranges = []
            for r in ranges:
                if isinstance(r, (list, tuple)) and len(r) == 2:
                    start, end = r[0], r[1]
                    if isinstance(start, (int, float)) and isinstance(end, (int, float)):
                        valid_ranges.append([int(start), int(end)])
            normalized_mistakes.append({
                "type": mistake_type,
                "count": count,
                "ranges": valid_ranges,
                "fragments": [str(x).strip() for x in fragments if isinstance(x, str) and x.strip()],
            })
    allowed = {"punctuation", "spelling", "grammar", "style"}
    common_mistakes = [x for x in normalized_mistakes if x["type"] in allowed]
    return {"criteries": result_criteries, "common_mistakes": common_mistakes}


def _normalize_result_ege(raw: dict[str, Any]) -> dict[str, Any]:
    """Приводит ответ модели к формату: criteries (K1–K10), common_mistakes. Макс балл по критерию ограничиваем."""
    criteries = raw.get("criteries") or raw.get("criteria") or {}
    result_criteries = {}
    for i in range(1, 11):
        key = f"K{i}"
        max_val = EGE_MAX_BY_CRITERION.get(key, 0)
        val = criteries.get(key) or criteries.get(f"k{i}") or criteries.get(str(i))
        if isinstance(val, dict):
            s = val.get("score")
            score = min(int(s), max_val) if s is not None else 0
            result_criteries[key] = {
                "score": score,
                "comment": str(val.get("comment", "")),
                "found_in_text": val.get("found_in_text") if isinstance(val.get("found_in_text"), list) else [],
                "suggestions": val.get("suggestions") if isinstance(val.get("suggestions"), list) else [],
            }
        else:
            result_criteries[key] = {"score": 0, "comment": "", "found_in_text": [], "suggestions": []}

    mistakes = raw.get("common_mistakes") or raw.get("mistakes") or []
    if not isinstance(mistakes, list):
        mistakes = []
    normalized_mistakes = []
    for m in mistakes:
        if isinstance(m, dict) and "type" in m:
            raw_type = str(m.get("type", ""))
            mistake_type = _normalize_mistake_type(raw_type)
            count = int(m["count"]) if m.get("count") is not None else 0
            ranges = m.get("ranges") or []
            fragments = m.get("fragments") or []
            if not isinstance(ranges, list):
                ranges = []
            if not isinstance(fragments, list):
                fragments = []
            valid_ranges = []
            for r in ranges:
                if isinstance(r, (list, tuple)) and len(r) == 2:
                    start, end = r[0], r[1]
                    if isinstance(start, (int, float)) and isinstance(end, (int, float)):
                        valid_ranges.append([int(start), int(end)])
            normalized_mistakes.append({
                "type": mistake_type,
                "count": count,
                "ranges": valid_ranges,
                "fragments": [str(x).strip() for x in fragments if isinstance(x, str) and x.strip()],
            })
    allowed = {"punctuation", "spelling", "grammar", "style"}
    common_mistakes = [x for x in normalized_mistakes if x["type"] in allowed]
    return {"criteries": result_criteries, "common_mistakes": common_mistakes}


def validate_theme_sync(theme: str) -> dict[str, Any]:
    """Проверка темы сочинения моделью: осмысленная формулировка или нет. Возвращает {"valid": bool, "message": str}."""
    theme_stripped = theme.strip()[:512]
    if len(theme_stripped) < 2:
        return {"valid": False, "message": "Тема слишком короткая. Напишите формулировку темы сочинения."}

    prompt = PROMPT_VALIDATE_THEME.format(theme=theme_stripped)
    for attempt in range(2):
        out = _chat_completion(prompt, max_tokens=256, temperature=0)
        response_text = _get_response_text(out)
        if response_text:
            break
        logger.warning(
            "validate_theme_sync: пустой ответ модели (попытка %s), тема=%r",
            attempt + 1,
            theme_stripped[:100],
        )
    else:
        return {"valid": False, "message": "Не удалось проверить тему. Попробуйте ещё раз."}

    try:
        raw = _extract_json(response_text)
        valid = bool(raw.get("valid", False))
        message = str(raw.get("message", "")) or ""
        return {"valid": valid, "message": message or ("Тема не прошла проверку." if not valid else "")}
    except json.JSONDecodeError as e:
        logger.warning(
            "validate_theme_sync: не удалось распарсить JSON, тема=%r, ответ=%r, err=%s",
            theme_stripped[:80],
            response_text[:300],
            e,
        )
        return {"valid": False, "message": "Не удалось проверить тему. Попробуйте ещё раз."}


def evaluate_essay_sync(theme: str, text: str, essay_type: str = "essay") -> dict[str, Any]:
    """
    Синхронная оценка сочинения. essay_type: "essay" (итоговое, k1–k5, макс 25) или "ege" (К1–К10, макс 22).
    Возвращает: criteries, common_mistakes, max_score, total_score (сырые баллы), total_score_per (0–1).
    """
    is_ege = essay_type == "ege"
    if is_ege:
        prompt_tpl = PROMPT_EGE
        max_score = float(EGE_MAX_SCORE)
        criterion_keys = [f"K{i}" for i in range(1, 11)]
        default_criteries = {f"K{i}": {"score": 0, "comment": "", "found_in_text": [], "suggestions": []} for i in range(1, 11)}
        normalizer = _normalize_result_ege
    else:
        prompt_tpl = PROMPT_ESSAY
        max_score = ESSAY_MAX_SCORE
        criterion_keys = [f"k{i}" for i in range(1, 6)]
        default_criteries = {f"k{i}": {"score": 0, "comment": "", "found_in_text": [], "suggestions": []} for i in range(1, 6)}
        normalizer = _normalize_result_essay

    text_truncated = text[:8000]
    # Экранируем фигурные скобки в тексте пользователя, чтобы они не конфликтовали с .format()
    text_escaped = text_truncated.replace("{", "{{").replace("}", "}}")
    prompt = prompt_tpl.format(theme=theme, text=text_escaped)
    out = _chat_completion(prompt, max_tokens=4096, temperature=0.3)
    response_text = _get_response_text(out)
    if not response_text:
        logger.warning("essay_eval: модель вернула пустой ответ")
        return {
            "criteries": default_criteries,
            "common_mistakes": [],
            "max_score": max_score,
            "total_score": 0.0,
            "total_score_per": 0.0,
        }

    try:
        raw = _extract_json(response_text)
    except json.JSONDecodeError as e:
        logger.warning("essay_eval: не удалось распарсить JSON из ответа (первые 500 символов): %s ... ошибка: %s", response_text[:500], e)
        raw = {}

    normalized = normalizer(raw)
    criteries = normalized["criteries"]
    common_mistakes_raw = normalized["common_mistakes"]
    text_len = len(text_truncated)
    common_mistakes_resolved = _resolve_ranges_from_fragments(common_mistakes_raw, text_truncated)
    common_mistakes = _apply_ranges_to_text(common_mistakes_resolved, text_len)

    total_raw = sum(criteries.get(k, {}).get("score", 0) for k in criterion_keys)
    total_raw = min(total_raw, max_score)
    total_score_per = round(total_raw / max_score, 2) if max_score else 0.0

    return {
        "criteries": criteries,
        "common_mistakes": common_mistakes,
        "max_score": max_score,
        "total_score": total_raw,
        "total_score_per": total_score_per,
    }
