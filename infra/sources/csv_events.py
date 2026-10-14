from __future__ import annotations

import csv
import email.utils
import hashlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

csv.field_size_limit(sys.maxsize)

from application.ports.source import SourceAdapter
from domain.models.event import Event


class CsvEventSourceAdapter(SourceAdapter):
    """Loads archived news rows as Events and attaches ticker-company matches."""

    def __init__(self, path: str | Path, tickers_path: str | Path | None = None):
        self.path = Path(path)
        self._company_patterns: list[tuple[str, str, re.Pattern[str]]] = []
        if tickers_path is not None:
            self._load_company_patterns(Path(tickers_path))

    def _load_company_patterns(self, path: Path) -> None:
        with path.open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream)
            if not reader.fieldnames or "ticker" not in reader.fieldnames:
                raise ValueError(f"{path} must contain a ticker column")
            for row in reader:
                ticker = (row.get("ticker") or "").strip().upper()
                company = (row.get("company") or "").strip()
                if not ticker:
                    continue
                for label in (company, ticker if len(ticker) >= 3 else ""):
                    if label:
                        self._company_patterns.append(
                            (label, ticker, re.compile(rf"(?<!\w){re.escape(label)}(?!\w)", re.IGNORECASE))
                        )
        self._company_patterns.sort(key=lambda item: len(item[0]), reverse=True)

    @staticmethod
    def _parse_datetime(value: str, line: int) -> datetime:
        value = value.strip()
        parsed: datetime | None = None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            try:
                parsed = email.utils.parsedate_to_datetime(value)
            except (TypeError, ValueError, OverflowError):
                pass
        if parsed is None:
            raise ValueError(f"Invalid published_at on CSV line {line}: {value!r}")
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _event_files(self) -> list[Path]:
        if self.path.is_file():
            return [self.path]
        if self.path.is_dir():
            return sorted(self.path.rglob("*.csv"))
        raise FileNotFoundError(f"CSV event source does not exist: {self.path}")

    def fetch_events(self, query: str = "", *, limit: int | None = 10) -> list[Event]:
        if limit is not None and limit < 1:
            raise ValueError("limit must be at least 1")
        query_text = query.strip().casefold()
        events: list[Event] = []
        seen: set[str] = set()
        for path in self._event_files():
            with path.open(newline="", encoding="utf-8-sig") as stream:
                reader = csv.DictReader(stream)
                required = {"published_at", "title", "content", "source"}
                missing = required.difference(reader.fieldnames or [])
                if missing:
                    continue
                for line, row in enumerate(reader, start=2):
                    title = (row.get("title") or "").strip()
                    content = (row.get("content") or "").strip()
                    source = (row.get("source") or "").strip()
                    if not title or not content or not source:
                        continue
                    if query_text and query_text not in f"{title}\n{content}".casefold():
                        continue
                    published_at = self._parse_datetime(row["published_at"] or "", line)
                    fingerprint = hashlib.sha256(
                        f"{published_at.isoformat()}\n{source}\n{title}".encode("utf-8")
                    ).hexdigest()[:16]
                    if fingerprint in seen:
                        continue
                    seen.add(fingerprint)
                    companies = self._find_companies(f"{title}\n{content}")
                    domain = (row.get("domain") or "").strip().casefold() or None
                    events.append(
                        Event(
                            id=f"csv-{fingerprint}",
                            published_at=published_at,
                            source=source,
                            title=title,
                            content=content,
                            domain=domain,
                            companies_mentioned=companies,
                        )
                    )
        events.sort(key=lambda item: (item.published_at, item.id))
        return events if limit is None else events[:limit]

    def _find_companies(self, text: str) -> list[str]:
        matches: list[tuple[int, str]] = []
        seen_tickers: set[str] = set()
        for label, ticker, pattern in self._company_patterns:
            match = pattern.search(text)
            if match and ticker not in seen_tickers:
                matches.append((match.start(), label))
                seen_tickers.add(ticker)
        matches.sort(key=lambda item: item[0])
        return [label for _, label in matches]
