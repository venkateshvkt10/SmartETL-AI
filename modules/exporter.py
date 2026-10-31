from io import BytesIO
import pandas as pd

def to_excel_bytes(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="CleanedData")
    return buffer.getvalue()
