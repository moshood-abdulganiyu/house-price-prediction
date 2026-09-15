
const API_URL = "https://house-price-prediction-f449.onrender.com/";

const form = document.getElementById("predict-form");
const submitBtn = document.getElementById("submit-btn");

const emptyEl = document.getElementById("estimate-empty");
const loadingEl = document.getElementById("estimate-loading");
const resultEl = document.getElementById("estimate-result");
const errorEl = document.getElementById("estimate-error");
const priceEl = document.getElementById("estimate-price");
const errorMessageEl = document.getElementById("estimate-error-message");

function showState(state) {
  emptyEl.hidden = state !== "empty";
  loadingEl.hidden = state !== "loading";
  resultEl.hidden = state !== "result";
  errorEl.hidden = state !== "error";
}

function formatPrice(lakhs) {
  if (lakhs >= 100) {
    return "\u20B9" + (lakhs / 100).toFixed(2) + " Cr";
  }
  return "\u20B9" + lakhs.toFixed(2) + " Lakh";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = {
    location: document.getElementById("location").value.trim(),
    size: document.getElementById("bhk").value,
    total_sqft: document.getElementById("sqft").value,
    bath: Number(document.getElementById("bath").value),
    balcony: Number(document.getElementById("balcony").value),
  };

  submitBtn.disabled = true;
  showState("loading");

  try {
    const response = await fetch(`${API_URL}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const body = await response.json().catch(() => null);
      const detail = body && body.detail ? body.detail : `Request failed (${response.status})`;
      throw new Error(detail);
    }

    const data = await response.json();
    priceEl.textContent = formatPrice(data.predicted_price_lakhs);
    showState("result");
  } catch (err) {
    errorMessageEl.textContent =
      err.message === "Failed to fetch"
        ? "Could not reach the prediction API. Is the backend running?"
        : err.message;
    showState("error");
  } finally {
    submitBtn.disabled = false;
  }
});
