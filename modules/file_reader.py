
import pandas as pd


def read_uploaded_file(uploaded_file):

    name = uploaded_file.name.lower()

    try:
        if name.endswith(".csv"):

            # Read uploaded file as bytes
            file_bytes = uploaded_file.getvalue()

            encodings = [
                "utf-8-sig",
                "utf-8",
                "cp1252",
                "latin1"
            ]

            for encoding in encodings:
                try:
                    from io import BytesIO

                    df = pd.read_csv(
                        BytesIO(file_bytes),
                        encoding=encoding
                    )

                    return df

                except UnicodeDecodeError:
                    continue

            raise ValueError(
                "Unable to detect CSV encoding. "
                "Please save the file as UTF-8."
            )

        elif name.endswith((".xlsx", ".xls")):

            return pd.read_excel(uploaded_file)

        elif name.endswith(".json"):

            return pd.read_json(uploaded_file)

        else:
            raise ValueError("Unsupported file format")

    except Exception as error:
        raise ValueError(
            f"File reading failed: {error}"
        )
