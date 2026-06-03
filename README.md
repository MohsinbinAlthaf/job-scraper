# job-scraper

Scrapes jobs directly from company career pages via Greenhouse, Lever, and Ashby APIs — before they show up on LinkedIn or Naukri.

Stores everything in SQLite and exposes a simple search API on top.

---

## Features

- Greenhouse, Lever, Ashby, and generic HTML scraper support
- FastAPI search server with filters and pagination
- SQLite storage — no external database needed
- Auto-scheduler via APScheduler (re-scrapes every 6h)
- Deduplication — no duplicate jobs ever

---

## Setup

```bash
git clone https://github.com/MohsinbinAlthaf/job-scraper.git
cd job-scraper

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

---

## Usage

**One-time scrape**

```python
from scrapers.ats_scrapers import scrape_greenhouse
from db.database import init_db, upsert_jobs

init_db()
jobs = scrape_greenhouse("airbnb")
print(f"{len(jobs)} jobs found")
```

**Start the scheduler** (scrapes all targets every 6h)

```bash
python -m scheduler.runner
```

**Start the API server**

```bash
uvicorn api.server:app --reload --port 8000
```

Swagger UI → `http://localhost:8000/docs`

---

## API

**`GET /jobs`** — search jobs

| Param | Type | Description |
|-------|------|-------------|
| `q` | string | Search in title / description |
| `company` | string | Filter by company slug |
| `location` | string | Filter by location keyword |
| `limit` | int | Max results (default 50) |
| `offset` | int | Pagination offset |

```bash
curl "http://localhost:8000/jobs?q=engineer&location=remote"
curl "http://localhost:8000/jobs?company=airbnb&limit=20"
```

**`GET /stats`** — job count and breakdown by company

**`GET /health`** — health check

---

## Adding Companies

Edit `TARGETS` in `scheduler/runner.py`:

```python
TARGETS = [
    (scrape_greenhouse, "airbnb",   "Airbnb"),
    (scrape_greenhouse, "stripe",   "Stripe"),
    (scrape_lever,      "netflix",  "Netflix"),
    (scrape_ashby,      "openai",   "OpenAI"),
]
```

| ATS | Slug to use |
|-----|-------------|
| Greenhouse | slug from `boards.greenhouse.io/SLUG` |
| Lever | slug from `jobs.lever.co/SLUG` |
| Ashby | slug from `jobs.ashbyhq.com/SLUG` |

---

## Stack

- **Scraping** — `requests` + `BeautifulSoup4`
- **Storage** — `SQLite`
- **API** — `FastAPI` + `Uvicorn`
- **Scheduling** — `APScheduler`

---

## License

MIT © [Mohsin](https://github.com/MohsinbinAlthaf)
