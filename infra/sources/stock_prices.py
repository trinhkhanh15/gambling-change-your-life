from __future__ import annotations

import csv
import re
from math import isfinite
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from pathlib import Path

from domain.models.prediction import Direction, Prediction
from domain.models.reality import Reality


@dataclass(frozen=True)
class ForecastMarketContext:
    ticker: str
    baseline_date: date
    horizon_end: date
    baseline: float

    def prediction_fields(self) -> dict:
        return {
            "target": self.ticker,
            "metrics": ["adjusted_price_return"],
            "horizon_start": self.baseline_date,
            "horizon_end": self.horizon_end,
            "baseline": self.baseline,
        }


class StockPriceOutcomeResolver:
    """Resolves a prediction against the local daily-price CSV; makes no network calls."""

    def __init__(self, prices_path: str | Path, tickers_path: str | Path):
        self.prices_path = Path(prices_path)
        self.tickers_path = Path(tickers_path)
        self._aliases: dict[str, str] = {}
        self._prices: dict[str, list[tuple[date, float]]] = {}
        self._load_tickers()
        self._load_prices()
        all_dates = [day for series in self._prices.values() for day, _ in series]
        self.latest_date = max(all_dates) if all_dates else None

    def _load_tickers(self) -> None:
        with self.tickers_path.open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream)
            if not reader.fieldnames or "ticker" not in reader.fieldnames:
                raise ValueError(f"{self.tickers_path} must contain a ticker column")
            for row in reader:
                ticker = (row.get("ticker") or "").strip().upper()
                if not ticker:
                    continue
                self._aliases[self._normalize(ticker)] = ticker
                company = (row.get("company") or "").strip()
                if company:
                    self._aliases[self._normalize(company)] = ticker

    def _load_prices(self) -> None:
        with self.prices_path.open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream)
            required = {"ticker", "trade_date", "close"}
            missing = required.difference(reader.fieldnames or [])
            if missing:
                raise ValueError(
                    f"{self.prices_path} is missing columns: {', '.join(sorted(missing))}"
                )
            for row in reader:
                ticker = (row.get("ticker") or "").strip().upper()
                try:
                    trade_date = date.fromisoformat((row.get("trade_date") or "").strip())
                    price_text = (row.get("adj_close") or "").strip() or (row.get("close") or "").strip()
                    price = float(price_text)
                except (ValueError, TypeError):
                    continue
                if ticker and isfinite(price) and price > 0:
                    self._prices.setdefault(ticker, []).append((trade_date, price))
        for series in self._prices.values():
            series.sort(key=lambda item: item[0])

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", value.casefold())

    def canonical_ticker(self, target: str) -> str | None:
        key = self._normalize(target)
        if key in self._aliases:
            return self._aliases[key]
        symbol = target.strip().upper()
        return symbol if symbol in self._prices else None

    def forecast_context(
        self,
        target: str,
        published_at: datetime,
        *,
        horizon_sessions: int = 5,
    ) -> ForecastMarketContext | None:
        if horizon_sessions < 1:
            raise ValueError("horizon_sessions must be at least 1")
        ticker = self.canonical_ticker(target)
        if ticker is None:
            return None
        series = self._prices.get(ticker, [])
        event_date = published_at.date()
        baseline_index = next(
            (index for index in range(len(series) - 1, -1, -1) if series[index][0] < event_date),
            None,
        )
        if baseline_index is None or baseline_index + horizon_sessions >= len(series):
            return None
        baseline_date, baseline = series[baseline_index]
        horizon_end = series[baseline_index + horizon_sessions][0]
        return ForecastMarketContext(ticker, baseline_date, horizon_end, baseline)

    def forecast_context_diagnostic(
        self,
        target: str,
        published_at: datetime,
        *,
        horizon_sessions: int = 5,
    ) -> str:
        """Explain why a forecast context is unavailable without changing resolution."""
        if horizon_sessions < 1:
            raise ValueError("horizon_sessions must be at least 1")
        ticker = self.canonical_ticker(target)
        if ticker is None:
            return f"target {target!r} does not map to a ticker in {self.tickers_path.name}"

        series = self._prices.get(ticker, [])
        event_date = published_at.date()
        baseline_index = next(
            (index for index in range(len(series) - 1, -1, -1) if series[index][0] < event_date),
            None,
        )
        if baseline_index is None:
            return f"no {ticker} price row is strictly earlier than event date {event_date}"

        later_rows = len(series) - baseline_index - 1
        if later_rows < horizon_sessions:
            return (
                f"only {later_rows} later {ticker} price rows are available; "
                f"need {horizon_sessions} to form the horizon"
            )
        return "a forecast market window is available"

    def resolve(self, prediction: Prediction) -> Reality | None:
        if prediction.metrics != ["adjusted_price_return"]:
            raise ValueError("stock-price resolution requires only adjusted_price_return")
        ticker = self.canonical_ticker(prediction.target)
        if ticker is None:
            return None
        prices = dict(self._prices.get(ticker, []))
        actual_value = prices.get(prediction.horizon_end)
        baseline_value = prices.get(prediction.horizon_start)
        if actual_value is None or baseline_value is None or baseline_value <= 0:
            return None
        if prediction.baseline != baseline_value:
            raise ValueError("prediction baseline does not match the market baseline")
        direction = (
            Direction.UP if actual_value > baseline_value
            else Direction.DOWN if actual_value < baseline_value
            else Direction.FLAT
        )
        observed_at = datetime.combine(prediction.horizon_end, time.max, tzinfo=timezone.utc)
        return Reality(
            id=f"reality-{prediction.id}-v{prediction.version}",
            prediction_id=prediction.id,
            target=prediction.target,
            metric="adjusted_price_return",
            baseline=prediction.baseline,
            actual_value=actual_value,
            actual_direction=direction,
            observed_at=observed_at,
            source=self.prices_path.name,
            reasoning=(
                f"Adjusted close on {prediction.horizon_end.isoformat()} compared with "
                f"the baseline on {prediction.horizon_start.isoformat()}. "
                "Driver attribution was not performed: price data alone cannot establish causes."
            ),
        )
