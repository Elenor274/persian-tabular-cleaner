"""Command-line interface for cleaning CSV and Excel files."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from .cleaner import CleanerConfig, clean_dataframe


def _columns(value: str) -> tuple[str, ...]:
    return tuple(column.strip() for column in value.split(",") if column.strip())


def _read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path, encoding="utf-8-sig")
    if suffix in {".xlsx", ".xlsm"}:
        return pd.read_excel(path)
    raise ValueError("Input must be a .csv, .xlsx, or .xlsm file.")


def _write_table(data: pd.DataFrame, path: Path) -> None:
    suffix = path.suffix.lower()
    path.parent.mkdir(parents=True, exist_ok=True)
    if suffix == ".csv":
        data.to_csv(path, index=False, encoding="utf-8-sig")
        return
    if suffix == ".xlsx":
        data.to_excel(path, index=False)
        return
    raise ValueError("Output must be a .csv or .xlsx file.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="persian-clean",
        description="Clean Persian CSV and Excel columns with an audit report.",
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--text-columns", type=_columns, default=())
    parser.add_argument("--phone-columns", type=_columns, default=())
    parser.add_argument("--jalali-date-columns", type=_columns, default=())
    parser.add_argument(
        "--digits",
        choices=("english", "persian", "keep"),
        default="english",
    )
    parser.add_argument(
        "--local-phones",
        action="store_true",
        help="Write phones as 09... instead of +98...",
    )
    parser.add_argument("--strict-columns", action="store_true")
    parser.add_argument("--report", type=Path, help="Optional JSON report path")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        data = _read_table(args.input)
        cleaned, report = clean_dataframe(
            data,
            CleanerConfig(
                text_columns=args.text_columns,
                phone_columns=args.phone_columns,
                jalali_date_columns=args.jalali_date_columns,
                digit_style=args.digits,
                international_phones=not args.local_phones,
                strict_columns=args.strict_columns,
            ),
        )
        _write_table(cleaned, args.output)
    except (KeyError, OSError, ValueError) as error:
        build_parser().error(str(error))

    payload = json.dumps(report.to_dict(), ensure_ascii=False, indent=2)
    print(payload)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload + "\n", encoding="utf-8")
    return 0
