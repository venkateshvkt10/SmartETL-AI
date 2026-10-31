# SmartETL AI

A beginner-friendly ETL and data-quality web application built with Python and Streamlit.

## Current starter features
- Upload CSV, Excel and JSON files.
- Preview uploaded data.
- Remove exact duplicate rows.
- Fill numeric nulls using mean, median or zero (optional).
- Trim whitespace from text fields.
- Flag remaining missing values.
- Download cleaned CSV/Excel and a validation CSV.

## Local setup (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## Git and GitHub

Create a **private** GitHub repository named `SmartETL-AI`, then run:

```bash
git init
git add .
git commit -m "Initial SmartETL AI starter"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/SmartETL-AI.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

## Important
- This is a starter project, not production-ready.
- The current duplicate rule removes exact duplicate rows only. Business-key duplicate rules will be configurable in a later phase.
- Null filling currently applies only to numeric columns. Missing text values are flagged, not fabricated.
- Do not upload confidential or personal data.
- Before public deployment, add authentication, upload limits, safe temporary-file handling and tests.

## Planned roadmap
1. Configurable data profiling and cleaning rules.
2. Required-field, data-type, email, date and range validation.
3. Rejected-record export and detailed error messages.
4. AI-assisted report writing with a non-AI fallback.
5. Private deployment and access control.
