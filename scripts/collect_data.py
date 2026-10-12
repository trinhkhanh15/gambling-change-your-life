import calendar
import csv
import sys
import time
import types
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from threading import Lock
from urllib.parse import urlencode, urlparse

import feedparser
import requests
import trafilatura
from trafilatura import extract_metadata

try:
    from googlenewsdecoder import gnewsdecoder
except ModuleNotFoundError as exc:
    if exc.name == "googlenewsdecoder":
        raise SystemExit(
            "Missing dependency: install it with `pip install googlenewsdecoder`."
        ) from exc
    raise
except ImportError as exc:
    if "Modest backend is deprecated" not in str(exc):
        raise

    # googlenewsdecoder still imports selectolax.parser, which selectolax 1.x
    # disables. Its maintained Lexbor parser exposes the API this decoder uses.
    from selectolax.lexbor import LexborHTMLParser

    parser_compat = types.ModuleType("selectolax.parser")
    parser_compat.HTMLParser = LexborHTMLParser
    sys.modules["selectolax.parser"] = parser_compat
    from googlenewsdecoder import gnewsdecoder


OUT = Path("data/raw_news_websearch")
TARGET_PER_DAY = 3

PERIODS = [
    (date(2025, 1, 1), date(2025, 3, 31)),
    (date(2025, 7, 1), date(2025, 12, 31)),
    (date(2026, 1, 1), date(2026, 6, 30)),
]

DOMAINS = {
    "ai_infra": '"AI infrastructure" OR "AI data center" OR "data center"',
    "llm": '"large language model" OR LLM OR OpenAI OR Anthropic',
    "energy": '"energy company" OR electricity OR power grid OR oil',
    "robotics": 'robotics OR "industrial robot" OR automation',
}

FIELDS = ["published_at", "title", "content", "source"]
google_decoder_lock = Lock()


class Progress:
    def __init__(self, total_days):
        self.total_days = total_days
        self.completed_days = 0
        self.started_at = time.monotonic()
        self.lock = Lock()

    def update(self, month, day, articles):
        with self.lock:
            self.completed_days += 1
            elapsed = time.monotonic() - self.started_at
            rate = self.completed_days / elapsed if elapsed else 0
            remaining = self.total_days - self.completed_days
            eta_seconds = remaining / rate if rate else 0
            eta = str(timedelta(seconds=int(eta_seconds)))
            percent = self.completed_days / self.total_days

            print(
                f"[{self.completed_days}/{self.total_days} {percent:.1%} "
                f"| ETA {eta}] {month} {day.isoformat()}: "
                f"{articles}/{TARGET_PER_DAY} articles",
                flush=True,
            )


def month_jobs():
    """Return the requested date range for each month."""
    jobs = []

    for start, end in PERIODS:
        cursor = start.replace(day=1)

        while cursor <= end:
            last_day = calendar.monthrange(cursor.year, cursor.month)[1]
            month_start = cursor
            month_end = cursor.replace(day=last_day)

            jobs.append((
                max(start, month_start),
                min(end, month_end),
            ))

            if cursor.month == 12:
                cursor = date(cursor.year + 1, 1, 1)
            else:
                cursor = date(cursor.year, cursor.month + 1, 1)

    return jobs


def search_day(session, query, day):
    # Search a wider window because publishers and RSS feeds may report
    # publication times in different time zones. Filter back to the target day.
    search_start = day - timedelta(days=1)
    search_end = day + timedelta(days=2)
    search = (
        f'{query} after:{search_start.isoformat()} '
        f'before:{search_end.isoformat()}'
    )
    params = {
        "q": search,
        "hl": "en-US",
        "gl": "US",
        "ceid": "US:en",
    }
    url = "https://news.google.com/rss/search?" + urlencode(params)

    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
    except Exception as exc:
        return [], f"search error: {type(exc).__name__}: {exc}"

    items = []
    for entry in feed.entries:
        published = entry.get("published", "")
        try:
            published_day = parsedate_to_datetime(published).date()
        except (TypeError, ValueError, OverflowError):
            parsed = entry.get("published_parsed")
            if not parsed:
                continue
            published_day = datetime(*parsed[:6], tzinfo=timezone.utc).date()

        if published_day == day and entry.get("link"):
            items.append(entry)

    diagnostic = (
        f"RSS entries={len(feed.entries)}, target-date matches={len(items)}"
    )
    if getattr(feed, "bozo", False):
        diagnostic += f", feed parse warning={feed.get('bozo_exception')}"
    return items, diagnostic


def extract_article(session, entry):
    url = entry.get("link")
    if not url:
        return None, "missing URL"

    try:
        if "news.google.com" in urlparse(url).netloc:
            # Google News RSS URLs are opaque and no longer redirect to the
            # publisher. Resolve them before fetching the article page.
            with google_decoder_lock:
                decoded = gnewsdecoder(url, interval=0.25, timeout=20)

            if not isinstance(decoded, dict):
                return None, "Google News URL decoder returned an invalid result"

            decoded_url = decoded.get("decoded_url")
            decode_succeeded = decoded.get("success") or decoded.get("status")
            if not decode_succeeded or not decoded_url:
                return None, (
                    "Google News URL decode failed: "
                    f"{decoded.get('message', 'no publisher URL returned')}"
                )
            url = decoded_url

        response = session.get(url, timeout=30, allow_redirects=True)
        if response.status_code != 200:
            return None, f"HTTP {response.status_code}"

        final_url = response.url
        if "news.google.com" in urlparse(final_url).netloc:
            return None, "URL did not resolve to publisher"

        html = response.text
        content = trafilatura.extract(
            html,
            url=final_url,
            include_comments=False,
            include_tables=True,
            favor_precision=True,
        )

        if not content:
            return None, "article text not extracted"
        if len(content.strip()) < 800:
            return None, f"extracted text too short ({len(content.strip())} chars)"

        metadata = extract_metadata(html, default_url=final_url)
        title = (metadata.title if metadata else None) or entry.get("title", "")
        source = (
            (metadata.sitename if metadata else None)
            or (entry.get("source", {}).get("title") if entry.get("source") else None)
            or urlparse(final_url).netloc
        )

        return {
            "published_at": entry.get("published", ""),
            "title": title,
            "content": content.strip(),
            "source": source,
        }, None
    except Exception as exc:
        return None, f"fetch/extract error: {type(exc).__name__}: {exc}"


def ensure_csv(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with path.open("w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow(FIELDS)


def append_row(path, row):
    with path.open("a", encoding="utf-8", newline="") as f:
        csv.DictWriter(f, fieldnames=FIELDS).writerow(row)


def parse_published_day(value):
    try:
        return parsedate_to_datetime(value).date()
    except (TypeError, ValueError, OverflowError):
        return None


def process_month(start, end, progress):
    """One worker owns and writes all CSVs for this month."""
    month_dir = OUT / start.strftime("%Y-%m")
    paths = {
        domain: month_dir / f"{domain}.csv"
        for domain in DOMAINS
    }

    for path in paths.values():
        ensure_csv(path)

    existing_counts = {}
    existing_articles = set()
    for path in paths.values():
        with path.open("r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                existing_articles.add((row["published_at"], row["title"]))
                published_day = parse_published_day(row["published_at"])
                if published_day:
                    existing_counts[published_day] = (
                        existing_counts.get(published_day, 0) + 1
                    )

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; ResearchDataset/1.0)"
    })

    seen_urls = set()
    shortfalls = []
    article_count = 0

    day = start
    while day <= end:
        collected_today = existing_counts.get(day, 0)
        if collected_today >= TARGET_PER_DAY:
            progress.update(start.strftime("%Y-%m"), day, collected_today)
            day += timedelta(days=1)
            continue

        candidates = {}
        search_diagnostics = {}
        for domain, query in DOMAINS.items():
            candidates[domain], search_diagnostics[domain] = search_day(
                session, query, day
            )

        extraction_failures = {}
        max_rounds = max(
            (len(items) for items in candidates.values()),
            default=0,
        )

        # Rotate domains so one topic does not monopolize the daily results.
        for index in range(max_rounds):
            for domain, items in candidates.items():
                if index >= len(items) or collected_today >= TARGET_PER_DAY:
                    continue

                entry = items[index]
                url = entry.get("link")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)

                row, failure = extract_article(session, entry)
                time.sleep(0.25)

                if row:
                    article_key = (row["published_at"], row["title"])
                    if article_key in existing_articles:
                        continue
                    append_row(paths[domain], row)
                    existing_articles.add(article_key)
                    existing_counts[day] = existing_counts.get(day, 0) + 1
                    collected_today += 1
                    article_count += 1
                elif failure:
                    extraction_failures[failure] = (
                        extraction_failures.get(failure, 0) + 1
                    )

            if collected_today >= TARGET_PER_DAY:
                break

        if collected_today < TARGET_PER_DAY:
            candidate_counts = ", ".join(
                f"{domain}={len(items)} ({search_diagnostics[domain]})"
                for domain, items in candidates.items()
            )
            print(
                f"[Debug {day.isoformat()}] candidates: {candidate_counts}; "
                f"extraction failures: {extraction_failures or 'none'}",
                flush=True,
            )
            shortfalls.append({
                "date": day.isoformat(),
                "collected": collected_today,
                "target": TARGET_PER_DAY,
            })

        progress.update(start.strftime("%Y-%m"), day, collected_today)
        day += timedelta(days=1)

    session.close()
    return start.strftime("%Y-%m"), article_count, shortfalls


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = month_jobs()
    total_days = sum((end - start).days + 1 for start, end in jobs)
    progress = Progress(total_days)
    all_shortfalls = []

    # One worker per month.
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        futures = [
            pool.submit(process_month, start, end, progress)
            for start, end in jobs
        ]

        for future in as_completed(futures):
            month, article_count, shortfalls = future.result()
            all_shortfalls.extend(shortfalls)
            print(
                f"{month}: {article_count} articles; "
                f"{len(shortfalls)} days below target"
            )

    shortfalls_path = OUT / "shortfalls.csv"
    with shortfalls_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["date", "collected", "target"],
        )
        writer.writeheader()
        writer.writerows(sorted(all_shortfalls, key=lambda row: row["date"]))

    print(f"Finished. Output: {OUT.resolve()}")
    print(f"Days below target: {len(all_shortfalls)}")


if __name__ == "__main__":
    main()
