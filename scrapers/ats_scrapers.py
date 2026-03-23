"""
ATS-specific job scrapers for Greenhouse, Lever, Ashby, and generic career pages.
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional
import logging
import re

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


# ─────────────────────────────────────────
#  GREENHOUSE
# ─────────────────────────────────────────
def scrape_greenhouse(company_slug: str) -> list[dict]:
    """
    Scrape jobs from Greenhouse ATS.
    Example: scrape_greenhouse("airbnb")
    """
    url = f"https://api.greenhouse.io/v1/boards/{company_slug}/jobs?content=true"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        jobs = []
        for job in data.get("jobs", []):
            jobs.append({
                "title": job.get("title"),
                "company": company_slug,
                "location": ", ".join(
                    [loc.get("name", "") for loc in job.get("offices", [])]
                ) or "Remote",
                "url": job.get("absolute_url"),
                "job_id": str(job.get("id")),
                "ats": "greenhouse",
                "description": BeautifulSoup(
                    job.get("content", ""), "html.parser"
                ).get_text(separator="\n", strip=True)[:2000],
                "department": ", ".join(
                    [d.get("name", "") for d in job.get("departments", [])]
                ),
            })
        logger.info(f"[Greenhouse] {company_slug}: {len(jobs)} jobs found")
        return jobs
    except Exception as e:
        logger.error(f"[Greenhouse] Error for {company_slug}: {e}")
        return []


# ─────────────────────────────────────────
#  LEVER
# ─────────────────────────────────────────
def scrape_lever(company_slug: str) -> list[dict]:
    """
    Scrape jobs from Lever ATS.
    Example: scrape_lever("netflix")
    """
    url = f"https://api.lever.co/v0/postings/{company_slug}?mode=json"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        jobs = []
        for job in data:
            jobs.append({
                "title": job.get("text"),
                "company": company_slug,
                "location": job.get("categories", {}).get("location", "Remote"),
                "url": job.get("hostedUrl"),
                "job_id": job.get("id"),
                "ats": "lever",
                "description": BeautifulSoup(
                    job.get("descriptionBody", ""), "html.parser"
                ).get_text(separator="\n", strip=True)[:2000],
                "department": job.get("categories", {}).get("department", ""),
            })
        logger.info(f"[Lever] {company_slug}: {len(jobs)} jobs found")
        return jobs
    except Exception as e:
        logger.error(f"[Lever] Error for {company_slug}: {e}")
        return []


# ─────────────────────────────────────────
#  ASHBY
# ─────────────────────────────────────────
def scrape_ashby(company_slug: str) -> list[dict]:
    """
    Scrape jobs from Ashby ATS.
    Example: scrape_ashby("openai")
    """
    url = "https://jobs.ashbyhq.com/api/non-user-graphql"
    query = {
        "operationName": "ApiJobBoardWithTeams",
        "variables": {"organizationHostedJobsPageName": company_slug},
        "query": """
            query ApiJobBoardWithTeams($organizationHostedJobsPageName: String!) {
                jobBoard: jobBoardWithTeams(
                    organizationHostedJobsPageName: $organizationHostedJobsPageName
                ) {
                    jobPostings {
                        id title locationName departmentName
                        externalLink isRemote
                    }
                }
            }
        """,
    }
    try:
        resp = requests.post(url, json=query, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        postings = (
            resp.json()
            .get("data", {})
            .get("jobBoard", {})
            .get("jobPostings", [])
        )
        jobs = []
        for job in postings:
            jobs.append({
                "title": job.get("title"),
                "company": company_slug,
                "location": job.get("locationName") or ("Remote" if job.get("isRemote") else "Unknown"),
                "url": job.get("externalLink")
                or f"https://jobs.ashbyhq.com/{company_slug}/{job.get('id')}",
                "job_id": job.get("id"),
                "ats": "ashby",
                "description": "",
                "department": job.get("departmentName", ""),
            })
        logger.info(f"[Ashby] {company_slug}: {len(jobs)} jobs found")
        return jobs
    except Exception as e:
        logger.error(f"[Ashby] Error for {company_slug}: {e}")
        return []


# ─────────────────────────────────────────
#  GENERIC HTML CAREER PAGE
# ─────────────────────────────────────────
def scrape_generic(careers_url: str, company_name: str) -> list[dict]:
    """
    Fallback scraper for plain HTML career pages.
    Looks for <a> tags containing job-like keywords.
    """
    try:
        resp = requests.get(careers_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        job_keywords = re.compile(
            r"(engineer|developer|designer|manager|analyst|intern|"
            r"marketing|sales|product|data|devops|qa|support)",
            re.IGNORECASE,
        )
        seen = set()
        jobs = []
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            if job_keywords.search(text) and text not in seen:
                seen.add(text)
                href = a["href"]
                if not href.startswith("http"):
                    base = "/".join(careers_url.split("/")[:3])
                    href = base + "/" + href.lstrip("/")
                jobs.append({
                    "title": text,
                    "company": company_name,
                    "location": "See listing",
                    "url": href,
                    "job_id": href,
                    "ats": "generic",
                    "description": "",
                    "department": "",
                })
        logger.info(f"[Generic] {company_name}: {len(jobs)} jobs found")
        return jobs
    except Exception as e:
        logger.error(f"[Generic] Error for {company_name}: {e}")
        return []
