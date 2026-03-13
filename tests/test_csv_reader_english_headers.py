from datetime import date

from csv_to_sepa.csv_reader import parse_csv


def test_parse_minimal_csv_with_english_headers(tmp_path) -> None:
    csv_content = (
        "CreditorName;RemittanceInformation;Amount;CreditorIBAN;CreditorBIC\n"
        "Receiver One;Invoice 1001;24,00;DE37370502991325006652;COKSDE33XXX\n"
    )
    file_path = tmp_path / "minimal_en.csv"
    file_path.write_text(csv_content, encoding="utf-8")

    payments = parse_csv(file_path, execution_date=date(2026, 3, 16))

    assert len(payments) == 1
    assert payments[0].creditor_name == "Receiver One"
    assert str(payments[0].amount) == "24.00"


def test_parse_extended_csv_with_english_headers(tmp_path) -> None:
    csv_content = (
        "CreditorName;RemittanceInformation;Amount;CreditorIBAN;CreditorBIC;EndToEndId;ExecutionDate;PurposeCode\n"
        "Receiver Two;Invoice 2002;63,27;DE89120300001012637888;BYLADEM1001;INV-2002;2026-03-20;TRAD\n"
    )
    file_path = tmp_path / "extended_en.csv"
    file_path.write_text(csv_content, encoding="utf-8")

    payments = parse_csv(file_path, execution_date=date(2026, 3, 16))

    assert len(payments) == 1
    assert payments[0].end_to_end_id == "INV-2002"
    assert payments[0].execution_date == date(2026, 3, 20)
    assert payments[0].purpose_code == "TRAD"
