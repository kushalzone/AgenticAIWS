# PackBot Pro

AI-powered travel packing strategist. Describe your trip, get a
category-by-category packing list tuned to destination, duration, season,
luggage type, and personal context — generated entirely on your own
machine by a local LLM via Ollama.

## Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Notebook Layout](#notebook-layout)
- [Web UI](#web-ui)
- [API Reference](#api-reference)
- [Data Model](#data-model)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Project Files](#project-files)

## Architecture

```
JUPYTER NOTEBOOK (single Python kernel)
  Cell 1  SYSTEM_PROMPT
  Cell 2  imports + storage helpers
  Cell 3  HTML_PAGE
  Cell 4  Flask app + routes
  Cell 5  app.run() in a Thread + open browser
           |
           |  app.run() in a background thread
           v
+---------+  HTTP  +-------------+  ollama.chat()  +------------+
|BROWSER  |------->| FLASK       |---------------->| OLLAMA     |
|:5000    |<-------| SERVER:5000 |<----------------| llama3.1:8b|
+---------+  JSON  +------+------+                  | :11434     |
                       |                             +------------+
                       |  read / write
                       v
                +------------------+
                | packbot_trips.json|
                +------------------+
```

| Layer       | Tech                | Port   | Runs in              |
|-------------|---------------------|--------|----------------------|
| Notebook    | Python (Jupyter)    | —      | Jupyter kernel       |
| Web server  | Flask               | 5000   | thread in the kernel |
| LLM runtime | Ollama + llama3.1   | 11434  | separate OS process  |
| Browser UI  | HTML + CSS + JS     | —      | your browser tab     |
| Persistence | JSON file           | —      | `./packbot_trips.json` |

## Prerequisites

| Requirement | Version / Note                          |
|-------------|-----------------------------------------|
| Python      | 3.10+                                   |
| Jupyter     | any recent version (lab or classic)     |
| Ollama      | latest — `curl -fsSL https://ollama.ai/install.sh \| sh` |
| Model       | `llama3.1:8b` (default, ~4.7 GB download) |
| GPU (opt.)  | any CUDA/NVidia GPU for faster inference|
| `pip` pkgs  | `flask`, `ollama`                       |

```bash
pip install flask ollama
ollama pull llama3.1:8b
```

## Quick Start

1. Open the notebook:
   ```bash
   jupyter notebook packbot_pro.ipynb
   ```
2. Run all 5 cells top-to-bottom (Shift+Enter on each, or
   **Kernel > Restart & Run All**).
3. A browser tab opens automatically at `http://localhost:5000`.
4. Fill in the trip details, click **Generate Packing List**.
5. The formatted result appears in the browser; it is also saved
   to `packbot_trips.json`.

> The last cell blocks (Flask `app.run()`). Stop the kernel or
> `Ctrl+C` in the terminal to shut down the server.

## Notebook Layout

| Cell | Purpose                                  | Key objects |
|------|------------------------------------------|-------------|
| 1    | System prompt for the LLM                | `SYSTEM_PROMPT` |
| 2    | Imports, `load_trips()`, `save_trip()`   | `TRIPS_FILE`, `PORT` |
| 3    | Complete HTML/CSS/JS single-page app     | `HTML_PAGE` |
| 4    | Flask app + 4 route handlers             | `app`, `index`, `api_generate`, `api_history`, `api_history_detail` |
| 5    | Start server in a thread, open browser   | `app.run()` |

All cells share one Python namespace; order matters (1 before 2, etc.).

## Web UI

Served at `http://localhost:5000`. Dark-themed, single-page, no
external dependencies beyond two CDN scripts (`marked.js`,
`DOMPurify`).

**Form fields (11):**

| Field              | Type            | Notes                          |
|--------------------|-----------------|--------------------------------|
| Destination *      | text            | required                       |
| Dates              | text            | free-form                      |
| Duration (days)    | number 1–90     | default 7                      |
| Trip Type          | select          | Leisure / Business / Adventure / Mixed |
| Activities         | textarea        |                                |
| Accommodation      | select          | Hotel / Airbnb / Hostel / Camping |
| Transport          | select          | Flight / Train / Road Trip / Cruise |
| Luggage            | select          | Carry-on / Checked / Backpack  |
| Gender             | select          | Male / Female / Neutral-Other  |
| Remote Work?       | select          | No / Yes-light / Yes-full      |
| Medical / Special  | textarea        | optional                       |

**Features:**

- Generate button with spinner + status message
- Result rendered as formatted markdown (headings, tables, lists,
  code blocks, checkboxes) via `marked.js`
- Copy-to-clipboard button on the result card
- Trip history list with **View** modal per trip
- Template loader: pick a saved trip, values populate the form
- Responsive layout (mobile-friendly)

## API Reference

Base URL: `http://localhost:5000`

### `GET /`

Returns the full HTML page (the web UI).

### `POST /api/generate`

Generates a packing list.

**Request body** (`application/json`):

```json
{
  "destination":  "Japan",
  "dates":        "April 1-10, 2025",
  "duration":     10,
  "trip_type":    "Leisure",
  "activities":   "temples, food tours, photography",
  "accommodation":"Hotel",
  "transport":    "Flight",
  "bags":         "Carry-on Only",
  "gender":       "Male",
  "work":         "No",
  "medical":      ""
}
```

**Response** `200`:

```json
{
  "result": "## EXECUTIVE SUMMARY\n...",
  "id":     3
}
```

**Response** `400` (missing destination):

```json
{ "error": "Destination is required." }
```

**Response** `502` (Ollama unreachable):

```json
{ "error": "Ollama error: Connection refused — make sure ollama serve is running." }
```

### `GET /api/history`

Returns the full array of saved trips.

```json
[
  {
    "id": 1,
    "destination": "Japan",
    "dates": "April 1-10, 2025",
    "duration": 10,
    "trip_type": "Leisure",
    "result": "## EXECUTIVE SUMMARY\n...",
    "created": "2025-06-14T10:32:00"
  }
]
```

### `GET /api/history/:id`

Returns a single trip by its integer `id`.

**Response** `200`: same object shape as above.
**Response** `404`: `{"error": "Trip not found."}`

## Data Model

**File:** `packbot_trips.json` (created on first save)

```json
[
  {
    "id":          1,
    "destination": "Japan",
    "dates":       "April 1-10, 2025",
    "duration":    10,
    "trip_type":   "Leisure",
    "result":      "## EXECUTIVE SUMMARY\n...(full markdown)...",
    "created":     "2025-06-14T10:32:00"
  }
]
```

| Field         | Type   | Source          |
|---------------|--------|-----------------|
| `id`          | int    | auto (len+1)    |
| `destination` | str    | form input      |
| `dates`       | str    | form input      |
| `duration`    | int    | form input      |
| `trip_type`   | str    | form input      |
| `result`      | str    | LLM output      |
| `created`     | str    | `datetime.now()`|

## Configuration

| Setting          | Where                       | Default       | How to change |
|------------------|-----------------------------|---------------|---------------|
| LLM model        | Cell 4 (`api_generate`)     | `llama3.1:8b` | edit the `model=` string |
| Temperature      | Cell 4 (`api_generate`)     | `0.4`         | edit `options={"temperature": ...}` |
| Server port      | Cell 2 (`PORT`)             | `5000`        | change `PORT = ...` |
| History file     | Cell 2 (`TRIPS_FILE`)       | `packbot_trips.json` | change the string |
| System prompt    | Cell 1 (`SYSTEM_PROMPT`)    | (built-in)    | edit the triple-quoted string |
| Host bind        | Cell 5 (`app.run`)          | `0.0.0.0`     | change `host=` |

## Troubleshooting

| Symptom                              | Fix |
|--------------------------------------|-----|
| `ModuleNotFoundError: flask`         | `pip install flask` |
| `ModuleNotFoundError: ollama`        | `pip install ollama` |
| `Connection refused` on generate     | Start Ollama: `ollama serve` |
| `404 model not found`                | Pull it: `ollama pull llama3.1:8b` |
| Port 5000 already in use             | Change `PORT` in Cell 2, restart kernel |
| Slow generation (>60 s)              | Normal on CPU; use a GPU or a smaller model |
| Browser tab opens but shows nothing  | Check terminal for Flask errors; ensure all 5 cells ran in order |
| Result is blank / truncated          | Check `ollama` logs; try `temperature: 0.2` |
| JSON file corrupted                  | Delete `packbot_trips.json`; history restarts empty |

## Project Files

```
project/
├── packbot_pro.ipynb          # the 5-cell notebook (this app)
├── packbot_trips.json         # trip history (auto-created)
├── packbot_architecture.png   # architecture diagram (from diagram notebook)
├── packbot_architecture.html  # architecture diagram (HTML version)
└── requirements.txt           # flask, ollama
```

**requirements.txt:**

```
flask>=2.0
ollama>=0.1
```

---

**PackBot Pro** — zero cloud calls, zero API keys, all inference local.
