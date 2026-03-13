from __future__ import annotations

import csv
from pathlib import Path


MINIMAL_HEADERS = ["Name", "Verwendungszweck", "Betrag", "IBAN", "BIC"]
EXTENDED_HEADERS = [
    "Name",
    "Verwendungszweck",
    "Betrag",
    "IBAN",
    "BIC",
    "EndToEndId",
    "ExecutionDate",
    "PurposeCode",
]


def create_csv_template(output: str | Path, mode: str, delimiter: str = ";", encoding: str = "utf-8-sig") -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)

    headers = _headers_for_mode(mode)
    with path.open("w", encoding=encoding, newline="") as handle:
        writer = csv.writer(handle, delimiter=delimiter)
        writer.writerow(headers)


def _headers_for_mode(mode: str) -> list[str]:
    normalized = mode.strip().lower()
    if normalized == "minimal":
        return MINIMAL_HEADERS
    if normalized == "extended":
        return EXTENDED_HEADERS
    raise ValueError("mode must be 'minimal' or 'extended'")
