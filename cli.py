#!/usr/bin/env python3
import sys
import argparse
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from db import init_db, save_endpoint, get_endpoint, list_endpoints, search_endpoints
from fetcher import fetch_url, clean_html_for_llm
from generator import generate_scraper
from executor import execute_scraper

def cmd_list(args):
    eps = list_endpoints()
    if not eps:
        print(json.dumps({"listings": [], "total": 0}, indent=2))
        return
    out = {
        "listings": [
            {
                "slug": e["slug"],
                "name": e["name"],
                "url": e["url"],
                "category": e["category"],
                "tags": [t for t in e["tags"].split(",") if t],
                "task": e["task"]
            }
            for e in eps
        ],
        "total": len(eps)
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))

def cmd_search(args):
    eps = search_endpoints(args.query)
    out = {
        "query": args.query,
        "listings": [
            {
                "slug": e["slug"],
                "name": e["name"],
                "url": e["url"],
                "category": e["category"],
                "tags": [t for t in e["tags"].split(",") if t],
                "task": e["task"]
            }
            for e in eps
        ],
        "total": len(eps)
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))

def cmd_docs(args):
    ep = get_endpoint(args.slug)
    if not ep:
        print(json.dumps({"error": f"Endpoint '{args.slug}' not found."}, indent=2), file=sys.stderr)
        sys.exit(1)
    
    docs = {
        "slug": ep["slug"],
        "name": ep["name"],
        "url": ep["url"],
        "task": ep["task"],
        "category": ep["category"],
        "tags": [t for t in ep["tags"].split(",") if t],
        "schema": ep["schema"],
        "sample_output": ep["sample_output"],
        "example_cli": f"agent-data-local call {ep['slug']}"
    }
    print(json.dumps(docs, ensure_ascii=False, indent=2))

def cmd_parse(args):
    url = args.url
    task = args.task
    print(f"[*] Fetching live content from: {url}", file=sys.stderr)
    try:
        raw_html = fetch_url(url)
    except Exception as e:
        print(json.dumps({"error": f"Failed to fetch {url}: {e}"}, indent=2), file=sys.stderr)
        sys.exit(1)

    print(f"[*] Analyzing content ({len(raw_html)} bytes)...", file=sys.stderr)
    cleaned = clean_html_for_llm(raw_html)

    print(f"[*] Synthesizing scraper code via 9Router LLM...", file=sys.stderr)
    try:
        spec = generate_scraper(url, task, cleaned)
    except Exception as e:
        print(json.dumps({"error": f"LLM generation failed: {e}"}, indent=2), file=sys.stderr)
        sys.exit(1)

    slug = spec.get("slug")
    name = spec.get("name", slug)
    category = spec.get("category", "general")
    tags = spec.get("tags", [])
    schema = spec.get("schema", {})
    code = spec.get("python_code", "")

    print(f"[*] Testing synthesized scraper on live data...", file=sys.stderr)
    try:
        sample_output = execute_scraper(code, raw_html, base_url=url)
    except Exception as e:
        print(json.dumps({"error": f"Scraper verification failed: {e}"}, indent=2), file=sys.stderr)
        sys.exit(1)

    save_endpoint(
        slug=slug,
        name=name,
        url=url,
        task=task,
        category=category,
        tags=tags,
        scraper_code=code,
        schema=schema,
        sample_output=sample_output
    )

    print(f"[✓] Endpoint successfully verified and registered: {slug}", file=sys.stderr)
    result = {
        "status": "success",
        "slug": slug,
        "name": name,
        "category": category,
        "schema": schema,
        "sample_output": sample_output,
        "example_cli": f"agent-data-local call {slug}"
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

def cmd_call(args):
    ep = get_endpoint(args.slug)
    if not ep:
        print(json.dumps({"error": f"Endpoint '{args.slug}' not found."}, indent=2), file=sys.stderr)
        sys.exit(1)

    target_url = args.url if args.url else ep["url"]
    try:
        raw_html = fetch_url(target_url)
    except Exception as e:
        print(json.dumps({"error": f"Failed to fetch {target_url}: {e}"}, indent=2), file=sys.stderr)
        sys.exit(1)

    try:
        data = execute_scraper(ep["scraper_code"], raw_html, base_url=target_url)
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"error": f"Extraction failed: {e}"}, indent=2), file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Local Agent Data Engine - Self-hosted real-time structured data for AI agents")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = subparsers.add_parser("list", help="List all registered catalog endpoints")
    p_list.set_defaults(func=cmd_list)

    # search
    p_search = subparsers.add_parser("search", help="Search endpoints catalog")
    p_search.add_argument("query", help="Search query")
    p_search.set_defaults(func=cmd_search)

    # docs
    p_docs = subparsers.add_parser("docs", help="Get schema and docs for an endpoint")
    p_docs.add_argument("slug", help="Endpoint slug")
    p_docs.set_defaults(func=cmd_docs)

    # parse
    p_parse = subparsers.add_parser("parse", help="Build a structured API endpoint for a URL")
    p_parse.add_argument("url", help="Target site URL")
    p_parse.add_argument("-t", "--task", required=True, help="Description of data fields to extract")
    p_parse.set_defaults(func=cmd_parse)

    # call
    p_call = subparsers.add_parser("call", help="Fetch live structured data from an endpoint")
    p_call.add_argument("slug", help="Endpoint slug")
    p_call.add_argument("--url", help="Override target URL")
    p_call.set_defaults(func=cmd_call)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
