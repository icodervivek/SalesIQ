"""Dataset validation for uploaded sales CSVs."""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

REQUIRED_COLUMNS = ["date", "product_id", "product_name", "units_sold", "revenue"]
RECOMMENDED_COLUMNS = ["category", "region", "unit_price"]
OPTIONAL_COLUMNS = ["discount", "marketing_spend"]
ALL_KNOWN_COLUMNS = REQUIRED_COLUMNS + RECOMMENDED_COLUMNS + OPTIONAL_COLUMNS


@dataclass
class ValidationReport:
    is_valid: bool
    row_count: int
    missing_required_columns: list[str] = field(default_factory=list)
    missing_recommended_columns: list[str] = field(default_factory=list)
    invalid_date_rows: int = 0
    duplicate_rows: int = 0
    missing_value_rows: int = 0
    invalid_numeric_rows: int = 0
    negative_value_rows: int = 0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "row_count": self.row_count,
            "missing_required_columns": self.missing_required_columns,
            "missing_recommended_columns": self.missing_recommended_columns,
            "invalid_date_rows": self.invalid_date_rows,
            "duplicate_rows": self.duplicate_rows,
            "missing_value_rows": self.missing_value_rows,
            "invalid_numeric_rows": self.invalid_numeric_rows,
            "negative_value_rows": self.negative_value_rows,
            "warnings": self.warnings,
        }


def validate_dataset(df: pd.DataFrame) -> ValidationReport:
    """Runs structural + data-quality checks without mutating the input."""
    missing_required = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    missing_recommended = [c for c in RECOMMENDED_COLUMNS if c not in df.columns]

    if missing_required:
        return ValidationReport(
            is_valid=False,
            row_count=len(df),
            missing_required_columns=missing_required,
            missing_recommended_columns=missing_recommended,
            warnings=[f"Missing required column(s): {', '.join(missing_required)}"],
        )

    warnings: list[str] = []

    parsed_dates = pd.to_datetime(df["date"], errors="coerce")
    invalid_date_rows = int(parsed_dates.isna().sum())

    duplicate_rows = int(df.duplicated().sum())

    numeric_cols = [c for c in ("units_sold", "unit_price", "revenue", "discount", "marketing_spend") if c in df.columns]
    numeric_parsed = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    invalid_numeric_rows = int(numeric_parsed.isna().sum().sum() - df[numeric_cols].isna().sum().sum())

    missing_value_rows = int(df[REQUIRED_COLUMNS].isna().any(axis=1).sum())
    negative_value_rows = int((numeric_parsed[[c for c in ("units_sold", "unit_price", "revenue") if c in numeric_parsed.columns]] < 0).sum().sum())

    if missing_recommended:
        warnings.append(f"Missing recommended column(s): {', '.join(missing_recommended)} — related analytics will be limited.")
    if invalid_date_rows:
        warnings.append(f"{invalid_date_rows} row(s) have unparsable dates.")
    if duplicate_rows:
        warnings.append(f"{duplicate_rows} duplicate row(s) detected.")
    if missing_value_rows:
        warnings.append(f"{missing_value_rows} row(s) have missing values in required fields.")
    if negative_value_rows:
        warnings.append(f"{negative_value_rows} negative numeric value(s) detected.")

    return ValidationReport(
        is_valid=True,
        row_count=len(df),
        missing_required_columns=[],
        missing_recommended_columns=missing_recommended,
        invalid_date_rows=invalid_date_rows,
        duplicate_rows=duplicate_rows,
        missing_value_rows=missing_value_rows,
        invalid_numeric_rows=max(invalid_numeric_rows, 0),
        negative_value_rows=negative_value_rows,
        warnings=warnings,
    )
