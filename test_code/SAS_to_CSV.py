import io
import pandas as pd
import json
import random
from typing import Dict, List
from sas7bdat import SAS7BDAT

try:
    sas_file = "./sample_data/sas_customers.sas7bdat"
    sas_df = pd.read_sas(sas_file, format="sas7bdat")
    # Convert all object/bytes columns to str
    for col in sas_df.select_dtypes([object]).columns:
        sas_df[col] = sas_df[col].apply(lambda x: x.decode("utf-8").strip() if isinstance(x, bytes) else x)
    
    print(f"SAS dataset loaded: {sas_df.shape[0]} rows, {sas_df.shape[1]} cols")
except Exception as e:
    print(f"❌ Error reading SAS dataset: {e}")

if sas_df is not None:
    print(sas_df.head())
