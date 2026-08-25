import json

import pandas as pd
import pytest

from persian_tabular_cleaner.cli import main


def test_cli_cleans_csv_and_writes_report(tmp_path, capsys) -> None:
    source = tmp_path / "input.csv"
    destination = tmp_path / "output.csv"
    report_path = tmp_path / "report.json"
    pd.DataFrame(
        {
            "name": ["علي  رضايي"],
            "phone": ["۰۹۱۲۱۲۳۴۵۶۷"],
            "joined": ["۱۴۰۳/۰۱/۰۱"],
        }
    ).to_csv(source, index=False, encoding="utf-8-sig")

    result = main(
        [
            str(source),
            str(destination),
            "--text-columns",
            "name",
            "--phone-columns",
            "phone",
            "--jalali-date-columns",
            "joined",
            "--report",
            str(report_path),
        ]
    )

    cleaned = pd.read_csv(destination, encoding="utf-8-sig")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert result == 0
    assert cleaned.loc[0, "name"] == "علی رضایی"
    assert cleaned.loc[0, "phone"] == 989121234567
    assert cleaned.loc[0, "joined"] == "2024-03-20"
    assert report["changed_cells"] == 3
    assert json.loads(capsys.readouterr().out)["rows"] == 1


def test_cli_rejects_unknown_input_format(tmp_path) -> None:
    source = tmp_path / "input.txt"
    source.write_text("data", encoding="utf-8")

    with pytest.raises(SystemExit, match="2"):
        main([str(source), str(tmp_path / "output.csv")])
