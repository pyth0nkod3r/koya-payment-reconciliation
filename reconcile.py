#!/usr/bin/env python3
"""Payment reconciliation.

Reads payments.jsonl and works out how much money we actually collected.
Run:  python3 reconcile.py

Rules (per README):
- Only the LATEST attempt (by `ts`) for each `txn_id` counts.
- A payment is collected only if that latest attempt is `success`.
- Ignore lines that can't be parsed and events without a `txn_id`.
"""
import json
from datetime import datetime, timezone


def parse_amount(value):
    """Amount may be a number or a string like \"4,804.15\"."""
    if isinstance(value, str):
        value = value.replace(",", "").strip()
    return float(value)


def parse_ts(value):
    """Parse an ISO-8601 UTC timestamp like 2026-09-21T15:30:26Z."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


latest = {}  # txn_id -> (ts, event)

with open("payments.jsonl") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if not isinstance(event, dict):
            continue
        txn_id = event.get("txn_id")
        if not txn_id:
            continue
        ts = parse_ts(event["ts"])
        if txn_id not in latest or ts > latest[txn_id][0]:
            latest[txn_id] = (ts, event)

total = 0.0
count = 0
for _ts, event in latest.values():
    if event.get("status") == "success":
        total += parse_amount(event["amount"])
        count += 1

with open("expected.txt") as f:
    expected = int(f.read().strip())

if count != expected:
    print(f"Check failed: counted {count} successful payments, expected {expected}.")
    print("Something in the data isn't being handled the way the README describes.")
else:
    print(f"Check passed: {count} successful payments.")
    print(f"Your code: KOYA-{round(total)}")
