"""Small, predictable normalizers for common Persian business data."""

from __future__ import annotations

import re
import unicodedata
from datetime import date
from typing import Literal

from persiantools.jdatetime import JalaliDate

DigitStyle = Literal["english", "persian", "keep"]

_PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
_ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
_ENGLISH_DIGITS = "0123456789"

_TO_ENGLISH = str.maketrans(
    _PERSIAN_DIGITS + _ARABIC_DIGITS,
    _ENGLISH_DIGITS + _ENGLISH_DIGITS,
)
_TO_PERSIAN = str.maketrans(
    _ENGLISH_DIGITS + _ARABIC_DIGITS,
    _PERSIAN_DIGITS + _PERSIAN_DIGITS,
)
_ARABIC_TO_PERSIAN = str.maketrans(
    {
        "ي": "ی",
        "ى": "ی",
        "ك": "ک",
        "ة": "ه",
        "ۀ": "هٔ",
    }
)
_BIDI_CONTROLS = dict.fromkeys(
    map(ord, "\u200e\u200f\u202a\u202b\u202c\u202d\u202e\ufeff")
)
_DIACRITICS = re.compile("[\u064b-\u065f\u0670\u06d6-\u06ed]")
_WHITESPACE = re.compile(r"[ \t\r\f\v]+")


def normalize_digits(value: object, style: DigitStyle = "english") -> str:
    """Convert Persian, Arabic, and English digits to one chosen script."""
    text = str(value)
    if style == "english":
        return text.translate(_TO_ENGLISH)
    if style == "persian":
        return text.translate(_TO_PERSIAN)
    if style == "keep":
        return text
    raise ValueError("style must be 'english', 'persian', or 'keep'.")


def normalize_persian_text(
    value: object,
    *,
    digit_style: DigitStyle = "english",
    remove_diacritics: bool = True,
) -> str:
    """Normalize Persian characters, hidden controls, digits, and spacing."""
    text = unicodedata.normalize("NFKC", str(value))
    text = text.translate(_BIDI_CONTROLS).translate(_ARABIC_TO_PERSIAN)
    if remove_diacritics:
        text = _DIACRITICS.sub("", text)
    text = normalize_digits(text, digit_style)
    text = "\n".join(_WHITESPACE.sub(" ", line).strip() for line in text.splitlines())
    text = re.sub(r"\s*\u200c\s*", "\u200c", text)
    return text.strip()


def normalize_iranian_mobile(value: object, *, international: bool = True) -> str:
    """Normalize a valid Iranian mobile number to +98 or local 09 format."""
    raw = normalize_digits(value, "english").strip()
    digits = re.sub(r"\D", "", raw)

    if digits.startswith("0098"):
        digits = digits[2:]
    if digits.startswith("98") and len(digits) == 12:
        local = "0" + digits[2:]
    elif digits.startswith("9") and len(digits) == 10:
        local = "0" + digits
    else:
        local = digits

    if not re.fullmatch(r"09\d{9}", local):
        raise ValueError("Not a valid Iranian mobile number.")

    return "+98" + local[1:] if international else local


def jalali_to_gregorian(value: object) -> date:
    """Parse a YYYY/MM/DD Jalali date and return a Gregorian date."""
    text = normalize_digits(value, "english").strip()
    parts = re.split(r"[-/.]", text)
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise ValueError("Jalali date must use YYYY/MM/DD, YYYY-MM-DD, or YYYY.MM.DD.")

    year, month, day = map(int, parts)
    try:
        return JalaliDate(year, month, day).to_gregorian()
    except (TypeError, ValueError) as error:
        raise ValueError("Invalid Jalali date.") from error
