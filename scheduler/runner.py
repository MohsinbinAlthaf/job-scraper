"""
Scheduler — runs all scrapers on a configurable interval using APScheduler.

Run: python -m scheduler.runner
"""

import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from scrapers.ats_scrapers import scrape_greenhouse, scrape_lever, scrape_ashby, scrape_generic
from db.database import init_db, upsert_jobs, log_run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
#  ADD YOUR TARGET COMPANIES HERE
# ─────────────────────────────────────────
TARGETS = [
    # (scraper_function,  slug/url,      display_name)
    (scrape_greenhouse, "airbnb",        "Airbnb"),
    (scrape_greenhouse, "shopify",       "Shopify"),
    (scrape_lever,      "netflix",       "Netflix"),
    (scrape_lever,      "reddit",        "Reddit"),
    (scrape_ashby,      "openai",        "OpenAI"),
    (scrape_ashby,      "anthropic",     "Anthropic"),
    # For plain HTML career pages, use scrape_generic with the full URL:
    # (scrape_generic, "https://careers.example.com", "Example Corp"),
]

INTERVAL_HOURS = 6  # re-scrape every 6 hours


def run_all():
    logger.info("=== Starting scrape run ===")
    for scraper_fn, slug, company_name in TARGETS:
        try:
            jobs = scraper_fn(slug)
            new = upsert_jobs(jobs)
            log_run(company_name, scraper_fn.__name__, len(jobs), new)
            logger.info(f"  ✓ {company_name}: {len(jobs)} total, {new} new")
        except Exception as e:
            logger.error(f"  ✗ {company_name}: {e}")
    logger.info("=== Scrape run complete ===")


def start_scheduler():
    init_db()
    run_all()  # immediate first run on startup

    scheduler = BlockingScheduler()
    scheduler.add_job(run_all, "interval", hours=INTERVAL_HOURS)
    logger.info(f"Scheduler started — will re-scrape every {INTERVAL_HOURS}h")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    start_scheduler()
