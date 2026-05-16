"""
app.py
BC CV Screener — Stage 8
Streamlit frontend. Upload CVs → screen via Claude → write to Google Sheet.
"""

import streamlit as st
import tempfile
import os
from datetime import datetime

from extractor import extract_text
from screener import screen_cv
from sheets_writer import write_screening_results

# ── Page config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="BC CV Screener",
    page_icon="🟠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Brand CSS ──────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500&family=DM+Mono&display=swap');

html, body, [class*="css"] {
  font-family: 'DM Sans', sans-serif;
  background-color: #FFF8F0 !important;
}
.topbar {
  background: #2C1810;
  padding: 16px 24px 14px;
  border-radius: 10px 10px 0 0;
}
.topbar-title { color: #FF9203; font-size: 17px; font-weight: 500; }
.topbar-sub { color: #a08070; font-size: 11px; margin-top: 3px; }
.tagline {
  background: white;
  border-bottom: 0.5px solid #e8d5c0;
  padding: 10px 24px;
  font-size: 13px;
  color: #8B5A2B;
  font-style: italic;
  margin-bottom: 20px;
}
.section-label {
  font-size: 11px;
  color: #8B5A2B;
  font-weight: 500;
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.status-ok {
  background: #e8f5e8;
  border: 0.5px solid #b0d8b0;
  border-radius: 8px;
  padding: 12px 16px;
  font-size: 13px;
  color: #2a7a2a;
  margin: 16px 0;
}
.status-warn {
  background: #fff0e8;
  border: 0.5px solid #f0b890;
  border-radius: 8px;
  padding: 12px 16px;
  font-size: 13px;
  color: #c05000;
  margin: 16px 0;
}
.metric-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin: 16px 0;
}
.metric {
  background: white;
  border-radius: 8px;
  border: 0.5px solid #e8d5c0;
  padding: 14px 8px;
  text-align: center;
}
.metric-num { font-size: 26px; font-weight: 500; }
.metric-lbl { font-size: 11px; color: #a08070; margin-top: 2px; }
.error-card {
  background: white;
  border: 0.5px solid #f0d0c0;
  border-radius: 8px;
  padding: 14px 16px;
  margin-top: 16px;
}
.error-title { font-size: 12px; font-weight: 500; color: #c03030; margin-bottom: 10px; }
.error-row {
  font-size: 12px;
  color: #8B5A2B;
  padding: 5px 0;
  border-bottom: 0.5px solid #f0e8e0;
}
.error-row:last-child { border-bottom: none; }

.stButton > button {
  background: #603813 !important;
  color: white !important;
  border: none !important;
  border-radius: 8px !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  width: 100% !important;
  padding: 12px !important;
}
.stButton > button:hover { background: #8B5A2B !important; }
.stButton > button:disabled { background: #c0a090 !important; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="topbar">
  <div class="topbar-title">Brown Collab — AI CV Screener</div>
  <div class="topbar-sub">Internal tool · v1.0</div>
</div>
<div class="tagline">Screen CVs against your elimination rules — in minutes.</div>
""", unsafe_allow_html=True)

# ── API key ────────────────────────────────────────────────────────────────────

try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except Exception:
    st.error("ANTHROPIC_API_KEY not found in .streamlit/secrets.toml")
    st.stop()

# ── Config row ─────────────────────────────────────────────────────────────────

col1, col2, col3 = st.columns([2, 1, 1])

MONTHS = ["January","February","March","April","May","June",
          "July","August","September","October","November","December"]
current_month = datetime.now().month

with col1:
    st.markdown('<div class="section-label">Select role</div>', unsafe_allow_html=True)
    role_display = st.selectbox(
        "role", ["Production Coordinator"],
        label_visibility="collapsed",
    )
    role_key = "production_coordinator"

with col2:
    st.markdown('<div class="section-label">Month</div>', unsafe_allow_html=True)
    month = st.selectbox(
        "month", MONTHS,
        index=current_month - 1,
        label_visibility="collapsed",
    )

with col3:
    st.markdown('<div class="section-label">Year</div>', unsafe_allow_html=True)
    year = st.selectbox(
        "year", [2026, 2025, 2027],
        index=0,
        label_visibility="collapsed",
    )

screening_date = f"{month} {year}"

# ── Upload ─────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-label" style="margin-top:20px; margin-bottom:6px;">Upload CVs</div>',
            unsafe_allow_html=True)

# Session state key increments to reset file uploader
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

uploaded_files = st.file_uploader(
    "Upload CVs",
    type=["pdf", "docx"],
    accept_multiple_files=True,
    label_visibility="collapsed",
    key=f"uploader_{st.session_state.uploader_key}",
)

st.caption("PDF or DOCX · Drag and drop or click Upload · Up to 50 files recommended")

if uploaded_files:
    st.caption(f"{len(uploaded_files)} file{'s' if len(uploaded_files) != 1 else ''} selected · "
               f"Screening date: {screening_date}")

# ── Run button ─────────────────────────────────────────────────────────────────

st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
if "run_done" not in st.session_state:
    st.session_state.run_done = False
run = st.button("▶  Run Screening", disabled=not uploaded_files)

# ── Screening ──────────────────────────────────────────────────────────────────

if run and uploaded_files:
    st.session_state.run_done = True

    total = len(uploaded_files)
    progress_bar = st.progress(0, text=f"Starting — 0 of {total}")
    status_text = st.empty()

    all_cv_rows = []
    passed_r0_rows = []
    errors = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for i, uploaded_file in enumerate(uploaded_files):

            cv_name = uploaded_file.name
            status_text.caption(f"Screening: {cv_name}")

            tmp_path = os.path.join(tmpdir, cv_name)
            with open(tmp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            fmt = "PDF" if cv_name.lower().endswith(".pdf") else "DOCX"

            try:
                # Step 1 — extract text
                extract_result = extract_text(tmp_path)
                raw_text = extract_result.get('text', '') if isinstance(extract_result, dict) else extract_result

                if not raw_text or len(raw_text.strip()) < 50:
                    errors.append({
                        "file": cv_name,
                        "reason": "OCR failed — unreadable file",
                        "type": "ocr",
                    })
                    progress_bar.progress((i + 1) / total, text=f"Processed {i + 1} of {total}")
                    continue

                # Step 2 — screen via Claude
                result = screen_cv(
                    cv_text=raw_text,
                    filename=cv_name,
                    screening_date=screening_date,
                    role=role_key,
                    api_key=api_key,
                )

                # Build CV Pass-Fail row
                cv_row = {
                    "Candidate":              result.get("candidate", cv_name),
                    "Experience Band":        result.get("experience_band", ""),
                    "Experience (Pass/Fail)": result.get("experience_pf", ""),
                    "Identity/Activity":      result.get("identity_activity", ""),
                    "External-Facing":        result.get("external_facing", ""),
                    "CV Quality":             result.get("cv_quality", ""),
                    "Excellence Signal":      result.get("excellence_signal", "—"),
                    "Decision":               result.get("decision", "FLAG"),
                    "Reason":                 result.get("reason", ""),
                    "Format":                 fmt,
                }
                all_cv_rows.append(cv_row)

                decision = result.get("decision", "FLAG")

                if decision == "PASS":
                    r0_row = {
                        "Name":                       result.get("candidate", cv_name),
                        "CV (Y/N)":                   "Y",
                        "Experience (months + band)":  result.get("experience_band", ""),
                        "Internship/Part-time":        "N/A",
                        "Current Role":                "N/A",
                        "Industry":                    "N/A",
                        "Key Skills":                  "N/A",
                        "Current Location":            "N/A",
                        "DOB":                         "N/A",
                        "UG Grad Year":                "N/A",
                        "PG Grad Year":                "N/A",
                        "Email":                       "N/A",
                        "Phone":                       "N/A",
                        "Summary":                     "N/A",
                        "Round 0 Pass/Fail":           "PASS",
                    }
                    passed_r0_rows.append(r0_row)

                elif decision == "FLAG":
                    errors.append({
                        "file": cv_name,
                        "reason": result.get("reason", "Band unclear — review manually"),
                        "type": "flag",
                    })

            except Exception as e:
                errors.append({
                    "file": cv_name,
                    "reason": f"Unexpected error — {str(e)[:80]}",
                    "type": "error",
                })

            progress_bar.progress((i + 1) / total, text=f"Processed {i + 1} of {total}")

    status_text.empty()
    progress_bar.empty()

    # ── Write to sheet ─────────────────────────────────────────────────────────

    sheet_error = None
    if all_cv_rows or passed_r0_rows:
        sheet_result = write_screening_results(all_cv_rows, passed_r0_rows)
        sheet_error = (sheet_result["cv_pass_fail"].get("error") or
                       sheet_result["round_0"].get("error"))

    # ── Summary ────────────────────────────────────────────────────────────────

    n_screened = len(all_cv_rows)
    n_pass = len(passed_r0_rows)
    n_flag = sum(1 for e in errors if e["type"] == "flag")

    if sheet_error:
        st.markdown(f"""
        <div class="status-warn">
          ⚠️ &nbsp; {n_screened} screened &nbsp;·&nbsp; {n_pass} passed &nbsp;·&nbsp;
          {n_flag} flagged &nbsp;·&nbsp; Sheet write failed: {sheet_error}
        </div>""", unsafe_allow_html=True)
    else:
        saved = "Saved to tracker ✓" if all_cv_rows else "Nothing to save"
        st.markdown(f"""
        <div class="status-ok">
          ✓ &nbsp; {n_screened} screened &nbsp;·&nbsp; {n_pass} passed &nbsp;·&nbsp;
          {n_flag} flagged &nbsp;·&nbsp; {saved}
        </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="metric-row">
      <div class="metric">
        <div class="metric-num" style="color:#2C1810;">{n_screened}</div>
        <div class="metric-lbl">Screened</div>
      </div>
      <div class="metric">
        <div class="metric-num" style="color:#2a7a2a;">{n_pass}</div>
        <div class="metric-lbl">Pass</div>
      </div>
      <div class="metric">
        <div class="metric-num" style="color:#c07000;">{n_flag}</div>
        <div class="metric-lbl">Flagged</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Clear button ──────────────────────────────────────────────────────────
    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    if st.button("Clear and screen more"):
        st.session_state.uploader_key += 1
        st.session_state.pop("run_done", None)
        st.rerun()

    # ── Processing errors only ─────────────────────────────────────────────────

    processing_errors = [e for e in errors if e["type"] in ("ocr", "timeout", "error")]

    if processing_errors:
        rows_html = "".join(
            f'<div class="error-row"><strong>{e["file"]}</strong> &nbsp;'
            f'<span style="color:#c03030;">{e["reason"]}</span></div>'
            for e in processing_errors
        )
        st.markdown(f"""
        <div class="error-card">
          <div class="error-title">
            ⚠ {len(processing_errors)} CV{'s' if len(processing_errors) != 1 else ''}
            could not be processed — re-upload to retry
          </div>
          {rows_html}
        </div>""", unsafe_allow_html=True)