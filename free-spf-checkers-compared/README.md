# Free SPF checkers compared: data and scripts

Data and scripts behind the DMARKOFF blog article [Free SPF Checkers Compared: What They Get Wrong About Five Real-World SPF Records](https://dmarkoff.com/blog/free-spf-checkers-compared)

The article compares what 10 free SPF checkers report for six public domains with what RFC 7208 says should happen. This folder lets you check the RFC 7208 side yourself. You can recompute every verdict, DNS-querying term count and void-lookup count in the article's reference table with [pySPF](https://pypi.org/project/pyspf/), against the DNS records as they were published during the test (15–20 October 2026).

## Quick start

You need Python 3.11 or later.

```bash
cd free-spf-checkers-compared
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python verify.py
```

The last line should read `14/14 scenarios match the expected results`. The full output is in [results/verify.txt](results/verify.txt).

The run makes no network requests: DNS answers come from [fixtures/dns-2026-10-21.json](fixtures/dns-2026-10-21.json). Add `--live` to check today's DNS through 1.1.1.1 instead. Once a domain changes its records, live results can differ from the article.

## The scenarios

Each row is one SPF check, with MAIL FROM `postmaster@<domain>` and HELO `<domain>`. `192.0.2.1` is a documentation address (RFC 5737) that no record lists. Each of the other IPs is listed somewhere in the domain's record tree. The last two rows evaluate a candidate fix from the article instead of the published record.

| Sender IP | Domain | Result | DNS-querying terms | Void lookups | Why |
|---|---|---|---|---|---|
| 192.0.2.1 | gitlab.com | permerror | 11 | 1 | The 11th DNS-querying term, `include:_spf2.mailgun.org`, is over the limit of 10 |
| 209.85.128.1 | gitlab.com | pass | 2 | 0 | Google, matched in `_spf.google.com` |
| 67.212.179.10 | gitlab.com | permerror | 11 | 1 | Listed in `_spf.sendergen.com`, which evaluation never reaches |
| 192.0.2.1 | sisley.fr | permerror | 2 | 1 | `include:mailer1.eu.threatsim.com` has no TXT records |
| 37.71.118.23 | sisley.fr | pass | 1 | 0 | `ip4`, listed before the broken include |
| 192.0.2.1 | korben.info | softfail | 4 | 2 | Two `ptr` terms in OVH's record, no reverse DNS for the sender |
| 8.33.137.105 | korben.info | pass | 3 | 0 | OVH's `ip4` |
| 50.31.98.110 | project7.com | fail | 8 | 0 | `ip4=50.31.98.110` is an unknown modifier, so it's ignored |
| 192.0.2.1 | turnlss.com | permerror | 8 | 3 | 3rd void lookup, at `exists:%{i}._spf.corp.salesforce.com` |
| 40.92.0.1 | turnlss.com | pass | 1 | 0 | Microsoft 365 |
| 209.85.128.1 | turnlss.com | pass | 5 | 1 | Google, through salesforce.com's corporate record |
| 192.0.2.1 | google.com | softfail | 1 | 0 | Control |
| 209.85.128.1 | turnlss.com, candidate without `include:salesforce.com` | softfail | 3 | 1 | Dropping that include also drops Google |
| 50.31.98.110 | project7.com, candidate with `ip4:50.31.98.110` | pass | 8 | 0 | Typo fixed |

"DNS-querying terms" is pySPF's lookup counter. It includes the term at which evaluation stops, so the gitlab.com rows count the 11th term, which is never queried. A void lookup is a DNS query that returns no records; the TXT query for an include target counts too. RFC 7208 §4.6.4 recommends a limit of two void lookups, which is pySPF's default.

## Tracing a check

`verify.py` gives the verdicts. To see how a check gets there, `trace_spf.py` prints every DNS-querying term, void lookup and match:

```bash
.venv/bin/python trace_spf.py eval 192.0.2.1 turnlss.com
```

```
turnlss.com: "v=spf1 include:spf.protection.outlook.com include:_spf.salesforce.com include:salesforce.com include:_spf.wpengine.com ~all"
[term 1] include:spf.protection.outlook.com
  spf.protection.outlook.com: "v=spf1 ip4:40.92.0.0/15 ip4:40.107.0.0/16 ip4:52.100.0.0/15 ip4:52.102.0.0/16 ip4:52.103.0.0/17 ip4:104.47.0.0/17 ip6:2a01:111:f400::/48 ip6:2a01:111:f403::/49 ip6:2a01:111:f403:8000::/51 ip6:2a01:111:f403:c000::/51 ip6:2a01:111:f403:f000::/52 -all"
    MATCH -all -> fail
[term 2] include:_spf.salesforce.com
  _spf.salesforce.com: "v=spf1 exists:%{i}._spf.mta.salesforce.com -all"
  [term 3] exists:%{i}._spf.mta.salesforce.com
    exists -> 192.0.2.1._spf.mta.salesforce.com A: NXDOMAIN []
    void lookup #1 (NXDOMAIN for 192.0.2.1._spf.mta.salesforce.com)
    MATCH -all -> fail
[term 4] include:salesforce.com
  salesforce.com: "v=spf1 include:_spf.google.com include:_spf.salesforce.com exists:%{i}._spf.corp.salesforce.com ~all"
  [term 5] include:_spf.google.com
    _spf.google.com: "v=spf1 ip4:74.125.0.0/16 ip4:209.85.128.0/17 ip6:2001:4860:4864::/56 ip6:2404:6800:4864::/56 ip6:2607:f8b0:4864::/56 ip6:2800:3f0:4864::/56 ip6:2a00:1450:4864::/56 ip6:2c0f:fb50:4864::/56 ~all"
      MATCH ~all -> softfail
  [term 6] include:_spf.salesforce.com
    _spf.salesforce.com: "v=spf1 exists:%{i}._spf.mta.salesforce.com -all"
    [term 7] exists:%{i}._spf.mta.salesforce.com
      exists -> 192.0.2.1._spf.mta.salesforce.com A: NXDOMAIN []
      void lookup #2 (NXDOMAIN for 192.0.2.1._spf.mta.salesforce.com)
      MATCH -all -> fail
  [term 8] exists:%{i}._spf.corp.salesforce.com
    exists -> 192.0.2.1._spf.corp.salesforce.com A: NXDOMAIN []
    void lookup #3 (NXDOMAIN for 192.0.2.1._spf.corp.salesforce.com)
PERMERROR: void lookup limit: 3 void lookups (recommended limit 2)
RESULT: permerror | DNS-querying terms reached 8 | void lookups 3
```

Other modes:

- `trace_spf.py static gitlab.com` lists every DNS-querying term in the record tree in order, 13 for gitlab.com. It also prints the RFC 7208 §3.4 size measure (domain name plus the text of all TXT records) from the article's record-size section.
- `trace_spf.py static gitlab.com --record "v=spf1 ..."` does the same for a draft record. The article's gitlab.com draft without the Zuora `a:` term comes out at 12.
- `trace_spf.py all` traces every scenario and walks each domain's tree. Its output is [results/trace.txt](results/trace.txt).

The tracer is a reading aid, not a full SPF implementation. It reads the same fixture as `verify.py`, and on all 14 scenarios it matches pySPF's result, term count and void count.

## What's in this folder

| Path | Contents |
|---|---|
| `verify.py` | Runs the scenarios through pySPF and checks each result and void count against `scenarios.json` |
| `scenarios.json` | Sending IP, domain, optional candidate record, expected result and void lookups |
| `trace_spf.py` | Step-by-step RFC 7208 trace |
| `spfdns.py` | DNS layer shared by both scripts: replays the fixture or queries 1.1.1.1 |
| `fixtures/dns-2026-10-21.json` | Every DNS answer the scripts need |
| `results/` | Output of `verify.py` and `trace_spf.py all` |
| `data/dns-snapshot-2026-10-15.txt`, `data/dns-snapshot-2026-10-20.txt` | Every TXT record along each SPF chain, captured through 1.1.1.1 at the start and at the end of the test window with `trace_spf.py dump` (needs `dig`) |
| `data/dmarkoff-api/` | Raw responses from DMARKOFF's SPF checker for the six domains and for the draft records in the article, listed in `2026-10-20/drafts/drafts.tsv` |
| `screenshots/` | The 20 screenshots used in the article, with the same file names |

## About the DNS data

The fixture was recorded through 1.1.1.1 on 21 October 2026, the day after the test window closed, with `verify.py --live --save` and `trace_spf.py all --live --save`. Every TXT answer in it is identical to the 20 October capture. The 15 October capture differs only by two extra, unrelated TXT records at sisley.fr (55 → 57), which affect only the record-size figure; the article notes this change.

The captures hold TXT records only. The fixture's A and PTR answers come from 21 October: reverse DNS for the test IPs, the addresses of `zgateway.zuora.com` and the Salesforce `exists` lookups.

To record a fresh fixture and check against it:

```bash
.venv/bin/python verify.py --live --save fixtures/my-dns.json
.venv/bin/python trace_spf.py all --live --save fixtures/my-dns.json
.venv/bin/python verify.py --fixture fixtures/my-dns.json
```

## Notes

- The checkers in the article were run on the domain name alone and don't evaluate a specific sender. The sender IPs here pin down what RFC 7208 implies for each record: does it work, and if not, where does it break.
- For the article, the sender-specific verdicts were also confirmed with Kitterman's web tester, which runs pySPF with its own DNS resolver.
- We don't republish the page text we captured from other vendors' checkers. The screenshots are what the article shows.

## How to cite

The article:

> Markau, A. (2026, October 23). *Free SPF Checkers Compared: What They Get Wrong About Five Real-World SPF Records*. DMARKOFF blog. https://dmarkoff.com/blog/free-spf-checkers-compared

This folder:

> Markau, A., & DMARKOFF. (2026). *Free SPF checkers compared: data and scripts* [Data set]. GitHub. https://github.com/dmarcoff/articles/tree/main/free-spf-checkers-compared

The scripts are under the MIT License and the rest under CC BY 4.0, except third-party content; see [License](../README.md#license).
