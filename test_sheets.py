from sheets_writer import write_cv_pass_fail, write_round_0

test_cv = [{
    "Candidate":              "Test Candidate",
    "Experience Band":        "0 months (Fresher)",
    "Experience (Pass/Fail)": "✅",
    "Identity/Activity":      "✅",
    "External-Facing":        "✅",
    "CV Quality":             "✅",
    "Excellence Signal":      "—",
    "Decision":               "PASS",
    "Reason":                 "",
    "Format":                 "PDF",
}]

test_r0 = [{
    "candidate":            "Test Candidate",
    "experience_band":      "0 months (Fresher)",
    "internship_part_time": "6 months — content writing internship",
    "current_role":         "N/A",
    "industry":             "N/A",
    "key_skills":           "Coordination, follow-up",
    "current_location":     "Mumbai",
    "dob":                  "N/A",
    "ug_grad_year":         "2025",
    "pg_grad_year":         "N/A",
    "email":                "test@example.com",
    "phone":                "N/A",
    "summary":              "Fresh graduate with internship coordination experience.",
    "decision":             "PASS",
}]

print("CV Pass-Fail:", write_cv_pass_fail(test_cv))
print("Round 0:     ", write_round_0(test_r0))
