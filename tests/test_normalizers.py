from datetime import date

import pytest

from persian_tabular_cleaner import (
    jalali_to_gregorian,
    normalize_digits,
    normalize_iranian_mobile,
    normalize_persian_text,
)


def test_normalizes_arabic_characters_digits_and_spacing() -> None:
    assert normalize_persian_text("  علي  كريمي  ۱۲۳  ") == "علی کریمی 123"


def test_can_render_persian_digits() -> None:
    assert normalize_digits("Invoice 123 / ٤٥", "persian") == "Invoice ۱۲۳ / ۴۵"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("0912 123 4567", "+989121234567"),
        ("+98-912-123-4567", "+989121234567"),
        ("۰۰۹۸۹۱۲۱۲۳۴۵۶۷", "+989121234567"),
    ],
)
def test_normalizes_iranian_mobile(raw: str, expected: str) -> None:
    assert normalize_iranian_mobile(raw) == expected


def test_rejects_invalid_mobile() -> None:
    with pytest.raises(ValueError, match="valid Iranian"):
        normalize_iranian_mobile("021-12345678")


def test_converts_jalali_new_year() -> None:
    assert jalali_to_gregorian("۱۴۰۳/۰۱/۰۱") == date(2024, 3, 20)
