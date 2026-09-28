# ---------------------------------------------------------------
# SuperKart Sales Forecast API (Flask)
# ---------------------------------------------------------------
import joblib
import pandas as pd
from flask import Flask, request, jsonify

# Create the Flask application object
superkart_api = Flask("SuperKart Sales Predictor")

# Load the serialized pipeline ONCE at start-up (not on every request) -> fast responses
model = joblib.load("superkart_model.joblib")

# The exact features (and order) the model was trained on
FEATURES = [
    "Product_Weight", "Product_Sugar_Content", "Product_Allocated_Area", "Product_Type", "Product_MRP",
    "Store_Establishment_Year", "Store_Size", "Store_Location_City_Type", "Store_Type",
]


def clean(df):
    """Apply the same label clean-up used in training and keep only the model features."""
    df = df.copy()
    df["Product_Sugar_Content"] = df["Product_Sugar_Content"].replace({"reg": "Regular"})
    return df[FEATURES]


@superkart_api.get("/")
def home():
    """Health-check route."""
    return "Welcome to the SuperKart Sales Prediction API!"


@superkart_api.post("/v1/predict")
def predict_sales():
    """Online inference: one JSON record in -> one prediction out."""
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Send a JSON body."}), 400

    missing = [f for f in FEATURES if f not in payload]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    try:
        sample = clean(pd.DataFrame([payload]))
        prediction = float(model.predict(sample)[0])
        return jsonify({"Predicted_Sales": round(prediction, 2)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@superkart_api.post("/v1/predictbatch")
def predict_sales_batch():
    """Batch inference: CSV file in -> {row_index: prediction} out."""
    if "file" not in request.files:
        return jsonify({"error": "Upload a CSV file under the key 'file'."}), 400

    try:
        batch = pd.read_csv(request.files["file"])
        missing = [f for f in FEATURES if f not in batch.columns]
        if missing:
            return jsonify({"error": f"CSV is missing columns: {missing}"}), 400

        preds = model.predict(clean(batch)).round(2)
        return jsonify({str(i): float(p) for i, p in zip(batch.index, preds)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# Local run only; in Docker we use gunicorn (see Dockerfile)
if __name__ == "__main__":
    superkart_api.run(debug=False, host="0.0.0.0", port=7860)
