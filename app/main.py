from urllib.parse import urlencode

from fastapi import Depends, FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import Base, engine, get_db
from app.models import Job
from app.rss_service import (
    build_summary_preview,
    fetch_jobs,
    format_source_name,
    highlight_text,
    job_matches_keywords,
    parse_keywords,
    should_include_by_age,
)

app = FastAPI(title="Job Radar")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

Base.metadata.create_all(bind=engine)


def normalize_days(value) -> int:
    try:
        if value is None or value == "":
            return 5
        parsed = int(value)
        return parsed if parsed >= 1 else 5
    except Exception:
        return 5


def build_job_view_models(jobs, keywords_list, days):
    view_jobs = []

    for job in jobs:
        combined = f"{job.title or ''} {job.summary or ''}"

        if keywords_list and not job_matches_keywords(combined, keywords_list):
            continue

        if days is not None and not should_include_by_age(job.published, days):
            continue

        preview_summary = build_summary_preview(job.summary or "", keywords_list)

        view_jobs.append(
            {
                "id": job.id,
                "title": job.title,
                "summary": job.summary or "",
                "preview_summary": preview_summary,
                "link": job.link,
                "published": job.published,
                "source": job.source,
                "source_name": format_source_name(job.source),
                "score": job.score,
                "highlighted_title": highlight_text(job.title or "", keywords_list),
                "highlighted_preview_summary": highlight_text(preview_summary, keywords_list),
                "highlighted_summary": highlight_text(job.summary or "", keywords_list),
            }
        )

    return view_jobs


def build_redirect_url(
    keywords: str = "",
    days: int | None = None,
    inserted: int | None = None,
) -> str:
    params = {}

    if keywords:
        params["keywords"] = keywords

    if days is not None:
        params["days"] = days

    if inserted is not None:
        params["inserted"] = inserted

    if not params:
        return "/"

    return f"/?{urlencode(params)}"


@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    keywords: str = Query(default=""),
    days: int = Query(default=5, ge=1),
    inserted: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    keywords_list = parse_keywords(keywords)
    days = normalize_days(days)

    jobs = (
        db.query(Job)
        .order_by(Job.published.desc(), Job.score.desc())
        .limit(500)
        .all()
    )

    view_jobs = build_job_view_models(jobs, keywords_list, days)

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "jobs": view_jobs,
            "keywords": keywords,
            "days": days,
            "inserted": inserted,
            "active_keywords": keywords_list,
            "job_count": len(view_jobs),
        },
    )


@app.post("/refresh")
def refresh_jobs(
    keywords: str = Form(default=""),
    days: str = Form(default=""),
    db: Session = Depends(get_db),
):
    keywords_list = parse_keywords(keywords)
    normalized_days = normalize_days(days)

    jobs = fetch_jobs(custom_keywords=keywords_list, max_age_days=normalized_days)
    inserted = 0

    for job_data in jobs:
        job = Job(**job_data)
        db.add(job)
        try:
            db.commit()
            inserted += 1
        except IntegrityError:
            db.rollback()

    return RedirectResponse(
        url=build_redirect_url(
            keywords=keywords,
            days=normalized_days,
            inserted=inserted,
        ),
        status_code=303,
    )


@app.get("/jobs")
def get_jobs(
    keywords: str = Query(default=""),
    days: int = Query(default=5, ge=1),
    db: Session = Depends(get_db),
):
    keywords_list = parse_keywords(keywords)
    days = normalize_days(days)

    jobs = (
        db.query(Job)
        .order_by(Job.published.desc(), Job.score.desc())
        .all()
    )

    filtered_jobs = []
    for job in jobs:
        combined = f"{job.title or ''} {job.summary or ''}"

        if keywords_list and not job_matches_keywords(combined, keywords_list):
            continue

        if days is not None and not should_include_by_age(job.published, days):
            continue

        filtered_jobs.append(job)

    return filtered_jobs