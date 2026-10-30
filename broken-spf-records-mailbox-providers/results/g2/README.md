# Mailgun run g2 (2026-10-29)

How far past 10 DNS lookups Gmail and Yahoo go. In g1, Gmail and the Yahoo family passed m02, Mailgun's
include after 11 includes that match nothing, while Microsoft and Apple refused it; a reader of the
article asked how far that goes. The cases of `experiments/spf-mailgun-limit` were sent once each
through Mailgun's shared IPs (US region) to 19 GlockApps seeds (project 6): 18 tracked seeds (5 Gmail,
2 Google Workspace, 3 Yahoo, 2 AOL, 1 AT&T, 2 Outlook, 2 Hotmail, 1 Apple) and GlockApps' own monitor,
which accepts every message and reports no placement (`spamassassin-filter.seed.example` in the
published copy), so it says nothing about SPF.
DKIM off, as in g1; Mailgun added its own `d=mailgun.org` signature to the mail for Gmail and the Yahoo
family, which doesn't align.

Every Mailgun IP that sent this run is listed in `_spf1.mailgun.org`, so a receiver needs N+2 lookups
to reach the sender: N includes that match nothing, then `_spf.mailgun.org` and `_spf1.mailgun.org`.
m01 and m02 are the same domains and records as in g1. m13 to m16 are new domains, verified in
Mailgun and given their case records before the run; `dns.json` holds the records as public DNS
served them right before sending.

| Case | Record | Lookups to the sender | Sent (UTC) | GlockApps test |
|---|---|---|---|---|
| m14 | 20 includes, then Mailgun | 22 | 13:02 | 2026-10-29-13:01:30:553t |
| m01 | `include:_spf.mailgun.org` (control) | 2 | 13:03 | 2026-10-29-13:01:27:885t |
| m16 | 732 characters of `ip4:` in 192.0.2.0/24, then Mailgun | 2 | 13:04 | 2026-10-29-13:01:32:091t |
| m02 | 11 includes, then Mailgun (as in g1) | 13 | 13:05 | 2026-10-29-13:01:28:724t |
| m15 | 25 includes, then Mailgun | 27 | 13:06 | 2026-10-29-13:01:31:371t |
| m13 | 15 includes, then Mailgun | 17 | 13:07 | 2026-10-29-13:01:29:557t |

m16 is as long as m15 (three 255-byte strings, a DNS answer over 512 bytes) but needs only Mailgun's
lookups: if a receiver refused it, the record's length and not the count would explain m13 to m15.

## Results

| Receivers | m01 (2) | m16 (2, long) | m02 (13) | m13 (17) | m14 (22) | m15 (27) |
|---|---|---|---|---|---|---|
| Gmail, Google Workspace (7) | accepted | accepted | accepted | accepted | 550 5.7.26 | 550 5.7.26 |
| Yahoo, AOL, AT&T (6) | accepted | accepted | accepted | accepted | 554 5.7.9 | 554 5.7.9 |
| Outlook, Hotmail (4) | accepted | accepted | 550 5.7.509 | 550 5.7.509 | 550 5.7.509 | 550 5.7.509 |
| Apple (1) | accepted | accepted | 554 5.7.1 | 554 5.7.1 | 554 5.7.1 | 554 5.7.1 |

- **Gmail and the Yahoo family accept 17 lookups and refuse 22**, at SMTP, on DMARC. Every seed of
  each provider gave the same answer. Their cutoff lies between 18 and 22; the cases don't narrow it
  further.
- **Microsoft and Apple refuse everything over 10**, as in g1.
- **m16 was accepted everywhere**, so the length of the record isn't what the others react to.
- **The receivers' own headers agree.** On m13 (17 lookups), the `Authentication-Results` written by
  Gmail (two seeds), Google Workspace, Yahoo, AOL and AT&T read `spf=pass` and `dmarc=pass`
  (checked in GlockApps' Header view on 2026-10-29).
- **Folders** were the same as g1's: Gmail and Workspace deliver to the inbox, the Yahoo family to
  spam, whether the record is broken or not (m01 and m16 too), so they say nothing about SPF here.

## Files

- `events.csv`: every Mailgun event for these messages, as in `results/g1` (`experiments/spf-mailgun/events_csv.py`).
  All refusals were permanent and immediate; no message was deferred.
- `dns.json`: the case records as public DNS (1.1.1.1) served them before sending.
- `glockapps.csv`: per case and provider group, where the message landed (placement only; GlockApps'
  per-seed SPF values are left out, see `results/r1`). The counts match each test's totals.
- `dmarc.csv`: the receivers' aggregate reports for the g2 mail (read 2026-10-30), from DMARKOFF
  (`experiments/spf-mailgun-limit/results_g2g3.py`). Google's day follows Pacific time, so this mail
  is in its 2026-10-29 report.

## DMARC aggregate reports

Google and Yahoo reported on 2026-10-30 for every case, except Yahoo for m15. Microsoft's reports
(Outlook.com, Microsoft 365) usually arrive about 36 hours after the day and weren't in yet.

- **Pass up to 17 lookups.** Google and Yahoo record SPF `pass` and DMARC `pass` for m01, m02, m13
  and m16.
- **The refusals at 22 and 27 show up as `reject`,** with different SPF labels: Yahoo records
  `permerror` for m14, Google records `fail` for m14 and m15. In g3, Google labels the same count
  `permerror` when the includes are nested (m20).
