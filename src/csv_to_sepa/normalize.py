from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


_SPACE_RE = re.compile(r"\s+")
_E2E_ALLOWED_RE = re.compile(r"[^A-Za-z0-9\-\./:]")


def normalize_whitespace(value: str) -> str:
    text = value.replace("\r", " ").replace("\n", " ").strip()
    return _SPACE_RE.sub(" ", text)


def transliterate_german(value: str) -> str:
    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "Ä": "Ae",
        "Ö": "Oe",
        "Ü": "Ue",
        "ß": "ss",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def sanitize_text(value: str, max_length: int, strict_ascii: bool = False) -> str:
    text = normalize_whitespace(value)
    if strict_ascii:
        text = transliterate_german(text)
        text = text.encode("ascii", errors="ignore").decode("ascii")
    return text[:max_length]


def parse_amount_eur(amount_raw: str) -> Decimal:
    value = normalize_whitespace(amount_raw)
    if not value:
        raise ValueError("amount is empty")
    normalized = value.replace(".", "").replace(",", ".")
    try:
        amount = Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError(f"invalid amount: {amount_raw}") from exc
    if amount <= Decimal("0"):
        raise ValueError("amount must be positive")
    if amount > Decimal("999999999.99"):
        raise ValueError("amount exceeds SEPA range")
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def parse_execution_date(value: str | None, offset_days: int = 1) -> date:
    if value and value.strip():
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    return date.today() + timedelta(days=offset_days)


def generate_end_to_end_id(seed: str, row_number: int) -> str:
    digest = hashlib.sha1(f"{seed}|{row_number}".encode("utf-8")).hexdigest()[:10].upper()
    candidate = f"E2E-{row_number}-{digest}"
    candidate = _E2E_ALLOWED_RE.sub("", candidate)
    return candidate[:35]


def sanitize_end_to_end_id(value: str) -> str:
    candidate = normalize_whitespace(value)
    candidate = _E2E_ALLOWED_RE.sub("", candidate)
    return candidate[:35]
