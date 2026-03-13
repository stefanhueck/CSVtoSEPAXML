from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(slots=True)
class AppConfig:
    debtor_name: str
    debtor_iban: str
    debtor_bic: str | None = None
    initiating_party_name: str | None = None
    default_execution_date: str | None = None
    execution_date_offset_days: int = 1
    charge_bearer: str = "SLEV"
    batch_booking: bool = False


@dataclass(slots=True)
class PaymentRecord:
    row_number: int
    creditor_name: str
    creditor_iban: str
    creditor_bic: str | None
    amount: Decimal
    remittance_unstructured: str
    execution_date: date
    end_to_end_id: str


@dataclass(slots=True)
class ValidationIssue:
    row_number: int
    field: str
    code: str
    message: str


class ValidationError(Exception):
    def __init__(self, issues: list[ValidationIssue]):
        self.issues = issues
        super().__init__(f"{len(issues)} validation issue(s) found")
