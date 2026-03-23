<div align="center">

# 🔍 Job Scraper

### Surface hidden jobs directly from company career pages — before they hit the big boards.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://sqlite.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](CONTRIBUTING.md)

</div>

---

## 🧠 What is this?

Most job seekers only see what's posted on LinkedIn or Naukri — but those are already days old, already crowded, and often missing the real opportunities.

**Job Scraper** goes directly to the source. It hits company career pages via ATS APIs (Greenhouse, Lever, Ashby) and HTML fallback scrapers, stores everything locally in SQLite, and exposes a clean search API — so you can find jobs the moment they're posted, before the noise begins.

> Built as part of an **Opportunity Intelligence Platform** — a system for surfacing hidden, emerging, and underserved job roles in real time.

---

## ✨ Features

- 🏢 **Multi-ATS Support** — Greenhouse, Lever, Ashby, and generic HTML career pages
- ⚡ **FastAPI REST Server** — search, filter, and paginate scraped jobs via HTTP
- 🗄️ **SQLite Storage** — lightweight, zero-config, no external DB needed
- 🔄 **Auto-Scheduler** — re-scrapes all targets every N hours via APScheduler
- 🚫 **Deduplication** — jobs are upserted by `(job_id, company)` — no duplicates ever
- 📊 **Stats Endpoint** — total jobs, breakdown by company, recent scrape runs
- 🧩 **Extensible** — adding a new company is one line in `TARGETS`

---

## 📁 Project Structure

```
job-scraper/
│
├── scrapers/
│   ├── __init__.py
│   └── ats_scrapers.py       # Greenhouse, Lever, Ashby, Generic scrapers
│
├── db/
│   ├── __init__.py
│   └── database.py           # SQLite layer — init, upsert, search, stats
│
├── api/
│   ├── __init__.py
│   └── server.py             # FastAPI app — /jobs, /stats, /health
│
├── scheduler/
│   ├── __init__.py
│   └── runner.py             # APScheduler — runs all scrapers on interval
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Scheduler (APScheduler)           │
│          runs every 6h → calls all scrapers         │
└───────────────────────┬─────────────────────────────┘
                        │
          ┌─────────────▼──────────────┐
          │        ATS Scrapers        │
          │                            │
          │  Greenhouse API  (JSON)    │
          │  Lever API       (JSON)    │
          │  Ashby GraphQL   (JSON)    │
          │  Generic HTML    (scrape)  │
          └─────────────┬──────────────┘
                        │  list[dict]
          ┌─────────────▼──────────────┐
          │       SQLite Database      │
          │                            │
          │   jobs table               │
          │   scrape_runs table        │
          └─────────────┬──────────────┘
                        │
          ┌─────────────▼──────────────┐
          │        FastAPI Server      │
          │                            │
          │  GET /jobs   → search      │
          │  GET /stats  → analytics   │
          │  GET /health → uptime      │
          └────────────────────────────┘
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.11 or higher
- pip

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/job-scraper.git
cd job-scraper
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Activate:
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🚀 Running the Project

### Option A — One-time scrape (quick test)

```python
# run this from the project root
from scrapers.ats_scrapers import scrape_greenhouse, scrape_lever
from db.database import init_db, upsert_jobs

init_db()

jobs = scrape_greenhouse("airbnb")
new = upsert_jobs(jobs)
print(f"Airbnb: {len(jobs)} jobs found, {new} new")

jobs = scrape_lever("reddit")
new = upsert_jobs(jobs)
print(f"Reddit: {len(jobs)} jobs found, {new} new")
```

---

### Option B — Start the auto-scheduler (scrapes every 6h)

```bash
python -m scheduler.runner
```

Output:
```
2024-01-15 10:00:00 [INFO] === Starting scrape run ===
2024-01-15 10:00:01 [INFO]   ✓ Airbnb: 124 total, 12 new
2024-01-15 10:00:02 [INFO]   ✓ Shopify: 89 total, 5 new
2024-01-15 10:00:03 [INFO]   ✓ Netflix: 201 total, 0 new
2024-01-15 10:00:04 [INFO]   ✓ OpenAI: 67 total, 8 new
2024-01-15 10:00:05 [INFO] === Scrape run complete ===
2024-01-15 10:00:05 [INFO] Scheduler started — will re-scrape every 6h
```

---

### Option C — Start the API server

```bash
uvicorn api.server:app --reload --port 8000
```

Then open **http://localhost:8000/docs** for the interactive Swagger UI.

---

## 🔗 API Reference

### `GET /jobs` — Search Jobs

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | `""` | Search in title and description |
| `company` | string | `""` | Filter by company slug (e.g. `airbnb`) |
| `location` | string | `""` | Filter by location keyword (e.g. `remote`) |
| `limit` | int | `50` | Max results (1–200) |
| `offset` | int | `0` | Pagination offset |

**Example requests:**

```bash
# All remote engineering jobs
curl "http://localhost:8000/jobs?q=engineer&location=remote"

# All Airbnb jobs
curl "http://localhost:8000/jobs?company=airbnb"

# Product manager roles, paginated
curl "http://localhost:8000/jobs?q=product+manager&limit=20&offset=40"
```

**Example response:**

```json
{
  "count": 3,
  "jobs": [
    {
      "id": 1,
      "job_id": "4523891",
      "company": "airbnb",
      "title": "Senior Software Engineer, Payments",
      "location": "San Francisco, CA",
      "department": "Engineering",
      "url": "https://careers.airbnb.com/positions/4523891",
      "ats": "greenhouse",
      "description": "We're looking for a Senior Software Engineer...",
      "scraped_at": "2024-01-15T10:00:01"
    }
  ]
}
```

---

### `GET /stats` — Scrape Analytics

```bash
curl "http://localhost:8000/stats"
```

```json
{
  "total_jobs": 1842,
  "by_company": [
    { "company": "netflix", "cnt": 412 },
    { "company": "airbnb",  "cnt": 234 },
    { "company": "openai",  "cnt": 189 }
  ],
  "recent_runs": [
    {
      "company": "Airbnb",
      "ats": "scrape_greenhouse",
      "jobs_found": 124,
      "new_jobs": 12,
      "ran_at": "2024-01-15T10:00:01"
    }
  ]
}
```

---

### `GET /health` — Health Check

```json
{ "status": "healthy" }
```

---

## 🏢 Adding More Companies

Open `scheduler/runner.py` and add entries to the `TARGETS` list:

```python
TARGETS = [
    # Greenhouse
    (scrape_greenhouse, "airbnb",       "Airbnb"),
    (scrape_greenhouse, "shopify",      "Shopify"),
    (scrape_greenhouse, "stripe",       "Stripe"),      # ← add like this

    # Lever
    (scrape_lever,      "netflix",      "Netflix"),
    (scrape_lever,      "reddit",       "Reddit"),

    # Ashby
    (scrape_ashby,      "openai",       "OpenAI"),
    (scrape_ashby,      "anthropic",    "Anthropic"),

    # Generic HTML career pages (full URL)
    (scrape_generic, "https://careers.google.com/jobs/results/", "Google"),
]
```

### Finding the right slug

| ATS | URL pattern on their careers page | Slug to use |
|-----|----------------------------------|-------------|
| Greenhouse | `boards.greenhouse.io/SLUG` | `SLUG` |
| Lever | `jobs.lever.co/SLUG` | `SLUG` |
| Ashby | `jobs.ashbyhq.com/SLUG` | `SLUG` |
| Generic | Full careers URL | Full URL |

---

## 🛠 Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Scraping | `requests` + `BeautifulSoup4` | Lightweight, reliable HTTP + HTML parsing |
| ATS APIs | `requests` (JSON / GraphQL) | Greenhouse, Lever, Ashby all have public APIs |
| Storage | `SQLite` via `sqlite3` | Zero-config, file-based, perfect for single-node |
| API | `FastAPI` + `Uvicorn` | Fast, auto-docs, async-ready |
| Scheduling | `APScheduler` | In-process scheduler, no Redis/Celery needed |

---

## 🗺️ Roadmap

- [ ] Add Workday & iCIMS scrapers
- [ ] Telegram / WhatsApp alert for new job matches
- [ ] Keyword-based filtering rules (notify only if title matches)
- [ ] Docker + `docker-compose` setup
- [ ] Deploy to Railway / Render (one-click)
- [ ] Frontend dashboard (React) for browsing jobs
- [ ] Export to CSV / Google Sheets

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

```bash
# Fork the repo, then:
git checkout -b feature/your-feature-name
git commit -m "feat: add your feature"
git push origin feature/your-feature-name
# → Open a PR
```

---

## 📄 License

MIT © [Mohsin](https://github.com/YOUR_USERNAME)

---

<div align="center">
  <sub>Built with ❤️ as part of an Opportunity Intelligence Platform</sub>
</div>
