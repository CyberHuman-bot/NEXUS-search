import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import json
import os
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

INDEX_FILE = "search_index.json"
index_lock = Lock()
robots_cache = {}
robots_lock = Lock()

BOT_NAME = "MiniSearchBot"

session = requests.Session()
session.headers.update({"User-Agent": f"Mozilla/5.0 (compatible; {BOT_NAME}/1.0)"})

def load_index():
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r") as f:
            return json.load(f)
    return {}

def save_index(index):
    with open(INDEX_FILE, "w") as f:
        json.dump(index, f, indent=2)

def clean_text(text):
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:5000]

def get_robots_parser(base_url):
    """Fetch and cache robots.txt for a domain."""
    parsed = urlparse(base_url)
    domain = f"{parsed.scheme}://{parsed.netloc}"

    with robots_lock:
        if domain in robots_cache:
            return robots_cache[domain]

    robots_url = f"{domain}/robots.txt"
    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except Exception:
        rp = None  # If robots.txt is unreachable, assume all allowed

    with robots_lock:
        robots_cache[domain] = rp

    return rp

def is_allowed(url):
    """Check if URL is allowed by robots.txt."""
    rp = get_robots_parser(url)
    if rp is None:
        return True
    return rp.can_fetch(BOT_NAME, url)

def get_page_data(url):
    try:
        if not is_allowed(url):
            print(f"  🚫 Blocked by robots.txt: {url}")
            return None, set()

        resp = session.get(url, timeout=8)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        title = (soup.title.string or soup.title.get_text() or url).strip() if soup.title else url
        description = ""

        # 1. Open Graph description (usually the most curated)
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            description = og_desc.get("content", "").strip()

        # 2. Standard meta description
        if not description:
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                description = meta_desc.get("content", "").strip()

        # 3. Twitter card description
        if not description:
            twitter_desc = soup.find("meta", attrs={"name": "twitter:description"})
            if twitter_desc:
                description = twitter_desc.get("content", "").strip()

        # 4. First substantial <p> tag on the page
        if not description:
            for p in soup.find_all("p"):
                text = p.get_text(separator=" ").strip()
                if len(text) > 80:
                    description = text[:400]
                    break

        # 5. Fallback: first 400 chars of body text
        if not description:
            description = body_text[:400]

        body_text = clean_text(soup.get_text(separator=" "))

        links = set()
        for a in soup.find_all("a", href=True):
            full = urljoin(url, a["href"])
            parsed = urlparse(full)
            if parsed.scheme in ("http", "https"):
                clean = parsed._replace(fragment="", query="").geturl()
                links.add(clean)

        return {
            "url": url,
            "title": title,
            "description": description,
            "content": body_text,
            "indexed_at": datetime.now().isoformat(),
        }, links

    except Exception as e:
        print(f"  ✗ Failed {url}: {e}")
        return None, set()

def crawl(seed_urls, max_pages=50, stay_on_domain=True, delay=0, workers=10):
    index = load_index()
    visited = set(index.keys())
    queue = list(dict.fromkeys(u for u in seed_urls if u not in visited))
    crawled = 0
    seed_domain = urlparse(seed_urls[0]).netloc if seed_urls else ""

    print(f"\n🕷  Crawling | max={max_pages} | threads={workers} | domain_only={stay_on_domain}\n")

    while queue and crawled < max_pages:
        batch_size = min(workers, max_pages - crawled, len(queue))
        batch = []
        for url in queue[:]:
            if url not in visited and len(batch) < batch_size:
                batch.append(url)
                queue.remove(url)
                visited.add(url)

        if not batch:
            break

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(get_page_data, url): url for url in batch}
            for future in as_completed(futures):
                url = futures[future]
                data, links = future.result()
                if data:
                    crawled += 1
                    print(f"[{crawled}] ✓ {data['title'][:70]}")
                    with index_lock:
                        index[url] = data
                        save_index(index)

                    for link in links:
                        if link not in visited and link not in queue:
                            if stay_on_domain:
                                if urlparse(link).netloc == seed_domain:
                                    queue.append(link)
                            else:
                                queue.append(link)

    print(f"\n✅ Done. {crawled} new pages. Total in index: {len(index)}")
    return index


if __name__ == "__main__":
    import sys
    urls = sys.argv[1:] if len(sys.argv) > 1 else ["https://example.com"]
    crawl(urls, max_pages=30, stay_on_domain=True, workers=10)