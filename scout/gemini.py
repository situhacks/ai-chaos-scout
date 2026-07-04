"""Optional Gemini image generation for concept visuals.

Stdlib-only (urllib). Imported lazily by render_report.py so a missing key or
network failure never breaks rendering. Do NOT commit any API key.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

_GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash-exp:generateContent"
)


def generate_concept_visual(prompt: str, api_key: str) -> bytes | None:
    """Call Gemini to generate a concept image. Returns PNG bytes or None on failure."""
    if not api_key:
        return None

    url = f"{_GEMINI_ENDPOINT}?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE", "TEXT"],
            "temperature": 0.7,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return None

    # Extract inline image data from response
    try:
        for candidate in result.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                if "inlineData" in part:
                    import base64
                    return base64.b64decode(part["inlineData"]["data"])
    except (KeyError, TypeError, ValueError):
        pass

    return None
