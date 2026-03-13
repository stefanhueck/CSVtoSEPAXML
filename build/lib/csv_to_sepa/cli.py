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


def main() -> None:
    parser = argparse.ArgumentParser(description="CSV to SEPA pain.001.001.09 converter")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_config_parser = subparsers.add_parser("init-config", help="Create a config JSON file")
    init_config_parser.add_argument("output", help="Path to output config JSON")
    init_config_parser.set_defaults(func=cmd_init_config)

    template_parser = subparsers.add_parser("create-template", help="Create a CSV template file")
    template_parser.add_argument("output", help="Path to output CSV template")
    template_parser.add_argument(
        "--mode",
        choices=["minimal", "extended"],
        default="minimal",
        help="Template mode (minimal or extended)",
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
    validate_csv_parser.set_defaults(func=cmd_validate_csv)

    convert_parser = subparsers.add_parser("convert", help="Convert CSV to pain.001.001.09 XML")
    convert_parser.add_argument("config", help="Path to config JSON")
    convert_parser.add_argument("input", help="Path to input CSV")
    convert_parser.add_argument("output", help="Path to output XML")
    convert_parser.add_argument("--delimiter", default=";", help="CSV delimiter (default: ;)")
    convert_parser.add_argument("--encoding", default="utf-8-sig", help="CSV encoding (default: utf-8-sig)")
    convert_parser.add_argument("--execution-date", help="Override execution date YYYY-MM-DD")
    convert_parser.add_argument("--strict-ascii", action="store_true", help="Transliterate text to ASCII")
    convert_parser.set_defaults(func=cmd_convert)

    validate_xml_parser = subparsers.add_parser("validate-xml", help="Validate XML against XSD using lxml")
    validate_xml_parser.add_argument("input", help="Path to XML file")
    validate_xml_parser.add_argument("xsd", help="Path to XSD file")
    validate_xml_parser.set_defaults(func=cmd_validate_xml)

    args = parser.parse_args()
    args.func(args)


def cmd_init_config(args: argparse.Namespace) -> None:
    config = create_config_interactive(args.output)
    print(f"Config written to {args.output}")
    print(f"Debtor IBAN: {config.debtor_iban}")


def cmd_create_template(args: argparse.Namespace) -> None:
    create_csv_template(
        output=args.output,
        mode=args.mode,
        delimiter=args.delimiter,
        encoding=args.encoding,
    )
    print(f"CSV template written to {args.output} (mode={args.mode})")


def cmd_validate_csv(args: argparse.Namespace) -> None:
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
    print(f"CSV valid. Rows: {len(payments)} Total: {total:.2f} EUR")


def cmd_convert(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    execution_date = parse_execution_date(args.execution_date or config.default_execution_date, config.execution_date_offset_days)
    payments = parse_csv(
        file_path=args.input,
        execution_date=execution_date,
        delimiter=args.delimiter,
        encoding=args.encoding,
        strict_ascii=args.strict_ascii,
    )
    try:
        validate_payments(config, payments)
    except ValidationError as exc:
        _print_validation_issues(exc)
        raise SystemExit(2) from exc

    xml_bytes = build_pain_001_001_09(config, payments)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(xml_bytes)

    total = sum(p.amount for p in payments)
    print(f"XML written to {args.output}")
    print(f"Transactions: {len(payments)} Total: {total:.2f} EUR")


def cmd_validate_xml(args: argparse.Namespace) -> None:
    try:
        from lxml import etree
    except ImportError as exc:
        raise SystemExit("lxml is required for validate-xml (pip install .[xml])") from exc

    xml_doc = etree.parse(args.input)
    xsd_doc = etree.parse(args.xsd)
    schema = etree.XMLSchema(xsd_doc)

    if schema.validate(xml_doc):
        print("XML is valid against XSD")
        return

    for error in schema.error_log:
        print(f"line {error.line}: {error.message}")
    raise SystemExit(1)


def _print_validation_issues(exc: ValidationError) -> None:
    print("Validation failed:")
    for issue in exc.issues:
        prefix = f"row {issue.row_number}" if issue.row_number else "global"
        print(f"- {prefix} | {issue.field} | {issue.code} | {issue.message}")


if __name__ == "__main__":
    main()
