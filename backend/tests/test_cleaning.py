import pandas as pd

from ml.preprocessing.cleaning import clean_sales_data
from ml.preprocessing.validation import validate_dataset


def _sample_raw_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02", "not-a-date", "2024-01-01", "2024-01-04"],
            "product_id": ["P1", "P1", "P1", "P1", "P1"],
            "product_name": ["Widget", "Widget", "Widget", "Widget", "Widget"],
            "category": ["A", "A", "A", "A", None],
            "region": ["North", "North", "North", "North", "North"],
            "units_sold": [10, -5, 8, 10, 12],
            "unit_price": [100.0, 100.0, 100.0, 100.0, None],
            "discount": [0, None, 0, 0, 0],
            "marketing_spend": [None, 200.0, 0, None, 0],
            "revenue": [1000.0, 500.0, 800.0, 1000.0, 1200.0],
        }
    )


def test_validate_dataset_flags_issues():
    report = validate_dataset(_sample_raw_df())
    assert report.is_valid
    assert report.invalid_date_rows == 1
    assert report.duplicate_rows == 1
    assert report.negative_value_rows >= 1


def test_validate_dataset_missing_required_columns():
    df = _sample_raw_df().drop(columns=["revenue"])
    report = validate_dataset(df)
    assert not report.is_valid
    assert "revenue" in report.missing_required_columns


def test_clean_sales_data_removes_invalid_rows():
    cleaned, summary = clean_sales_data(_sample_raw_df())
    assert summary.dropped_invalid_dates == 1
    assert summary.dropped_duplicates == 1
    assert (cleaned["units_sold"] >= 0).all()
    assert cleaned["unit_price"].isna().sum() == 0
    assert cleaned["category"].isna().sum() == 0


def test_clean_sales_data_is_sorted_by_date():
    cleaned, _ = clean_sales_data(_sample_raw_df())
    assert cleaned["date"].is_monotonic_increasing
