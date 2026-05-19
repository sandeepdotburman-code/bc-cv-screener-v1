# screener.py
# Loads the rubric, sends CV text to Claude, returns structured screening result.
# Called by app.py — one CV at a time.

import anthropic
import yaml
import json
import os

# ── Load rubric ───────────────────────────────────────────────────────────────

def load_rubric(role: str) -> dict:
    """Load the YAML rubric file for the given role."""
    rubric_path = os.path.join('rubrics', f'{role}.yaml')
    with open(rubric_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def rubric_to_prompt(rubric: dict) -> str:
    """
    Convert the YAML rubric dict to a plain English system prompt for Claude.
    We dump the full YAML as text — Claude reads YAML natively and accurately.
    """
    return yaml.dump(rubric, allow_unicode=True, default_flow_style=False)

# ── Screen a single CV ────────────────────────────────────────────────────────

def screen_cv(cv_text: str, filename: str, screening_date: str, role: str, api_key: str) -> dict:
    """
    Send CV text to Claude with the rubric as system prompt.
    Returns a structured dict with screening results.

    Args:
        cv_text: extracted text from the CV
        filename: original filename (used in reason strings)
        screening_date: e.g. 'May 2026'
        role: rubric file name without extension e.g. 'production_coordinator'
        api_key: Anthropic API key from secrets

    Returns dict with keys:
        candidate, cv_format, experience_band, experience_pf,
        identity_activity, external_facing, cv_quality,
        excellence_signal, decision, reason, raw_response
    """

    rubric = load_rubric(role)
    system_prompt = rubric_to_prompt(rubric)

    client = anthropic.Anthropic(api_key=api_key)

    user_message = f"""Screening Date: {screening_date}

Filename: {filename}

CV TEXT:
{cv_text}

---

Screen this CV against the rubric. Return ONLY a JSON object with exactly these keys — no preamble, no explanation, no markdown:

{{
  "candidate": "full name from CV",
  "experience_band": "band string per rubric rules",
  "experience_pf": "✅ or ❌ or N/A",
  "identity_activity": "✅ or ❌ or blank",
  "external_facing": "✅ or ❌ or blank",
  "cv_quality": "✅ or ❌ or blank",
  "excellence_signal": "⭐ or —",
  "decision": "PASS or FAIL or FLAG",
  "reason": "one line only for FLAG and non-obvious FAIL, blank otherwise",
  "current_role": "current job title and company, or N/A if not found",
  "industry": "industry or sector, or N/A if not found",
  "key_skills": "comma-separated list of key skills, or N/A if not found",
  "current_location": "city and country, or N/A if not found",
  "dob": "date of birth as DD/MM/YYYY or YYYY, or N/A if not found",
  "ug_grad_year": "undergraduate graduation year as YYYY, or N/A if not found",
  "pg_grad_year": "postgraduate graduation year as YYYY, or N/A if not found",
  "email": "email address, or N/A if not found",
  "phone": "phone number, or N/A if not found",
  "internship_part_time": "yes/no and brief description if mentioned, or N/A if not found",
  "summary": "2-3 sentence professional summary of the candidate"
}}"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": user_message}
            ],
            system=system_prompt
        )

        raw = message.content[0].text.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        result = json.loads(raw)
        result['raw_response'] = raw
        return result

    except json.JSONDecodeError as e:
        return {
            'candidate': filename,
            'experience_band': 'Parse error',
            'experience_pf': '',
            'identity_activity': '',
            'external_facing': '',
            'cv_quality': '',
            'excellence_signal': '',
            'decision': 'FLAG',
            'reason': f'Claude response could not be parsed — {str(e)}. Navdeep to review manually.',
            'current_role': '',
            'industry': '',
            'key_skills': '',
            'current_location': '',
            'dob': '',
            'ug_grad_year': '',
            'pg_grad_year': '',
            'email': '',
            'phone': '',
            'internship_part_time': '',
            'summary': '',
            'raw_response': raw if 'raw' in dir() else ''
        }

    except Exception as e:
        return {
            'candidate': filename,
            'experience_band': 'API error',
            'experience_pf': '',
            'identity_activity': '',
            'external_facing': '',
            'cv_quality': '',
            'excellence_signal': '',
            'decision': 'FLAG',
            'reason': f'API call failed — {str(e)}. Navdeep to review manually.',
            'current_role': '',
            'industry': '',
            'key_skills': '',
            'current_location': '',
            'dob': '',
            'ug_grad_year': '',
            'pg_grad_year': '',
            'email': '',
            'phone': '',
            'internship_part_time': '',
            'summary': '',
            'raw_response': ''
        }