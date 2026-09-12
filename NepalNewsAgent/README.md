# Tinkering with Agentic AI.

Some useful commands.

### Run ollama
```code
ollama
```
### Install jupyterlab
```code
pip install jupyterlab
```
### Start jupyter
```code
jupyter lab
```

````markdown
# 🇳🇵 Nepali News Scraping Agent

A **local, zero-cloud, zero-API-key** pipeline that scrapes top Devanagari-Nepali news
headlines, generates an AI summary with a local LLM, and outputs a styled
hyperlinked HTML page.

Runs entirely on your machine. No API keys. No token costs. No data leaves
localhost.

---

## Architecture

```
┌──────────────┐      ┌──────────────┐      ┌─────────────────────┐
│  SCRAPER     │ ───► │  OLLAMA AI   │ ───► │  OUTPUT             │
│  (requests + │      │  (local LLM  │      │  • Styled HTML page  │
│   BeautifulSoup)│   │   on your    │      │  • JSON file         │
│              │      │   hardware)  │      │  • Inline notebook   │
└──────────────┘      └──────────────┘      └─────────────────────┘
  8 Nepali sites        Devanagari            hyperlinked titles
  HTTPS/HTTP/no-verify  3-tier fallback       grouped by source
  Devanagari filter     summary generation    dark theme + Devanagari font
  30+ char min length   retry × 3
```

### Stage 1 — Scraper

- Hits **8 Devanagari-Nepali sites** (`onlinekhabar`, `ekantipur`, `setopati`,
  `gorkhapatra`, `nepalnews`, `nagariknews`, and more).
- Each site has a **backup URL list** — if the primary domain's DNS is down,
  the next URL is tried automatically.
- `safe_get()` cascades through **HTTPS → HTTP → `verify=False`**, so
  certificate-mismatch sites still work.
- Strips `<nav>`, `<header>`, `<footer>`, `.sidebar`, `.menu`, `.ad`,
  `.related-posts`, and similar elements **before** scanning for articles.
- Targets real article containers (`<article>`, `.entry-title`, `.news-title`,
  `.post-title`, …) instead of grabbing every `<a>` tag.
- Every candidate title must pass **three gates**:
  - ≥ **30 characters** (eliminates short nav words like "राजनीति")
  - Contains at least one **Devanagari character** (U+0900 – U+097F)
  - Does **not** contain UI words ("लोगिन", "टिप्पणी", "फ्यासबुक", …)
- Global URL de-duplication across all sites.
- Picks the **top 50** headlines.

### Stage 2 — Ollama AI Summary

- Sends the 50 headlines to a **local LLM** (default: `llama3.2`; also works
  with `qwen2`, `mistral`, `phi3`, etc.).
- **3-tier prompt fallback**:
  1. Devanagari system prompt → Devanagari summary (ideal)
  2. Single English prompt asking for Devanagari output
  3. Plain English summary (last resort)
- Each tier retries up to **3×** with back-off.
- If all tiers fail, the HTML simply omits the summary block — the page
  still renders.

### Stage 3 — Output

- A self-contained **dark-themed HTML file** with:
  - Devanagari-friendly font (`Mukta` / `Noto Sans Devanagari`)
  - All UI labels in Nepali
  - Headlines grouped by source, numbered, hyperlinked (`target="_blank"`)
  - AI summary block (if successful)
  - Timestamp footer
- A **JSON file** with structured data (date, model, summary, all 50
  articles) — ready for downstream tools, APIs, or databases.
- Optional **inline preview** inside the notebook.

---

## How It Differs From a Typical Cloud Scraper

| Aspect          | This Pipeline                            | Typical Cloud Scraper         |
|-----------------|------------------------------------------|-------------------------------|
| **AI**          | Local via Ollama — no API key, no cost   | Sends to OpenAI / Anthropic   |
| **Privacy**     | Headlines never leave localhost          | Sent to a third-party server  |
| **Language**    | Devanagari-only filter + Devanagari AI   | Usually English-first         |
| **Resilience**  | URL fallbacks, SSL cascade, 3-tier AI    | Single request, fails on error|
| **Cost**        | $0 after `ollama pull`                   | Per-token API billing         |
| **Offline**     | Works fully offline once model is loaded | Requires internet for AI step |

---

## Prerequisites

```bash
# Python dependencies
pip install requests beautifulsoup4 lxml jupyter

# Ollama (https://ollama.com)
ollama serve
ollama pull llama3.2        # or: qwen2:7b, mistral, phi3
```

> **Best Devanagari-performing small model:** `qwen2:7b`
> (`ollama pull qwen2:7b`)

---

## Usage

1. Open the notebook: `jupyter notebook NepaliNewsScrapingAgent.ipynb`
2. Run cells top-to-bottom:
   - **Cell 1** – Imports & config
   - **Cell 2** – Verify Ollama is running
   - **Cell 3** – Ollama helper functions
   - **Cell 4** – Scrape all sites → collect top 50
   - **Cell 5** – AI summary via Ollama
   - **Cell 6** – Generate HTML + JSON
   - **Cell 7** – Inline preview
3. Open `nepali_news.html` in your browser.

---

## Project Structure

```
project/
├── NepaliNewsScrapingAgent.ipynb    # the notebook (all code)
├── nepali_news.html                 # generated HTML output
├── nepali_news.json                 # structured JSON output
├── .gitignore
└── .ipynb_checkpoints/              # gitignored
```

---

## Possible Extensions

- **Article body scraping** — fetch each headline's full text and send it to
  Ollama for a deeper summary.
- **Scheduling** — wrap the pipeline in a function and call it from a cron
  job, Task Scheduler, or a small FastAPI endpoint.
- **Database** — pipe the JSON into SQLite, Supabase, or Elasticsearch for
  historical tracking.
- **Translation** — add a second Ollama call: *"Translate these 50 headlines
  to English."*
- **Topic clustering** — feed the JSON into another Ollama call: *"Cluster
  these into politics, economy, sports, and summarize each cluster."*
- **JS-rendered sites** — swap `requests` for `playwright` on sites that load
  content via JavaScript (Next.js, Nuxt, etc.).

---

## Tech Stack

| Layer        | Tool                                  |
|--------------|---------------------------------------|
| Scraper      | Python `requests` + `BeautifulSoup`   |
| AI           | [Ollama](https://ollama.com) (local) |
| Model        | `llama3.2` / `qwen2:7b` / `mistral`  |
| Output       | HTML5 + CSS (Devanagari fonts)        |
| Notebook     | Jupyter                               |
| Runtime      | Any OS with Python 3.9+               |
````
