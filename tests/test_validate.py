from datetime import date, timedelta
from decimal import Decimal

import pytest

from csv_to_sepa.models import AppConfig, PaymentRecord, ValidationError
from csv_to_sepa.validate import validate_bic, validate_iban, validate_payments


def test_validate_iban_ok() -> None:
    assert validate_iban("DE89370400440532013000")


def test_validate_bic_ok() -> None:
    assert validate_bic("COKSDE33XXX")


def test_validate_payments_reject_self_transfer() -> None:
    config = AppConfig(debtor_name="Sender", debtor_iban="DE89370400440532013000")
    payments = [
        PaymentRecord(
            row_number=2,
            creditor_name="Receiver",
            creditor_iban="DE89370400440532013000",
            creditor_bic=None,
            amount=Decimal("10.00"),
            remittance_unstructured="Test",
            execution_date=date.today() + timedelta(days=1),
            end_to_end_id="E2E-1",
        )
    ]

    with pytest.raises(ValidationError):
        validate_payments(config, payments)
