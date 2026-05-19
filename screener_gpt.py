# screener_gpt.py
# Loads the rubric, sends CV text to GPT, returns structured screening result.
# Identical dict structure to screener.py — drop-in parallel screener.

import yaml
import json
import os
from openai import OpenAI

# ── Load rubric ───────────────────────────────────────────────────────────────

def load_rubric(role: str) -> dict:
    """Load the YAML rubric file for the given role."""
    rubric_path = os.path.join('rubrics', f'{role}.yaml')
    with open(rubric_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def rubric_to_prompt(rubric: dict) -> str:
    """Convert the YAML rubric dict to a plain text system prompt."""
    return yaml.dump(rubric, allow_unicode=True, default_flow_style=False)

# ── Screen a single CV ────────────────────────────────────────────────────────

def screen_cv_gpt(cv_text: str, filename: str, screening_date: str, role: str, api_key: str) -> dict:
    """
    Send CV text to GPT with the rubric as system prompt.
    Returns a structured dict with identical keys to screener.py.

    Args:
        cv_text: extracted text from the CV
        filename: original filename (used in reason strings)
        screening_date: e.g. 'May 2026'
        role: rubric file name without extension e.g. 'production_coordinator'
        api_key: OpenAI API key from secrets

    Returns dict with keys:
        candidate, cv_format, experience_band, experience_pf,
        identity_activity, external_facing, cv_quality,
        excellence_signal, decision, reason,
        current_role, industry, key_skills, current_location,
        dob, ug_grad_year, pg_grad_year, email, phone,
        internship_part_time, summary
    """

    rubric = load_rubric(role)
    system_prompt = rubric_to_prompt(rubric)

    client = OpenAI(api_key=api_key)

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
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=2000,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content.strip()
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
            'reason': f'GPT response could not be parsed — {str(e)}. Navdeep to review manually.',
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
            'reason': f'GPT API call failed — {str(e)}. Navdeep to review manually.',
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