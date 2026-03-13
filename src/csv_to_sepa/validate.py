from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

from .models import AppConfig, PaymentRecord, ValidationError, ValidationIssue

_BIC_RE = re.compile(r"^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$")
_E2E_RE = re.compile(r"^[A-Za-z0-9\-\./:]{1,35}$")
_PURPOSE_RE = re.compile(r"^[A-Z0-9]{4}$")


def validate_iban(iban: str) -> bool:
    value = iban.replace(" ", "").upper()
    if len(value) < 15 or len(value) > 34:
        return False
    if not value[:2].isalpha() or not value[2:4].isdigit():
        return False
    rearranged = value[4:] + value[:4]
    numeric = ""
    for char in rearranged:
        if char.isdigit():
            numeric += char
        elif "A" <= char <= "Z":
            numeric += str(ord(char) - 55)
        else:
            return False
    return int(numeric) % 97 == 1


def validate_bic(bic: str) -> bool:
    return bool(_BIC_RE.match(bic.strip().upper()))


def validate_payments(config: AppConfig, payments: list[PaymentRecord]) -> None:
    issues: list[ValidationIssue] = []
    seen_e2e: set[str] = set()

    if not payments:
        issues.append(
            ValidationIssue(
                row_number=0,
                field="CSV",
                code="EMPTY_FILE",
                message="No payment rows found in CSV",
            )
        )

    for payment in payments:
        if not payment.creditor_name:
            issues.append(_issue(payment.row_number, "Name", "REQUIRED", "creditor name is empty"))
        if len(payment.creditor_name) > 70:
            issues.append(_issue(payment.row_number, "Name", "TOO_LONG", "name exceeds 70 chars"))
        if not validate_iban(payment.creditor_iban):
            issues.append(_issue(payment.row_number, "IBAN", "INVALID_IBAN", "invalid creditor IBAN"))
        if payment.creditor_bic and not validate_bic(payment.creditor_bic):
            issues.append(_issue(payment.row_number, "BIC", "INVALID_BIC", "invalid creditor BIC"))
        if payment.amount <= Decimal("0"):
            issues.append(_issue(payment.row_number, "Betrag", "INVALID_AMOUNT", "amount must be > 0"))
        if len(payment.remittance_unstructured) > 140:
            issues.append(
                _issue(
                    payment.row_number,
                    "Verwendungszweck",
                    "TOO_LONG",
                    "remittance text exceeds 140 chars",
                )
            )
        if len(payment.end_to_end_id) > 35:
            issues.append(
                _issue(
                    payment.row_number,
                    "EndToEndId",
                    "TOO_LONG",
                    "EndToEndId exceeds 35 chars",
                )
            )
        if not _E2E_RE.match(payment.end_to_end_id):
            issues.append(
                _issue(
                    payment.row_number,
                    "EndToEndId",
                    "INVALID_FORMAT",
                    "EndToEndId must match [A-Za-z0-9-./:] and be 1..35 chars",
                )
            )
        if payment.end_to_end_id in seen_e2e:
            issues.append(
                _issue(
                    payment.row_number,
                    "EndToEndId",
                    "DUPLICATE",
                    "EndToEndId must be unique",
                )
            )
            if payment.execution_date < date.today():
                issues.append(
                    _issue(
                        payment.row_number,
                        "ExecutionDate",
                        "IN_PAST",
                        "execution date must not be in the past",
                    )
                )

            if payment.purpose_code and not _PURPOSE_RE.match(payment.purpose_code):
                issues.append(
                    _issue(
                        payment.row_number,
                        "PurposeCode",
                        "INVALID_FORMAT",
                        "PurposeCode must be 4 upper-case letters or digits",
                    )
                )

        seen_e2e.add(payment.end_to_end_id)

        if payment.creditor_iban == config.debtor_iban:
            issues.append(
                _issue(
                    payment.row_number,
                    "IBAN",
                    "SELF_TRANSFER",
                    "creditor IBAN must differ from debtor IBAN",
                )
            )

    if not validate_iban(config.debtor_iban):
        issues.append(_issue(0, "Config.debtor_iban", "INVALID_IBAN", "invalid debtor IBAN"))
    if config.debtor_bic and not validate_bic(config.debtor_bic):
        issues.append(_issue(0, "Config.debtor_bic", "INVALID_BIC", "invalid debtor BIC"))

    if issues:
        raise ValidationError(issues)


def _issue(row: int, field: str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(row_number=row, field=field, code=code, message=message)
