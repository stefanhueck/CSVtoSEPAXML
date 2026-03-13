import argparse
import json

import pytest

from csv_to_sepa.cli import cmd_convert, cmd_validate_csv


def test_cmd_validate_csv_english_output(capsys, tmp_path) -> None:
    config_path = tmp_path / "config.json"
    csv_path = tmp_path / "input.csv"

    config_path.write_text(
        json.dumps(
            {
                "debtor_name": "Example Org",
                "debtor_iban": "DE89370400440532013000",
                "debtor_bic": None,
                "initiating_party_name": None,
                "default_execution_date": "2026-03-20",
                "execution_date_offset_days": 1,
                "charge_bearer": "SLEV",
                "batch_booking": False,
            }
        ),
        encoding="utf-8",
    )
    csv_path.write_text(
        "Name;Verwendungszweck;Betrag;IBAN;BIC\n"
        "Augstein Rolf;Test;24,00;DE37370502991325006652;COKSDE33XXX\n",
        encoding="utf-8",
    )

    args = argparse.Namespace(
        config=str(config_path),
        input=str(csv_path),
        delimiter=";",
        encoding="utf-8-sig",
        execution_date=None,
        strict_ascii=False,
        language="en",
    )
    cmd_validate_csv(args)

    stdout = capsys.readouterr().out
    assert "CSV valid." in stdout


def test_cmd_validate_csv_german_output(capsys, tmp_path) -> None:
    config_path = tmp_path / "config.json"
    csv_path = tmp_path / "input.csv"

    config_path.write_text(
        json.dumps(
            {
                "debtor_name": "Example Org",
                "debtor_iban": "DE89370400440532013000",
                "debtor_bic": None,
                "initiating_party_name": None,
                "default_execution_date": "2026-03-20",
                "execution_date_offset_days": 1,
                "charge_bearer": "SLEV",
                "batch_booking": False,
            }
        ),
        encoding="utf-8",
    )
    csv_path.write_text(
        "Name;Verwendungszweck;Betrag;IBAN;BIC\n"
        "Augstein Rolf;Test;24,00;DE37370502991325006652;COKSDE33XXX\n",
        encoding="utf-8",
    )

    args = argparse.Namespace(
        config=str(config_path),
        input=str(csv_path),
        delimiter=";",
        encoding="utf-8-sig",
        execution_date=None,
        strict_ascii=False,
        language="de",
    )
    cmd_validate_csv(args)

    stdout = capsys.readouterr().out
    assert "CSV ist gültig." in stdout


def test_cmd_validate_csv_parse_error_has_helpful_logs(capsys, tmp_path) -> None:
    config_path = tmp_path / "config.json"
    csv_path = tmp_path / "input_invalid_amount.csv"

    config_path.write_text(
        json.dumps(
            {
                "debtor_name": "Example Org",
                "debtor_iban": "DE89370400440532013000",
                "debtor_bic": None,
                "initiating_party_name": None,
                "default_execution_date": "2026-03-20",
                "execution_date_offset_days": 1,
                "charge_bearer": "SLEV",
                "batch_booking": False,
            }
        ),
        encoding="utf-8",
    )
    csv_path.write_text(
        "Name;Verwendungszweck;Betrag;IBAN;BIC\n"
        "Augstein Rolf;Test;xx,yy;DE37370502991325006652;COKSDE33XXX\n",
        encoding="utf-8",
    )

    args = argparse.Namespace(
        config=str(config_path),
        input=str(csv_path),
        delimiter=";",
        encoding="utf-8-sig",
        execution_date=None,
        strict_ascii=False,
        language="en",
    )

    with pytest.raises(SystemExit):
        cmd_validate_csv(args)

    stdout = capsys.readouterr().out
    assert "Command failed:" in stdout
    assert "Row 2, field Betrag" in stdout
    assert "Possible causes:" in stdout


def test_cmd_convert_validation_error_has_structured_logs(capsys, tmp_path) -> None:
    config_path = tmp_path / "config.json"
    csv_path = tmp_path / "input_invalid_iban.csv"
    output_path = tmp_path / "output.xml"

    config_path.write_text(
        json.dumps(
            {
                "debtor_name": "Example Org",
                "debtor_iban": "DE89370400440532013000",
                "debtor_bic": None,
                "initiating_party_name": None,
                "default_execution_date": "2026-03-20",
                "execution_date_offset_days": 1,
                "charge_bearer": "SLEV",
                "batch_booking": False,
            }
        ),
        encoding="utf-8",
    )
    csv_path.write_text(
        "Name;Verwendungszweck;Betrag;IBAN;BIC\n"
        "Augstein Rolf;Test;24,00;DE123;COKSDE33XXX\n",
        encoding="utf-8",
    )

    args = argparse.Namespace(
        config=str(config_path),
        input=str(csv_path),
        output=str(output_path),
        delimiter=";",
        encoding="utf-8-sig",
        execution_date=None,
        strict_ascii=False,
        language="en",
    )

    with pytest.raises(SystemExit):
        cmd_convert(args)

    stdout = capsys.readouterr().out
    assert "Validation failed:" in stdout
    assert "INVALID_IBAN" in stdout
