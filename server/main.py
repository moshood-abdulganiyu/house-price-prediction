"""FastAPI backend for house price prediction.

Loads the trained Pipeline once at startup and exposes a typed /predict
endpoint. Feature prep and inference logic both live in src/, this file
just wires them into an API - same split as the Titanic project.
"""

import sys
from pathlib import Path

# repo root on sys.path so `from src...` imports work regardless of cwd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.model import load_model, predict_price
from src.preprocess import load_keep_locations, prepare_features

app = FastAPI(title="House Price Prediction API")

MODEL = load_model()
KEEP_LOCATIONS = load_keep_locations(
    Path(__file__).resolve().parent / "keep_locations.json"
)


class PredictRequest(BaseModel):
    location: str = Field(..., examples=["Whitefield"])
    size: str = Field(..., examples=["2 BHK"])
    total_sqft: str = Field(..., examples=["1200"])
    bath: float = Field(..., ge=0)
    balcony: float = Field(..., ge=0)


class PredictResponse(BaseModel):
    predicted_price_lakhs: float


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest):
    try:
        features = prepare_features(
            location=payload.location,
            size=payload.size,
            total_sqft=payload.total_sqft,
            bath=payload.bath,
            balcony=payload.balcony,
            keep_locations=KEEP_LOCATIONS,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    price = predict_price(MODEL, features)
    return PredictResponse(predicted_price_lakhs=price)