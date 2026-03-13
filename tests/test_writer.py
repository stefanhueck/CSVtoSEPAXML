from datetime import date
from decimal import Decimal
from xml.etree import ElementTree as ET

from csv_to_sepa.models import AppConfig, PaymentRecord
from csv_to_sepa.pain001_writer import NS, build_pain_001_001_09


def test_writer_generates_ctrlsum_and_nboftxs() -> None:
    config = AppConfig(debtor_name="Sender", debtor_iban="DE89370400440532013000")
    payments = [
        PaymentRecord(
            row_number=2,
            creditor_name="Augstein Rolf",
            creditor_iban="DE37370502991325006652",
            creditor_bic="COKSDE33XXX",
            amount=Decimal("24.00"),
            remittance_unstructured="Jagdpachtverteilung",
            execution_date=date(2026, 3, 14),
            end_to_end_id="E2E-1",
        ),
        PaymentRecord(
            row_number=3,
            creditor_name="Agnes Paula",
            creditor_iban="DE89120300001012637888",
            creditor_bic="BYLADEM1001",
            amount=Decimal("63.27"),
            remittance_unstructured="Jagdpachtverteilung",
            execution_date=date(2026, 3, 14),
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
