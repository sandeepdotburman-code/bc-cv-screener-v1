from sheets_writer import write_cv_pass_fail, write_round_0

test_cv = [{
    "Candidate": "Test Candidate",
    "Experience Band": "0 months (Fresher)",
    "Experience (Pass/Fail)": "✅",
    "Identity/Activity": "✅",
    "External-Facing": "✅",
    "CV Quality": "✅",
    "Excellence Signal": "—",
    "Decision": "PASS",
    "Reason": "",
    "Format": "PDF",
}]

test_r0 = [{
    "Name": "Test Candidate",
    "CV (Y/N)": "Y",
    "Experience (months + band)": "0 months (Fresher)",
    "Internship/Part-time": "6 months — content writing internship",
    "Current Role": "N/A",
    "Industry": "N/A",
    "Key Skills": "Coordination, follow-up",
    "Current Location": "Mumbai",
    "DOB": "N/A",
    "UG Grad Year": "2025",
    "PG Grad Year": "N/A",
    "Email": "test@example.com",
    "Phone": "N/A",
    "Summary": "Fresh graduate with internship coordination experience.",
    "Round 0 Pass/Fail": "PASS",
}]

print(write_cv_pass_fail(test_cv))
print(write_round_0(test_r0))