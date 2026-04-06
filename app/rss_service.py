import html
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import feedparser
from bs4 import BeautifulSoup
from markupsafe import Markup, escape

FEEDS = [
    {
        "name": "RemoteOK",
        "url": "https://remoteok.com/remote-dev-jobs.rss",
    },
    {
        "name": "We Work Remotely",
        "url": "https://weworkremotely.com/remote-jobs.rss",
    },
    {
        "name": "Remotive",
        "url": "https://remotive.com/feed",
    },
    {
        "name": "We Work Remotely Programming",
        "url": "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    },
    {
        "name": "We Work Remotely DevOps",
        "url": "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    },
]

DEFAULT_KEYWORDS = [
    "python",
    "react",
    "typescript",
    "node",
    "express",
    "full stack",
    "backend",
    "platform",
    "internal tools",
    "api",
    "aws",
    "ai",
    "llm",
    "fastapi",
    "postgres",
]

EXCLUDE = [
    "designer",
    "sales",
    "account executive",
    "recruiter",
]


def normalize_whitespace(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text or "").strip()



def cleanup_multiline_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]

    cleaned = []
    blank_streak = 0
    for line in lines:
        if not line:
            blank_streak += 1
            if blank_streak <= 1:
                cleaned.append("")
            continue

        blank_streak = 0
        cleaned.append(line)

    return "\n".join(cleaned).strip()



def strip_html_preserve_newlines(raw_html: str) -> str:
    if not raw_html:
        return ""

    decoded = html.unescape(raw_html)
    soup = BeautifulSoup(decoded, "html.parser")

    for tag in soup.find_all(["br"]):
        tag.replace_with("\n")

    for tag in soup.find_all(["p", "div", "li", "ul", "ol"]):
        tag.append("\n")

    text = soup.get_text()
    return cleanup_multiline_text(text)



def parse_date(entry):
    candidates = [
        entry.get("published"),
        entry.get("updated"),
        entry.get("pubDate"),
    ]

    for value in candidates:
        if not value:
            continue
        try:
            dt = parsedate_to_datetime(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            pass

    return None



def parse_keywords(raw_keywords: str | None) -> list[str]:
    if not raw_keywords:
        return []

    parts = [part.strip().lower() for part in raw_keywords.split(",")]
    return [part for part in parts if part]



def get_effective_keywords(custom_keywords: list[str] | None = None) -> list[str]:
    if custom_keywords:
        return custom_keywords
    return DEFAULT_KEYWORDS



def job_matches_keywords(text: str, keywords: list[str] | None = None) -> bool:
    effective_keywords = get_effective_keywords(keywords)
    lower = (text or "").lower()
    return any(keyword in lower for keyword in effective_keywords)



def matches_exclude(text: str) -> bool:
    lower = (text or "").lower()
    return any(bad in lower for bad in EXCLUDE)



def should_include_by_age(published_dt: datetime | None, max_age_days: int | None) -> bool:
    if max_age_days is None:
        return True

    if published_dt is None:
        return False

    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    published_utc = published_dt.astimezone(timezone.utc)
    return published_utc >= cutoff



def score_job(text: str, custom_keywords: list[str] | None = None) -> int:
    lower = (text or "").lower()
    score = 0

    weights = {
        "python": 3,
        "react": 3,
        "typescript": 3,
        "node": 2,
        "express": 2,
        "backend": 3,
        "platform": 3,
        "internal tools": 4,
        "api": 2,
        "aws": 2,
        "ai": 2,
        "llm": 3,
        "fastapi": 3,
        "postgres": 2,
        "full stack": 2,
    }

    for keyword, points in weights.items():
        if keyword in lower:
            score += points

    calm_signals = ["platform", "backend", "internal", "infrastructure", "tools"]
    for signal in calm_signals:
        if signal in lower:
            score += 1

    if custom_keywords:
        for keyword in custom_keywords:
            if keyword in lower:
                score += weights.get(keyword, 3)

    return score



def highlight_text(text: str, keywords: list[str] | None = None) -> Markup:
    if not text:
        return Markup("")

    escaped_text = escape(text)

    if not keywords:
        return Markup(str(escaped_text).replace("\n", "<br>"))

    normalized_keywords = sorted(
        {keyword.strip() for keyword in keywords if keyword.strip()},
        key=len,
        reverse=True,
    )

    if not normalized_keywords:
        return Markup(str(escaped_text).replace("\n", "<br>"))

    pattern = re.compile(
        "(" + "|".join(re.escape(keyword) for keyword in normalized_keywords) + ")",
        flags=re.IGNORECASE,
    )

    highlighted = pattern.sub(
        r'<mark class="keyword-hit">\1</mark>',
        str(escaped_text),
    )

    highlighted = highlighted.replace("\n", "<br>")
    return Markup(highlighted)



def build_summary_preview(
    summary: str,
    keywords: list[str] | None = None,
    preview_chars: int = 320,
) -> str:
    if not summary:
        return ""

    text = cleanup_multiline_text(summary)

    if len(text) <= preview_chars:
        return text

    if keywords:
        lower_text = text.lower()

        for keyword in keywords:
            kw = keyword.strip().lower()
            if not kw:
                continue

            match_index = lower_text.find(kw)
            if match_index != -1:
                start = max(0, match_index - 120)
                end = min(len(text), match_index + max(len(kw), 1) + 180)

                while start > 0 and text[start] not in ".\n ":
                    start -= 1

                while end < len(text) and text[end - 1] not in ".\n ":
                    end += 1
                    if end >= len(text):
                        end = len(text)
                        break

                snippet = text[start:end].strip()

                if start > 0:
                    snippet = "… " + snippet
                if end < len(text):
                    snippet = snippet + " …"

                return snippet

    preview = text[:preview_chars].rstrip()

    last_break = max(preview.rfind("."), preview.rfind("\n"))
    if last_break >= int(preview_chars * 0.55):
        preview = preview[: last_break + 1]

    if len(preview) < len(text):
        preview += " …"

    return preview.strip()



def format_source_name(source: str) -> str:
    lower = (source or "").lower()

    if "remoteok.com" in lower:
        return "RemoteOK"
    if "weworkremotely.com/categories/remote-programming-jobs.rss" in lower:
        return "We Work Remotely Programming"
    if "weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss" in lower:
        return "We Work Remotely DevOps"
    if "weworkremotely.com" in lower:
        return "We Work Remotely"
    if "remotive.com" in lower:
        return "Remotive"

    return source



def fetch_jobs(custom_keywords: list[str] | None = None, max_age_days: int | None = None):
    all_jobs = []
    seen = set()

    for feed in FEEDS:
        feed_url = feed["url"]
        parsed = feedparser.parse(feed_url)

        for entry in parsed.entries:
            title = normalize_whitespace(entry.get("title", ""))
            raw_summary = entry.get("summary", "") or entry.get("description", "")
            summary = strip_html_preserve_newlines(raw_summary)
            link = entry.get("link", "")
            published_dt = parse_date(entry)

            combined = f"{title}\n{summary}"

            if not job_matches_keywords(combined, custom_keywords):
                continue

            if matches_exclude(combined):
                continue

            if not should_include_by_age(published_dt, max_age_days):
                continue

            key = (title.lower(), link.lower())
            if key in seen:
                continue
            seen.add(key)

            all_jobs.append(
                {
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "published": published_dt,
                    "source": feed_url,
                    "score": score_job(combined, custom_keywords),
                }
            )

    all_jobs.sort(
        key=lambda job: (
            job["score"],
            job["published"] or datetime.min.replace(tzinfo=timezone.utc),
        ),
        reverse=True,
    )

    return all_jobs
