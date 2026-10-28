#!/usr/bin/env python3
"""Print every share quoted in the article, computed from the CSV files in data/.

Usage: python3 summary.py
"""
import csv
import os

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
RANKS = ["1-1000", "1001-10000", "10001-100000"]


def rows(name):
    with open(os.path.join(DATA, name + ".csv"), newline="") as f:
        return list(csv.DictReader(f))


def by(name, *keys, value="domains"):
    """Map the key columns of a CSV (a tuple when there are several) to an integer column."""
    out = {}
    for r in rows(name):
        k = tuple(r[c] for c in keys)
        out[k[0] if len(k) == 1 else k] = int(r[value])
    return out


def pct(n, d):
    return f"{100 * n / d:.1f}%"


def line(label, n, d):
    print(f"  {label:<46} {n:>7,} of {d:>7,}  {pct(n, d):>6}")


def main():
    pop = {r["group"]: {k: int(v) for k, v in r.items() if k != "group"} for r in rows("populations")}
    counts = by("counts", "measure", value="value")

    print("Populations")
    for g in ("analyzed", "non_null_mx", "no_mx", "null_mx"):
        p = pop[g]
        print(f"  {g:<12} {p['domains']:>6,} domains: SPF {pct(p['with_spf'], p['domains'])}, "
              f"DMARC {pct(p['with_dmarc'], p['domains'])}, reject or quarantine {pct(p['reject_or_quarantine'], p['domains'])}")
    mx = pop["non_null_mx"]
    line("DMARC domains with MX that enforce", mx["reject_or_quarantine"], mx["with_dmarc"])

    print("\nSPF lookups (single SPF records, longest evaluation path)")
    hist = by("spf_lookups", "lookups")
    total = sum(hist.values())
    over = sum(v for k, v in hist.items() if k == "20+" or int(k) > 10)
    line("more than 10 lookups", over, total)
    line("9 or 10 lookups", hist["9"] + hist["10"], total)
    for r in rows("spf_over_limit_by_rank"):
        line(f"over the limit, ranks {r['rank_group']}", int(r["over_limit"]), int(r["single_spf_records"]))
    allt = by("spf_all_terms", "all_term")
    for term in ("~all", "-all", "?all", "+all", "none"):
        line(f"all term {term}", allt[term], total)
    print(f"  no all term: {counts['spf_records_without_all_with_redirect']:,} end in a redirect, "
          f"{counts['spf_records_without_all_or_redirect']:,} don't")

    print("\nDMARC policy by rank, domains with a non-null MX")
    pol = by("dmarc_policy_by_rank_mx", "rank_group", "policy")
    for rk in RANKS:
        n = sum(v for (r, _), v in pol.items() if r == rk)
        line(f"ranks {rk}: reject or quarantine", pol[(rk, "reject")] + pol[(rk, "quarantine")], n)
        line(f"ranks {rk}: no DMARC record", pol[(rk, "no_record")], n)

    print("\nDMARC details (all analyzed domains)")
    enf = {r["policy"]: {k: int(v) for k, v in r.items() if k != "policy"} for r in rows("dmarc_enforcing")}
    enforcing = sum(e["domains"] for e in enf.values())
    line("enforcing domains with sp=none", sum(e["sp_none"] for e in enf.values()), enforcing)
    print(f"  pct below 100: {sum(by('dmarc_pct_below_100', 'pct').values()):,} domains, "
          f"{by('dmarc_pct_below_100', 'pct')['0']:,} with pct=0, "
          f"{sum(e['pct_below_100'] for e in enf.values()):,} of them enforcing")
    print(f"  enforcing with SPF permerror: {sum(e['spf_permerror_record'] + e['spf_permerror_evaluation'] for e in enf.values()):,}")
    print(f"  malformed p= values: {sum(by('dmarc_malformed_p', 'p_value').values())}, "
          f"misplaced records: {sum(int(r['dmarc_record_misplaced']) for r in rows('rank_groups'))}")

    print("\nReporting addresses (domains with a DMARC record)")
    rua = by("rua_by_rank", "rank_group", "rua")
    dmarc = sum(rua.values())
    outside = sum(v for (_, k), v in rua.items() if k in ("outside_only", "own_and_outside"))
    line("at least one outside address", outside, dmarc)
    line("own domain only", sum(v for (_, k), v in rua.items() if k == "own_only"), dmarc)
    line("no rua", sum(v for (_, k), v in rua.items() if k == "no_rua"), dmarc)
    for rk in RANKS:
        n = sum(v for (r, _), v in rua.items() if r == rk)
        line(f"ranks {rk}: outside address", rua[(rk, "outside_only")] + rua[(rk, "own_and_outside")], n)
    bypol = by("dmarc_policy_by_rua", "rua", "policy")
    for r in ("none", "at_least_one"):
        n = sum(v for (k, _), v in bypol.items() if k == r)
        line(f"rua {r}: p=none", bypol[(r, "none")], n)
    line("outside addresses not authorized", counts["outside_rua_unauthorized"], counts["domains_with_outside_rua"])
    kinds = by("rua_outside_kinds", "kind")
    vendor = kinds["vendor"]
    for v, n in by("rua_vendors_top12", "vendor").items():
        line(f"vendor {v}", n, vendor)
    vc = by("rua_vendor_count", "vendors")
    line("two or more vendors", sum(n for k, n in vc.items() if int(k) >= 2), sum(vc.values()))

    print("\nSPF permerror by reporting address (domains with SPF)")
    for r in rows("spf_permerror_by_rua"):
        line(r["rua"], int(r["spf_permerror"]), int(r["with_spf"]))
    for r in rows("spf_permerror_by_rua_rank"):
        line(f"{r['rua']}, ranks {r['rank_group']}", int(r["spf_permerror"]), int(r["with_spf"]))

    print("\nOther records, domains with a non-null MX")
    rec = by("mail_records_mx", "record")
    for k in ("dnssec", "bimi_record", "bimi_certificate", "tls_rpt", "mta_sts_record"):
        line(k, rec[k], rec["non_null_mx"])
    modes = by("mta_sts_modes", "mode")
    print(f"  MTA-STS modes: " + ", ".join(f"{k} {v:,}" for k, v in modes.items()))

    print("\nBIMI")
    bd = by("bimi_by_dmarc", "dmarc", value="bimi_records")
    line("records not meeting Gmail's DMARC requirement", sum(v for k, v in bd.items() if k != "enforcing"), sum(bd.values()))
    certs = by("bimi_certificates", "certificate_type", "state")
    line("certificates expired", sum(v for (_, s), v in certs.items() if s == "expired"), sum(certs.values()))
    line("certificates expiring within 30 days", sum(v for (_, s), v in certs.items() if s == "within_30_days"), sum(certs.values()))


if __name__ == "__main__":
    main()
