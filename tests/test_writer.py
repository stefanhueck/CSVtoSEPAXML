from datetime import date, timedelta
from decimal import Decimal
from xml.etree import ElementTree as ET

from csv_to_sepa.models import AppConfig, PaymentRecord
from csv_to_sepa.pain001_writer import NS, build_pain_001_001_09


def test_writer_generates_ctrlsum_and_nboftxs() -> None:
    execution_date = date.today() + timedelta(days=1)
    config = AppConfig(debtor_name="Sender", debtor_iban="DE89370400440532013000")
    payments = [
        PaymentRecord(
            row_number=2,
            creditor_name="Augstein Rolf",
            creditor_iban="DE37370502991325006652",
            creditor_bic="COKSDE33XXX",
            amount=Decimal("24.00"),
            remittance_unstructured="Jagdpachtverteilung",
            execution_date=execution_date,
            end_to_end_id="E2E-1",
        ),
        PaymentRecord(
            row_number=3,
            creditor_name="Agnes Paula",
            creditor_iban="DE89120300001012637888",
            creditor_bic="BYLADEM1001",
            amount=Decimal("63.27"),
            remittance_unstructured="Jagdpachtverteilung",
            execution_date=execution_date,
            end_to_end_id="E2E-2",
        ),
    ]

    xml_bytes = build_pain_001_001_09(config, payments)
    root = ET.fromstring(xml_bytes)
    ns = {"n": NS}

    nb_of_txs = root.findtext(".//n:GrpHdr/n:NbOfTxs", namespaces=ns)
    ctrl_sum = root.findtext(".//n:GrpHdr/n:CtrlSum", namespaces=ns)

    assert nb_of_txs == "2"
    assert ctrl_sum == "87.27"


def test_writer_splits_payment_info_by_execution_date_and_writes_purpose() -> None:
    execution_date_1 = date.today() + timedelta(days=1)
    execution_date_2 = date.today() + timedelta(days=2)
    config = AppConfig(debtor_name="Sender", debtor_iban="DE89370400440532013000")
    payments = [
        PaymentRecord(
            row_number=2,
            creditor_name="A",
            creditor_iban="DE37370502991325006652",
            creditor_bic=None,
            amount=Decimal("10.00"),
            remittance_unstructured="Ref A",
            execution_date=execution_date_1,
            end_to_end_id="E2E-1",
            purpose_code="SALA",
        ),
        PaymentRecord(
            row_number=3,
            creditor_name="B",
            creditor_iban="DE89120300001012637888",
            creditor_bic=None,
            amount=Decimal("11.00"),
            remittance_unstructured="Ref B",
            execution_date=execution_date_2,
            end_to_end_id="E2E-2",
            purpose_code=None,
        ),
    ]

    xml_bytes = build_pain_001_001_09(config, payments)
    root = ET.fromstring(xml_bytes)
    ns = {"n": NS}

    payment_infos = root.findall(".//n:PmtInf", namespaces=ns)
    purpose_codes = root.findall(".//n:CdtTrfTxInf/n:Purp/n:Cd", namespaces=ns)

    assert len(payment_infos) == 2
    assert len(purpose_codes) == 1
    assert purpose_codes[0].text == "SALA"
