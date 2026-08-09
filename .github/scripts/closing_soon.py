#!/usr/bin/env python3
"""
closing_soon.py — flag opportunities closing within CLOSING_SOON_DAYS as 🔥 [CLOSING SOON].

Scans every <!-- *_TABLE_START --> ... <!-- *_TABLE_END --> region in README.md.
For each row with status ✅ [OPEN] or 🔥 [CLOSING SOON]:
  - Find the earliest upcoming date in the row
  - If 0–CLOSING_SOON_DAYS days away: flip status to 🔥 [CLOSING SOON]
  - If further out: flip status back to ✅ [OPEN]
  - If every date in the row has already passed: clear a stale 🔥 badge back to
    ✅ [OPEN] and report the row as expired, so the weekly audit can archive it
  - If no date at all (rolling postings): leave alone

[OPENS SOON] and [CLOSED] rows are never modified.
Idempotent — safe to run daily.

The closing-soon window lives in util.CLOSING_SOON_DAYS, shared with
update_readmes.py so badge and row ordering can never disagree.
"""

import os
import re
from datetime import datetime

import util

PST = util.PST
README = os.path.join(os.path.dirname(__file__), "..", "..", "README.md")

OPEN = "✅ **[OPEN]**"
CLOSING = "🔥 **[CLOSING SOON]**"

TABLE_RE = re.compile(r"(<!-- \w+_TABLE_START -->)(.*?)(<!-- \w+_TABLE_END -->)", re.DOTALL)


def row_label(row):
    """'Organization — Opportunity' for reporting, from a markdown table row."""
    cells = [c.strip() for c in row.split("|")]
    return f"{cells[2]} — {cells[3]}" if len(cells) > 3 else row.strip()[:60]


def update_row(row, today):
    """Return (new_row, changed, expired_label)."""
    has_open = OPEN in row
    has_closing = CLOSING in row
    if not (has_open or has_closing):
        return row, False, None

    # Exclude the trailing "Date Posted" column from deadline detection — a row
    # posted today renders its post-date as "today", which would otherwise be
    # read as a 0-days-away deadline and wrongly flip the row to CLOSING SOON.
    cells = row.split("|")
    scan_text = "|".join(cells[:-2]) if len(cells) >= 3 else row

    deadline = util.earliest_upcoming(scan_text, today)
    if not deadline:
        # No upcoming date. If the row does carry dates and they have all passed,
        # a 🔥 badge is stale and actively misleading — clear it and report the
        # row so it can be archived. Rows with no dates at all are rolling
        # postings and are left untouched.
        if has_closing and util.find_dates(scan_text):
            return row.replace(CLOSING, OPEN, 1), True, row_label(row)
        return row, False, None

    days_until = (deadline.date() - today.date()).days
    target = CLOSING if 0 <= days_until <= util.CLOSING_SOON_DAYS else OPEN
    current = CLOSING if has_closing else OPEN
    if target == current:
        return row, False, None
    return row.replace(current, target, 1), True, None


def process_table_body(body, today):
    lines = body.split("\n")
    changed = 0
    expired = []
    for i, line in enumerate(lines):
        if not line.startswith("| "):
            continue
        if "Status |" in line or re.match(r"\|\s*-+", line):
            continue
        new_line, did, expired_label = update_row(line, today)
        if did:
            lines[i] = new_line
            changed += 1
        if expired_label:
            expired.append(expired_label)
    return "\n".join(lines), changed, expired


def main():
    with open(README, "r") as f:
        content = f.read()

    today = datetime.now(tz=PST)
    total = 0
    expired = []

    def replace(m):
        nonlocal total
        new_body, n, exp = process_table_body(m.group(2), today)
        total += n
        expired.extend(exp)
        return m.group(1) + new_body + m.group(3)

    new_content = TABLE_RE.sub(replace, content)

    if new_content != content:
        with open(README, "w") as f:
            f.write(new_content)

    print(f"Updated {total} row(s) (window: {util.CLOSING_SOON_DAYS} days).")
    if expired:
        print(f"{len(expired)} row(s) have a passed deadline and should be archived:")
        for label in expired:
            print(f"  - {label}")

    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a") as f:
            f.write(f"changes={total}\n")
            f.write(f"expired={len(expired)}\n")


if __name__ == "__main__":
    main()
