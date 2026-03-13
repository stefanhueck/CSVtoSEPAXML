import argparse

import pytest

from csv_to_sepa.cli import cmd_validate_xml


def test_validate_xml_missing_xsd_shows_friendly_message(capsys, tmp_path) -> None:
    xml_path = tmp_path / "input.xml"
    xml_path.write_text("<root/>", encoding="utf-8")

    args = argparse.Namespace(
        input=str(xml_path),
        xsd=str(tmp_path / "missing.xsd"),
        language="en",
    )

    with pytest.raises(SystemExit) as exc:
        cmd_validate_xml(args)

    assert "XSD file not found" in str(exc.value)


def test_validate_xml_missing_xml_shows_friendly_message(capsys, tmp_path) -> None:
    xsd_path = tmp_path / "schema.xsd"
    xsd_path.write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\">
  <xs:element name=\"root\" type=\"xs:string\"/>
</xs:schema>
""",
        encoding="utf-8",
    )

    args = argparse.Namespace(
        input=str(tmp_path / "missing.xml"),
        xsd=str(xsd_path),
        language="en",
    )

    with pytest.raises(SystemExit) as exc:
        cmd_validate_xml(args)

    assert "XML input file not found" in str(exc.value)
