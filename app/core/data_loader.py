from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List
import os

import pandas as pd

from app.core.config import settings
from app.utils.time_utils import normalize_date_column, add_month_column
from app.utils.state_utils import normalize_state_column


REQUIRED_COLUMNS: List[str] = [
    "date",
    "state",
    "district",
    "pincode",
    "age_0_5",
    "age_5_17",
    "age_18_greater",
    "demo_age_5_17",
    "demo_age_17_",
    "bio_age_5_17",
    "bio_age_17_",
]


class DataValidationError(Exception):
    """Raised when the underlying data is missing required structure."""


def _validate_columns(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise DataValidationError(f"Dataset missing required columns: {missing}")


def _validate_non_empty(df: pd.DataFrame) -> None:
    if df.empty:
        raise DataValidationError("Dataset is empty after loading.")


# Use the sample merged CSV path as per prompt
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
MERGED_AADHAAR_CSV = os.path.join(DATA_PATH, "merged_aadhaar_data_sample.csv")


@lru_cache(maxsize=1)
def get_merged_aadhaar_dataframe() -> pd.DataFrame:
    """
    Load and cache the merged Aadhaar analytics dataset.

    - Parses date with dayfirst=True, errors='coerce'
    - Drops invalid dates
    - Adds `month` column as YYYY-MM
    """
    df = pd.read_csv(MERGED_AADHAAR_CSV)

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
        df = df[df["date"].notna()].copy()
        df["month"] = df["date"].dt.to_period("M").astype(str)

    # Ensure key numeric columns exist and are numeric (fill NaN with 0)
    numeric_cols = [
        "age_0_5",
        "age_5_17",
        "age_18_greater",
        "demo_age_5_17",
        "demo_age_17_",
        "bio_age_5_17",
        "bio_age_17_",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


@lru_cache(maxsize=1)
def get_dataset() -> pd.DataFrame:
    """Load and cache the main Aadhaar dataset as a pandas DataFrame.

    - Uses an LRU cache so the CSV is read only once per process lifetime.
    - Validates required columns and non-empty data.
    - Parses the date column and adds a `month` column in YYYY-MM format.
    """

    path: Path = settings.data_file
    if not path.exists():
        raise FileNotFoundError(f"Data file not found at path: {path}")

    df = pd.read_csv(path)

    _validate_non_empty(df)
    _validate_columns(df)

    df = normalize_date_column(df, "date")
    _validate_non_empty(df.dropna(subset=["date"]))

    df = add_month_column(df, "date", "month")

    # Normalize state names so analytics always see canonical forms
    df = normalize_state_column(df, "state")

    # Ensure expected dtypes
    df["pincode"] = df["pincode"].astype(str).str.strip()

    numeric_cols = [
        "age_0_5",
        "age_5_17",
        "age_18_greater",
        "demo_age_5_17",
        "demo_age_17_",
        "bio_age_5_17",
        "bio_age_17_",
    ]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce").fillna(0)

    return df
