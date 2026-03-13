from __future__ import annotations

import json
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
        json.dump(config.__dict__, handle, indent=2, ensure_ascii=False)


def create_config_interactive(output_path: str | Path) -> AppConfig:
    debtor_name = input("Debtor name: ").strip()
    debtor_iban = input("Debtor IBAN: ").strip().replace(" ", "").upper()
    debtor_bic = input("Debtor BIC (optional): ").strip().upper() or None
    initiating_party_name = input("Initiating party name (empty = debtor name): ").strip() or None
    default_execution_date = input("Default execution date YYYY-MM-DD (optional): ").strip() or None
    charge_bearer = (input("Charge bearer [SLEV]: ").strip().upper() or "SLEV")

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
        if len(config.default_execution_date) != 10:
            raise ValueError("default_execution_date must be YYYY-MM-DD")
