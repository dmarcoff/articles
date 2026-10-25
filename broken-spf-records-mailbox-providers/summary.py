#!/usr/bin/env python3
"""Print what every receiver did with each SPF case, run by run.

The direct runs (p1, r1, r2) are read from smtp.csv, where the last attempt for each recipient
decides. The Mailgun run (g1) is read from events.csv. Each cell counts recipients:

  A  accepted at SMTP (for g1: delivered)
  R  refused (for g1: failed permanently, including bounces that came after acceptance)
  D  still deferred with a 4xx reply when the run ended (for g1: until Mailgun gave up after 8 hours)

Accepted is not delivered to the mailbox: see glockapps.csv for where each message landed, and
dmarc.csv for each receiver's own verdict.

Usage: python3 summary.py [run ...]     (default: p1 r1 r2 g1)
"""

import collections
import csv
import pathlib
import sys

RESULTS = pathlib.Path(__file__).resolve().parent / "results"


def direct(run):
    last = {}
    with open(RESULTS / run / "smtp.csv", newline="") as f:
        for row in csv.DictReader(f):
            key = (row["case"], row["n"])
            if key not in last or int(row["attempt"]) >= int(last[key]["attempt"]):
                last[key] = row
    cells = collections.defaultdict(collections.Counter)
    for (case, _), row in last.items():
        if row["stage"] == "accepted":
            outcome = "A"
        elif row["code"].startswith("4"):
            outcome = "D"
        else:
            outcome = "R"
        cells[(row["rcpt_domain"], case)][outcome] += 1
    return cells


def mailgun(run):
    events = collections.defaultdict(collections.Counter)
    with open(RESULTS / run / "events.csv", newline="") as f:
        for row in csv.DictReader(f):
            kind = row["event"]
            if kind == "failed":
                kind = "failed_" + (row["severity"] or "unknown")
                if row.get("reason") == "old":  # Mailgun gave up retrying a deferral after 8 hours
                    kind = "failed_old"
            events[(row["rcpt_domain"], row["case"])][kind] += 1
    cells = collections.defaultdict(collections.Counter)
    for key, e in events.items():
        sent, delivered, failed = e["accepted"], e["delivered"], e["failed_permanent"]
        if delivered + failed > sent:  # accepted at SMTP, then bounced
            delivered = sent - failed
        cells[key]["A"] += delivered
        cells[key]["R"] += failed
        cells[key]["D"] += max(sent - delivered - failed, 0)
    return cells


def cell(counter):
    parts = [k for k in "ARD" if counter[k]]
    if len(parts) == 1:
        return parts[0]
    return "".join(f"{k}{counter[k]}" for k in parts)


def show(run):
    cells = mailgun(run) if (RESULTS / run / "events.csv").exists() else direct(run)
    domains = sorted({d for d, _ in cells})
    cases = sorted({c for _, c in cells})
    width = max(len(d) for d in domains) + 2
    print(f"== {run}")
    print("receiver".ljust(width) + "".join(c.rjust(7) for c in cases))
    for d in domains:
        print(d.ljust(width) + "".join(cell(cells[(d, c)]).rjust(7) if (d, c) in cells else "".rjust(7) for c in cases))
    print()


def main():
    for run in sys.argv[1:] or ["p1", "r1", "r2", "g1"]:
        show(run)


if __name__ == "__main__":
    main()
