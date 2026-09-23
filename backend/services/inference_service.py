import os
import joblib
import numpy as np
import pandas as pd
import shap
from typing import Dict, Any, Optional, List

ARTIFACTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "artifacts"))

class InferenceService:
    def __init__(self):
        self.model = None
        self.preprocessor = None
        self.lookup_df = None
        self.explainer = None
        self.is_loaded = False

    def load_artifacts(self):
        if self.is_loaded:
            return

        model_path = os.path.join(ARTIFACTS_DIR, "model.joblib")
        prep_path = os.path.join(ARTIFACTS_DIR, "preprocessor.joblib")
        lookup_path = os.path.join(ARTIFACTS_DIR, "yield_lookup.csv")

        if not (os.path.exists(model_path) and os.path.exists(prep_path) and os.path.exists(lookup_path)):
            raise FileNotFoundError(
                f"Model artifacts not found in {ARTIFACTS_DIR}. Please run `python train_export.py` first."
            )

        print(f"Loading ML artifacts from {ARTIFACTS_DIR}...")
        self.model = joblib.load(model_path)
        self.preprocessor = joblib.load(prep_path)
        self.lookup_df = pd.read_csv(lookup_path)
        
        # Initialize SHAP explainer for XGBoost tree model
        self.explainer = shap.TreeExplainer(self.model)
        self.is_loaded = True
        print("Inference service initialized and ready.")

    def get_metadata(self) -> Dict[str, Any]:
        self.load_artifacts()
        return {
            "states": self.preprocessor["states"],
            "state_to_districts": self.preprocessor["state_to_districts"],
            "crops": self.preprocessor["crops"],
            "seasons": self.preprocessor["seasons"]
        }

    def resolve_lag_yield(
        self, state: str, district: str, crop: str, season: str, target_year: int, custom_lag: Optional[float]
    ) -> tuple[float, bool]:
        """Returns (lag_yield, is_estimated)"""
        if custom_lag is not None and custom_lag >= 0:
            return float(custom_lag), False

        # Filter exact district-crop-season match from lookup
        match = self.lookup_df[
            (self.lookup_df["State"].str.lower() == state.lower()) &
            (self.lookup_df["District"].str.lower() == district.lower()) &
            (self.lookup_df["Crop"].str.lower() == crop.lower()) &
            (self.lookup_df["Season"].str.lower() == season.lower())
        ]

        if not match.empty:
            # Look for previous year (target_year - 1)
            prev = match[match["YearStart"] == target_year - 1]
            if not prev.empty:
                return float(prev["Yield_Kg_Ha"].iloc[-1]), False
            # Otherwise use the most recent recorded year
            sorted_match = match.sort_values("YearStart", ascending=False)
            return float(sorted_match["Yield_Kg_Ha"].iloc[0]), False

        # If not found in district, fallback to state-crop median
        state_match = self.lookup_df[
            (self.lookup_df["State"].str.lower() == state.lower()) &
            (self.lookup_df["Crop"].str.lower() == crop.lower())
        ]
        if not state_match.empty:
            return float(state_match["Yield_Kg_Ha"].median()), True

        # Fallback to global crop mean
        crop_mean = self.preprocessor["crop_mean_map"].get(crop, self.preprocessor["global_mean"])
        return float(crop_mean), True

    def predict_yield(
        self, state: str, district: str, crop: str, season: str, year: int = 2025, custom_lag: Optional[float] = None
    ) -> Dict[str, Any]:
        self.load_artifacts()

        # 1. Resolve lag_yield
        lag_yield, is_estimated = self.resolve_lag_yield(state, district, crop, season, year, custom_lag)

        # 2. Extract encodings
        global_mean = self.preprocessor["global_mean"]
        district_te = self.preprocessor["district_te_map"].get(district, global_mean)
        state_te = self.preprocessor["state_te_map"].get(state, global_mean)

        # 3. Construct feature DataFrame
        feature_dict = {
            "YearStart": year,
            "District_te": district_te,
            "State_te": state_te,
            "lag_yield": lag_yield
        }
        for ohe_col in self.preprocessor["ohe_columns"]:
            if ohe_col == f"crop_{crop}":
                feature_dict[ohe_col] = 1.0
            elif ohe_col == f"season_{season}":
                feature_dict[ohe_col] = 1.0
            else:
                feature_dict[ohe_col] = 0.0

        feature_cols = self.preprocessor["feature_cols"]
        X_sample = pd.DataFrame([feature_dict])[feature_cols]

        # 4. Predict
        raw_pred = float(self.model.predict(X_sample)[0])
        pred_kg_ha = max(0.0, round(raw_pred, 1))

        # 1 kg/ha = 0.00404686 Quintals/acre
        pred_quintal_acre = round(pred_kg_ha * 0.00404686, 2)

        # 5. Benchmark calculations (District and State averages)
        district_data = self.lookup_df[
            (self.lookup_df["District"].str.lower() == district.lower()) &
            (self.lookup_df["Crop"].str.lower() == crop.lower())
        ]
        district_avg = float(district_data["Yield_Kg_Ha"].mean()) if not district_data.empty else None

        state_data = self.lookup_df[
            (self.lookup_df["State"].str.lower() == state.lower()) &
            (self.lookup_df["Crop"].str.lower() == crop.lower())
        ]
        state_avg = float(state_data["Yield_Kg_Ha"].mean()) if not state_data.empty else None

        delta_district_pct = round(((pred_kg_ha - district_avg) / district_avg) * 100, 1) if district_avg else None
        delta_state_pct = round(((pred_kg_ha - state_avg) / state_avg) * 100, 1) if state_avg else None

        # 6. SHAP Explainability computation
        shap_impacts = []
        try:
            shap_values = self.explainer(X_sample)
            values = shap_values.values[0]
            feature_names = feature_cols

            clean_names = {
                "lag_yield": f"Prior Year Yield ({round(lag_yield, 1)} kg/ha)",
                "District_te": f"{district} District Benchmark",
                "State_te": f"{state} Regional Baseline",
                "YearStart": f"Target Year ({year}) Trend",
                f"crop_{crop}": f"Crop Potential ({crop})",
                f"season_{season}": f"Season Factor ({season})"
            }

            for fname, impact, val in zip(feature_names, values, X_sample.iloc[0]):
                if abs(impact) >= 0.5:
                    clean_name = clean_names.get(fname, fname)
                    shap_impacts.append({
                        "feature": fname,
                        "feature_name_clean": clean_name,
                        "impact": round(float(impact), 1),
                        "value": float(val)
                    })

            # Sort by absolute impact descending
            shap_impacts = sorted(shap_impacts, key=lambda x: abs(x["impact"]), reverse=True)[:6]
        except Exception as e:
            print(f"SHAP explanation note: {e}")

        return {
            "state": state,
            "district": district,
            "crop": crop,
            "season": season,
            "year": year,
            "predicted_yield_kg_ha": pred_kg_ha,
            "predicted_yield_quintal_acre": pred_quintal_acre,
            "lag_yield_used": round(lag_yield, 1),
            "is_lag_estimated": is_estimated,
            "district_avg_yield": round(district_avg, 1) if district_avg else None,
            "state_avg_yield": round(state_avg, 1) if state_avg else None,
            "delta_vs_district_pct": delta_district_pct,
            "delta_vs_state_pct": delta_state_pct,
            "confidence_level": "High" if not is_estimated else "Medium (Estimated Prior)",
            "shap_feature_importance": shap_impacts
        }

    def get_historical_trends(self, state: str, district: str, crop: str) -> Dict[str, Any]:
        self.load_artifacts()
        subset = self.lookup_df[
            (self.lookup_df["State"].str.lower() == state.lower()) &
            (self.lookup_df["District"].str.lower() == district.lower()) &
            (self.lookup_df["Crop"].str.lower() == crop.lower())
        ].sort_values("YearStart")

        trends = []
        for _, row in subset.iterrows():
            trends.append({
                "year": f"{row['YearStart']}-{(row['YearStart']+1)%100:02d}",
                "year_start": int(row["YearStart"]),
                "yield_kg_ha": round(float(row["Yield_Kg_Ha"]), 1),
                "season": str(row["Season"])
            })

        yields = [t["yield_kg_ha"] for t in trends]
        return {
            "state": state,
            "district": district,
            "crop": crop,
            "trends": trends,
            "min_yield": min(yields) if yields else None,
            "max_yield": max(yields) if yields else None,
            "avg_yield": round(sum(yields)/len(yields), 1) if yields else None
        }

# Global singleton
inference_service = InferenceService()
