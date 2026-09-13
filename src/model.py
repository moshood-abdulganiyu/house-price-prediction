"""Load the trained Pipeline and run predictions.

Thin wrapper - all the actual model logic lives in server/model.joblib
(StandardScaler + RandomForestRegressor(n_estimators=50, max_depth=12),
trained in 04_modeling.ipynb). This module just loads it and calls predict.
"""

from pathlib import Path
from typing import Optional, Union

import joblib
import pandas as pd

# src/model.py -> parent is src/, parent.parent is the repo root
_DEFAULT_MODEL_PATH = Path(__file__).resolve().parent.parent / "server" / "model.joblib"
_DEFAULT_KEEP_LOCATIONS_PATH = (
    Path(__file__).resolve().parent.parent / "server" / "keep_locations.json"
)


def load_model(path: Optional[Union[str, Path]] = None):
    """Load the pickled Pipeline. Defaults to server/model.joblib."""
    return joblib.load(path or _DEFAULT_MODEL_PATH)


def predict_price(model, features: pd.DataFrame) -> float:
    """Run the pipeline on a single-row feature DataFrame, return price in lakhs."""
    return float(model.predict(features)[0])