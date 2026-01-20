import numpy as np
import pandas as pd
from pathlib import Path

from catboost import CatBoostRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import joblib


DATA_PATH = Path("data/merged_aadhaar_data_sample.csv")
MODEL_PATH = Path("migration_score_model.pkl")
THRESHOLDS_PATH = Path("migration_thresholds.pkl")


def build_aggregated_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build district-month level training dataset from pincode-level records.

    Aggregation:
      (state, district, month) -> sum of numeric columns
    """
    # Ensure date is parsed
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["date"])

    # Month column as YYYY-MM
    df["month"] = df["date"].dt.to_period("M").astype(str)

    group_cols = ["state", "district", "month"]
    num_cols = [
        "age_0_5", "age_5_17", "age_18_greater",
        "demo_age_5_17", "demo_age_17_",
        "bio_age_5_17", "bio_age_17_",
    ]

    agg = df.groupby(group_cols)[num_cols].sum().reset_index()

    # Target in log scale: log1p(demo_age_17_)
    agg["target_score"] = np.log1p(agg["demo_age_17_"])

    return agg


def add_features(agg: pd.DataFrame) -> pd.DataFrame:
    """
    Add surge-sensitive features:
      - child/adult demo ratios
      - child bio ratio
      - rolling means (3-month) per (state, district)
    """
    agg = agg.copy()

    # Ratios
    agg["total_demo"] = agg["demo_age_5_17"] + agg["demo_age_17_"] + 1
    agg["child_demo_ratio"] = agg["demo_age_5_17"] / agg["total_demo"]
    agg["adult_demo_ratio"] = agg["demo_age_17_"] / agg["total_demo"]

    agg["total_bio"] = agg["bio_age_5_17"] + agg["bio_age_17_"] + 1
    agg["child_bio_ratio"] = agg["bio_age_5_17"] / agg["total_bio"]

    # Month as a proper datetime for sorting
    agg["month_dt"] = pd.to_datetime(agg["month"] + "-01", errors="coerce")
    agg = agg.dropna(subset=["month_dt"])
    agg = agg.sort_values(["state", "district", "month_dt"])

    # Rolling trend features per district (3-month window)
    for col in ["demo_age_17_", "demo_age_5_17", "bio_age_5_17", "bio_age_17_"]:
        roll_name = f"{col}_roll3"
        agg[roll_name] = (
            agg
            .groupby(["state", "district"], group_keys=False)[col]
            .transform(lambda x: x.rolling(3, min_periods=1).mean())
        )

    return agg


def train_and_save_model(agg: pd.DataFrame) -> None:
    """
    Train CatBoostRegressor on the aggregated dataset and save model + thresholds.

    - Target: target_score = log1p(demo_age_17_)
    - Thresholds:
        raw_min, raw_max from expm1(target_score) distribution
        watch, surge as fixed inflow_score thresholds (4.0, 5.0)
    """
    features = [
        "state", "district",
        "age_0_5", "age_5_17", "age_18_greater",
        "demo_age_5_17", "demo_age_17_",
        "bio_age_5_17", "bio_age_17_",
        "child_demo_ratio", "adult_demo_ratio",
        "child_bio_ratio",
        "demo_age_17__roll3", "demo_age_5_17_roll3",
        "bio_age_5_17_roll3", "bio_age_17__roll3",
    ]

    # Rename cols to match feature names exactly
    agg = agg.rename(columns={
        "demo_age_17_": "demo_age_17_",
        "demo_age_5_17_roll3": "demo_age_5_17_roll3",
        "demo_age_17__roll3": "demo_age_17__roll3",
        "bio_age_5_17_roll3": "bio_age_5_17_roll3",
        "bio_age_17__roll3": "bio_age_17__roll3",
    })

    # Make sure rolling columns exist with exact names
    agg["demo_age_17__roll3"] = agg["demo_age_17__roll3"] if "demo_age_17__roll3" in agg.columns else agg["demo_age_17_roll3"]
    agg["demo_age_5_17_roll3"] = agg["demo_age_5_17_roll3"]
    agg["bio_age_5_17_roll3"] = agg["bio_age_5_17_roll3"]
    agg["bio_age_17__roll3"] = agg["bio_age_17__roll3"] if "bio_age_17__roll3" in agg.columns else agg["bio_age_17_roll3"]

    X = agg[features]
    y = agg["target_score"].astype(float)

    cat_features = ["state", "district"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = CatBoostRegressor(
        iterations=500,
        depth=8,
        learning_rate=0.05,
        loss_function="MAE",
        verbose=100,
    )

    model.fit(X_train, y_train, cat_features=cat_features)

    pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, pred)
    print(f"Validation MAE (log-scale target): {mae:.4f}")

    # Compute raw_min/raw_max from training distribution (expm1 of target)
    raw_train = np.expm1(agg["target_score"].values)
    raw_min = np.quantile(raw_train, 0.05)
    raw_max = np.quantile(raw_train, 0.95)

    thresholds = {
        "raw_min": float(raw_min),
        "raw_max": float(raw_max),
        "watch": 4.0,
        "surge": 5.0,
    }

    joblib.dump(model, MODEL_PATH)
    joblib.dump(thresholds, THRESHOLDS_PATH)

    print(f"Saved model to {MODEL_PATH}")
    print(f"Saved thresholds to {THRESHOLDS_PATH}")
    print("Done ✅")


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data file not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    print(f"Loaded raw data: {df.shape[0]} rows")

    agg = build_aggregated_dataset(df)
    print(f"Aggregated dataset: {agg.shape[0]} district-month rows")

    agg = add_features(agg)
    print("Feature engineering complete.")

    train_and_save_model(agg)


if __name__ == "__main__":
    main()
