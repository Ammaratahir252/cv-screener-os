"""Talk to the AI service. Answers are saved in the cache folder so the same CV
always gives the same result, and reviewers can re-run everything without an API key."""
import hashlib
import json
import os
import re
import time
from pathlib import Path

import requests

ENDPOINTS = {
    "groq": ("https://api.groq.com/openai/v1/chat/completions", "GROQ_API_KEY"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", "GEMINI_API_KEY"),
    "openai": ("https://api.openai.com/v1/chat/completions", "OPENAI_API_KEY"),
}


class AIError(Exception):
    """An error with a message written for a non-developer.
    fatal=True means every other CV would fail the same way, so the run stops."""
    def __init__(self, message, fatal=False, kind="error"):
        super().__init__(message)
        self.fatal = fatal
        self.kind = kind  # "quota" = allowance used up; "skipped" = not asked because of that


def _wait_text(seconds):
    if seconds >= 3600:
        return f"about {round(seconds / 3600)} hour(s)"
    if seconds >= 60:
        return f"about {round(seconds / 60)} minute(s)"
    return f"{int(seconds)} seconds"


def _quota_used_up(resp):
    """True when the 429 is a daily allowance / quota, not a short per-minute limit."""
    try:
        msg = json.dumps(resp.json()).lower()
    except ValueError:
        msg = ""
    try:
        wait = float(resp.headers.get("retry-after", 0))
    except ValueError:
        wait = 0
    daily = any(w in msg for w in ("per day", "tpd", "rpd", "quota", "insufficient_quota",
                                    "resource_exhausted", "billing"))
    if not wait:
        m = re.search(r"try again in (?:(\d+)h)?(?:(\d+)m)?([\d.]+)s", msg)
        if m:
            h, mi, sec = (float(x) if x else 0 for x in m.groups())
            wait = h * 3600 + mi * 60 + sec
    return daily or wait > 60, wait


def ask_json(provider, model, system, user, cache_dir: Path, use_cache=True, offline=False):
    """offline=True: only use saved answers (used after the AI allowance has run out)."""
    if provider not in ENDPOINTS:
        raise AIError(f"Unknown provider '{provider}' in settings.yaml. Use groq, gemini or openai.", fatal=True)
    url, key_name = ENDPOINTS[provider]
    cache_key = hashlib.sha256(json.dumps([provider, model, system, user]).encode()).hexdigest()[:24]
    cache_file = cache_dir / f"{cache_key}.json"

    if use_cache and cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    if offline:
        raise AIError("Not checked: the AI allowance ran out earlier in this run. Check it again later.",
                      kind="skipped")
    api_key = os.environ.get(key_name, "").strip()
    if not api_key:
        raise AIError(f"No API key found. Open the .env file and paste your key after {key_name}= "
                      "(see README, 'First time only', step 4).", fatal=True)
    for attempt in range(4):
        try:
            resp = requests.post(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": model, "temperature": 0,
                      "response_format": {"type": "json_object"},
                      "messages": [{"role": "system", "content": system},
                                   {"role": "user", "content": user}]},
                timeout=60,
            )
        except requests.RequestException:
            raise AIError("Could not reach the AI service. Check your internet connection and try again.")
        if resp.status_code != 429 or attempt == 3:
            break
        used_up, wait_s = _quota_used_up(resp)
        if used_up:
            when = f"Try again in {_wait_text(wait_s)}" if wait_s else "Try again later (usually tomorrow)"
            raise AIError(f"The free AI allowance is used up for now. {when}. CVs already checked are saved "
                          "and will not be asked again. Or use another AI service (see README).",
                          fatal=True, kind="quota")
        # Free plans allow only a few requests per minute: wait and try again automatically.
        try:
            wait = min(float(resp.headers.get("retry-after", 10)), 30)
        except ValueError:
            wait = 10
        print(f"    (AI service busy, waiting {wait:.0f} s and trying again...)")
        time.sleep(wait + 1)
    if resp.status_code == 402:
        raise AIError("The AI account has no credit left. Add credit or use a free key (see README).",
                      fatal=True, kind="quota")
    if resp.status_code in (401, 403):
        raise AIError("The AI service rejected the API key. Check the key in your .env file.", fatal=True)
    if resp.status_code == 429:
        raise AIError("The AI service is still busy after 4 tries. Wait one minute and run again.")
    if resp.status_code in (400, 404):
        try:
            detail = resp.json().get("error", {}).get("message", "")[:200]
        except ValueError:
            detail = ""
        if resp.status_code == 404 or "model" in detail.lower():
            raise AIError(f"The AI service does not know the model '{model}'. It may have been retired. "
                          f"Put a current model name in settings.yaml (see the provider's model list). "
                          f"Service said: {detail}", fatal=True)
        raise AIError(f"The AI service refused the request ({resp.status_code}): {detail}")
    if resp.status_code >= 400:
        raise AIError(f"The AI service returned an error ({resp.status_code}). Try again in a few minutes.")
    try:
        content = resp.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
    except (KeyError, ValueError, IndexError):
        raise AIError("The AI gave an answer in the wrong format. Run again; if it repeats, mark this CV for manual review.")

    cache_dir.mkdir(exist_ok=True)
    cache_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return data
