from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path

from .models import AppConfig
from .validate import validate_bic, validate_iban


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    config = AppConfig(**raw)
    _validate_config(config)
    return config


def save_config(path: str | Path, config: AppConfig) -> None:
    config_path = Path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as handle:
        json.dump(asdict(config), handle, indent=2, ensure_ascii=False)


def create_config_interactive(output_path: str | Path) -> AppConfig:
    today_iso = date.today().isoformat()

    debtor_name = _prompt_non_empty("Debtor name")
    debtor_iban = _prompt_iban("Debtor IBAN")
    debtor_bic = _prompt_optional_bic("Debtor BIC (optional)")
    initiating_party_name = input("Initiating party name (optional, leer = Debtor name): ").strip() or None
    default_execution_date = _prompt_optional_date_with_default(
        f"Default execution date YYYY-MM-DD (optional, leer = heute {today_iso})",
        default_value=today_iso,
    )
    charge_bearer = _prompt_charge_bearer(
        "Charge bearer (optional, SLEV/SHAR/DEBT/CRED, leer = SLEV)",
        default_value="SLEV",
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


def _prompt_non_empty(label: str) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print("Hinweis: Feld darf nicht leer sein. Eingabe bitte wiederholen.")


def _prompt_iban(label: str) -> str:
    while True:
        value = input(f"{label}: ").strip().replace(" ", "").upper()
        if validate_iban(value):
            return value
        print("Hinweis: Ungültige IBAN, Eingabe bitte wiederholen.")


def _prompt_optional_bic(label: str) -> str | None:
    while True:
        value = input(f"{label}: ").strip().upper()
        if not value:
            return None
        if validate_bic(value):
            return value
        print("Hinweis: Ungültige BIC, Eingabe bitte wiederholen oder leer lassen.")


def _prompt_optional_date_with_default(label: str, default_value: str) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if not value:
            print(f"Hinweis: default_execution_date wird auf {default_value} gesetzt.")
            return default_value
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            print("Hinweis: Ungültiges Datum, Format ist YYYY-MM-DD. Eingabe bitte wiederholen.")


def _prompt_charge_bearer(label: str, default_value: str) -> str:
    allowed = {"SLEV", "SHAR", "DEBT", "CRED"}
    while True:
        value = input(f"{label}: ").strip().upper()
        if not value:
            print(f"Hinweis: charge_bearer wird auf {default_value} gesetzt.")
            return default_value
        if value in allowed:
            return value
        print("Hinweis: Ungültiger charge_bearer, erlaubt sind SLEV, SHAR, DEBT, CRED.")
