import argparse

import pytest

from csv_to_sepa.cli import cmd_check_namespace


def test_check_namespace_shows_message_and_suggestions(capsys, tmp_path) -> None:
    xml_path = tmp_path / "sample.xml"
    xml_path.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Document xmlns=\"urn:iso:std:iso:20022:tech:xsd:pain.001.001.09\">
  <CstmrCdtTrfInitn/>
</Document>
""",
        encoding="utf-8",
    )

    args = argparse.Namespace(input=str(xml_path), language="en")
    cmd_check_namespace(args)

    stdout = capsys.readouterr().out
    assert "Detected XML namespace" in stdout
    assert "pain.001.001.09" in stdout
    assert "./xsd/pain.001.001.09.xsd" in stdout


def test_check_namespace_missing_xml_gives_friendly_message(tmp_path) -> None:
    args = argparse.Namespace(input=str(tmp_path / "missing.xml"), language="en")
    with pytest.raises(SystemExit) as exc:
        cmd_check_namespace(args)
    assert "XML input file not found" in str(exc.value)
