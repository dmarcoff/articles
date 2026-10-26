# Run r2 (2026-10-23)

The second full run of the 13 SPF cases from 184.195.33.8, done the same way as r1: GlockApps
project 6, marker in `X-API-Campaign-id`, 3 s between recipients, two batches (the connector allows
10 tests an hour), the order shuffled with seed "r2", deferred messages retried 10 and 25 minutes
after each batch.

| Case | Sent (UTC) | GlockApps test |
|---|---|---|
| s02 | 08:02 | 2026-10-23-08:01:44:452t |
| s00 | 08:11 | 2026-10-23-08:01:45:584t |
| s11 | 08:18 | 2026-10-23-08:01:46:456t |
| s06 | 08:25 | 2026-10-23-08:01:47:217t |
| s09 | 08:32 | 2026-10-23-08:01:48:170t |
| s04 | 08:40 | 2026-10-23-08:01:49:101t |
| s12 | 08:47 | 2026-10-23-08:01:49:984t |
| s05 | 08:54 | 2026-10-23-08:01:51:106t |
| s08 | 09:02 | 2026-10-23-08:01:51:980t |
| s10 | 09:09 | 2026-10-23-08:01:52:860t |
| s03 | 09:28 | 2026-10-23-09:28:13:556t |
| s07 | 09:35 | 2026-10-23-09:28:14:390t |
| s01 | 09:43 | 2026-10-23-09:28:15:155t |

The seed list had 110 addresses in the first batch (GlockApps dropped one Gmail seed) and 112 in
the second (that seed back, plus a new rambler.ru seed). `smtp.csv`, `dns.json` and
`glockapps.csv` as in r1; `headers.md` keeps a Gmail seed's verdict on s02, and Libero's,
Virgilio's, Proton's and Yandex's on s02 and s11. `dmarc.csv` as in r1
(re-read 2026-10-25); Mail.ru sent no report for s01, s03, s07, s08 and s10 this time.

## Same as r1

Every receiver that evaluates SPF did in r2 what it did in r1, case for case: the table in
`results/r1/README.md` holds for both runs. About 59 seeds refused the IP itself in every case.
After the retries, the same receivers kept deferring: Interia for s09 and s12, ukr.net for s06
(`Temporary error during SPF verification`).

GlockApps placement repeats r1 too (see "Where the accepted messages went" in
`results/r1/README.md`); Gmail put a few more passing messages in the inbox this time, and a Gmail
seed's header for s02 reads `spf=pass` and `dmarc=pass` for the record that needs 11 lookups.

The cells that changed are all outside SPF:

- Virgilio rate-limited in r1 (`too many messages, slow down`) and didn't in r2.
- Interia refused all three s11 messages at RCPT (r1: two refused, one deferred).
- rambler.ru, new in the second batch, accepted s01, s03 and s07 from our IP.
- **Outlook and Hotmail let our PBL-listed IP through now and then**: one message each for r1's
  s01, s03 and s07, and two for r2's s09, where the rest of their seeds got the Spamhaus refusal.
  Where they did, r1's s11 got `5.7.509 Access denied … does not pass DMARC`, but r2's s09 (`ipv4:`)
  was accepted, and no bounce followed. **Outlook.com's DMARC report for 2026-10-23 settles it:
  both s09 messages `spf=pass`, DMARC `pass`. `ipv4:` is the only term that could match our IP, so
  Outlook.com reads it as `ip4:`.** Neither reached a
  seed, like every message Microsoft accepted from this IP. Through Mailgun (g1) Microsoft refused
  m09 (`includes:`) with 5.7.509 on every seed, so the leniency covers `ipv4:`, not unknown
  mechanisms in general.
