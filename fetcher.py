import httpx
from bs4 import BeautifulSoup
import re
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,fa;q=0.8",
    "Cache-Control": "no-cache",
}

def fetch_url(url: str, timeout: float = 15.0) -> str:
    # verify=False is strictly used for read-only public web data extraction across Iranian domestic CAs
    try:
        with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=timeout, verify=False) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.text
    except Exception as e:
        # Fallback to local SOCKS5 proxy if direct fails
        try:
            with httpx.Client(headers=HEADERS, proxy="socks5://127.0.0.1:10808", follow_redirects=True, timeout=timeout, verify=False) as client:
                resp = client.get(url)
                resp.raise_for_status()
                return resp.text
        except Exception:
            raise e

def clean_html_for_llm(html: str, max_chars: int = 40000) -> str:
    soup = BeautifulSoup(html, "html.parser")
    
    # Extract embedded JSON data first if present (Next.js, Nuxt, ld+json)
    embedded_data = []
    for tag in soup.find_all("script"):
        t_type = tag.get("type", "")
        t_id = tag.get("id", "")
        if t_type == "application/ld+json" or t_id in ("__NEXT_DATA__", "__NUXT_DATA__"):
            if tag.string:
                embedded_data.append(tag.string.strip())
        tag.decompose()

    for tag in soup(["style", "svg", "noscript", "iframe"]):
        tag.decompose()

    # Prepend embedded data if found
    prefix = ""
    if embedded_data:
        prefix = "=== EMBEDDED JSON DATA ON PAGE ===\n" + "\n---\n".join(embedded_data[:3]) + "\n\n=== CLEANED HTML ===\n"

    # Simplify HTML
    body = soup.body or soup
    body_text = str(body)
    # Collapse multiple whitespaces and newlines
    body_text = re.sub(r"\n\s*\n+", "\n", body_text)
    body_text = re.sub(r"[ \t]+", " ", body_text)

    combined = prefix + body_text
    if len(combined) > max_chars:
        return combined[:max_chars] + "\n...[TRUNCATED FOR LENGTH]..."
    return combined
