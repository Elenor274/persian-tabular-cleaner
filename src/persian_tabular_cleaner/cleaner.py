"""DataFrame-level cleaning with a machine-readable audit report."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Any

import pandas as pd

from .normalizers import (
    DigitStyle,
    jalali_to_gregorian,
    normalize_iranian_mobile,
    normalize_persian_text,
)


@dataclass(frozen=True, slots=True)
class CleanerConfig:
    """Declare which columns should receive each safe transformation."""

    text_columns: tuple[str, ...] = ()
    phone_columns: tuple[str, ...] = ()
    jalali_date_columns: tuple[str, ...] = ()
    digit_style: DigitStyle = "english"
    international_phones: bool = True
    strict_columns: bool = False


@dataclass(slots=True)
class CleaningReport:
    """Summarize exactly what a cleaning run changed or rejected."""

    rows: int
    columns: int
    changed_cells: int = 0
    column_changes: dict[str, int] = field(default_factory=dict)
    invalid_values: dict[str, int] = field(default_factory=dict)
    missing_columns: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _is_blank(value: object) -> bool:
    return pd.isna(value) or (isinstance(value, str) and not value.strip())


def _changed(before: object, after: object) -> bool:
    if pd.isna(before) and pd.isna(after):
        return False
    return str(before) != str(after)


def _clean_column(
    frame: pd.DataFrame,
    column: str,
    converter: Callable[[object], object],
    report: CleaningReport,
) -> None:
    changes = 0
    invalid = 0
    cleaned_values: list[object] = []

    for value in frame[column].tolist():
        if _is_blank(value):
            cleaned_values.append(value)
            continue
        try:
            cleaned = converter(value)
        except ValueError:
            cleaned = value
            invalid += 1
        cleaned_values.append(cleaned)
        changes += int(_changed(value, cleaned))

    frame[column] = cleaned_values
    if changes:
        report.column_changes[column] = report.column_changes.get(column, 0) + changes
        report.changed_cells += changes
    if invalid:
        report.invalid_values[column] = report.invalid_values.get(column, 0) + invalid


def clean_dataframe(
    data: pd.DataFrame,
    config: CleanerConfig,
) -> tuple[pd.DataFrame, CleaningReport]:
    """Return a cleaned copy and an audit report without mutating the input."""
    cleaned = data.copy(deep=True)
    report = CleaningReport(rows=len(cleaned), columns=len(cleaned.columns))

    requested = dict.fromkeys(
        (*config.text_columns, *config.phone_columns, *config.jalali_date_columns)
    )
    report.missing_columns = [name for name in requested if name not in cleaned.columns]
    if config.strict_columns and report.missing_columns:
        missing = ", ".join(report.missing_columns)
        raise KeyError(f"Missing configured columns: {missing}")

    for column in config.text_columns:
        if column in cleaned.columns:
            _clean_column(
                cleaned,
                column,
                lambda value: normalize_persian_text(
                    value,
                    digit_style=config.digit_style,
                ),
                report,
            )

    for column in config.phone_columns:
        if column in cleaned.columns:
            _clean_column(
                cleaned,
                column,
                lambda value: normalize_iranian_mobile(
                    value,
                    international=config.international_phones,
                ),
                report,
            )

    for column in config.jalali_date_columns:
        if column in cleaned.columns:
            _clean_column(
                cleaned,
                column,
                lambda value: jalali_to_gregorian(value).isoformat(),
                report,
            )

    return cleaned, report
