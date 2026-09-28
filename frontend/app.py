# ---------------------------------------------------------------
# SuperKart Sales Forecast - Streamlit front-end
# ---------------------------------------------------------------
import os
import io
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SuperKart Sales Forecast", page_icon="🛒", layout="centered")

# Address of the Flask API. In Docker we reach it by container name over the shared network.
BACKEND_URL = os.getenv("BACKEND_URL", "http://superkart-backend:7860")
# The 4 stores in the training data and their attributes
STORES = {
    "OUT001": {"Store_Size": "High",   "Store_Location_City_Type": "Tier 2", "Store_Type": "Supermarket Type1",   "Year": 1987},
    "OUT002": {"Store_Size": "Small",  "Store_Location_City_Type": "Tier 3", "Store_Type": "Food Mart",           "Year": 1998},
    "OUT003": {"Store_Size": "Medium", "Store_Location_City_Type": "Tier 1", "Store_Type": "Departmental Store",  "Year": 1999},
    "OUT004": {"Store_Size": "Medium", "Store_Location_City_Type": "Tier 2", "Store_Type": "Supermarket Type2",   "Year": 2009},
}
PRODUCT_TYPES = ["Baking Goods", "Breads", "Breakfast", "Canned", "Dairy", "Frozen Foods", "Fruits and Vegetables",
                 "Hard Drinks", "Health and Hygiene", "Household", "Meat", "Others", "Seafood", "Snack Foods",
                 "Soft Drinks", "Starchy Foods"]

st.title("🛒 SuperKart Sales Forecast")
st.caption("Predict the total revenue of a product in a store using the deployed ML model.")

tab_single, tab_batch = st.tabs(["Single prediction", "Batch prediction"])

# ------------------------- Online (single) inference -------------------------
with tab_single:
    st.subheader("Enter product and store details")
    col1, col2 = st.columns(2)

    with col1:
        product_type = st.selectbox("Product type", PRODUCT_TYPES)
        sugar = st.selectbox("Sugar content", ["Low Sugar", "Regular", "No Sugar"])
        weight = st.number_input("Product weight", min_value=1.0, max_value=30.0, value=12.65, step=0.1)
        area = st.number_input("Allocated display area (ratio)", min_value=0.0, max_value=0.5, value=0.07, step=0.001, format="%.3f")
        mrp = st.number_input("Product MRP", min_value=10.0, max_value=400.0, value=147.0, step=0.5)

    with col2:
        store_id = st.selectbox("Store", list(STORES.keys()))
        s = STORES[store_id]
        st.info(f"**{s['Store_Type']}** | Size: {s['Store_Size']} | {s['Store_Location_City_Type']} | Est. {s['Year']}")

    if st.button("Predict sales", type="primary"):
        payload = {
            "Product_Weight": weight,
            "Product_Sugar_Content": sugar,
            "Product_Allocated_Area": area,
            "Product_Type": product_type,
            "Product_MRP": mrp,
            "Store_Establishment_Year": s["Year"],
            "Store_Size": s["Store_Size"],
            "Store_Location_City_Type": s["Store_Location_City_Type"],
            "Store_Type": s["Store_Type"],
        }
        try:
            r = requests.post(f"{BACKEND_URL}/v1/predict", json=payload, timeout=30)
            if r.ok:
                st.success(f"Predicted sales: **{r.json()['Predicted_Sales']:,.2f}**")
            else:
                st.error(f"API error {r.status_code}: {r.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Could not reach the backend at {BACKEND_URL}: {e}")

# ------------------------------ Batch inference ------------------------------
with tab_batch:
    st.subheader("Upload a CSV for batch forecasting")
    st.caption("Required columns: Product_Weight, Product_Sugar_Content, Product_Allocated_Area, Product_Type, Product_MRP, "
               "Store_Establishment_Year, Store_Size, Store_Location_City_Type, Store_Type")
    uploaded = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded is not None:
        batch_df = pd.read_csv(uploaded)
        st.write("Preview of uploaded data:")
        st.dataframe(batch_df.head())

        if st.button("Predict for all rows"):
            try:
                csv_bytes = batch_df.to_csv(index=False).encode("utf-8")
                r = requests.post(f"{BACKEND_URL}/v1/predictbatch",
                                  files={"file": ("batch.csv", csv_bytes, "text/csv")}, timeout=120)
                if r.ok:
                    preds = r.json()
                    result = batch_df.copy()
                    result["Predicted_Sales"] = [preds[str(i)] for i in result.index]
                    st.success(f"Predicted {len(result)} rows. Total forecast revenue: {result['Predicted_Sales'].sum():,.2f}")
                    st.dataframe(result)
                    st.download_button("Download predictions (CSV)", result.to_csv(index=False).encode("utf-8"),
                                       file_name="superkart_predictions.csv", mime="text/csv")
                else:
                    st.error(f"API error {r.status_code}: {r.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Could not reach the backend at {BACKEND_URL}: {e}")
