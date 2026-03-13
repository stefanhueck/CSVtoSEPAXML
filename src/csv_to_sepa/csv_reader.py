from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from .models import PaymentRecord
from .normalize import generate_end_to_end_id, parse_amount_eur, sanitize_text

HEADER_ALIASES = {
    "Name": "creditor_name",
    "Verwendungszweck": "remittance_unstructured",
    "Betrag": "amount",
    "IBAN": "creditor_iban",
    "BIC": "creditor_bic",
}

REQUIRED_TARGET_FIELDS = {
    "creditor_name",
    "remittance_unstructured",
    "amount",
    "creditor_iban",
}


def parse_csv(
    file_path: str | Path,
    execution_date: date,
    delimiter: str = ";",
    encoding: str = "utf-8-sig",
    strict_ascii: bool = False,
) -> list[PaymentRecord]:
    path = Path(file_path)
    with path.open("r", encoding=encoding, newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        if reader.fieldnames is None:
            raise ValueError("CSV header row is missing")

        mapped_headers = [_map_header(h) for h in reader.fieldnames]
        if not REQUIRED_TARGET_FIELDS.issubset(set(mapped_headers)):
            raise ValueError(
                "CSV header must contain at least: Name;Verwendungszweck;Betrag;IBAN"
            )

        payments: list[PaymentRecord] = []
        for row_number, row in enumerate(reader, start=2):
            normalized_row = {_map_header(k): (v or "") for k, v in row.items()}
            seed = "|".join(
                [
                    normalized_row.get("creditor_name", ""),
                    normalized_row.get("creditor_iban", ""),
                    normalized_row.get("amount", ""),
                    normalized_row.get("remittance_unstructured", ""),
                ]
            )
            payment = PaymentRecord(
                row_number=row_number,
                creditor_name=sanitize_text(
                    normalized_row.get("creditor_name", ""),
                    max_length=70,
                    strict_ascii=strict_ascii,
                ),
                creditor_iban=normalized_row.get("creditor_iban", "").replace(" ", "").upper(),
                creditor_bic=(normalized_row.get("creditor_bic", "").strip().upper() or None),
                amount=parse_amount_eur(normalized_row.get("amount", "")),
                remittance_unstructured=sanitize_text(
                    normalized_row.get("remittance_unstructured", ""),
                    max_length=140,
                    strict_ascii=strict_ascii,
                ),
                execution_date=execution_date,
                end_to_end_id=generate_end_to_end_id(seed=seed, row_number=row_number),
            )
            payments.append(payment)
        return payments


def _map_header(header_name: str) -> str:
    return HEADER_ALIASES.get(header_name.strip(), header_name.strip())
