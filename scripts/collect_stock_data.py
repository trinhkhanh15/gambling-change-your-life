#!/usr/bin/env python3
"""Collect daily OHLCV and corporate-action data for a supplied ticker list."""

from __future__ import annotations

import argparse
import csv
import math
import os
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path


DEFAULT_PERIODS = [
    (date(2025, 1, 1), date(2025, 3, 31)),
    (date(2025, 7, 1), date(2025, 12, 31)),
    (date(2026, 1, 1), date(2026, 6, 30)),
]
PRICE_FIELDS = [
    "ticker",
    "company",
    "domain",
    "trade_date",
    "open",
    "high",
    "low",
    "close",
    "adj_close",
    "volume",
    "dividends",
    "stock_splits",
    "currency",
    "source",
]
ERROR_FIELDS = ["ticker", "start_date", "end_date", "error"]
SOURCE = "Yahoo Finance via yfinance"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Collect daily historical stock prices for the requested periods."
    )
    parser.add_argument(
        "--tickers-file",
        type=Path,
        default=Path("data/stock_tickers.csv"),
        help="CSV with a required ticker column and optional currency column.",
    )
    parser.add_argument(
        "--tickers",
        nargs="+",
        help="Ticker symbols; if supplied, skips --tickers-file.",
    )
    parser.add_argument(
        "--start",
        type=date.fromisoformat,
        help="Optional inclusive start date; use together with --end.",
    )
    parser.add_argument(
        "--end",
        type=date.fromisoformat,
        help="Optional inclusive end date; use together with --start.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/market/stock_prices_daily.csv"),
    )
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    if (args.start is None) != (args.end is None):
        parser.error("--start and --end must be supplied together")
    if args.start and args.end and args.start > args.end:
        parser.error("--start must be on or before --end")
    if args.workers < 1:
        parser.error("--workers must be at least 1")

    return args


def load_tickers(args):
    if args.tickers:
        return [
            {
                "ticker": symbol.strip().upper(),
                "company": "",
                "domain": "",
                "currency": "",
            }
            for symbol in args.tickers
            if symbol.strip()
        ]

    path = args.tickers_file
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["ticker", "company", "domain", "currency"])
        raise SystemExit(
            f"Created {path} as a template. Add ticker symbols, then rerun."
        )

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "ticker" not in reader.fieldnames:
            raise SystemExit(f"{path} must contain a 'ticker' column.")
        tickers = []
        seen = set()
        for row in reader:
            symbol = (row.get("ticker") or "").strip().upper()
            if not symbol or symbol in seen:
                continue
            seen.add(symbol)
            tickers.append({
                "ticker": symbol,
                "company": (row.get("company") or "").strip(),
                "domain": (row.get("domain") or "").strip(),
                "currency": (row.get("currency") or "").strip().upper(),
            })

    if not tickers:
        raise SystemExit(f"No tickers found in {path}.")
    return tickers


def requested_periods(args):
    if args.start and args.end:
        return [(args.start, args.end)]
    return DEFAULT_PERIODS


def csv_number(value, integer=False):
    if value is None:
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if not math.isfinite(number):
        return ""
    return str(int(number)) if integer else repr(number)


def fetch_ticker(ticker_info, periods):
    # Import here so --help and template generation work before yfinance is installed.
    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency. Install it with: python -m pip install yfinance"
        ) from exc

    # yfinance deprecated the per-call `raise_errors` argument. Configure the
    # replacement before requesting history so provider errors still reach the
    # retry/error-reporting logic below.
    yf.config.debug.hide_exceptions = False

    symbol = ticker_info["ticker"]
    company = ticker_info.get("company") or symbol
    domain = ticker_info.get("domain", "")
    currency = ticker_info.get("currency", "")
    ticker = yf.Ticker(symbol)
    rows = []
    errors = []

    for start, inclusive_end in periods:
        # yfinance treats `end` as exclusive, so advance one day to include the
        # requested final calendar date.
        exclusive_end = inclusive_end + timedelta(days=1)
        history = None
        last_error = None

        for attempt in range(3):
            try:
                history = ticker.history(
                    start=start.isoformat(),
                    end=exclusive_end.isoformat(),
                    interval="1d",
                    auto_adjust=False,
                    actions=True,
                    repair=False,
                )
                last_error = None
                break
            except Exception as exc:  # provider errors vary by ticker and request
                last_error = f"{type(exc).__name__}: {exc}"
                if attempt < 2:
                    time.sleep(2 ** (attempt + 1))

        if last_error:
            errors.append({
                "ticker": symbol,
                "start_date": start.isoformat(),
                "end_date": inclusive_end.isoformat(),
                "error": last_error,
            })
            continue

        if history is None or history.empty:
            errors.append({
                "ticker": symbol,
                "start_date": start.isoformat(),
                "end_date": inclusive_end.isoformat(),
                "error": "No daily rows returned",
            })
            continue

        for index, values in history.iterrows():
            trade_date = index.date().isoformat()
            close = csv_number(values.get("Close"))
            if not close:
                continue

            rows.append({
                "ticker": symbol,
                "company": company,
                "domain": domain,
                "trade_date": trade_date,
                "open": csv_number(values.get("Open")),
                "high": csv_number(values.get("High")),
                "low": csv_number(values.get("Low")),
                "close": close,
                "adj_close": csv_number(values.get("Adj Close")),
                "volume": csv_number(values.get("Volume"), integer=True),
                "dividends": csv_number(values.get("Dividends")),
                "stock_splits": csv_number(values.get("Stock Splits")),
                "currency": currency,
                "source": SOURCE,
            })

    return symbol, rows, errors


def read_existing_prices(path):
    existing = {}
    if not path.exists():
        return existing

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != PRICE_FIELDS:
            raise SystemExit(
                f"Existing {path} has an unexpected header. "
                "Move it aside before collecting with this schema."
            )
        for row in reader:
            key = (row["ticker"], row["trade_date"])
            existing[key] = row
    return existing


def write_csv_atomic(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="",
        dir=path.parent,
        delete=False,
    ) as f:
        temp_path = Path(f.name)
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temp_path, path)


def main():
    args = parse_args()
    tickers = load_tickers(args)
    periods = requested_periods(args)
    existing = read_existing_prices(args.output)
    all_errors = []

    print(
        f"Collecting daily prices for {len(tickers)} tickers across "
        f"{len(periods)} period(s), with {min(args.workers, len(tickers))} workers.",
        flush=True,
    )

    with ThreadPoolExecutor(max_workers=min(args.workers, len(tickers))) as pool:
        futures = [pool.submit(fetch_ticker, info, periods) for info in tickers]
        for completed, future in enumerate(as_completed(futures), start=1):
            symbol, rows, errors = future.result()
            all_errors.extend(errors)
            for row in rows:
                existing[(row["ticker"], row["trade_date"])] = row
            print(
                f"[{completed}/{len(tickers)}] {symbol}: "
                f"{len(rows)} daily rows, {len(errors)} period errors",
                flush=True,
            )

    sorted_rows = sorted(
        existing.values(),
        key=lambda row: (row["ticker"], row["trade_date"]),
    )
    write_csv_atomic(args.output, PRICE_FIELDS, sorted_rows)

    errors_path = args.output.with_name("stock_collection_errors.csv")
    if all_errors:
        write_csv_atomic(errors_path, ERROR_FIELDS, all_errors)
    elif errors_path.exists():
        errors_path.unlink()

    print(f"Saved {len(sorted_rows)} daily rows to {args.output.resolve()}")
    if all_errors:
        print(f"Some periods failed; see {errors_path.resolve()}")


if __name__ == "__main__":
    main()
