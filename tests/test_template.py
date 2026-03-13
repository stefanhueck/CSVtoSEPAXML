from csv_to_sepa.template import create_csv_template


def test_create_template_minimal(tmp_path) -> None:
    output = tmp_path / "minimal.csv"
    create_csv_template(output=output, mode="minimal")
    header = output.read_text(encoding="utf-8-sig").splitlines()[0]
    assert header == "Name;Verwendungszweck;Betrag;IBAN;BIC"


def test_create_template_extended(tmp_path) -> None:
    output = tmp_path / "extended.csv"
    create_csv_template(output=output, mode="extended")
    header = output.read_text(encoding="utf-8-sig").splitlines()[0]
    assert header == "Name;Verwendungszweck;Betrag;IBAN;BIC;EndToEndId;ExecutionDate;PurposeCode"
