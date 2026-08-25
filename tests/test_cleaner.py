import pandas as pd
import pytest

from persian_tabular_cleaner import CleanerConfig, clean_dataframe


def test_cleans_selected_columns_and_reports_invalid_values() -> None:
    original = pd.DataFrame(
        {
            "name": ["  علي  رضايي ", "مریم کریمی"],
            "phone": ["۰۹۱۲ ۱۲۳ ۴۵۶۷", "not-a-phone"],
            "joined": ["۱۴۰۳/۰۱/۰۱", "invalid"],
        }
    )

    cleaned, report = clean_dataframe(
        original,
        CleanerConfig(
            text_columns=("name",),
            phone_columns=("phone",),
            jalali_date_columns=("joined",),
        ),
    )

    assert cleaned.loc[0, "name"] == "علی رضایی"
    assert cleaned.loc[0, "phone"] == "+989121234567"
    assert cleaned.loc[0, "joined"] == "2024-03-20"
    assert cleaned.loc[1, "phone"] == "not-a-phone"
    assert report.changed_cells == 3
    assert report.invalid_values == {"phone": 1, "joined": 1}
    assert original.loc[0, "name"] == "  علي  رضايي "


def test_reports_missing_columns_without_failing_by_default() -> None:
    _, report = clean_dataframe(
        pd.DataFrame({"name": ["علی"]}),
        CleanerConfig(phone_columns=("mobile",)),
    )
    assert report.missing_columns == ["mobile"]


def test_strict_mode_rejects_missing_columns() -> None:
    with pytest.raises(KeyError, match="mobile"):
        clean_dataframe(
            pd.DataFrame({"name": ["علی"]}),
            CleanerConfig(phone_columns=("mobile",), strict_columns=True),
        )
