from __future__ import annotations

from typing import Optional

import pandas as pd

from app.analytics.aflb import compute_aflb_alerts
from app.analytics.urrdf import compute_urrdf_alerts
from app.core.data_loader import get_dataset


class AnalyticsService:
    """Service layer orchestrating data loading and analytics computations."""

    def __init__(self) -> None:
        # In a more complex app, dependencies could be injected here
        self._model = None
        self._thresholds = None

    def _get_base_df(self) -> pd.DataFrame:
        return get_dataset()

    def urrdf_alerts(self, month: Optional[str] = None):
        df = self._get_base_df()
        return compute_urrdf_alerts(df, month=month, top_n=10)

    def aflb_alerts(self, month: Optional[str] = None):
        df = self._get_base_df()
        return compute_aflb_alerts(df, month=month, top_n=20)

    def predict_migration_model(self, month: Optional[str] = None, top_n: int = 10) -> pd.DataFrame:
        """Load trained migration model and predict inflow-style scores for district-months.

        Returns a DataFrame with columns:
          state, district, month, ml_inflow_score, tier, recommendations
        """
        # Lazy-load dataset
        df = self._get_base_df()

        # Lazy-load model and thresholds
        if self._model is None or self._thresholds is None:
            try:
                import joblib
                from pathlib import Path
                model_path = Path("migration_score_model.pkl")
                thresh_path = Path("migration_thresholds.pkl")
                if not model_path.exists() or not thresh_path.exists():
                    raise FileNotFoundError("Trained model or thresholds file not found. Expected: migration_score_model.pkl and migration_thresholds.pkl")
                self._model = joblib.load(model_path)
                self._thresholds = joblib.load(thresh_path)
            except Exception as exc:
                # Re-raise as FileNotFoundError for router handling
                raise FileNotFoundError(str(exc)) from exc

        # Prepare district-month aggregation similar to training
        group_cols = ["state", "district", "month"]
        num_cols = [
            "age_0_5",
            "age_5_17",
            "age_18_greater",
            "demo_age_5_17",
            "demo_age_17_",
            "bio_age_5_17",
            "bio_age_17_",
        ]

        agg = df.groupby(group_cols, as_index=False)[num_cols].sum()

        # Feature engineering used during training
        agg["total_demo"] = agg["demo_age_5_17"] + agg["demo_age_17_"] + 1
        agg["child_demo_ratio"] = agg["demo_age_5_17"] / agg["total_demo"]
        agg["adult_demo_ratio"] = agg["demo_age_17_"] / agg["total_demo"]

        agg["total_bio"] = agg["bio_age_5_17"] + agg["bio_age_17_"] + 1
        agg["child_bio_ratio"] = agg["bio_age_5_17"] / agg["total_bio"]

        # month datetime for sorting and rolling
        agg["month_dt"] = pd.to_datetime(agg["month"] + "-01", errors="coerce")
        agg = agg.sort_values(["state", "district", "month_dt"]).reset_index(drop=True)

        # rolling features for columns
        roll_cols = ["demo_age_17_", "demo_age_5_17", "bio_age_5_17", "bio_age_17_"]
        for col in roll_cols:
            agg[f"{col}_roll3"] = (
                agg.groupby(["state", "district"])[col]
                .transform(lambda x: x.rolling(window=3, min_periods=1).mean().shift(1))
            )

        # Build feature matrix for model. Try to include the same features used in training.
        feature_cols = [
            "state",
            "district",
            "age_0_5",
            "age_5_17",
            "age_18_greater",
            "demo_age_5_17",
            "demo_age_17_",
            "bio_age_5_17",
            "bio_age_17_",
            "child_demo_ratio",
            "adult_demo_ratio",
            "child_bio_ratio",
            "demo_age_17___roll3",
            "demo_age_5_17_roll3",
            "bio_age_5_17_roll3",
            "bio_age_17___roll3",
        ]

        # The model might expect slightly different column names; normalize names we computed
        # Map the computed roll names to the expected names used in training (handle single/double underscores)
        agg = agg.rename(columns={
            "demo_age_17__roll3": "demo_age_17___roll3",
            "bio_age_17__roll3": "bio_age_17___roll3",
        })

        # Ensure roll columns exist; fill missing with 0
        for col in [
            "demo_age_17___roll3",
            "demo_age_5_17_roll3",
            "bio_age_5_17_roll3",
            "bio_age_17___roll3",
        ]:
            if col not in agg.columns:
                agg[col] = 0.0

        # Select latest month if requested, otherwise find latest
        if month is None:
            target_month = agg["month"].max()
        else:
            target_month = month

        # Predict for all district-month rows for the target month
        pred_df = agg[agg["month"] == target_month].copy()
        if pred_df.empty:
            return pred_df

        # Prepare X for model; model may accept a DataFrame directly (CatBoost)
        X = pred_df[[
            "state",
            "district",
            "age_0_5",
            "age_5_17",
            "age_18_greater",
            "demo_age_5_17",
            "demo_age_17_",
            "bio_age_5_17",
            "bio_age_17_",
            "child_demo_ratio",
            "adult_demo_ratio",
            "child_bio_ratio",
            "demo_age_17___roll3",
            "demo_age_5_17_roll3",
            "bio_age_5_17_roll3",
            "bio_age_17___roll3",
        ]].copy()

        # Some models (e.g., sklearn) need numeric-only arrays; CatBoost can handle cat features
        try:
            preds_log = self._model.predict(X)
        except Exception:
            # Fallback: try passing numpy array
            preds_log = self._model.predict(X.values)

        import numpy as np
        from app.utils.migration_scoring import to_inflow_score, inflow_tier, recommendations_for_tier

        raw_min = float(self._thresholds.get("raw_min", 0.0))
        raw_max = float(self._thresholds.get("raw_max", 1.0))
        watch = float(self._thresholds.get("watch", 4.0))
        surge = float(self._thresholds.get("surge", 5.0))

        # Ensure preds_log is iterable
        preds_log = np.array(preds_log, dtype=float)

        # Convert and attach
        pred_df["ml_inflow_score"] = [to_inflow_score(float(v), raw_min, raw_max) for v in preds_log]
        pred_df["tier"] = pred_df["ml_inflow_score"].apply(lambda x: inflow_tier(x, watch=watch, surge=surge))
        pred_df["recommendations"] = pred_df["tier"].apply(recommendations_for_tier)

        result = pred_df.sort_values("ml_inflow_score", ascending=False).head(top_n)

        return result[["state", "district", "month", "ml_inflow_score", "tier", "recommendations"]]



analytics_service = AnalyticsService()
