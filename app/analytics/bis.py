from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from app.schemas.biometric_alerts import BiometricIntegrityAlert


def _ensure_month_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure `date` is parsed and `month` column exists.

    - Parses date with dayfirst=True, errors='coerce'
    - Drops rows with NaT dates
    - Adds month as YYYY-MM string
    """
    if "date" in df.columns and not np.issubdtype(df["date"].dtype, np.datetime64):
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    # Drop NaT
    df = df[df["date"].notna()].copy()
    if "month" not in df.columns:
        df["month"] = df["date"].dt.to_period("M").astype(str)
    return df


def _detect_optional_bio_columns(df: pd.DataFrame) -> Optional[Tuple[str, str]]:
    """
    Try to detect iris and fingerprint update columns in a tolerant way.

    Returns (iris_col, finger_col) or None if any is missing.
    """
    cols_lower = {c.lower(): c for c in df.columns}

    iris_candidates = [
        name for key, name in cols_lower.items()
        if "iris" in key and "update" in key
    ]
    finger_candidates = [
        name for key, name in cols_lower.items()
        if ("finger" in key or "fp" in key) and "update" in key
    ]

    if not iris_candidates or not finger_candidates:
        return None

    # First candidate of each list is enough
    return iris_candidates[0], finger_candidates[0]


def _tier_capture_gap(ratio: float) -> str:
    if ratio < 0.30:
        return "LOW"
    if ratio <= 0.60:
        return "MEDIUM"
    return "HIGH"


def _tier_imbalance(score: Optional[float]) -> Optional[str]:
    if score is None:
        return None
    if score < 0.20:
        return "LOW"
    if score <= 0.40:
        return "MEDIUM"
    return "HIGH"


def _tags_for_alert(capture_gap_tier: str, imbalance_tier: Optional[str]) -> List[str]:
    tags: List[str] = []
    if capture_gap_tier == "HIGH":
        tags.append("High capture gap")
    elif capture_gap_tier == "MEDIUM":
        tags.append("Moderate capture gap")

    if imbalance_tier in ("MEDIUM", "HIGH"):
        tags.append("Equipment / Operational anomaly")

    return tags


def _recommendations_for_alert(
    capture_gap_tier: str,
    imbalance_tier: Optional[str],
) -> List[str]:
    recs: List[str] = []

    if capture_gap_tier == "HIGH":
        recs.append("Prioritize biometric capture drives in this pincode")
        recs.append("Review enrolment vs biometric station coverage")
    elif capture_gap_tier == "MEDIUM":
        recs.append("Plan additional biometric capture sessions")
        recs.append("Nudge residents to update biometrics during routine visits")
    else:
        recs.append("Maintain current biometric capture coverage")

    if imbalance_tier in ("MEDIUM", "HIGH"):
        # Only equipment / operational language, not fraud
        recs.append("Check biometric equipment health (iris vs fingerprint)")
        recs.append("Audit operator workflows for iris and fingerprint capture balance")

    return recs


def compute_bis_alerts(
    df: pd.DataFrame,
    month: Optional[str] = None,
    limit: int = 20,
) -> List[BiometricIntegrityAlert]:
    """
    Compute Biometric Integrity Score (BIS) alerts on a pincode-month basis.

    Steps:
    - Ensure date/month columns
    - Filter to requested or latest month
    - Aggregate by state, district, pincode, month
    - Compute enrol_total, bio_total, capture_gap_ratio, imbalance_score (if possible)
    - Rank by capture_gap_ratio desc and return up to `limit` alerts
    """
    if df.empty:
        return []

    df = _ensure_month_column(df)

    # Determine month
    if month is None:
        month = df["month"].dropna().max()
    if month is None or month not in set(df["month"].dropna().unique()):
        # Caller should convert this to HTTP 404
        return []

    month_df = df[df["month"] == month].copy()
    if month_df.empty:
        return []

    # Ensure numeric columns, fill NaN with 0
    numeric_cols = [
        "age_0_5",
        "age_5_17",
        "age_18_greater",
        "bio_age_5_17",
        "bio_age_17_",
    ]
    for col in numeric_cols:
        if col in month_df.columns:
            month_df[col] = pd.to_numeric(month_df[col], errors="coerce").fillna(0)
        else:
            month_df[col] = 0

    # Detect optional iris/fingerprint columns
    iris_finger_cols = _detect_optional_bio_columns(month_df)
    iris_col, finger_col = (iris_finger_cols if iris_finger_cols else (None, None))

    group_cols = ["state", "district", "pincode", "month"]
    agg_dict = {
        "age_0_5": "sum",
        "age_5_17": "sum",
        "age_18_greater": "sum",
        "bio_age_5_17": "sum",
        "bio_age_17_": "sum",
    }
    if iris_col:
        agg_dict[iris_col] = "sum"
    if finger_col:
        agg_dict[finger_col] = "sum"

    grouped = month_df.groupby(group_cols, dropna=False).agg(agg_dict).reset_index()

    # Compute totals and ratios
    grouped["enrol_total"] = (
        grouped["age_0_5"] + grouped["age_5_17"] + grouped["age_18_greater"]
    ).astype(int)
    grouped["bio_total"] = (
        grouped["bio_age_5_17"] + grouped["bio_age_17_"]
    ).astype(int)

    # Avoid division by zero
    grouped["capture_gap_ratio"] = (
        (grouped["enrol_total"] - grouped["bio_total"])
        / grouped["enrol_total"].replace(0, 1)
    )

    # Optional imbalance
    if iris_col and finger_col:
        # compute imbalance_score
        iris_val = grouped[iris_col].fillna(0)
        finger_val = grouped[finger_col].fillna(0)
        grouped["imbalance_score"] = (
            (iris_val - finger_val).abs() / (iris_val + finger_val + 1)
        )
    else:
        grouped["imbalance_score"] = np.nan

    # Sort and trim
    grouped = grouped.sort_values("capture_gap_ratio", ascending=False).head(limit)

    alerts: List[BiometricIntegrityAlert] = []
    for _, row in grouped.iterrows():
        capture_gap_ratio = float(row["capture_gap_ratio"])
        capture_gap_tier = _tier_capture_gap(capture_gap_ratio)

        imbalance_val = row["imbalance_score"]
        imbalance_score: Optional[float]
        if pd.isna(imbalance_val):
            imbalance_score = None
        else:
            imbalance_score = float(imbalance_val)

        imbalance_tier = _tier_imbalance(imbalance_score)

        tags = _tags_for_alert(capture_gap_tier, imbalance_tier)
        recommendations = _recommendations_for_alert(
            capture_gap_tier=capture_gap_tier,
            imbalance_tier=imbalance_tier,
        )

        alerts.append(
            BiometricIntegrityAlert(
                state=str(row.get("state", "")),
                district=str(row.get("district", "")),
                pincode=str(row.get("pincode", "")),
                month=str(row.get("month", month)),
                enrol_total=int(row["enrol_total"]),
                bio_total=int(row["bio_total"]),
                capture_gap_ratio=round(capture_gap_ratio, 2),
                capture_gap_tier=capture_gap_tier,
                imbalance_score=round(imbalance_score, 2)
                if imbalance_score is not None
                else None,
                imbalance_tier=imbalance_tier,
                tags=tags,
                recommendations=recommendations,
            )
        )

    return alerts
