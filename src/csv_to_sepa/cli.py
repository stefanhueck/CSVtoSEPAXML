from __future__ import annotations

import argparse
from pathlib import Path

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

    xml_doc = etree.parse(args.input)
    xsd_doc = etree.parse(args.xsd)
    schema = etree.XMLSchema(xsd_doc)

    if schema.validate(xml_doc):
        print(msg["xml_valid"])
        return

    for error in schema.error_log:
        print(f"line {error.line}: {error.message}")
    raise SystemExit(1)


def _print_validation_issues(exc: ValidationError, language: str) -> None:
    msg = _messages(language)
    print(msg["validation_failed"])
    for issue in exc.issues:
        if issue.row_number:
            prefix = msg["validation_prefix_row"].format(row=issue.row_number)
        else:
            prefix = msg["validation_prefix_global"]
        print(f"- {prefix} | {issue.field} | {issue.code} | {issue.message}")


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
