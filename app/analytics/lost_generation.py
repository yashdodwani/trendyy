from __future__ import annotations

from typing import List, Optional

import numpy as np
import pandas as pd

from app.schemas.biometric_alerts import LostGenerationAlert


def _ensure_month_column(df: pd.DataFrame) -> pd.DataFrame:
    if "date" in df.columns and not np.issubdtype(df["date"].dtype, np.datetime64):
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df = df[df["date"].notna()].copy()
    if "month" not in df.columns:
        df["month"] = df["date"].dt.to_period("M").astype(str)
    return df


def _tier_fafi_ratio(ratio: float) -> str:
    if ratio < 0.20:
        return "LOW"
    if ratio <= 0.45:
        return "MEDIUM"
    return "HIGH"


def _impact_statement(tier: str) -> str:
    if tier == "HIGH":
        return "Large cohort of children may face future authentication failures if biometrics are not updated soon."
    if tier == "MEDIUM":
        return "Noticeable backlog of child biometric updates; risk will grow without targeted interventions."
    return "Child biometric updates are broadly aligned with enrolments; maintain routine coverage."


def _recommendations_for_tier(tier: str) -> List[str]:
    if tier == "HIGH":
        return [
            "Schedule school-based biometric update camps",
            "Deploy mobile biometric vans",
            "Set 30-day district update target",
        ]
    if tier == "MEDIUM":
        return [
            "Run biometric update drives in schools",
            "Increase awareness in parent communities",
        ]
    return ["Continue routine biometric camps"]


def compute_lost_generation_alerts(
    df: pd.DataFrame,
    month: Optional[str] = None,
    limit: int = 15,
) -> List[LostGenerationAlert]:
    """
    Compute Future Authentication Failure Index (FAFI) alerts at district-month level.

    FAFI = enrol_age_0_5 - bio_age_5_17
    FAFI_ratio = FAFI / max(enrol_age_0_5, 1)
    """
    if df.empty:
        return []

    df = _ensure_month_column(df)

    if month is None:
        month = df["month"].dropna().max()
    if month is None or month not in set(df["month"].dropna().unique()):
        return []

    month_df = df[df["month"] == month].copy()
    if month_df.empty:
        return []

    # Ensure numeric
    for col in ["age_0_5", "bio_age_5_17"]:
        if col in month_df.columns:
            month_df[col] = pd.to_numeric(month_df[col], errors="coerce").fillna(0)
        else:
            month_df[col] = 0

    group_cols = ["state", "district", "month"]
    grouped = (
        month_df.groupby(group_cols, dropna=False)[["age_0_5", "bio_age_5_17"]]
        .sum()
        .reset_index()
    )

    grouped["enrol_age_0_5"] = grouped["age_0_5"].astype(int)
    grouped["bio_age_5_17_total"] = grouped["bio_age_5_17"].astype(int)

    grouped["fafi_value"] = (
        grouped["enrol_age_0_5"] - grouped["bio_age_5_17_total"]
    ).astype(int)

    grouped["fafi_ratio"] = (
        grouped["fafi_value"] / grouped["enrol_age_0_5"].replace(0, 1)
    )

    grouped = grouped.sort_values("fafi_ratio", ascending=False).head(limit)

    alerts: List[LostGenerationAlert] = []
    for _, row in grouped.iterrows():
        fafi_ratio = float(row["fafi_ratio"])
        tier = _tier_fafi_ratio(fafi_ratio)
        impact = _impact_statement(tier)
        recs = _recommendations_for_tier(tier)

        alerts.append(
            LostGenerationAlert(
                state=str(row.get("state", "")),
                district=str(row.get("district", "")),
                month=str(row.get("month", month)),
                enrol_age_0_5=int(row["enrol_age_0_5"]),
                bio_age_5_17=int(row["bio_age_5_17_total"]),
                fafi_value=int(row["fafi_value"]),
                fafi_ratio=round(fafi_ratio, 2),
                tier=tier,
                impact_statement=impact,
                recommendations=recs,
            )
        )

    return alerts
