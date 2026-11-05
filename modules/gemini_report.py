
import os
import json
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types


# Load environment variables from project root
load_dotenv()


def gemini_is_configured():
    """
    Check whether a Gemini API key is available.
    """
    return bool(
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
    )


def _safe_list(value, limit=15):
    """
    Convert report items into a safe, limited list.
    """
    if not isinstance(value, (list, tuple)):
        return []

    return [
        str(item)[:500]
        for item in value[:limit]
    ]


def build_quality_summary(quality_report, pipeline_summary):
    """
    Prepare a compact summary for Gemini.

    The original uploaded dataset and its records
    are NOT sent to Gemini.
    """

    quality_data = {
        "quality_score": quality_report.get("quality_score"),
        "grade": quality_report.get("grade"),
        "completeness": quality_report.get("completeness"),
        "validity": quality_report.get("validity"),
        "issues": _safe_list(
            quality_report.get("issues")
        ),
        "recommendations": _safe_list(
            quality_report.get("recommendations")
        )
    }

    pipeline_data = {
        "total_input_rows": pipeline_summary.get(
            "total_input_rows"
        ),
        "cleaned_rows": pipeline_summary.get(
            "cleaned_rows"
        ),
        "valid_records": pipeline_summary.get(
            "valid_records"
        ),
        "rejected_records": pipeline_summary.get(
            "rejected_records"
        ),
        "duplicates_removed": pipeline_summary.get(
            "duplicates_removed"
        ),
        "missing_cells_filled": pipeline_summary.get(
            "missing_cells_filled"
        ),
        "execution_time_seconds": pipeline_summary.get(
            "execution_time_seconds"
        ),
        "pipeline_status": pipeline_summary.get(
            "pipeline_status"
        )
    }

    return {
        "quality_report": quality_data,
        "pipeline_summary": pipeline_data
    }


def generate_gemini_quality_report(
    quality_report,
    pipeline_summary
):
    """
    Generate a business-friendly data quality
    explanation using the Gemini API.
    """

    api_key = (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
    )

    if not api_key:
        raise ValueError(
            "Gemini API key not found. "
            "Please configure GEMINI_API_KEY in your .env file."
        )

    model_name = os.getenv(
        "GEMINI_MODEL",
        "gemini-flash-latest"
    )

    # Prepare only quality metrics and pipeline counts.
    report_data = build_quality_summary(
        quality_report,
        pipeline_summary
    )

    json_summary = json.dumps(
        report_data,
        indent=2,
        ensure_ascii=False,
        default=str
    )

    prompt = f"""
You are an experienced Data Quality Analyst
and Data Engineering consultant.

Analyze the following ETL quality summary.

IMPORTANT RULES:
1. Use only the supplied metrics and issues.
2. Do not invent data, percentages or findings.
3. Do not claim that a problem exists unless it is
   supported by the supplied report.
4. Explain technical problems in simple business language.
5. Clearly distinguish measured results from suggestions.

ETL QUALITY SUMMARY:

{json_summary}

Generate a professional report using these sections:

# AI Data Quality Analysis

## 1. Executive Summary
Explain the overall dataset quality in simple language.

## 2. Quality Score Interpretation
Explain the supplied score, grade, completeness and validity.

## 3. Key Data Quality Issues
Explain each identified issue and its possible impact.

## 4. ETL Pipeline Analysis
Explain the supplied input, cleaned, valid and rejected counts.

## 5. Business Impact
Explain how the reported issues could affect reporting,
analytics and business decisions.

## 6. Recommended Actions
Give practical, prioritized recommendations.

## 7. Final Assessment
Provide a short professional conclusion.

Use clear headings and bullet points.
Keep the report concise, accurate and useful.
"""

    client = genai.Client(api_key=api_key)

    try:
        for attempt in range(2):

            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        max_output_tokens=1500
                    )
                )

                report_text = response.text

                if not report_text or not report_text.strip():
                    raise RuntimeError(
                        "Gemini returned an empty report."
                    )

                return report_text.strip()

            except Exception as error:

                error_message = str(error).upper()

                is_temporary_error = (
                    "503" in error_message
                    or "UNAVAILABLE" in error_message
                )

                if not is_temporary_error or attempt == 1:
                    raise

                print(
                    "Gemini temporarily unavailable. "
                    "Retrying in 10 seconds..."
                )

                time.sleep(10)

    finally:
        client.close()
