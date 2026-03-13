from __future__ import annotations

import argparse
from pathlib import Path
from xml.etree import ElementTree as ET

from .config import create_config_interactive, load_config
from .csv_reader import parse_csv
from .models import ValidationError
from .normalize import parse_execution_date
from .pain001_writer import build_pain_001_001_09
from .template import create_csv_template
from .validate import validate_payments


CLI_MESSAGES = {
    "en": {
        "config_written": "Config written to {path}",
        "debtor_iban": "Debtor IBAN: {iban}",
        "next_steps": "Next steps:",
        "next_validate": "- csv-to-sepa validate-csv {config} examples/input_minimal.csv",
        "next_convert": "- csv-to-sepa convert {config} examples/input_minimal.csv output.xml",
        "readme_hint": "- See README.md for full usage and extended CSV examples",
        "csv_valid": "CSV valid. Rows: {rows} Total: {total:.2f} EUR",
        "xml_written": "XML written to {path}",
        "xml_stats": "Transactions: {rows} Total: {total:.2f} EUR",
        "xml_valid": "XML is valid against XSD",
        "validation_failed": "Validation failed:",
        "command_failed": "Command failed:",
        "possible_causes": "Possible causes:",
        "cause_config": "- Invalid config file or missing required fields",
        "cause_csv": "- CSV format mismatch, invalid value, or wrong delimiter/encoding",
        "cause_dates": "- Invalid date in CSV or execution date settings",
        "cause_data": "- Business-rule violation (e.g. invalid IBAN/BIC, duplicate EndToEndId)",
        "validation_prefix_row": "row {row}",
        "validation_prefix_global": "global",
        "template_written": "CSV template written to {path} (mode={mode})",
        "xsd_import_error": "lxml is required for validate-xml (pip install .[xml])",
        "xml_input_missing": "XML input file not found: {path}",
        "xsd_input_missing": "XSD file not found: {path}",
        "xsd_input_missing_hint": "Hint: place the XSD file in your current directory or pass an explicit path, e.g. csv-to-sepa validate-xml output.xml ./xsd/pain.001.001.09.xsd\nDownload sources: EPC SCT C2PSP Implementation Guidelines page: https://www.europeanpaymentscouncil.eu/document-library/implementation-guidelines/sepa-credit-transfer-customer-psp-implementation-1\nISO 20022 message catalogue (business area 'pain'): https://www.iso20022.org/business-area/81/download",
        "xml_read_error": "Could not read XML/XSD: {error}",
        "namespace_detected": "Detected XML namespace: {namespace}",
        "namespace_message_id": "Detected message identifier: {message_id}",
        "namespace_suggest_intro": "Suggested XSD path(s):",
        "namespace_suggest_local": "- ./xsd/{message_id}.xsd",
        "namespace_suggest_epc": "- ./xsd/EPC132-08_2025_V1.0_{message_id}.xsd",
        "namespace_validate_example": "Validation example: csv-to-sepa validate-xml {xml_path} ./xsd/{message_id}.xsd",
        "namespace_not_found": "Could not detect XML namespace from document root",
        "namespace_parse_error": "Could not parse XML: {error}",
    },
    "de": {
        "config_written": "Konfiguration wurde geschrieben: {path}",
        "debtor_iban": "Debitor-IBAN: {iban}",
        "next_steps": "Nächste Schritte:",
        "next_validate": "- csv-to-sepa validate-csv {config} examples/input_minimal.csv",
        "next_convert": "- csv-to-sepa convert {config} examples/input_minimal.csv output.xml",
        "readme_hint": "- Siehe README.md für vollständige Nutzung und erweiterte CSV-Beispiele",
        "csv_valid": "CSV ist gültig. Zeilen: {rows} Summe: {total:.2f} EUR",
        "xml_written": "XML wurde geschrieben: {path}",
        "xml_stats": "Transaktionen: {rows} Summe: {total:.2f} EUR",
        "xml_valid": "XML ist gegen XSD gültig",
        "validation_failed": "Validierung fehlgeschlagen:",
        "command_failed": "Befehl fehlgeschlagen:",
        "possible_causes": "Mögliche Ursachen:",
        "cause_config": "- Ungültige Konfigurationsdatei oder fehlende Pflichtfelder",
        "cause_csv": "- CSV-Format passt nicht, ungültiger Wert, oder falscher Trenner/Encoding",
        "cause_dates": "- Ungültiges Datum in CSV oder in den Ausführungsdatum-Einstellungen",
        "cause_data": "- Verstoß gegen Fachregeln (z. B. ungültige IBAN/BIC, doppelte EndToEndId)",
        "validation_prefix_row": "Zeile {row}",
        "validation_prefix_global": "global",
        "template_written": "CSV-Template wurde geschrieben: {path} (Modus={mode})",
        "xsd_import_error": "lxml wird für validate-xml benötigt (pip install .[xml])",
        "xml_input_missing": "XML-Eingabedatei nicht gefunden: {path}",
        "xsd_input_missing": "XSD-Datei nicht gefunden: {path}",
        "xsd_input_missing_hint": "Hinweis: Lege die XSD-Datei im aktuellen Verzeichnis ab oder übergib einen expliziten Pfad, z. B. csv-to-sepa validate-xml output.xml ./xsd/pain.001.001.09.xsd\nBezugsquellen: EPC SCT C2PSP Implementation Guidelines-Seite: https://www.europeanpaymentscouncil.eu/document-library/implementation-guidelines/sepa-credit-transfer-customer-psp-implementation-1\nISO 20022 Message-Katalog (Business Area 'pain'): https://www.iso20022.org/business-area/81/download",
        "xml_read_error": "XML/XSD konnte nicht gelesen werden: {error}",
        "namespace_detected": "Erkannter XML-Namespace: {namespace}",
        "namespace_message_id": "Erkannte Message-ID: {message_id}",
        "namespace_suggest_intro": "Empfohlene XSD-Pfade:",
        "namespace_suggest_local": "- ./xsd/{message_id}.xsd",
        "namespace_suggest_epc": "- ./xsd/EPC132-08_2025_V1.0_{message_id}.xsd",
        "namespace_validate_example": "Validierungsbeispiel: csv-to-sepa validate-xml {xml_path} ./xsd/{message_id}.xsd",
        "namespace_not_found": "Konnte keinen XML-Namespace im Dokument-Root erkennen",
        "namespace_parse_error": "XML konnte nicht geparst werden: {error}",
    },
}


def main() -> None:
    parser = argparse.ArgumentParser(description="CSV to SEPA pain.001.001.09 converter")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_config_parser = subparsers.add_parser("init-config", help="Create a config JSON file")
    init_config_parser.add_argument("output", help="Path to output config JSON")
    init_config_parser.add_argument(
        "--language",
        choices=["en", "de"],
        default="en",
        help="Prompt language for interactive setup (default: en)",
    )
    init_config_parser.set_defaults(func=cmd_init_config)

    template_parser = subparsers.add_parser("create-template", help="Create a CSV template file")
    template_parser.add_argument("output", help="Path to output CSV template")
    template_parser.add_argument(
        "--mode",
        choices=["minimal", "extended"],
        default="minimal",
        help="Template mode (minimal or extended)",
    )
    template_parser.add_argument(
        "--template-header-language",
        choices=["de", "en"],
        default="en",
        help="Header label language for generated template (default: en)",
    )
    template_parser.add_argument(
        "--language",
        choices=["en", "de"],
        default="en",
        help="Output language (default: en)",
    )
    template_parser.add_argument("--delimiter", default=";", help="CSV delimiter (default: ;)")
    template_parser.add_argument("--encoding", default="utf-8-sig", help="CSV encoding (default: utf-8-sig)")
    template_parser.set_defaults(func=cmd_create_template)

    validate_csv_parser = subparsers.add_parser("validate-csv", help="Validate CSV without creating XML")
    validate_csv_parser.add_argument("config", help="Path to config JSON")
    validate_csv_parser.add_argument("input", help="Path to input CSV")
    validate_csv_parser.add_argument("--delimiter", default=";", help="CSV delimiter (default: ;)" )
    validate_csv_parser.add_argument("--encoding", default="utf-8-sig", help="CSV encoding (default: utf-8-sig)")
    validate_csv_parser.add_argument("--execution-date", help="Override execution date YYYY-MM-DD")
    validate_csv_parser.add_argument("--strict-ascii", action="store_true", help="Transliterate text to ASCII")
    validate_csv_parser.add_argument(
        "--language",
        choices=["en", "de"],
        default="en",
        help="Output language (default: en)",
    )
    validate_csv_parser.set_defaults(func=cmd_validate_csv)

    convert_parser = subparsers.add_parser("convert", help="Convert CSV to pain.001.001.09 XML")
    convert_parser.add_argument("config", help="Path to config JSON")
    convert_parser.add_argument("input", help="Path to input CSV")
    convert_parser.add_argument("output", help="Path to output XML")
    convert_parser.add_argument("--delimiter", default=";", help="CSV delimiter (default: ;)")
    convert_parser.add_argument("--encoding", default="utf-8-sig", help="CSV encoding (default: utf-8-sig)")
    convert_parser.add_argument("--execution-date", help="Override execution date YYYY-MM-DD")
    convert_parser.add_argument("--strict-ascii", action="store_true", help="Transliterate text to ASCII")
    convert_parser.add_argument(
        "--language",
        choices=["en", "de"],
        default="en",
        help="Output language (default: en)",
    )
    convert_parser.set_defaults(func=cmd_convert)

    validate_xml_parser = subparsers.add_parser("validate-xml", help="Validate XML against XSD using lxml")
    validate_xml_parser.add_argument("input", help="Path to XML file")
    validate_xml_parser.add_argument("xsd", help="Path to XSD file")
    validate_xml_parser.add_argument(
        "--language",
        choices=["en", "de"],
        default="en",
        help="Output language (default: en)",
    )
    validate_xml_parser.set_defaults(func=cmd_validate_xml)

    check_namespace_parser = subparsers.add_parser("check-namespace", help="Inspect XML namespace and suggest matching XSD filenames")
    check_namespace_parser.add_argument("input", help="Path to XML file")
    check_namespace_parser.add_argument(
        "--language",
        choices=["en", "de"],
        default="en",
        help="Output language (default: en)",
    )
    check_namespace_parser.set_defaults(func=cmd_check_namespace)

    args = parser.parse_args()
    args.func(args)


def cmd_init_config(args: argparse.Namespace) -> None:
    msg = _messages(args.language)
    config = create_config_interactive(args.output, language=args.language)
    print(msg["config_written"].format(path=args.output))
    print(msg["debtor_iban"].format(iban=config.debtor_iban))
    print(msg["next_steps"])
    print(msg["next_validate"].format(config=args.output))
    print(msg["next_convert"].format(config=args.output))
    print(msg["readme_hint"])


def cmd_create_template(args: argparse.Namespace) -> None:
    msg = _messages(args.language)
    create_csv_template(
        output=args.output,
        mode=args.mode,
        delimiter=args.delimiter,
        encoding=args.encoding,
        header_language=args.template_header_language,
    )
    print(msg["template_written"].format(path=args.output, mode=args.mode))


def cmd_validate_csv(args: argparse.Namespace) -> None:
    msg = _messages(args.language)
    try:
        config = load_config(args.config)
        execution_date = parse_execution_date(args.execution_date or config.default_execution_date, config.execution_date_offset_days)
        payments = parse_csv(
            file_path=args.input,
            execution_date=execution_date,
            delimiter=args.delimiter,
            encoding=args.encoding,
            strict_ascii=args.strict_ascii,
        )
        validate_payments(config, payments)
        total = sum(p.amount for p in payments)
        print(msg["csv_valid"].format(rows=len(payments), total=total))
    except ValidationError as exc:
        _print_validation_issues(exc, args.language)
        raise SystemExit(2) from exc
    except Exception as exc:
        _print_generic_error(exc, args.language)
        raise SystemExit(2) from exc


def cmd_convert(args: argparse.Namespace) -> None:
    msg = _messages(args.language)
    try:
        config = load_config(args.config)
        execution_date = parse_execution_date(args.execution_date or config.default_execution_date, config.execution_date_offset_days)
        payments = parse_csv(
            file_path=args.input,
            execution_date=execution_date,
            delimiter=args.delimiter,
            encoding=args.encoding,
            strict_ascii=args.strict_ascii,
        )
        validate_payments(config, payments)
    except ValidationError as exc:
        _print_validation_issues(exc, args.language)
        raise SystemExit(2) from exc
    except Exception as exc:
        _print_generic_error(exc, args.language)
        raise SystemExit(2) from exc

    xml_bytes = build_pain_001_001_09(config, payments)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(xml_bytes)

    total = sum(p.amount for p in payments)
    print(msg["xml_written"].format(path=args.output))
    print(msg["xml_stats"].format(rows=len(payments), total=total))


def cmd_validate_xml(args: argparse.Namespace) -> None:
    msg = _messages(args.language)
    try:
        from lxml import etree
    except ImportError as exc:
        raise SystemExit(msg["xsd_import_error"]) from exc

    xml_path = Path(args.input).expanduser()
    xsd_path = Path(args.xsd).expanduser()

    if not xml_path.exists():
        raise SystemExit(msg["xml_input_missing"].format(path=str(xml_path)))
    if not xsd_path.exists():
        raise SystemExit(
            f"{msg['xsd_input_missing'].format(path=str(xsd_path))}\n{msg['xsd_input_missing_hint']}"
        )

    try:
        xml_doc = etree.parse(str(xml_path))
        xsd_doc = etree.parse(str(xsd_path))
    except OSError as exc:
        raise SystemExit(msg["xml_read_error"].format(error=str(exc))) from exc

    schema = etree.XMLSchema(xsd_doc)

    if schema.validate(xml_doc):
        print(msg["xml_valid"])
        return

    for error in schema.error_log:
        print(f"line {error.line}: {error.message}")
    raise SystemExit(1)


def cmd_check_namespace(args: argparse.Namespace) -> None:
    msg = _messages(args.language)
    xml_path = Path(args.input).expanduser()

    if not xml_path.exists():
        raise SystemExit(msg["xml_input_missing"].format(path=str(xml_path)))

    namespace, message_id = _extract_namespace_and_message_id(xml_path)
    if not namespace or not message_id:
        raise SystemExit(msg["namespace_not_found"])

    print(msg["namespace_detected"].format(namespace=namespace))
    print(msg["namespace_message_id"].format(message_id=message_id))
    print(msg["namespace_suggest_intro"])
    print(msg["namespace_suggest_local"].format(message_id=message_id))
    print(msg["namespace_suggest_epc"].format(message_id=message_id))
    print(msg["namespace_validate_example"].format(xml_path=str(xml_path), message_id=message_id))


def _extract_namespace_and_message_id(xml_path: Path) -> tuple[str | None, str | None]:
    try:
        root = ET.parse(str(xml_path)).getroot()
    except ET.ParseError:
        return None, None

    tag = root.tag
    if not (isinstance(tag, str) and tag.startswith("{")):
        return None, None

    namespace = tag[1:].split("}", 1)[0]
    if "xsd:" not in namespace:
        return namespace, None
    message_id = namespace.rsplit("xsd:", 1)[-1]
    return namespace, message_id


def _print_validation_issues(exc: ValidationError, language: str) -> None:
    msg = _messages(language)
    print(msg["validation_failed"])
    for issue in exc.issues:
        if issue.row_number:
            prefix = msg["validation_prefix_row"].format(row=issue.row_number)
        else:
            prefix = msg["validation_prefix_global"]
        value_suffix = f" | value={issue.value}" if issue.value else ""
        print(f"- {prefix} | {issue.field} | {issue.code} | {issue.message}{value_suffix}")


def _print_generic_error(exc: Exception, language: str) -> None:
    msg = _messages(language)
    print(msg["command_failed"])
    print(f"- {type(exc).__name__}: {exc}")
    print(msg["possible_causes"])
    print(msg["cause_config"])
    print(msg["cause_csv"])
    print(msg["cause_dates"])
    print(msg["cause_data"])


def _messages(language: str) -> dict[str, str]:
    return CLI_MESSAGES["de"] if language.lower() == "de" else CLI_MESSAGES["en"]


if __name__ == "__main__":
    main()
