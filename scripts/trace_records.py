#!/usr/bin/env python3
"""Read a replay records.json as a table, or trace one prediction/thesis end to end.

  python3 scripts/trace_records.py data_storage/replays/q1_2026_luna/records.json
  python3 scripts/trace_records.py RECORDS --worst 10
  python3 scripts/trace_records.py RECORDS --ticker MSFT
  python3 scripts/trace_records.py RECORDS --id 3f9a1c            # prediction or thesis id (prefix ok)
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from pathlib import Path


def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {name: data["records"].get(name, {}) for name in
            ("Event", "Thesis", "Prediction", "Reality", "Evaluation", "LLMRun")}


def clip(text: str, width: int, full: bool) -> str:
    text = " ".join(str(text).split())
    return text if full or len(text) <= width else text[: width - 1] + "…"


def pct(value: float) -> str:
    return f"{value * 100:+.1f}%"


def find(records: dict[str, dict], prefix: str) -> tuple[str, dict] | None:
    for kind in ("Prediction", "Thesis"):
        hits = [item for key, item in records[kind].items() if prefix in key]
        if len(hits) == 1:
            return kind, hits[0]
        if len(hits) > 1:
            sys.exit(f"'{prefix}' matches {len(hits)} {kind} ids; use a longer prefix")
    return None


def rows(records: dict) -> list[dict]:
    """One row per prediction, joined with its thesis, reality and evaluation."""
    reality = {item["prediction_id"]: item for item in records["Reality"].values()}
    evaluation = {item["prediction_id"]: item for item in records["Evaluation"].values()}
    out = []
    for pred in records["Prediction"].values():
        thesis = records["Thesis"].get(pred["thesis_id"], {})
        real = reality.get(pred["id"])
        out.append({
            "pred": pred,
            "thesis": thesis,
            "real": real,
            "eval": evaluation.get(pred["id"]),
            "actual": (real["actual_value"] - real["baseline"]) / real["baseline"] if real else None,
            "trigger": trigger_events(records, pred, thesis),
        })
    return sorted(out, key=lambda row: (row["pred"]["horizon_start"], row["thesis"].get("ticker", "")))


def trigger_events(records: dict, pred: dict, thesis: dict) -> list[dict]:
    """Evidence added by the event(s) that produced this prediction (timestamp == information_cutoff)."""
    return [item for item in thesis.get("evidence", []) if item["timestamp"] == pred["information_cutoff"]]


def event_title(records: dict, event_id: str) -> str:
    event = records["Event"].get(event_id)
    return event["title"] if event else f"(event {event_id} not saved)"


def print_table(rows_: list[dict], records: dict, full: bool) -> None:
    print(f"{'#':>3} {'pred':<8} {'tkr':<5} {'v':>1} {'horizon':<11} {'predicted':<12} {'actual':<13} "
          f"{'dir':>3} {'mag':>3} {'mat':>4}  trigger event")
    for index, row in enumerate(rows_, start=1):
        pred, real, ev = row["pred"], row["real"], row["eval"]
        trigger = event_title(records, row["trigger"][-1]["event_id"]) if row["trigger"] else "-"
        horizon = f"{pred['horizon_start'][5:]}→{pred['horizon_end'][5:]}"
        actual = f"{real['actual_direction']} {pct(row['actual'])}" if real else f"({pred['status']})"
        scores = (f"{ev['direction_score']:>3.1f} {ev['magnitude_score']:>3.1f} {ev['matching_score']:>4.2f}"
                  if ev else "  -   -    -")
        print(f"{index:>3} {pred['id'][-6:]:<8} {row['thesis'].get('ticker', '?'):<5} {pred['version']:>1} "
              f"{horizon:<11} {pred['direction'] + ' ' + pct(pred['expected_change_pct']):<12} {actual:<13} "
              f"{scores}  {clip(trigger, 70, full)}")


def section(title: str) -> None:
    print(f"\n── {title} " + "─" * max(0, 76 - len(title)))


def para(label: str, text: str, full: bool, width: int = 100) -> None:
    body = " ".join(str(text).split())
    if not full and len(body) > 400:
        body = body[:399] + "…"
    print(textwrap.fill(f"{label}: {body}", width=width, subsequent_indent="    "))


def print_thesis(records: dict, thesis: dict, cutoff: str | None, full: bool) -> None:
    section(f"THESIS {thesis['id']}  {thesis['ticker']}  {thesis['status']}  strength={thesis['strength']:.2f}")
    para("claim", thesis["core_claim"], full)
    for assumption in thesis["core_assumptions"]:
        para("  assumes", assumption, full)
    if thesis.get("kill_reason"):
        para("killed because", thesis["kill_reason"], full)
    para("reasoning", thesis["reasoning"], full)
    print("\n  evidence timeline (▶ = known when the prediction was made, · = added later):")
    events = [("+", item) for item in thesis["evidence"]] + [("-", item) for item in thesis["counter_evidence"]]
    for sign, item in sorted(events, key=lambda pair: pair[1]["timestamp"]):
        mark = "·" if cutoff and item["timestamp"] > cutoff else "▶"
        print(f"  {mark} {item['timestamp'][:16]} {sign} {clip(event_title(records, item['event_id']), 60, full)}")
        para("        point", item["point"], full, width=110)


def print_trace(records: dict, row: dict, full: bool) -> None:
    pred, real, ev = row["pred"], row["real"], row["eval"]
    print_thesis(records, row["thesis"], pred["information_cutoff"], full)

    versions = sorted((p for p in records["Prediction"].values() if p["thesis_id"] == pred["thesis_id"]),
                      key=lambda p: p["version"])
    section(f"PREDICTION {pred['id']}  v{pred['version']}  {pred['status']}  (thesis has {len(versions)} versions)")
    print(f"  information cutoff: {pred['information_cutoff']}")
    print(f"  horizon:            {pred['horizon_start']} → {pred['horizon_end']}   baseline={pred['baseline']:.2f}")
    print(f"  predicted:          {pred['direction']} {pct(pred['expected_change_pct'])}   confidence={pred['confidence']:.2f}")
    para("  drivers", "; ".join(pred["predicted_drivers"]), full)
    para("  reasoning", pred["reasoning"], full)
    para("  resolves when", "; ".join(pred["resolution_criteria"]), full)
    others = [f"v{p['version']}={p['direction']} {pct(p['expected_change_pct'])} [{p['status']}]"
              for p in versions if p["id"] != pred["id"]]
    if others:
        print("  other versions:     " + ", ".join(others))

    section("REALITY")
    if real is None:
        print("  not resolved yet")
    else:
        print(f"  {real['metric']}: baseline {real['baseline']:.2f} → {real['actual_value']:.2f}  "
              f"= {real['actual_direction']} {pct(row['actual'])}   observed {real['observed_at'][:10]}")
        para("  how", real["reasoning"], full)
        if real.get("actual_drivers"):
            para("  drivers", "; ".join(real["actual_drivers"]), full)

    section("EVALUATION")
    if ev is None:
        print("  none")
        return
    reason = "n/a" if ev["reason_score"] is None else f"{ev['reason_score']:.1f}"
    miss = (pred["expected_change_pct"] - row["actual"]) * 100
    print(f"  direction={ev['direction_score']:.1f}  magnitude={ev['magnitude_score']:.1f}  reason={reason}  "
          f"matching={ev['matching_score']:.2f}   (predicted − actual = {miss:+.1f}pp)")
    para("  LLM explanation", ev["explanation"], full)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("records", type=Path, help="records.json written by app.e2e")
    parser.add_argument("--id", help="prediction or thesis id (substring ok): print the full trace")
    parser.add_argument("--ticker", help="only this thesis ticker")
    parser.add_argument("--worst", type=int, metavar="N", help="the N lowest matching scores")
    parser.add_argument("--full", action="store_true", help="do not truncate long text")
    args = parser.parse_args()

    records = load(args.records)
    all_rows = rows(records)

    if args.id:
        found = find(records, args.id)
        if found is None:
            sys.exit(f"no prediction or thesis matches '{args.id}'")
        kind, item = found
        selected = [row for row in all_rows if row["pred"]["id" if kind == "Prediction" else "thesis_id"] ==
                    item["id"]]
        if not selected:
            print_thesis(records, item, None, args.full)
            print("\n(this thesis has no predictions)")
            return 0
        for row in selected:
            print_trace(records, row, args.full)
        return 0

    if args.ticker:
        all_rows = [row for row in all_rows if row["thesis"].get("ticker", "").upper() == args.ticker.upper()]
    if args.worst:
        scored = [row for row in all_rows if row["eval"]]
        all_rows = sorted(scored, key=lambda row: row["eval"]["matching_score"])[: args.worst]

    runs = records["LLMRun"].values()
    print(f"{len(records['Event'])} events, {len(records['Thesis'])} theses, {len(records['Prediction'])} predictions, "
          f"{len(records['Evaluation'])} evaluations; LLM cost ${sum(run.get('cost_usd') or 0 for run in runs):.4f} "
          f"over {len(records['LLMRun'])} run(s)\n")
    print_table(all_rows, records, args.full)
    if all_rows:
        print("\nTrace one with:  --id <pred column>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
