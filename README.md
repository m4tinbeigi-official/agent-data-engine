# agent-data-engine

Self-hosted, token-efficient, real-time structured data engine for AI agents.
An open, unlimited alternative to `agent-data.dev`.

Turns any website into a live, structured JSON API in seconds using LLM synthesis and residential/local fetching.

## Features

- **On-demand API Synthesis (`parse`)**: Give any URL and task description. The engine visits the page, inspects DOM/JSON structures, synthesizes a robust Python extractor, verifies it on live data, and saves the endpoint.
- **Direct Live Extraction (`call`)**: Pull structured JSON without sending raw HTML or taking screenshots. Saves 80%+ tokens for agent workflows.
- **Embedded Catalog**: SQLite + FTS5 full-text search for instantly discovering existing APIs.
- **Built-in Endpoints (21 Live Endpoints)**:
  - `digikala-mobile-phone-search`: Live product listings, prices (IRR), ratings, and links from Digikala.
  - `torob-product-search`: Price comparison across hundreds of Iranian online stores from Torob.
  - `divar-tehran-laptops`: Real-time classified ads, prices, condition, and locations from Divar.
  - `balad-ir-tehran-coffee-shops`: Real-world commercial venues, addresses, and phone numbers from Balad Map.
  - `mrbilit-train-availability`: Real-time intercity train schedules, class seats, and prices from MrBilit.
  - `nobitex-market-stats-rls`: Live Nobitex crypto prices in Rials (BTC, ETH, USDT latest, high, low, change).
  - `taline-ir-gold-rates`: Live 18K gold buy/sell rates in Tomans from Taline.
  - `milli-gold-18k-price`: Live 18K gold price from Milli Gold.
  - `tgju-market-rates`: Live US Dollar, Euro, Gold 18K, Bahar Azadi, and Emami coin rates from TGJU.
  - `selva-ir-domain-registration-price`: Live `.ir` domain registration fee from Selva.
  - `zoomit-top-tech-news`: Latest tech news headlines and links from Zoomit.
  - `mrhermes-ir-blog-posts`: Latest AI agent and tech engineering articles from MrHermes.
  - `binance-crypto-ticker-prices`: Live BTC, ETH, SOL ticker rates from Binance.
  - `wttr-in-tehran-weather`: Real-time weather data for Tehran (temp, feels like, humidity, wind).
  - `ipinfo-geolocation-details`: Public IP, ISP, ASN, and geo-coordinates.
  - `github-trending-repositories`: Daily trending open-source projects on GitHub.
  - `github-user-latest-repos`: Latest public repositories and update metrics for user.
  - `github-status-operational`: Live uptime and incident status of GitHub systems.
  - `arxiv-cs-ai-recent-papers`: Latest artificial intelligence research papers published on arXiv.
  - `lobsters-discussions`: Top community-voted tech articles and stories from Lobste.rs.
  - `hn-top-5-stories`: Top Hacker News posts with points and comment counts.


## Installation

```bash
git clone https://github.com/m4tinbeigi-official/agent-data-engine.git
cd agent-data-engine

# Link CLI to local bin
ln -sf $(pwd)/cli.py ~/.local/bin/agent-data-local
```

### Requirements
- Python 3.10+
- `httpx`
- `beautifulsoup4`

```bash
pip install httpx beautifulsoup4
```

## Configuration

Set your LLM router or OpenAI-compatible endpoint:

```bash
export ROUTER_URL="http://localhost:20128/v1"   # Or https://api.openai.com/v1
export ROUTER_KEY="your-api-key"
export ROUTER_MODEL="ag/gemini-3.8-flash-high" # Or gpt-4o / claude-3-5-sonnet
```

## Usage

### 1. Build a new API for any website
```bash
agent-data-local parse "https://news.ycombinator.com" -t "extract top 5 stories with title, url, points, author, and comments count"
```

### 2. Fetch structured live data
```bash
agent-data-local call hn-top-5-stories
```

### 3. List and Search registered APIs
```bash
agent-data-local list
agent-data-local search "crypto"
agent-data-local docs tgju-market-rates
```

## License
MIT
