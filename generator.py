import urllib.request
import json
import re
from typing import Dict, Any

import os
from pathlib import Path

DEFAULT_MODEL = os.getenv("ROUTER_MODEL", "ag/gemini-3.8-flash-high")

def get_router_credentials():
    base_url = os.getenv("ROUTER_URL") or os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("ROUTER_KEY") or os.getenv("OPENAI_API_KEY")
    
    # Auto-detect from local hermes config if not set in env
    if not api_key:
        hermes_cfg = Path.home() / ".hermes" / "config.yaml"
        if hermes_cfg.exists():
            try:
                for line in hermes_cfg.read_text().splitlines():
                    line_s = line.strip()
                    if line_s.startswith("api_key:") and not api_key:
                        api_key = line_s.split(":", 1)[1].strip()
                    if line_s.startswith("base_url:") and not base_url:
                        base_url = line_s.split(":", 1)[1].strip()
            except Exception:
                pass
                
    base_url = base_url or "http://localhost:20128/v1"
    if not base_url.endswith("/chat/completions"):
        base_url = base_url.rstrip("/") + "/chat/completions"
    return base_url, (api_key or "")


SYSTEM_PROMPT = """You are an expert web data scraper and API engineer.
Given a webpage's HTML/embedded JSON and an extraction task, write a robust, self-contained Python extraction function.

Return ONLY a valid JSON object with EXACTLY this structure:
{
  "slug": "unique-kebab-case-slug",
  "name": "Human-friendly Title",
  "category": "finance|social|shopping|news|business|other",
  "tags": ["tag1", "tag2"],
  "schema": {
    "field1": "type description",
    "field2": "type description"
  },
  "python_code": "def extract(html: str, base_url: str = '') -> dict:\\n    # python code here"
}

RULES for python_code:
1. Must define EXACTLY `def extract(html: str, base_url: str = "") -> dict:`
2. Can use `from bs4 import BeautifulSoup`, `import json`, `import re`, `import urllib.parse` inside the function.
3. Must handle missing fields gracefully without crashing (e.g. use `.get()` or `if elem:`).
4. Return a clean dict with the requested structured data.
5. Do NOT include markdown backticks outside the json. Return pure JSON.
"""

def generate_scraper(url: str, task: str, cleaned_html: str, model: str = DEFAULT_MODEL) -> Dict[str, Any]:
    user_prompt = f"""Target URL: {url}
Requested Task: {task}

Page content:
{cleaned_html}
"""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "stream": False
    }

    router_url, router_key = get_router_credentials()
    headers = {"Content-Type": "application/json"}
    if router_key:
        headers["Authorization"] = f"Bearer {router_key}"

    req = urllib.request.Request(
        router_url,
        headers=headers,
        data=json.dumps(payload).encode()
    )

    with urllib.request.urlopen(req, timeout=45) as resp:
        res_data = json.loads(resp.read().decode())
        content = res_data["choices"][0]["message"]["content"].strip()

    # Clean markdown codeblocks if model wrapped in ```json
    if content.startswith("```"):
        content = re.sub(r"^```[a-zA-Z]*\n?", "", content)
        content = re.sub(r"\n?```$", "", content).strip()

    parsed = json.loads(content)
    return parsed
