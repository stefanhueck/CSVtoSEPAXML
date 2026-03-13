from decimal import Decimal

from csv_to_sepa.normalize import parse_amount_eur


def test_parse_amount_with_comma() -> None:
    assert parse_amount_eur("24,00") == Decimal("24.00")


def test_parse_amount_with_thousands() -> None:
    assert parse_amount_eur("1.234,56") == Decimal("1234.56")
