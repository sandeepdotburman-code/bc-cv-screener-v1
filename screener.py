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
  "reason": "one line only for FLAG and non-obvious FAIL, blank otherwise"
}}"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
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
            'raw_response': ''
        }