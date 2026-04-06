# Job Radar

A localhost job feed reader built with FastAPI that pulls remote job postings from multiple RSS feeds and helps surface relevant roles faster.

It supports custom keyword filtering, posting-age filters, highlighted keyword matches, and expandable summaries so you can scan more jobs with less noise.

## What it does

- reads remote job postings from multiple RSS feeds
- filters by custom comma-separated keywords
- filters by jobs posted within the last N days
- highlights matching keywords in job titles and summaries
- shows compact previews with an option to expand full summaries
- keeps the interface simple and fast for local use

## Why I built it

I wanted a lightweight way to monitor remote software jobs without manually checking multiple job boards. The goal was to create a local tool that pulls jobs into one place, helps narrow results quickly, and makes long postings easier to scan.

## Tech stack

- Python
- FastAPI
- Jinja2
- SQLAlchemy
- Bootstrap
- PostgreSQL
- RSS

## Features

### Custom keyword filtering
Enter keywords separated by commas, such as:

```text
python, react, platform, aws
```

Jobs are matched using **OR logic**, so a post is shown if it contains at least one keyword.

### Posted-within filter
Filter jobs by recency using the number of days posted.

Examples:
- `1` = last 1 day
- `2` = last 2 days

### Highlighted keyword matches
Matching keywords are highlighted in green within titles and summaries.

### Expandable summaries
Each job card shows a shorter preview by default. If the post is long, you can expand it to read the full summary.

If a keyword match exists in the summary, the preview is centered around that matching excerpt when possible.

## RSS sources

This project currently pulls from:

- RemoteOK
- We Work Remotely
- Remotive
- We Work Remotely Programming
- We Work Remotely DevOps / System Administration

## Local setup

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

### 2. Create the PostgreSQL database

Run this in PostgreSQL:

```sql
CREATE DATABASE job_radar;
```

### 3. Create the jobs table

Connect to the `job_radar` database, then run:

```sql
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    summary TEXT,
    link VARCHAR(1000) NOT NULL,
    published TIMESTAMPTZ,
    source VARCHAR(500) NOT NULL,
    score INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 4. Create and activate a virtual environment

#### Windows PowerShell
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

#### Git Bash
```bash
python -m venv venv
source venv/Scripts/activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure the database connection

By default, the app uses this string and you need to change password:

```text
postgresql://postgres:<insert_pass>@localhost:5432/job_radar
```

If your local PostgreSQL username, password, or port are different, set a `DATABASE_URL` environment variable before running the app.

#### PowerShell
```powershell
$env:DATABASE_URL="postgresql://YOUR_USER:YOUR_PASSWORD@localhost:5432/job_radar"
```

#### Git Bash
```bash
export DATABASE_URL="postgresql://YOUR_USER:YOUR_PASSWORD@localhost:5432/job_radar"
```

### 7. Start the app

```bash
uvicorn app.main:app --reload
```

### 8. Open in browser

```text
http://127.0.0.1:8000
```

## How to use

1. Enter keywords separated by commas, or leave blank
2. Optionally enter the number of days to filter by recency
3. Click **Apply Filters** to filter existing saved jobs
4. Click **Refresh Jobs** to fetch fresh jobs from the RSS feeds using the current filters

## Project structure

```text
app/
  db.py
  main.py
  models.py
  rss_service.py
  templates/
    index.html
  static/
    styles.css
```

## Notes

- This project is intended to run locally on localhost for now
- RSS summaries vary by source, so some job descriptions are much longer than others
- keyword matching currently uses OR logic

## Future improvements

- support toggling between OR and AND keyword matching
- save searches or favorite keywords
- add pagination
- improve date formatting in the UI
- add source toggles so users can enable or disable specific feeds
- deploy publicly

## Portfolio summary

Built a FastAPI-based remote job reader that aggregates multiple RSS feeds into a single local dashboard with keyword filtering, recency filters, highlighted matches, and expandable summaries for faster job triage.
