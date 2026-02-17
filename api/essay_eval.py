"""
Оценка сочинения локальной моделью (gemma-3-4b-it).
Тип essay: итоговое сочинение (k1–k5, зачет/незачет = 0 или 1, макс 5). Тип ege: ЕГЭ задание 27 (K1–K10, макс 22).
Возвращает criteries, common_mistakes, max_score, total_score (сырые баллы), total_score_per (0–1).
"""
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Модель загружается лениво при первом вызове
_llama_model = None

# Итоговое сочинение: по каждому критерию только «зачет» (1) или «незачет» (0), макс 5 баллов
PROMPT_ESSAY = """Ты — эксперт по проверке итоговых сочинений. По каждому из 5 критериев выставляется только «зачет» или «незачет». В JSON для каждого критерия укажи score: 1 (зачет) или 0 (незачет).

Критерии:
k1 — Соответствие теме. «Незачет» только если сочинение не по теме, нет ответа на вопрос или нет цели высказывания. Иначе «зачет».
k2 — Аргументация. Привлечение литературного материала. «Незачет» если нет аргументации, нет опоры на литературу, существенно искажён текст или примеры не подкрепляют аргументы. Иначе «зачет».
k3 — Композиция и логика рассуждения. «Незачет» если грубые логические нарушения мешают пониманию или нет тезисно-доказательной части. Иначе «зачет».
k4 — Качество письменной речи. «Незачет» если низкое качество речи существенно затрудняет понимание. Иначе «зачет».
k5 — Грамотность. «Незачет» если на 100 слов в среднем более 5 ошибок (орфография, пунктуация, грамматика). Иначе «зачет».

Для зачета за работу в целом нужны зачет по k1 и k2 и плюс зачет хотя бы по одному из k3 или k4. Критерий k5 учитывается отдельно.

Выяви типы ошибок по категориям: punctuation, spelling, grammar, style.

Для каждой ошибки укажи точные индексы начала и конца фрагмента в тексте (start и end - позиции символов в исходном тексте, начиная с 0). Например, если ошибка в слове "привет" на позициях 10-16, то start=10, end=16.

Используй только для входа только текст сочинения, никаких других данных. Сам ничего не добавляй.

Ответь ТОЛЬКО валидным JSON без markdown. У каждого критерия score — только 0 или 1:
{{"criteries": {{"k1": {{"score": 0 или 1, "comment": "...", "found_in_text": []}}, "k2": {{"score": 0 или 1, "comment": "...", "suggestions": []}}, "k3": {{"score": 0 или 1, "comment": "..."}}, "k4": {{"score": 0 или 1, "comment": "..."}}, "k5": {{"score": 0 или 1, "comment": "..."}}}}, "common_mistakes": [{{"type": "punctuation", "count": N, "ranges": [[start, end]]}}, {{"type": "spelling", "count": N, "ranges": [[start, end]]}}, {{"type": "grammar", "count": N, "ranges": [[start, end]]}}, {{"type": "style", "count": N, "ranges": [[start, end]]}}]}}

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

Выяви типы ошибок: punctuation, spelling, grammar, style.

Для каждой ошибки укажи точные индексы начала и конца фрагмента в тексте (start и end - позиции символов в исходном тексте, начиная с 0). Например, если ошибка в слове "привет" на позициях 10-16, то start=10, end=16.

Используй только для входа только текст сочинения, никаких других данных. Сам ничего не добавляй.

Ответь ТОЛЬКО валидным JSON без markdown, в формате:
{{"criteries": {{"k1": {{"score": N, "comment": "..."}}, "k2": {{"score": N, "comment": "..."}}, "k3": {{"score": N, "comment": "..."}}, "k4": {{"score": N, "comment": "..."}}, "k5": {{"score": N, "comment": "..."}}, "k6": {{"score": N, "comment": "..."}}, "k7": {{"score": N, "comment": "..."}}, "k8": {{"score": N, "comment": "..."}}, "k9": {{"score": N, "comment": "..."}}, "k10": {{"score": N, "comment": "..."}}}}, "common_mistakes": [{{"type": "punctuation", "count": N, "ranges": [[start, end]]}}, {{"type": "spelling", "count": N, "ranges": [[start, end]]}}, {{"type": "grammar", "count": N, "ranges": [[start, end]]}}, {{"type": "style", "count": N, "ranges": [[start, end]]}}]}}

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


def _model_path() -> Path:
    path = os.getenv("LLAMA_MODEL_PATH")
    if path:
        p = Path(path)
        if p.is_dir():
            default = p / "gemma-3-4b-it-UD-Q6_K_XL.gguf"
            if default.exists():
                return default
            ggufs = list(p.glob("*.gguf"))
            if ggufs:
                return ggufs[0]
            return default
        return p
    repo = Path(__file__).resolve().parents[1]
    return repo / "gemma-3-4b-it-UD-Q6_K_XL.gguf"


def _get_model():
    global _llama_model
    if _llama_model is None:
        from llama_cpp import Llama

        path = _model_path()
        if not path.exists():
            raise FileNotFoundError(f"Модель не найдена: {path}")
        _llama_model = Llama(
            model_path=str(path),
            n_ctx=8192,
            n_gpu_layers=-1,
            n_threads=6,
            n_batch=512,
            verbose=False,
        )
    return _llama_model

GEMMA_USER_PREFIX = "<start_of_turn>user\n"
GEMMA_USER_SUFFIX = "<end_of_turn>\n<start_of_turn>model\n"

GEMMA_TOP_K = 64
GEMMA_TOP_P = 0.95
GEMMA_REPEAT_PENALTY = 1.0
GEMMA_MIN_P = 0.01


def _gemma_prompt(prompt: str) -> str:
    """Оборачивает промпт в формат Gemma (user turn + начало ответа model)."""
    return GEMMA_USER_PREFIX + prompt + GEMMA_USER_SUFFIX


def _extract_json(text: str) -> dict[str, Any]:
    """Достаёт первый полный JSON-объект из ответа модели (игнорирует текст после него — «Extra data»)."""
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

    last = text.rfind("}")
    if last != -1 and last > first:
        text = text[first : last + 1]
    return json.loads(text)


def _get_response_text(out: dict[str, Any]) -> str:
    """Достаёт текст ответа из ответа модели (llama-cpp: text или message.content)."""
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
        if isinstance(m, dict) and "type" in m and "count" in m:
            mistake_type = str(m["type"])
            count = int(m["count"])
            # Обрабатываем ranges - массив [start, end] индексов
            ranges = m.get("ranges", [])
            if isinstance(ranges, list):
                # Валидируем ranges: должны быть массивы из двух чисел [start, end]
                valid_ranges = []
                for r in ranges:
                    if isinstance(r, list) and len(r) == 2:
                        start, end = r[0], r[1]
                        if isinstance(start, (int, float)) and isinstance(end, (int, float)):
                            valid_ranges.append([int(start), int(end)])
                normalized_mistakes.append({
                    "type": mistake_type,
                    "count": count,
                    "ranges": valid_ranges
                })
            else:
                normalized_mistakes.append({"type": mistake_type, "count": count, "ranges": []})
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
        if isinstance(m, dict) and "type" in m and "count" in m:
            mistake_type = str(m["type"])
            count = int(m["count"])
            # Обрабатываем ranges - массив [start, end] индексов
            ranges = m.get("ranges", [])
            if isinstance(ranges, list):
                # Валидируем ranges: должны быть массивы из двух чисел [start, end]
                valid_ranges = []
                for r in ranges:
                    if isinstance(r, list) and len(r) == 2:
                        start, end = r[0], r[1]
                        if isinstance(start, (int, float)) and isinstance(end, (int, float)):
                            valid_ranges.append([int(start), int(end)])
                normalized_mistakes.append({
                    "type": mistake_type,
                    "count": count,
                    "ranges": valid_ranges
                })
            else:
                normalized_mistakes.append({"type": mistake_type, "count": count, "ranges": []})
    allowed = {"punctuation", "spelling", "grammar", "style"}
    common_mistakes = [x for x in normalized_mistakes if x["type"] in allowed]
    return {"criteries": result_criteries, "common_mistakes": common_mistakes}


def validate_theme_sync(theme: str) -> dict[str, Any]:
    """Проверка темы сочинения моделью: осмысленная формулировка или нет. Возвращает {"valid": bool, "message": str}."""
    theme_stripped = theme.strip()[:512]
    if len(theme_stripped) < 2:
        return {"valid": False, "message": "Тема слишком короткая. Напишите формулировку темы сочинения."}

    model = _get_model()
    prompt = PROMPT_VALIDATE_THEME.format(theme=theme_stripped)

    prompt_with_format = _gemma_prompt(prompt)
    for attempt in range(2):
        out = model(
            prompt_with_format,
            max_tokens=256,
            temperature=0,
            top_k=GEMMA_TOP_K,
            top_p=GEMMA_TOP_P,
            repeat_penalty=GEMMA_REPEAT_PENALTY,
            min_p=GEMMA_MIN_P,
            stop=["</s>", "<end_of_turn>"],
        )
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

    model = _get_model()
    text_truncated = text[:8000]
    # Экранируем фигурные скобки в тексте пользователя, чтобы они не конфликтовали с .format()
    text_escaped = text_truncated.replace("{", "{{").replace("}", "}}")
    prompt = prompt_tpl.format(theme=theme, text=text_escaped)
    prompt_with_format = _gemma_prompt(prompt)
    out = model(
        prompt_with_format,
        max_tokens=1536,
        temperature=0.3,
        top_k=GEMMA_TOP_K,
        top_p=GEMMA_TOP_P,
        repeat_penalty=GEMMA_REPEAT_PENALTY,
        min_p=GEMMA_MIN_P,
        stop=["</s>", "<end_of_turn>", "\n\n\n"],
    )
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
    common_mistakes = normalized["common_mistakes"]

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
