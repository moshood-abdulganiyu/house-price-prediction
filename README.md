# House Price Prediction

End-to-end ML portfolio project: data cleaning, EDA, model training, FastAPI backend, and a static frontend, deployed live across two services.

**Live demo:** [Frontend](https://huggingface.co/spaces/AbdukganiyMK/house-price-prediction-frontend)
**API docs:** [https://house-price-prediction-f449.onrender.com/docs](https://house-price-prediction-f449.onrender.com/docs)

![App screenshot](screenshots/demo.png)

## Problem

Predict the sale price of a Bengaluru house from its location, size (BHK), total square footage, number of bathrooms, and number of balconies. Regression, trained on a 13,303-row Bengaluru housing dataset.

## Approach

1. **Data cleaning** — `total_sqft` came in as mixed formats: ranges like "2100-2850" (averaged to a single value) and rows with non-numeric units mixed in (dropped or converted). `size` was a text field like "2 BHK", parsed with a regex to extract the numeric BHK count. Nulls in `society`, `balcony`, and `bath` were checked and handled explicitly rather than dropped by default.
2. **EDA** — explored price distribution, price per sqft by location, and outliers (e.g. a 1-bath, 10-BHK listing, or a price-per-sqft far outside the local range). Outlier rows were removed against a documented rule rather than a blanket cutoff, since this is scraped listing data with real data-entry errors, not just noise.
3. **Feature engineering** — `location` is high-cardinality (1000+ unique values). Rare locations were bucketed into an `other` category before one-hot encoding, so the model doesn't get a sparse, near-useless feature per rare location. The one-hot columns come from a fixed saved category list (`keep_locations.json`) rather than `pd.get_dummies()` recomputed per call, because that function decides which category to drop based on what's present in a given call, which breaks single-row inference — the same bug class documented in the Titanic project.
4. **Model** — compared Linear Regression, Ridge, and Random Forest Regressor. Random Forest won on the held-out test set by MAE, used as the primary comparison metric over R² because MAE is in lakhs and directly answers "how far off is a typical prediction", which is what matters for a price estimator. Final model: `StandardScaler` + `RandomForestRegressor`, bundled as a single scikit-learn `Pipeline` and saved with `joblib`.
5. **API** — FastAPI backend with a typed `/predict` endpoint (Pydantic request/response models), auto-generated docs at `/docs`.
6. **Frontend** — static HTML/CSS/JS form styled to a real estate reference design, Bengaluru house hero image, blue/white palette matched to the photo.

## Results

| Model               | R²    | MAE (lakhs) |
|----------------------|-------|-------------|
| Random Forest         | 0.640 | 31.40       |
| Ridge                  | 0.392 | 46.38       |
| Linear Regression      | 0.392 | 46.38       |

Random Forest selected for deployment based on the MAE comparison above. The version actually deployed is a size-tuned variant of this winner, not the one in the table above; see Known trade-offs.

## Architecture

Backend and frontend are deployed as two separate services, not bundled together:

- **Backend** — FastAPI on Render, deployed via Docker using the repo's `Dockerfile`.
- **Frontend** — static HTML/CSS/JS on a Hugging Face Static Space.

Same split as the Titanic project, for the same reason: Hugging Face Spaces puts free-tier Gradio accounts on ZeroGPU hardware, which can't be downgraded without a PRO subscription, and the Docker SDK on Spaces requires a paid plan. Splitting onto Render (backend) and a HF Static Space (frontend, no compute needed) avoided both paywalls. CORS on the backend is set to `allow_origins=["*"]` to allow the cross-origin frontend calls.

## Known trade-offs

**Model size vs. accuracy.** An unconstrained Random Forest (100 trees, no depth limit) pickles to 71.6 MB; a 200-tree version pickles to 143 MB, over GitHub's 100 MB push limit. Capping `max_depth=12` and dropping to 50 trees cuts the file to 3.2 MB, a ~40x reduction, while actually scoring slightly higher R² (0.647 vs. 0.632 for the 200-tree version) at the cost of a few lakhs more MAE (33.59 vs. 31.40). With 224 mostly-sparse one-hot location columns, the uncapped trees were overfitting to location-specific noise rather than learning a cleaner general pattern, so the capped version generalizes slightly better and ships an order of magnitude lighter. This is the config actually deployed in `server/model.joblib`.

**Dropped form fields.** `area_type` and `availability` are in the raw dataset and `area_type` carries real signal, but neither was built into the frontend form. This was a deliberate scope decision made before Step 8, not an oversight discovered after the fact.

**Reliability on high-end prices.** The dataset is right-skewed (max price 3,600 lakhs against a 72 lakh median). The model is least reliable on the small number of very expensive listings, since there just isn't much data up there to learn from. This is a real limitation of the current model, not something addressed in this pass.

## Running locally

Requires [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/moshood-abdulganiyu/house-price-prediction.git
cd house-price-prediction
uv sync
uv run uvicorn server.main:app --reload
```

API will be live at `http://localhost:8000`, docs at `http://localhost:8000/docs`.

For the frontend, open `client/index.html` directly, or serve it with any static file server. Update `API_URL` in `client/app.js` to point at your local backend if testing locally.

## Tech stack

- **ML:** scikit-learn, pandas, joblib
- **Backend:** FastAPI, uvicorn
- **Frontend:** HTML, CSS, JavaScript (no framework)
- **Dependency management:** uv
- **Deployment:** Render (backend), Hugging Face Static Spaces (frontend)
