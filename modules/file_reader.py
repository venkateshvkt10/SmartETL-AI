import json
import pandas as pd

def read_uploaded_file(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    if name.endswith(".json"):
        return pd.read_json(uploaded_file)
    raise ValueError("Supported formats are CSV, XLSX, XLS and JSON.")
