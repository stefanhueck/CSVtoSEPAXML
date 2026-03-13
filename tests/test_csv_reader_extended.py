from datetime import date

from csv_to_sepa.csv_reader import parse_csv


def test_parse_extended_csv_uses_optional_fields(tmp_path) -> None:
    csv_content = (
        "Name;Verwendungszweck;Betrag;IBAN;BIC;EndToEndId;ExecutionDate;PurposeCode\n"
        "Empfaenger A;Rechnung 1001;24,00;DE37370502991325006652;COKSDE33XXX;INV-1001;2026-03-20;SALA\n"
    )
    file_path = tmp_path / "extended.csv"
    file_path.write_text(csv_content, encoding="utf-8")

    payments = parse_csv(file_path, execution_date=date(2026, 3, 16))

    assert len(payments) == 1
    assert payments[0].end_to_end_id == "INV-1001"
    assert payments[0].execution_date == date(2026, 3, 20)
    assert payments[0].purpose_code == "SALA"
