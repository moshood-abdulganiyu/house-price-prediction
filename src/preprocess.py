"""Feature preparation shared between the training notebooks and the FastAPI
inference API.

Mirrors 01_cleaning.ipynb (total_sqft parsing, BHK extraction) and
03_feature_engineering.ipynb (location bucketing, one-hot encoding) exactly,
so a single /predict request gets the same treatment the model was trained on.
"""

import json
import re
from pathlib import Path
from typing import Optional, Union

import pandas as pd

UNIT_TO_SQFT = {
    "Sq. Meter": 10.7639,
    "Sq. Yards": 9,
    "Acres": 43560,
    "Guntha": 1089,
    "Perch": 272.25,
    "Cents": 435.6,
    "Grounds": 2400,
}


def parse_sqft(value) -> Optional[float]:
    """Convert a raw total_sqft value into a float.

    Handles the three formats found in the raw data:
    - a range like "2100 - 2850" -> mean of the two ends
    - a number with a unit suffix, e.g. "34.46Sq. Meter" -> converted to sqft
    - a plain number

    Returns None if the value can't be parsed (unrecognized unit or garbage
    input). Matches 01_cleaning.ipynb cell 9 exactly.
    """
    x = str(value).strip()

    if "-" in x:
        try:
            lo, hi = x.split("-")
            return (float(lo.strip()) + float(hi.strip())) / 2
        except ValueError:
            return None

    match = re.match(r"^([\d.]+)([A-Za-z. ]+)$", x)
    if match:
        number, unit = match.groups()
        unit = unit.strip()
        if unit in UNIT_TO_SQFT:
            return float(number) * UNIT_TO_SQFT[unit]
        return None  # unrecognized unit - surface this, don't silently guess

    try:
        return float(x)
    except ValueError:
        return None


def extract_bhk(size) -> Optional[float]:
    """Pull the numeric BHK count out of a raw size string, e.g. '2 BHK' -> 2.0.

    Matches 01_cleaning.ipynb cell 12 (str.extract with the same regex).
    """
    match = re.search(r"(\d+)", str(size))
    return float(match.group(1)) if match else None


def load_keep_locations(path: Union[str, Path]) -> list:
    """Load the fixed location category list saved by 03_feature_engineering.ipynb.

    This must be the exact list saved at training time - it defines both which
    locations get their own column and the column order the model was fit on.
    Already sorted alphabetically (that's how it was built and saved), so it's
    loaded as-is rather than re-sorted here.
    """
    with open(path) as f:
        return json.load(f)


def feature_columns(keep_locations: list) -> list:
    """The full, ordered list of columns the model's Pipeline was fit on.

    Order matters here: a fitted sklearn Pipeline doesn't reorder an inference
    DataFrame to match its training columns, it just consumes whatever order
    you give it. This must match X_train's column order from 04_modeling.ipynb:
    bath, balcony, total_sqft, bhk, then one location_* column per kept
    location (in KEEP_LOCATIONS order), then location_other.
    """
    return (
        ["bath", "balcony", "total_sqft", "bhk"]
        + [f"location_{loc}" for loc in keep_locations]
        + ["location_other"]
    )


def prepare_features(
    location: str,
    size: str,
    total_sqft,
    bath: float,
    balcony: float,
    keep_locations: list,
) -> pd.DataFrame:
    """Build a single-row DataFrame ready for model.predict(), from raw
    /predict request fields.

    Applies the same total_sqft parsing, BHK extraction, and location
    bucketing / one-hot encoding as the training notebooks, using the fixed
    keep_locations list so an unfamiliar location falls into 'other' instead
    of raising or silently being dropped.

    Raises ValueError if total_sqft or size can't be parsed - the API layer
    should catch this and return a 422, not let a None reach the model.
    """
    parsed_sqft = parse_sqft(total_sqft)
    if parsed_sqft is None:
        raise ValueError(f"Could not parse total_sqft: {total_sqft!r}")

    bhk = extract_bhk(size)
    if bhk is None:
        raise ValueError(f"Could not extract BHK from size: {size!r}")

    bucketed_location = location if location in keep_locations else "other"

    row = {"bath": bath, "balcony": balcony, "total_sqft": parsed_sqft, "bhk": bhk}
    for loc in keep_locations:
        row[f"location_{loc}"] = 1 if loc == bucketed_location else 0
    row["location_other"] = 1 if bucketed_location == "other" else 0

    columns = feature_columns(keep_locations)
    return pd.DataFrame([row], columns=columns)