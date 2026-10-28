# SPF and DMARC in the Tranco top 100,000: data

Aggregate tables behind the DMARKOFF blog article [SPF and DMARC in the Tranco Top 100,000: Our October 2026 DNS Snapshot](https://dmarkoff.com/blog/spf-dmarc-top-100k-domains-2026).

On 27 October 2026 we queried the DNS of the first 100,000 domains of the Tranco list [W3ZV9](https://tranco-list.eu/list/W3ZV9/1000000) for SPF, DMARC and its reporting addresses, MX, MTA-STS, TLS-RPT, BIMI and DNSSEC. 99,441 domains were analyzed. This folder holds every count the article quotes or charts, the queries that produced them and the list we used to match DMARC reporting addresses to organizations.

We publish aggregates only. Per-domain results stay private: some of them show misconfigurations that could be abused, such as SPF includes of domains anyone could register.

## Quick start

You need Python 3.9 or later; there are no dependencies.

```bash
cd spf-dmarc-top-100k-domains-2026
python3 summary.py
```

It prints every share in the article with its numerator and denominator. The output is in [summary.txt](summary.txt).

## Definitions

- **Analyzed domains:** the 99,441 domains whose checks finished without a timeout or a temporary DNS failure (SERVFAIL or a timeout), on the first try or on the retry. NXDOMAIN and empty answers count as answers. The 559 others are left out of every table.
- **Rank groups:** ranks 1 to 1,000, 1,001 to 10,000 and 10,001 to 100,000 in the Tranco list.
- **Non-null MX:** at least one MX record that isn't a null MX (RFC 7505). It's a DNS-defined subset, not a list of domains that send mail.
- **SPF lookups:** DNS-querying terms on the longest evaluation path, the one a receiver walks for a sender that matches no mechanism, nested includes and `redirect` included, counted past 10. Macros are expanded for a placeholder sender. The include costs in `spf_includes_top50.csv` count the include term itself plus everything it pulls in, as published on the scan day.
- **DMARC record:** found with the DNS tree walk of RFC 9989. A record found only in the domain's own TXT records, with nothing at `_dmarc`, is *misplaced*. A `p=` value receivers don't recognize is *malformed*. Legacy tags such as `pct` are reported as published.
- **Reporting addresses:** each `rua` address is grouped by its organizational domain under the Public Suffix List. *Own* means the same organizational domain as the policy domain; anything else is *outside*. Outside addresses are checked for the authorization record of RFC 9990, section 4 (`<policy domain>._report._dmarc.<report domain>`, wildcards included).
- **Outside destinations** are matched to organizations with [rua-organizations.csv](rua-organizations.csv): 108 organizational domains, each a DMARC `vendor`, an `in-house` sister domain (such as youtube.com reporting to google.com), a `government` collector or personal `mailbox` addresses at a mailbox provider. Organizations not in the list are *unidentified*. A domain with several addresses can fall into several groups.
- **BIMI:** the record at the default selector; the mark certificate from its `a=` URL, one per domain, with the expiry date read from the certificate itself.

## Files

All files are in [data/](data/). Counts are domains unless the column says otherwise.

| File | In the article | Columns |
|---|---|---|
| `populations.csv` | lead, key numbers, first table | `group` (analyzed, non_null_mx, no_mx, null_mx), domains with SPF, with a DMARC record, with `p=reject` or `p=quarantine` |
| `rank_groups.csv` | rank group table | analyzed domains, non-null MX, one SPF record, two or more, DMARC record at `_dmarc`, misplaced DMARC record, BIMI record |
| `counts.csv` | single figures | `measure`, `value`, `note` |
| `spf_lookups.csv` | Figure 1 | single SPF records by lookups; `20+` is 20 or more |
| `spf_over_limit_by_rank.csv` | SPF section | single SPF records, how many need more than 10 lookups, median lookups |
| `spf_permerror_checks.csv` | Figure 2 | `scope` (`record`: the record itself is broken; `evaluation`: it fails while evaluated), the checker's `failed_check` id, a description; a domain can fail more than one check |
| `spf_all_terms.csv` | SPF section | single SPF records by `all` term (`none` for no `all`), with `ptr`, with more than two void lookups |
| `spf_includes_top50.csv` | include cost table | the 50 includes found on the most domains, and the lookups each costs |
| `spf_missing_include_targets.csv` | "Includes that point nowhere" | domains with an include or redirect target that returned NXDOMAIN, by what its registrable domain is: `registered`, `unregistered` (doesn't resolve while its suffix does), `no-such-suffix`, `malformed` (not a host name), `unknown`; `names` is distinct target names |
| `dmarc_policy_by_rank_mx.csv` | Figure 3 | domains with a non-null MX by rank group and policy (`no_record` for no DMARC record) |
| `dmarc_policy_by_rank_all.csv` | not charted | the same for all analyzed domains |
| `dmarc_malformed_p.csv` | DMARC section | malformed `p=` values as written, lowercased |
| `dmarc_enforcing.csv` | DMARC section | domains with `p=reject` or `p=quarantine` by their `sp` value (a missing `sp` counts as the `p` value), legacy `pct` below 100 and `pct=0`, and SPF `permerror` on the domain itself by scope |
| `dmarc_pct_below_100.csv` | DMARC section | DMARC records by `pct` value, for values below 100 |
| `rua_by_rank.csv` | Figure 4 | domains with a DMARC record by rank group and where their `rua` addresses point |
| `dmarc_policy_by_rua.csv` | Figure 5 | domains with a DMARC record by whether they have a `rua` address, and policy |
| `rua_outside_kinds.csv` | reporting section | domains with outside addresses by kind of destination; groups overlap |
| `rua_authorization_mailboxes.csv` | reporting section | outside addresses at mailbox providers, and how many lack the authorization record |
| `rua_vendors_top12.csv` | Figure 6 | the 12 vendors with the most domains; the denominator is the `vendor` row of `rua_outside_kinds.csv` |
| `rua_vendor_count.csv` | reporting section | domains with vendor addresses by the number of distinct vendors |
| `spf_permerror_by_rua.csv` | Figure 7 | analyzed domains by reporting address group: domains, with at least one SPF record, with SPF `permerror` |
| `spf_permerror_by_rua_rank.csv` | Figure 7 text | the same for four groups by rank group |
| `mail_records_mx.csv` | Figure 8 | domains with a non-null MX publishing each record; `dnssec` is a signed delegation (a DS record in the parent zone), `dnssec_bogus` signed but failing validation |
| `mta_sts_modes.csv` | MTA-STS paragraph | domains with an MTA-STS record by the mode of the policy they serve, and how many publish TLS-RPT |
| `bimi_certificates.csv` | Figure 9 | mark certificates by type (`VMC`, `CMC`) and time to expiry on the scan day |
| `bimi_by_dmarc.csv` | BIMI paragraph | BIMI records by the domain's DMARC, and how many have a certificate |

## Queries

[queries.sql](queries.sql) holds the ClickHouse queries every table comes from, as we ran them on scan `full-100k` (`clickhouse-client --param_scan_id=full-100k`). The scanner and its tables aren't published; the comment above each query says what it reads.

## Missing include targets

The 14 registrable domains in the `unregistered` row of `spf_missing_include_targets.csv` were checked by hand with RDAP and registry WHOIS on 28 October 2026:

| Result | Registrable domains |
|---|---|
| registered, but not resolving (held or without name servers) | 5 |
| in a zone the public can't register in (`gov.sg`, `ne.jp`) | 3 |
| reserved by the registry | 1 |
| in its redemption period | 1 |
| no registration in the registry's WHOIS | 2 |
| no answer from the ccTLD registry | 2 |

Each is included by one domain. We don't publish the names.

## Caveats

- One snapshot: DNS on 27 October 2026, 20:48 to 21:10 UTC.
- The Tranco list ranks domains by popularity signals such as traffic, not by mail volume.
- The scan reads published DNS configuration. It doesn't show which identities real mail uses, delivery outcomes, or whether DMARC reports are received or read.
- 7,284 domains report to organizations we couldn't identify, so vendor counts are floors. They count domains, not customers, revenue or mail volume.
