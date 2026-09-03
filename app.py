import io
import streamlit as st
import pandas as pd
import json
import random
from typing import Dict, List

#Execution
#streamlit run app.py

# ---------------------------
# Common Functions
# --------------------------
#Convert the raw byte values (ASCII codes) instead of decoded strings
def decode_value(x):
    if isinstance(x, (bytes, bytearray)):
        #E.g. b'Alice' → decoded to "Alice"
        #.strip() cleans trailing spaces from SAS fixed-width CHAR fields.
        return x.decode("utf-8", errors="ignore").strip()
    if isinstance(x, (list, tuple)) or hasattr(x, "__iter__") and not isinstance(x, str):
        try:
            #Example [65,108,105,99,101] → converted to bytes([65,108,105,99,101]) 
            # = b"Alice" → "Alice"
            #.strip() cleans trailing spaces from SAS fixed-width CHAR fields.
            return bytes(x).decode("utf-8", errors="ignore").strip()
        except Exception:
            return x
    return x
# ---------------------------
# ---------------------------

# ---------------------------
# Simulated Knowledge Base (Mapping + Validation Templates)
# ---------------------------
MAPPINGS = {
    "customer": {
        "sas_table": "saslib.customer",
        "sf_table": "landing.customer",
        "columns": [
            {"src": "cust_id", "tgt": "cust_id", "transform": "CAST"},
            {"src": "first_name", "tgt": "first_name"},
            {"src": "last_name", "tgt": "last_name"},
            {"src": "email", "tgt": "email", "pii": True, "masking": "hash_email"},
            {"src": "birth_dt", "tgt": "birth_dt", "transform": "SAS_DATE_TO_DATE"},
            {"src": "is_active", "tgt": "is_active", "transform": "0/1 to BOOLEAN"},
        ],
    },
    "transaction": {
        "sas_table": "saslib.transaction",
        "sf_table": "landing.transaction",
        "columns": [
            {"src": "tran_id", "tgt": "tran_id"},
            {"src": "cust_id", "tgt": "cust_id"},
            {"src": "tran_dt", "tgt": "tran_dt", "transform": "SAS_DATETIME_TO_TIMESTAMP"},
            {"src": "amount", "tgt": "amount"},
            {"src": "currency", "tgt": "currency"},
            {"src": "product_id", "tgt": "product_id"},
        ],
    },
}

VALIDATION_TEMPLATES = [
    {"name": "row_count", "desc": "Row counts should match"},
    {"name": "sum_amount", "desc": "SUM(amount) should match within tolerance"},
    {"name": "distinct_cust", "desc": "Distinct customers should match"},
    {"name": "null_email", "desc": "No null emails allowed"},
]

# ---------------------------
# Helper functions
# ---------------------------
def generate_validation_tests(table: str) -> List[Dict]:
    """Simulate LLM generating tests from templates + mappings"""
    tests = []
    if table == "customer":
        tests.append({"name": "row_count", "sql": "SELECT COUNT(*) FROM landing.customer", "tolerance": 0})
        tests.append({"name": "null_email", "sql": "SELECT COUNT(*) FROM landing.customer WHERE email IS NULL", "tolerance": 0})
    if table == "transaction":
        tests.append({"name": "row_count", "sql": "SELECT COUNT(*) FROM landing.transaction", "tolerance": 0})
        tests.append({"name": "sum_amount", "sql": "SELECT SUM(amount) FROM landing.transaction", "tolerance": 0.001})
        tests.append({"name": "distinct_cust", "sql": "SELECT COUNT(DISTINCT cust_id) FROM landing.transaction", "tolerance": 0})
    return tests

def run_validation(test: Dict, sas_df: pd.DataFrame, sf_df: pd.DataFrame) -> Dict:
    """Run test by comparing pandas results"""
    result = {"test_name": test["name"], "status": "PASS", "sas_value": None, "sf_value": None, "explanation": ""}

    if test["name"] == "row_count":
        result["sas_value"] = len(sas_df)
        result["sf_value"] = len(sf_df)

    elif test["name"] == "sum_amount":
        result["sas_value"] = round(sas_df["amount"].sum(), 2)
        result["sf_value"] = round(sf_df["amount"].sum(), 2)

    elif test["name"] == "distinct_cust":
        result["sas_value"] = sas_df["cust_id"].nunique()
        result["sf_value"] = sf_df["cust_id"].nunique()

    elif test["name"] == "null_email":
        result["sas_value"] = sas_df["email"].isna().sum()
        result["sf_value"] = sf_df["email"].isna().sum()

    # Compare values
    if abs(result["sas_value"] - result["sf_value"]) > test["tolerance"]:
        result["status"] = "FAIL"
        result["explanation"] = f"Mismatch found: SAS={result['sas_value']} vs Snowflake={result['sf_value']}."
    else:
        result["explanation"] = "Validation passed ✅"

    return result

# ---------------------------
# Streamlit UI
# ---------------------------
st.title("🔍 Agentic RAG Migration Validation & Testing (SAS → Snowflake Demo)")

st.sidebar.header("Upload Data")
sas_file = st.sidebar.file_uploader("Upload SAS dataset (.sas7bdat or .xpt)", type=["sas7bdat", "xpt"])
sf_file = st.sidebar.file_uploader("Upload Snowflake migrated data (CSV)", type=["csv"])
sas_df = None
sf_df = None

if sas_file:
    try:
        # Pandas will auto-detect format
        sas_df = pd.read_sas(sas_file, format="sas7bdat")

        #Properly decode SAS character variables
        sas_df = sas_df.applymap(decode_value)
        sas_df.columns = sas_df.columns.str.lower()
        
        st.success(f"SAS dataset loaded: {sas_df.shape[0]} rows, {sas_df.shape[1]} cols")
    except Exception as e:
        st.error(f"❌ Error reading SAS dataset: {e}")

if sf_file:
    try:
        sf_df = pd.read_csv(io.StringIO(sf_file.getvalue().decode("utf-8")))
        st.success(f"Snowflake CSV loaded: {sf_df.shape[0]} rows, {sf_df.shape[1]} cols")
    except Exception as e:
        st.error(f"❌ Error reading Snowflake CSV: {e}")

#if sas_file and sf_file:
#    sas_df = pd.read_csv(sas_file)
#    sf_df = pd.read_csv(sf_file)

if sas_df is not None and sf_df is not None:
    st.subheader("📊 Preview Uploaded Data")
    st.write("**SAS Baseline:**")
    st.dataframe(sas_df.head())
    st.write("**Snowflake Data:**")
    st.dataframe(sf_df.head())

    # Choose table type
    table_choice = st.selectbox("Select Table to Validate", ["customer", "transaction"])

    if st.button("🔎 Run Validation"):
        tests = generate_validation_tests(table_choice)

        results = []
        for test in tests:
            result = run_validation(test, sas_df, sf_df)
            results.append(result)

        results_df = pd.DataFrame(results)

        st.subheader("✅ Validation Results")
        st.dataframe(results_df)

        # Summary
        pass_count = sum(1 for r in results if r["status"] == "PASS")
        fail_count = sum(1 for r in results if r["status"] == "FAIL")

        st.metric("Tests Passed", pass_count)
        st.metric("Tests Failed", fail_count)

        if fail_count > 0:
            st.warning("⚠️ Some tests failed. LLM explanation could suggest fixes here.")
            for r in results:
                if r["status"] == "FAIL":
                    st.error(f"❌ {r['test_name']}: {r['explanation']}")
        else:
            st.success("🎉 All tests passed!")
