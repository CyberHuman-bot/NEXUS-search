# NEXUS — Personal Search Engine

A web crawler + search engine you run locally. Crawl any website, index its content, then search it.

## Setup

```bash
pip install -r requirements.txt
python app.py
```

Then open **http://localhost:5000** in your browser.

## Usage

### Via the Web UI
1. Paste any URL into the top bar → click **INDEX SITE**
2. Wait for crawling to complete (watches domain links automatically)
3. Type in the search box → hit **SEARCH**

### Via Command Line (crawl only)
```bash
python crawler.py https://example.com https://another-site.com
```

## How It Works

```
Seed URL → crawler.py → fetches page → extracts text/links
         → follows links (same domain) → saves to search_index.json
         → app.py scores & ranks results by keyword frequency
```

### Scoring
- Title match: **10 pts** per hit
- Description match: **5 pts** per hit  
- Body text match: **1 pt** per hit

## Files
| File | Purpose |
|------|---------|
| `crawler.py` | Web scraper & indexer |
| `app.py` | Flask search server + UI |
| `search_index.json` | Your index (auto-created) |
| `requirements.txt` | Python deps |

## Tips
- Set `stay_on_domain=True` to only crawl one site (default)
- Set `stay_on_domain=False` to follow all links (careful — can be huge)
- `max_pages` limits how many pages per crawl (default: 30)
- The index is persistent — crawl multiple sites and they all merge