"""
FastAPI REST API — exposes scraped jobs via HTTP endpoints.

Run:  uvicorn api.server:app --reload
Docs: http://localhost:8000/docs
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from db.database import init_db, search_jobs, get_stats

app = FastAPI(
    title="Job Scraper API",
    description="Hidden job listings scraped directly from company career pages",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return {"status": "ok", "message": "Job Scraper API is running"}


@app.get("/jobs")
def get_jobs(
    q: str = Query("", description="Search by title or description"),
    company: str = Query("", description="Filter by company slug"),
    location: str = Query("", description="Filter by location keyword"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Search scraped jobs with optional filters."""
    jobs = search_jobs(query=q, company=company, location=location,
                       limit=limit, offset=offset)
    return {"count": len(jobs), "jobs": jobs}


@app.get("/stats")
def stats():
    """Returns total job count, breakdown by company, and recent scrape runs."""
    return get_stats()


@app.get("/health")
def health():
    return {"status": "healthy"}
