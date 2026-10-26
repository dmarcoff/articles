#!/usr/bin/env python3
"""Print the refusal and bounce counts behind the follow-up article, "What the Bounce Says".

Direct runs (p1, r1, r2) come from smtp.csv: each message (one case sent to one recipient) is
counted once, by its last attempt. A permanent refusal counts as about the IP when its text names
our address, a blocklist or a dynamic-IP policy; every other permanent refusal answered SPF or
DMARC. The Mailgun run (g1) comes from events.csv, with Mailgun's own reason for each failure.

Usage: python3 bounces.py
"""

import collections
import csv
import datetime
import pathlib
import re

RESULTS = pathlib.Path(__file__).resolve().parent / "results"
IP_REFUSAL = re.compile(r"Spamhaus|PBL|TSS09|Nemesis|Dialup|blacklisted|Abusix|dynamic IP", re.I)


def ts(value):
    return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))


def direct():
    outcome = collections.Counter()
    stage = collections.defaultdict(collections.Counter)
    temporary = collections.Counter()
    attempts, spans = collections.Counter(), []
    for run in ("p1", "r1", "r2"):
        tries = collections.defaultdict(list)
        with open(RESULTS / run / "smtp.csv", newline="") as f:
            for row in csv.DictReader(f):
                tries[(row["case"], row["n"])].append(row)
                if row["code"].startswith("4"):
                    temporary[(row["rcpt_domain"], row["code"], row["reply"][:60])] += 1
        for rows in tries.values():
            rows.sort(key=lambda r: int(r["attempt"]))
            last = rows[-1]
            if len(rows) > 1:
                attempts[len(rows)] += 1
                spans.append((ts(rows[-1]["time"]) - ts(rows[0]["time"])).total_seconds() / 60)
            if last["code"] == "250":
                kind = "accepted"
            elif last["code"].startswith("4") or not last["code"]:
                kind = "deferred or cut off when retries stopped"
            elif IP_REFUSAL.search(last["reply"]):
                kind = "refused for the IP"
            else:
                kind = "refused on SPF or DMARC"
            outcome[kind] += 1
            if kind.startswith("refused"):
                stage[kind][last["stage"]] += 1
    print("== Direct path (p1, r1, r2): messages by how they ended")
    print(f"{'messages':45}{sum(outcome.values()):>6}")
    for kind in ("accepted", "refused for the IP", "refused on SPF or DMARC",
                 "deferred or cut off when retries stopped"):
        detail = ", ".join(f"{s} {n}" for s, n in stage[kind].most_common())
        print(f"{kind:45}{outcome[kind]:>6}" + (f"   ({detail})" if detail else ""))
    print(f"\nretried messages by number of attempts: {dict(sorted(attempts.items()))}; "
          f"longest span {max(spans):.0f} min")
    print("\ntemporary replies (attempts), most frequent:")
    for (domain, code, reply), n in temporary.most_common(10):
        print(f"{n:>5}  {domain:22} {code} {reply}")


def mailgun():
    events = collections.defaultdict(list)
    with open(RESULTS / "g1" / "events.csv", newline="") as f:
        for row in csv.DictReader(f):
            events[(row["case"], row["rcpt_domain"])].append(row)
    accepted = sum(1 for rows in events.values() for r in rows if r["event"] == "accepted")
    reasons = collections.Counter()
    by_reason = collections.defaultdict(collections.Counter)
    temporary = 0
    late, schedules = [], []
    for (case, domain), rows in events.items():
        rows.sort(key=lambda r: r["time"])
        for r in rows:
            if r["event"] != "failed":
                continue
            if r["severity"] == "temporary":
                temporary += 1
                continue
            reasons[r["reason"]] += 1
            by_reason[r["reason"]][domain] += 1
        # A bounce that arrives after acceptance reaches Mailgun as a DSN, whose reply it prefixes
        # with "smtp;"; pair it with the last delivery before it.
        for r in rows:
            if r["event"] == "failed" and r["reply"].startswith("smtp;"):
                prior = [d for d in rows if d["event"] == "delivered" and d["time"] <= r["time"]]
                if prior:
                    late.append((ts(r["time"]) - ts(prior[-1]["time"])).total_seconds())
        if any(r["reason"] == "old" for r in rows):
            start = ts(next(r["time"] for r in rows if r["event"] == "accepted"))
            schedules.append((case, domain, [round((ts(r["time"]) - start).total_seconds() / 60)
                                             for r in rows if r["event"] == "failed"]))
    print("\n== Mailgun run (g1)")
    print(f"messages accepted by Mailgun: {accepted}")
    print(f"permanent failures: {sum(reasons.values())} {dict(reasons)}")
    print(f"temporary failures (attempts): {temporary}")
    print(f"delivered, then failed by a later bounce: {len(late)} messages, "
          f"{min(late):.1f} to {max(late):.1f} s after delivery")
    for reason in ("espblock", "generic", "old"):
        print(f"\n{reason} by recipient domain: " +
              ", ".join(f"{d} {n}" for d, n in sorted(by_reason[reason].items())))
    print("\nretries before Mailgun gave up (minutes after the first attempt):")
    for case, domain, minutes in schedules:
        print(f"  {case} {domain}: {minutes}")


if __name__ == "__main__":
    direct()
    mailgun()
