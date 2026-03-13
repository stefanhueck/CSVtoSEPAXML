from __future__ import annotations

from collections import defaultdict
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from xml.etree import ElementTree as ET

from .models import AppConfig, PaymentRecord

NS = "urn:iso:std:iso:20022:tech:xsd:pain.001.001.09"


def build_pain_001_001_09(config: AppConfig, payments: list[PaymentRecord]) -> bytes:
    ET.register_namespace("", NS)

    total_amount = sum((payment.amount for payment in payments), Decimal("0.00"))
    tx_count = len(payments)

    document = ET.Element(_tag("Document"))
    cstmr_cdt_trf_initn = ET.SubElement(document, _tag("CstmrCdtTrfInitn"))

    _build_group_header(cstmr_cdt_trf_initn, config, tx_count, total_amount)

    grouped = _group_by_execution_date(payments)
    for index, execution_date in enumerate(sorted(grouped.keys()), start=1):
        payment_group = grouped[execution_date]
        group_total = sum((payment.amount for payment in payment_group), Decimal("0.00"))
        _build_payment_info(cstmr_cdt_trf_initn, config, payment_group, group_total, index)

    xml_bytes = ET.tostring(document, encoding="utf-8", xml_declaration=True)
    return xml_bytes


def _build_group_header(parent: ET.Element, config: AppConfig, tx_count: int, total_amount: Decimal) -> None:
    grp_hdr = ET.SubElement(parent, _tag("GrpHdr"))
    now_utc = datetime.now(timezone.utc)
    msg_id = f"MSG-{now_utc.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"
    ET.SubElement(grp_hdr, _tag("MsgId")).text = msg_id[:35]
    ET.SubElement(grp_hdr, _tag("CreDtTm")).text = now_utc.replace(microsecond=0).isoformat()
    ET.SubElement(grp_hdr, _tag("NbOfTxs")).text = str(tx_count)
    ET.SubElement(grp_hdr, _tag("CtrlSum")).text = _format_amount(total_amount)

    initg_pty = ET.SubElement(grp_hdr, _tag("InitgPty"))
    ET.SubElement(initg_pty, _tag("Nm")).text = (config.initiating_party_name or config.debtor_name)[:70]


def _build_payment_info(
    parent: ET.Element,
    config: AppConfig,
    payments: list[PaymentRecord],
    total_amount: Decimal,
    payment_info_index: int,
) -> None:
    pmt_inf = ET.SubElement(parent, _tag("PmtInf"))
    now_utc = datetime.now(timezone.utc)
    pmt_inf_id = f"PMT-{now_utc.strftime('%Y%m%d%H%M%S')}-{payment_info_index:03d}-{uuid.uuid4().hex[:4].upper()}"
    ET.SubElement(pmt_inf, _tag("PmtInfId")).text = pmt_inf_id[:35]
    ET.SubElement(pmt_inf, _tag("PmtMtd")).text = "TRF"
    ET.SubElement(pmt_inf, _tag("BtchBookg")).text = "true" if config.batch_booking else "false"
    ET.SubElement(pmt_inf, _tag("NbOfTxs")).text = str(len(payments))
    ET.SubElement(pmt_inf, _tag("CtrlSum")).text = _format_amount(total_amount)

    pmt_tp_inf = ET.SubElement(pmt_inf, _tag("PmtTpInf"))
    svc_lvl = ET.SubElement(pmt_tp_inf, _tag("SvcLvl"))
    ET.SubElement(svc_lvl, _tag("Cd")).text = "SEPA"

    reqd_exctn_dt = ET.SubElement(pmt_inf, _tag("ReqdExctnDt"))
    ET.SubElement(reqd_exctn_dt, _tag("Dt")).text = payments[0].execution_date.isoformat()

    dbtr = ET.SubElement(pmt_inf, _tag("Dbtr"))
    ET.SubElement(dbtr, _tag("Nm")).text = config.debtor_name[:70]

    dbtr_acct = ET.SubElement(pmt_inf, _tag("DbtrAcct"))
    dbtr_acct_id = ET.SubElement(dbtr_acct, _tag("Id"))
    ET.SubElement(dbtr_acct_id, _tag("IBAN")).text = config.debtor_iban

    dbtr_agt = ET.SubElement(pmt_inf, _tag("DbtrAgt"))
    fin_inst_id = ET.SubElement(dbtr_agt, _tag("FinInstnId"))
    if config.debtor_bic:
        ET.SubElement(fin_inst_id, _tag("BICFI")).text = config.debtor_bic
    else:
        othr = ET.SubElement(fin_inst_id, _tag("Othr"))
        ET.SubElement(othr, _tag("Id")).text = "NOTPROVIDED"

    ET.SubElement(pmt_inf, _tag("ChrgBr")).text = config.charge_bearer

    for payment in payments:
        _build_tx(pmt_inf, payment)


def _build_tx(parent: ET.Element, payment: PaymentRecord) -> None:
    tx = ET.SubElement(parent, _tag("CdtTrfTxInf"))

    pmt_id = ET.SubElement(tx, _tag("PmtId"))
    ET.SubElement(pmt_id, _tag("InstrId")).text = payment.end_to_end_id
    ET.SubElement(pmt_id, _tag("EndToEndId")).text = payment.end_to_end_id

    amt = ET.SubElement(tx, _tag("Amt"))
    instd_amt = ET.SubElement(amt, _tag("InstdAmt"))
    instd_amt.set("Ccy", "EUR")
    instd_amt.text = _format_amount(payment.amount)

    if payment.purpose_code:
        purp = ET.SubElement(tx, _tag("Purp"))
        ET.SubElement(purp, _tag("Cd")).text = payment.purpose_code

    if payment.creditor_bic:
        cdtr_agt = ET.SubElement(tx, _tag("CdtrAgt"))
        fin_inst_id = ET.SubElement(cdtr_agt, _tag("FinInstnId"))
        ET.SubElement(fin_inst_id, _tag("BICFI")).text = payment.creditor_bic

    cdtr = ET.SubElement(tx, _tag("Cdtr"))
    ET.SubElement(cdtr, _tag("Nm")).text = payment.creditor_name

    cdtr_acct = ET.SubElement(tx, _tag("CdtrAcct"))
    cdtr_acct_id = ET.SubElement(cdtr_acct, _tag("Id"))
    ET.SubElement(cdtr_acct_id, _tag("IBAN")).text = payment.creditor_iban

    rmt_inf = ET.SubElement(tx, _tag("RmtInf"))
    ET.SubElement(rmt_inf, _tag("Ustrd")).text = payment.remittance_unstructured


def _tag(local_name: str) -> str:
    return f"{{{NS}}}{local_name}"


def _format_amount(amount: Decimal) -> str:
    return f"{amount.quantize(Decimal('0.01')):.2f}"


def _group_by_execution_date(payments: list[PaymentRecord]) -> dict:
    grouped: dict = defaultdict(list)
    for payment in payments:
        grouped[payment.execution_date].append(payment)
    return grouped
