"""
sheets_writer.py
BC CV Screener — Stage 7
Writes screener output to the BC PC Screener Google Sheet.

Sheet structure:
  Tab 1 — "CV Pass-Fail"  : headers on row 1, data from row 2
  Tab 2 — "Round 0"       : headers on row 3, data from row 4
"""

import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

# ── Constants ──────────────────────────────────────────────────────────────────

# Sheet IDs — test vs live
SHEET_IDS = {
    "test": "10jW5bqKiR-4HxWHcCA6MjALOBnvyEaYQcCNxDE2S9nc",  # BC PC Screener — Agent Test v1.0
    "live": "1W64AHbbVCt2o9End4nOYWwwqc1e3oeMVC_w-jKenYRQ",  # replace when live tracker is ready
}

def _get_sheet_id() -> str:
    try:
        env = st.secrets.get("ENV", "test")
    except Exception:
        env = "test"
    return SHEET_IDS.get(env, SHEET_IDS["test"])

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# CV Pass-Fail tab — columns in tracker order
CV_PASS_FAIL_COLUMNS = [
    "Candidate",
    "Format",
    "Experience Band",
    "Experience (Pass/Fail)",
    "Identity/Activity",
    "External-Facing",
    "CV Quality",
    "Excellence Signal",
    "Decision",
    "Reason",
]

# Round 0 tab — sheet column headers (in order)
ROUND_0_COLUMNS = [
    "Name",
    "CV (Y/N)",
    "Experience (months + band)",
    "Internship/Part-time",
    "Current Role",
    "Industry",
    "Key Skills",
    "Current Location",
    "DOB",
    "UG Grad Year",
    "PG Grad Year",
    "Email",
    "Phone",
    "Summary",
    "Round 0 Pass/Fail",
]

# Round 0 tab — screener dict keys, in the same column order as ROUND_0_COLUMNS
ROUND_0_KEYS = [
    "candidate",            # Name
    "cv_yn",                # CV (Y/N)  — injected as "Y" at write time
    "experience_band",      # Experience (months + band)
    "internship_part_time", # Internship/Part-time
    "current_role",         # Current Role
    "industry",             # Industry
    "key_skills",           # Key Skills
    "current_location",     # Current Location
    "dob",                  # DOB
    "ug_grad_year",         # UG Grad Year
    "pg_grad_year",         # PG Grad Year
    "email",                # Email
    "phone",                # Phone
    "summary",              # Summary
    "decision",             # Round 0 Pass/Fail
]


# ── Auth ───────────────────────────────────────────────────────────────────────

def _get_client() -> gspread.Client:
    """
    Authenticate using credentials.json (local) or st.secrets (Streamlit Cloud).
    Returns an authorised gspread client.
    """
    try:
        # Streamlit Cloud: credentials stored as a TOML table in secrets
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    except (KeyError, FileNotFoundError):
        # Local development: credentials.json in project root
        creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)

    return gspread.authorize(creds)


def _get_sheet():
    """Return the authorised Spreadsheet object."""
    client = _get_client()
    return client.open_by_key(_get_sheet_id())


# ── Internal helpers ───────────────────────────────────────────────────────────

def _row_from_dict(columns: list[str], data: dict) -> list:
    """
    Build an ordered list of values from a dict, using column names as keys.
    Missing keys → empty string (never raises).
    """
    return [str(data.get(col, "")) for col in columns]


def _append_rows(sheet, tab_name: str, rows: list[list], first_data_row: int) -> int:
    """
    Append rows to the named tab below any existing data.
    first_data_row is the row number where data starts (e.g. 2 for CV Pass-Fail, 4 for Round 0).
    Returns the number of rows written.
    """
    ws = sheet.worksheet(tab_name)

    if not rows:
        return 0

    # Read column A only and scan downward from first_data_row for the first empty cell.
    # get_all_values() includes trailing blank rows, so len()-based counting overshoots.
    col_a = ws.col_values(1)  # 1-indexed; col_a[i] is sheet row i+1
    next_row = first_data_row
    for i in range(first_data_row - 1, len(col_a)):
        if col_a[i].strip() == "":
            break
        next_row = i + 2  # advance past this occupied row

    # gspread range notation: A{next_row}
    start_cell = f"A{next_row}"
    ws.update(start_cell, rows, value_input_option="RAW")
    return len(rows)


# ── Public API ─────────────────────────────────────────────────────────────────

def write_cv_pass_fail(candidates: list[dict]) -> dict:
    """
    Write one row per candidate to the 'CV Pass-Fail' tab.

    Each dict should have keys matching CV_PASS_FAIL_COLUMNS.
    Missing keys are written as empty strings.

    Returns:
        {"written": int, "tab": "CV Pass-Fail", "error": None | str}
    """
    try:
        sheet = _get_sheet()
        rows = [_row_from_dict(CV_PASS_FAIL_COLUMNS, c) for c in candidates]
        written = _append_rows(sheet, "CV Pass-Fail", rows, first_data_row=2)
        return {"written": written, "tab": "CV Pass-Fail", "error": None}
    except gspread.exceptions.APIError as e:
        return {"written": 0, "tab": "CV Pass-Fail", "error": f"Sheets API error: {e}"}
    except Exception as e:
        return {"written": 0, "tab": "CV Pass-Fail", "error": str(e)}


def write_round_0(candidates: list[dict]) -> dict:
    """
    Write one row per passed candidate to the 'Round 0' tab.
    Headers are on row 3; data starts at row 4.

    Each dict should have keys matching ROUND_0_COLUMNS.
    Missing keys are written as empty strings.

    Returns:
        {"written": int, "tab": "Round 0", "error": None | str}
    """
    try:
        sheet = _get_sheet()
        rows = [_row_from_dict(ROUND_0_KEYS, {**c, "cv_yn": "Y"}) for c in candidates]
        written = _append_rows(sheet, "Round 0", rows, first_data_row=4)
        return {"written": written, "tab": "Round 0", "error": None}
    except gspread.exceptions.APIError as e:
        return {"written": 0, "tab": "Round 0", "error": f"Sheets API error: {e}"}
    except Exception as e:
        return {"written": 0, "tab": "Round 0", "error": str(e)}


def write_screening_results(
    all_candidates: list[dict],
    passed_candidates: list[dict],
) -> dict:
    """
    Convenience function: writes both tabs in one call.

    all_candidates  → CV Pass-Fail tab (all, including fails)
    passed_candidates → Round 0 tab (passed only)

    Returns:
        {
            "cv_pass_fail": {"written": int, "error": None | str},
            "round_0":      {"written": int, "error": None | str},
        }
    """
    cv_result = write_cv_pass_fail(all_candidates)
    r0_result = write_round_0(passed_candidates)
    return {
        "cv_pass_fail": cv_result,
        "round_0": r0_result,
    }