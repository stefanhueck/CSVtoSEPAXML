from __future__ import annotations

import csv
from pathlib import Path


MINIMAL_HEADERS_DE = ["Name", "Verwendungszweck", "Betrag", "IBAN", "BIC"]
MINIMAL_HEADERS_EN = ["CreditorName", "RemittanceInformation", "Amount", "CreditorIBAN", "CreditorBIC"]

EXTENDED_HEADERS_DE = [
    "Name",
    "Verwendungszweck",
    "Betrag",
    "IBAN",
    "BIC",
    "EndToEndId",
    "ExecutionDate",
    "PurposeCode",
]

EXTENDED_HEADERS_EN = [
    "CreditorName",
    "RemittanceInformation",
    "Amount",
    "CreditorIBAN",
    "CreditorBIC",
    "EndToEndId",
    "ExecutionDate",
    "PurposeCode",
]


def create_csv_template(
    output: str | Path,
    mode: str,
    delimiter: str = ";",
    encoding: str = "utf-8-sig",
    header_language: str = "en",
) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)

    headers = _headers_for_mode(mode, header_language)
    with path.open("w", encoding=encoding, newline="") as handle:
        writer = csv.writer(handle, delimiter=delimiter)
        writer.writerow(headers)


def _headers_for_mode(mode: str, header_language: str) -> list[str]:
    normalized = mode.strip().lower()
    lang = header_language.strip().lower()
    if lang not in {"de", "en"}:
        raise ValueError("header_language must be 'de' or 'en'")

    if normalized == "minimal":
        return MINIMAL_HEADERS_DE if lang == "de" else MINIMAL_HEADERS_EN
    if normalized == "extended":
        return EXTENDED_HEADERS_DE if lang == "de" else EXTENDED_HEADERS_EN
    raise ValueError("mode must be 'minimal' or 'extended'")
