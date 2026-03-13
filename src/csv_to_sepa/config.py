from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path

from .models import AppConfig
from .validate import validate_bic, validate_iban


MESSAGES = {
    "en": {
        "debtor_name": "Debtor name",
        "debtor_iban": "Debtor IBAN",
        "debtor_bic_optional": "Debtor BIC (optional)",
        "initiating_party_optional": "Initiating party name (optional, empty = Debtor name)",
        "default_execution_date_optional": "Default execution date YYYY-MM-DD (optional, empty = today {today})",
        "charge_bearer_optional": "Charge bearer (optional, SLEV/SHAR/DEBT/CRED, empty = SLEV)",
        "warn_non_empty": "Hint: field must not be empty. Please try again.",
        "warn_invalid_iban": "Hint: invalid IBAN. Please try again.",
        "warn_invalid_bic": "Hint: invalid BIC. Please try again or leave empty.",
        "warn_invalid_date": "Hint: invalid date, expected format YYYY-MM-DD. Please try again.",
        "info_default_date": "Hint: default_execution_date is set to {value}.",
        "info_default_charge_bearer": "Hint: charge_bearer is set to {value}.",
        "warn_invalid_charge_bearer": "Hint: invalid charge_bearer. Allowed values: SLEV, SHAR, DEBT, CRED.",
    },
    "de": {
        "debtor_name": "Name des Debitors",
        "debtor_iban": "IBAN des Debitors",
        "debtor_bic_optional": "BIC des Debitors (optional)",
        "initiating_party_optional": "Name der initiierenden Partei (optional, leer = Debitor-Name)",
        "default_execution_date_optional": "Standard-Ausführungsdatum YYYY-MM-DD (optional, leer = heute {today})",
        "charge_bearer_optional": "Charge bearer (optional, SLEV/SHAR/DEBT/CRED, leer = SLEV)",
        "warn_non_empty": "Hinweis: Feld darf nicht leer sein. Eingabe bitte wiederholen.",
        "warn_invalid_iban": "Hinweis: Ungültige IBAN, Eingabe bitte wiederholen.",
        "warn_invalid_bic": "Hinweis: Ungültige BIC, Eingabe bitte wiederholen oder leer lassen.",
        "warn_invalid_date": "Hinweis: Ungültiges Datum, Format ist YYYY-MM-DD. Eingabe bitte wiederholen.",
        "info_default_date": "Hinweis: default_execution_date wird auf {value} gesetzt.",
        "info_default_charge_bearer": "Hinweis: charge_bearer wird auf {value} gesetzt.",
        "warn_invalid_charge_bearer": "Hinweis: Ungültiger charge_bearer, erlaubt sind SLEV, SHAR, DEBT, CRED.",
    },
}


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    config = AppConfig(**raw)
    config.debtor_iban = "".join(config.debtor_iban.split()).upper()
    if config.debtor_bic:
        config.debtor_bic = "".join(config.debtor_bic.split()).upper()
    _validate_config(config)
    return config


def save_config(path: str | Path, config: AppConfig) -> None:
    config_path = Path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as handle:
        json.dump(asdict(config), handle, indent=2, ensure_ascii=False)


def create_config_interactive(output_path: str | Path, language: str = "en") -> AppConfig:
    lang = "de" if language.lower() == "de" else "en"
    msg = MESSAGES[lang]
    today_iso = date.today().isoformat()

    debtor_name = _prompt_non_empty(msg["debtor_name"], msg)
    debtor_iban = _prompt_iban(msg["debtor_iban"], msg)
    debtor_bic = _prompt_optional_bic(msg["debtor_bic_optional"], msg)
    initiating_party_name = input(f"{msg['initiating_party_optional']}: ").strip() or None
    default_execution_date = _prompt_optional_date_with_default(
        msg["default_execution_date_optional"].format(today=today_iso),
        default_value=today_iso,
        messages=msg,
    )
    charge_bearer = _prompt_charge_bearer(
        msg["charge_bearer_optional"],
        default_value="SLEV",
        messages=msg,
    )

    config = AppConfig(
        debtor_name=debtor_name,
        debtor_iban=debtor_iban,
        debtor_bic=debtor_bic,
        initiating_party_name=initiating_party_name,
        default_execution_date=default_execution_date,
        charge_bearer=charge_bearer,
    )
    _validate_config(config)
    save_config(output_path, config)
    return config


def _validate_config(config: AppConfig) -> None:
    if not config.debtor_name:
        raise ValueError("debtor_name must not be empty")
    if not validate_iban(config.debtor_iban):
        raise ValueError("debtor_iban is invalid")
    if config.debtor_bic and not validate_bic(config.debtor_bic):
        raise ValueError("debtor_bic is invalid")
    if config.charge_bearer not in {"SLEV", "SHAR", "DEBT", "CRED"}:
        raise ValueError("charge_bearer must be one of SLEV, SHAR, DEBT, CRED")
    if config.default_execution_date:
        try:
            datetime.strptime(config.default_execution_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("default_execution_date must be YYYY-MM-DD")


def _prompt_non_empty(label: str, messages: dict[str, str]) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print(messages["warn_non_empty"])


def _prompt_iban(label: str, messages: dict[str, str]) -> str:
    while True:
        value = "".join(input(f"{label}: ").split()).upper()
        if validate_iban(value):
            return value
        print(messages["warn_invalid_iban"])


def _prompt_optional_bic(label: str, messages: dict[str, str]) -> str | None:
    while True:
        value = input(f"{label}: ").strip().upper()
        if not value:
            return None
        if validate_bic(value):
            return value
        print(messages["warn_invalid_bic"])


def _prompt_optional_date_with_default(label: str, default_value: str, messages: dict[str, str]) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if not value:
            print(messages["info_default_date"].format(value=default_value))
            return default_value
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            print(messages["warn_invalid_date"])


def _prompt_charge_bearer(label: str, default_value: str, messages: dict[str, str]) -> str:
    allowed = {"SLEV", "SHAR", "DEBT", "CRED"}
    while True:
        value = input(f"{label}: ").strip().upper()
        if not value:
            print(messages["info_default_charge_bearer"].format(value=default_value))
            return default_value
        if value in allowed:
            return value
        print(messages["warn_invalid_charge_bearer"])
