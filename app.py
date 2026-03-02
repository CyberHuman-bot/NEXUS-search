from flask import Flask, request, jsonify, render_template_string
import json, os, re
from crawler import crawl, INDEX_FILE, load_index

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NEXUS Search</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=Space+Mono:ital@0;1&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #080a0f;
    --surface: #0f1218;
    --border: #1e2433;
    --accent: #00e5ff;
    --accent2: #7c3aed;
    --text: #e2e8f0;
    --muted: #64748b;
    --success: #22d3ee;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Space Mono', monospace;
    min-height: 100vh;
    overflow-x: hidden;
  }

  /* Grid background */
  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
      linear-gradient(var(--border) 1px, transparent 1px),
      linear-gradient(90deg, var(--border) 1px, transparent 1px);
    background-size: 40px 40px;
    opacity: 0.4;
    pointer-events: none;
    z-index: 0;
  }

  .glow-orb {
    position: fixed;
    width: 600px; height: 600px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(0,229,255,0.07) 0%, transparent 70%);
    top: -200px; left: 50%;
    transform: translateX(-50%);
    pointer-events: none;
    z-index: 0;
  }

  .container {
    max-width: 860px;
    margin: 0 auto;
    padding: 0 24px;
    position: relative;
    z-index: 1;
  }

  header {
    padding: 60px 0 40px;
    text-align: center;
  }

  .logo {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: clamp(3rem, 8vw, 5.5rem);
    letter-spacing: -2px;
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent2) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1;
  }

  .tagline {
    color: var(--muted);
    font-size: 0.75rem;
    letter-spacing: 4px;
    text-transform: uppercase;
    margin-top: 8px;
  }

  .search-wrap {
    margin: 40px 0 16px;
    position: relative;
  }

  .search-box {
    display: flex;
    border: 1px solid var(--border);
    border-radius: 4px;
    background: var(--surface);
    overflow: hidden;
    transition: border-color 0.2s;
  }

  .search-box:focus-within {
    border-color: var(--accent);
    box-shadow: 0 0 0 2px rgba(0,229,255,0.1);
  }

  #query {
    flex: 1;
    background: none;
    border: none;
    outline: none;
    padding: 16px 20px;
    color: var(--text);
    font-family: 'Space Mono', monospace;
    font-size: 1rem;
  }

  #query::placeholder { color: var(--muted); }

  .btn {
    background: var(--accent);
    color: #000;
    border: none;
    padding: 16px 28px;
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 0.9rem;
    letter-spacing: 1px;
    cursor: pointer;
    text-transform: uppercase;
    transition: background 0.2s;
  }

  .btn:hover { background: #33eeff; }

  .btn-crawl {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--muted);
    font-size: 0.75rem;
    padding: 10px 18px;
    margin-left: 8px;
    border-radius: 4px;
    cursor: pointer;
    font-family: 'Space Mono', monospace;
    transition: all 0.2s;
  }
  .btn-crawl:hover { border-color: var(--accent); color: var(--accent); }

  .crawl-row {
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
  }

  #crawl-url {
    flex: 1;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 10px 14px;
    color: var(--text);
    font-family: 'Space Mono', monospace;
    font-size: 0.8rem;
    outline: none;
  }
  #crawl-url:focus { border-color: var(--accent2); }
  #crawl-url::placeholder { color: var(--muted); }

  .stats-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.7rem;
    color: var(--muted);
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 32px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border);
  }

  .dot {
    display: inline-block;
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--accent);
    margin-right: 6px;
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }

  /* Results */
  .result-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 20px 24px;
    margin-bottom: 12px;
    transition: border-color 0.2s, transform 0.2s;
    animation: fadeIn 0.3s ease forwards;
    opacity: 0;
  }

  .result-card:nth-child(1) { animation-delay: 0.05s; }
  .result-card:nth-child(2) { animation-delay: 0.1s; }
  .result-card:nth-child(3) { animation-delay: 0.15s; }
  .result-card:nth-child(4) { animation-delay: 0.2s; }
  .result-card:nth-child(5) { animation-delay: 0.25s; }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .result-card:hover {
    border-color: var(--accent);
    transform: translateX(4px);
  }

  .result-rank {
    font-size: 0.65rem;
    color: var(--accent);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 6px;
    font-family: 'Syne', sans-serif;
  }

  .result-title a {
    color: var(--text);
    text-decoration: none;
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 1.1rem;
    line-height: 1.3;
  }

  .result-title a:hover { color: var(--accent); }

  .result-url {
    color: var(--muted);
    font-size: 0.7rem;
    margin: 6px 0 8px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .result-snippet {
    color: #94a3b8;
    font-size: 0.8rem;
    line-height: 1.6;
  }

  .result-snippet mark {
    background: rgba(0,229,255,0.15);
    color: var(--accent);
    border-radius: 2px;
    padding: 0 2px;
  }

  .score-badge {
    float: right;
    font-size: 0.65rem;
    color: var(--muted);
    font-family: 'Space Mono', monospace;
  }

  .empty-state {
    text-align: center;
    padding: 80px 0;
    color: var(--muted);
  }

  .empty-state .icon { font-size: 3rem; margin-bottom: 16px; }

  .toggle-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
    margin-top: -4px;
  }

  .toggle-label {
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    user-select: none;
  }

  .toggle-label input[type="checkbox"] { display: none; }

  .toggle-track {
    position: relative;
    width: 40px;
    height: 22px;
    background: var(--border);
    border-radius: 99px;
    border: 1px solid var(--border);
    transition: background 0.2s, border-color 0.2s;
    flex-shrink: 0;
  }

  .toggle-thumb {
    position: absolute;
    top: 3px; left: 3px;
    width: 14px; height: 14px;
    border-radius: 50%;
    background: var(--muted);
    transition: transform 0.2s, background 0.2s;
  }

  .toggle-label input:checked ~ .toggle-track {
    background: rgba(0,229,255,0.15);
    border-color: var(--accent);
  }

  .toggle-label input:checked ~ .toggle-track .toggle-thumb {
    transform: translateX(18px);
    background: var(--accent);
  }

  .toggle-text {
    font-size: 0.75rem;
    color: var(--text);
    font-family: 'Space Mono', monospace;
    white-space: nowrap;
  }

  .toggle-hint {
    font-size: 0.7rem;
    color: var(--muted);
    font-style: italic;
  }
    background: rgba(0,229,255,0.05);
    border: 1px solid rgba(0,229,255,0.2);
    border-radius: 4px;
    padding: 12px 16px;
    font-size: 0.75rem;
    color: var(--success);
    margin-bottom: 16px;
    display: none;
  }
</style>
</head>
<body>
<div class="glow-orb"></div>
<div class="container">
  <header>
    <div class="logo">NEXUS</div>
    <div class="tagline">Personal Search Engine</div>
  </header>

  <div id="status-msg" class="status-msg"></div>

  <!-- Crawl a new URL -->
  <div class="crawl-row">
    <input id="crawl-url" type="text" placeholder="https://example.com — crawl & index a website">
    <button class="btn-crawl" id="btn-crawl">⬢ INDEX SITE</button>
  </div>
  <div class="toggle-row">
    <label class="toggle-label">
      <input type="checkbox" id="toggle-domain" checked>
      <span class="toggle-track">
        <span class="toggle-thumb"></span>
      </span>
      <span class="toggle-text" id="toggle-text">Only this site</span>
    </label>
    <span class="toggle-hint" id="toggle-hint">Crawls pages within the same domain only</span>
  </div>

  <!-- Search -->
  <div class="search-wrap">
    <div class="search-box">
      <input id="query" type="text" placeholder="Search your indexed web..." autofocus>
      <button class="btn" id="btn-search">SEARCH</button>
    </div>
  </div>

  <div class="stats-bar">
    <span><span class="dot"></span><span id="index-count">0</span> pages indexed</span>
    <span id="result-count"></span>
  </div>

  <div id="results"></div>
</div>

<script>
async function loadStats() {
  const r = await fetch('/api/stats');
  const d = await r.json();
  document.getElementById('index-count').textContent = d.count;
}

function highlight(text, query) {
  if (!query) return text;
  const words = query.trim().split(/\s+/).filter(Boolean);
  let result = text;
  words.forEach(w => {
    const re = new RegExp('(' + w.replace(/[.*+?^${}()|[\]\\\/]/g,'\\$&') + ')', 'gi');
    result = result.replace(re, '<mark>$1</mark>');
  });
  return result;
}

async function doSearch() {
  const q = document.getElementById('query').value.trim();
  if (!q) return;
  const r = await fetch('/api/search?q=' + encodeURIComponent(q));
  const data = await r.json();
  renderResults(data.results, q, data.total);
}

function renderResults(results, q, total) {
  const container = document.getElementById('results');
  document.getElementById('result-count').textContent =
    total ? `${total} result${total !== 1 ? 's' : ''}` : '';

  if (!results.length) {
    container.innerHTML = `<div class="empty-state">
      <div class="icon">◈</div>
      <div>No results found for <strong>"${q}"</strong></div>
      <div style="margin-top:8px;font-size:0.75rem;">Try crawling more sites or different keywords.</div>
    </div>`;
    return;
  }

  container.innerHTML = results.map((r, i) => `
    <div class="result-card">
      <div class="result-rank">
        #${i+1}
        <span class="score-badge">score: ${r.score}</span>
      </div>
      <div class="result-title"><a href="${r.url}" target="_blank">${highlight(r.title, q)}</a></div>
      <div class="result-url">${r.url}</div>
      <div class="result-snippet">${highlight(r.snippet, q)}</div>
    </div>
  `).join('');
}

// Toggle label update
const toggleDomain = document.getElementById('toggle-domain');
const toggleText   = document.getElementById('toggle-text');
const toggleHint   = document.getElementById('toggle-hint');

toggleDomain.addEventListener('change', function() {
  if (this.checked) {
    toggleText.textContent = 'Only this site';
    toggleHint.textContent = 'Crawls pages within the same domain only';
  } else {
    toggleText.textContent = 'With its mentioned hyperlinks';
    toggleHint.textContent = 'Follows external links too — can index many more pages';
  }
});

async function startCrawl() {
  const url = document.getElementById('crawl-url').value.trim();
  if (!url) return;
  const stayOnDomain = document.getElementById('toggle-domain').checked;
  const msg = document.getElementById('status-msg');
  msg.style.display = 'block';
  msg.textContent = '⬢ Crawling ' + url + (stayOnDomain ? ' (same domain)' : ' (following all links)') + ' — this may take a moment...';

  try {
    const r = await fetch('/api/crawl', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({url, max_pages: 30, stay_on_domain: stayOnDomain})
    });
    const d = await r.json();
    msg.textContent = `✓ Done! Indexed ${d.new_pages} new pages. Total: ${d.total} pages.`;
    loadStats();
  } catch(e) {
    msg.textContent = '✗ Crawl failed: ' + e.message;
  }
}

document.getElementById('btn-search').addEventListener('click', doSearch);
document.getElementById('btn-crawl').addEventListener('click', startCrawl);
document.getElementById('query').addEventListener('keydown', function(e) {
  if (e.key === 'Enter') doSearch();
});

loadStats();

// Show indexed pages on load
fetch('/api/search?q=').then(r => r.json()).then(d => {
  if (d.results && d.results.length) renderResults(d.results, '', d.total);
});
</script>
</body>
</html>
"""

def score_result(data, query_terms):
    score = 0
    title = data.get("title", "").lower()
    desc = data.get("description", "").lower()
    content = data.get("content", "").lower()
    for term in query_terms:
        score += title.count(term) * 10
        score += desc.count(term) * 5
        score += content.count(term) * 1
    return score

def get_snippet(content, query_terms, length=200):
    content_lower = content.lower()
    best_pos = 0
    for term in query_terms:
        pos = content_lower.find(term)
        if pos != -1:
            best_pos = max(0, pos - 60)
            break
    snippet = content[best_pos:best_pos + length]
    if best_pos > 0:
        snippet = "…" + snippet
    if best_pos + length < len(content):
        snippet += "…"
    return snippet

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/stats")
def stats():
    idx = load_index()
    return jsonify({"count": len(idx)})

@app.route("/api/search")
def search():
    q = request.args.get("q", "").strip().lower()
    idx = load_index()

    if not q:
        # Return latest indexed pages
        results = []
        for url, data in list(idx.items())[:10]:
            results.append({
                "url": url,
                "title": data.get("title", url),
                "snippet": data.get("description") or data.get("content", "")[:200],
                "score": "-"
            })
        return jsonify({"results": results, "total": len(results)})

    query_terms = q.split()
    scored = []
    for url, data in idx.items():
        s = score_result(data, query_terms)
        if s > 0:
            scored.append((s, url, data))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for s, url, data in scored[:20]:
        results.append({
            "url": url,
            "title": data.get("title", url),
            "snippet": get_snippet(data.get("content", ""), query_terms),
            "score": s
        })

    return jsonify({"results": results, "total": len(results)})

@app.route("/api/crawl", methods=["POST"])
def api_crawl():
    body = request.get_json()
    url = body.get("url", "").strip()
    max_pages = int(body.get("max_pages", 30))
    stay_on_domain = body.get("stay_on_domain", True)
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    old_count = len(load_index())
    crawl([url], max_pages=max_pages, stay_on_domain=stay_on_domain, workers=10)
    new_count = len(load_index())

    return jsonify({"new_pages": new_count - old_count, "total": new_count})

if __name__ == "__main__":
    print("\n🔍 NEXUS Search Engine")
    print("   Open http://localhost:5000 in your browser\n")
    app.run(host="0.0.0.0, port=5000)
