#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

mkdir -p data_storage/replays/q1_luna
mkdir -p data_storage/replays/q2_luna

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Replay for 2025-Q1..."
./.venv/bin/python -u -m app.e2e \
  --events data/events_by_quarter/2025-Q1.csv \
  --tickers data/stock_tickers.csv \
  --start-date 2025-01-01 \
  --end-date 2025-03-31 \
  --data-dir data_storage/replays/q1_luna \
  --openai \
  --model gpt-5.6-luna >> data_storage/replays/q1.log 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Completed Replay for 2025-Q1. Starting 2025-Q2..."
./.venv/bin/python -u -m app.e2e \
  --events data/events_by_quarter/2025-Q2.csv \
  --tickers data/stock_tickers.csv \
  --start-date 2025-04-01 \
  --end-date 2025-06-30 \
  --data-dir data_storage/replays/q2_luna \
  --openai \
  --model gpt-5.6-luna >> data_storage/replays/q2.log 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] All replays completed successfully!"
