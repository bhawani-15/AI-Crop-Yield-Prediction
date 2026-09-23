import os
import joblib
import numpy as np
import pandas as pd
from xgboost import XGBRegressor

DATA_PATH = os.path.join(os.path.dirname(__file__), "agricultural_yield_india_cleaned_long.csv")
ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "artifacts")

def iqr_bounds(series: pd.Series, k: float = 3.0):
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    return max(0.0, q1 - k * iqr), q3 + k * iqr

def prepare_and_train():
    print(f"Loading raw dataset from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    df["YearStart"] = df["Year"].str.split("-").str[0].astype(int)

    # 1. Outlier removal using per-crop IQR (Q3 + 3*IQR)
    bad_idx = []
    for crop, g in df.groupby("Crop"):
        lo, hi = iqr_bounds(g["Yield_Kg_Ha"])
        bad_idx.extend(g[(g["Yield_Kg_Ha"] < lo) | (g["Yield_Kg_Ha"] > hi)].index.tolist())

    df_clean = df.drop(index=bad_idx).copy()
    print(f"Cleaned dataset shape: {df_clean.shape} (Removed {len(bad_idx)} outlier rows)")

    # 2. Sort and compute lag_yield (previous recorded year's yield)
    df_clean = df_clean.sort_values(["State", "District", "Crop", "Season", "YearStart"])
    grp_cols = ["State", "District", "Crop", "Season"]
    df_clean["lag_yield"] = df_clean.groupby(grp_cols)["Yield_Kg_Ha"].shift(1)

    # 3. Target Encoding statistics (smoothed means)
    global_mean = float(df_clean["Yield_Kg_Ha"].mean())
    m_smooth = 10

    district_stats = df_clean.groupby("District")["Yield_Kg_Ha"].agg(["mean", "count"])
    district_te_map = (
        (district_stats["mean"] * district_stats["count"] + global_mean * m_smooth)
        / (district_stats["count"] + m_smooth)
    ).to_dict()

    state_stats = df_clean.groupby("State")["Yield_Kg_Ha"].agg(["mean", "count"])
    state_te_map = (
        (state_stats["mean"] * state_stats["count"] + global_mean * m_smooth)
        / (state_stats["count"] + m_smooth)
    ).to_dict()

    crop_mean_map = df_clean.groupby("Crop")["Yield_Kg_Ha"].mean().to_dict()

    # Fill lag_yield missing with crop mean fallback
    df_clean["District_te"] = df_clean["District"].map(district_te_map).fillna(global_mean)
    df_clean["State_te"] = df_clean["State"].map(state_te_map).fillna(global_mean)
    df_clean["lag_yield"] = df_clean["lag_yield"].fillna(
        df_clean["Crop"].map(crop_mean_map).fillna(global_mean)
    )

    # 4. One-Hot Encoding for Crop & Season
    ohe_df = pd.get_dummies(df_clean[["Crop", "Season"]], prefix=["crop", "season"], dtype=float)
    ohe_columns = list(ohe_df.columns)

    num_feature_cols = ["YearStart", "District_te", "State_te", "lag_yield"]
    feature_cols = num_feature_cols + ohe_columns

    X = pd.concat([df_clean[num_feature_cols].reset_index(drop=True),
                   ohe_df.reset_index(drop=True)], axis=1)
    y = df_clean["Yield_Kg_Ha"].reset_index(drop=True)

    print(f"Training XGBoost on {len(X)} records across {len(feature_cols)} features...")
    model = XGBRegressor(
        n_estimators=400,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X, y)
    train_r2 = model.score(X, y)
    print(f"Model trained successfully! Fit R2: {train_r2:.4f}")

    # 5. Build Historical Yield Lookup for fast lag inference
    # Store latest known yield and full historical records
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    lookup_df = df_clean[["State", "District", "Crop", "Season", "YearStart", "Yield_Kg_Ha"]].copy()
    lookup_path = os.path.join(ARTIFACTS_DIR, "yield_lookup.csv")
    lookup_df.to_csv(lookup_path, index=False)
    print(f"Saved yield lookup table to {lookup_path}")

    # 6. Save Preprocessor Metadata
    preprocessor = {
        "global_mean": global_mean,
        "district_te_map": district_te_map,
        "state_te_map": state_te_map,
        "crop_mean_map": crop_mean_map,
        "num_feature_cols": num_feature_cols,
        "ohe_columns": ohe_columns,
        "feature_cols": feature_cols,
        "crops": sorted(df_clean["Crop"].unique().tolist()),
        "seasons": sorted(df_clean["Season"].unique().tolist()),
        "states": sorted(df_clean["State"].unique().tolist()),
        "state_to_districts": df_clean.groupby("State")["District"].unique().apply(lambda x: sorted(x.tolist())).to_dict()
    }
    prep_path = os.path.join(ARTIFACTS_DIR, "preprocessor.joblib")
    joblib.dump(preprocessor, prep_path)
    print(f"Saved preprocessor to {prep_path}")

    # 7. Save Trained XGBoost Model
    model_path = os.path.join(ARTIFACTS_DIR, "model.joblib")
    joblib.dump(model, model_path)
    print(f"Saved trained model to {model_path}")
    print("Training and serialization pipeline complete!")

if __name__ == "__main__":
    prepare_and_train()
