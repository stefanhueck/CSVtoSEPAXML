from datetime import date

from csv_to_sepa.config import create_config_interactive


def test_create_config_interactive_retries_and_defaults(monkeypatch, tmp_path) -> None:
    output = tmp_path / "config.json"
    today_iso = date.today().isoformat()

    inputs = iter(
        [
            "",  # debtor name invalid
            "Beispiel Verein",  # debtor name valid
            "DE00",  # invalid iban
            "DE89370400440532013000",  # valid iban
            "INVALID",  # invalid bic
            "",  # optional bic omitted
            "",  # initiating party optional -> None
            "13.03.2026",  # invalid date format
            "",  # default date -> today
            "WRONG",  # invalid charge bearer
            "",  # default charge bearer -> SLEV
        ]
    )

    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    config = create_config_interactive(output)

    assert config.debtor_name == "Beispiel Verein"
    assert config.debtor_iban == "DE89370400440532013000"
    assert config.debtor_bic is None
    assert config.default_execution_date == today_iso
    assert config.charge_bearer == "SLEV"
    assert output.exists()
