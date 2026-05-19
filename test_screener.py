"""
test_screener.py — end-to-end test: extract text from a real CV, run screen_cv,
print every field so we can verify the new extraction keys are populated.
"""

import tomllib
import os
from extractor import extract_text
from screener_claude import screen_cv

# ── Load API key from secrets.toml ─────────────────────────────────────────────
secrets_path = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")
with open(secrets_path, "rb") as f:
    secrets = tomllib.load(f)
api_key = secrets["ANTHROPIC_API_KEY"]

# ── Pick a test CV ─────────────────────────────────────────────────────────────
cv_path = os.path.join(os.path.dirname(__file__), "Test CVs", "ANUSHREE DAS.pdf")
cv_name = os.path.basename(cv_path)

print(f"Extracting text from: {cv_name}")
extract_result = extract_text(cv_path)
print(f"Extraction status   : {extract_result['status']}")

if extract_result["status"] != "ok":
    print(f"Extraction failed   : {extract_result['reason']}")
    raise SystemExit(1)

cv_text = extract_result["text"]
print(f"Text length         : {len(cv_text)} chars\n")

# ── Screen ─────────────────────────────────────────────────────────────────────
print("Calling Claude...")
result = screen_cv(
    cv_text=cv_text,
    filename=cv_name,
    screening_date="May 2026",
    role="production_coordinator",
    api_key=api_key,
)

# ── Print results ──────────────────────────────────────────────────────────────
FIELDS = [
    "candidate", "experience_band", "experience_pf",
    "identity_activity", "external_facing", "cv_quality",
    "excellence_signal", "decision", "reason",
    "current_role", "industry", "key_skills", "current_location",
    "dob", "ug_grad_year", "pg_grad_year",
    "email", "phone", "internship_part_time", "summary",
]

print("\n── Screening result ──────────────────────────────────────────────────────")
for field in FIELDS:
    val = result.get(field, "<MISSING>")
    print(f"  {field:<22} : {val}")

missing = [f for f in FIELDS if f not in result]
if missing:
    print(f"\n  MISSING KEYS: {missing}")
else:
    print("\n  All expected keys present.")
