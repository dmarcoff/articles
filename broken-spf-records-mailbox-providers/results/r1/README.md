# Run r1 (2026-10-22)

All 13 SPF cases, sent once each from 184.195.33.8 to the GlockApps seeds (project 6), marker in
`X-API-Campaign-id`, 3 s between recipients. The connector creates at most 10 tests an hour, so the
run went in two batches, each with a control; the order inside a batch was shuffled (seed "r1").

| Case | Record (our IP = 184.195.33.8) | Sent (UTC) | GlockApps test |
|---|---|---|---|
| s02 | 11 includes, then `ip4` | 06:57 | 2026-10-22-06:56:09:140t |
| s12 | no record | 07:05 | 2026-10-22-06:56:09:875t |
| s04 | 3 void lookups, then `ip4` | 07:12 | 2026-10-22-06:56:10:682t |
| s03 | `ip4`, then 11 includes | 07:19 | 2026-10-22-06:56:11:854t |
| s08 | `ip4=` (unknown modifier) | 07:26 | 2026-10-22-06:56:12:891t |
| s09 | `ipv4:` (unknown mechanism) | 07:33 | 2026-10-22-06:56:13:659t |
| s07 | `ip4`, then an include with no record | 07:40 | 2026-10-22-06:56:14:987t |
| s05 | 2 void lookups, then `ip4` | 07:48 | 2026-10-22-06:56:15:953t |
| s10 | `ptr:mailpath.io` | 07:55 | 2026-10-22-06:56:17:175t |
| s00 | `ip4`, DKIM signed (control) | 08:02 | 2026-10-22-06:56:18:104t |
| s11 | two records | 08:21 | 2026-10-22-08:20:39:805t |
| s06 | include with no record, then `ip4` | 08:28 | 2026-10-22-08:20:40:574t |
| s01 | `ip4` (control) | 08:36 | 2026-10-22-08:20:41:424t |

The seed list had 110 addresses for the first batch and 111 for the second (GlockApps briefly
dropped one Hotmail seed). Deferred messages were retried up to five times, 10 to 80 minutes apart; the
12 still deferred after that are receivers that keep deferring (below).

## Files

- `smtp.csv`: every delivery attempt with the receiver's reply, recipients reduced to their domain
  (`mailexp report --log runs/r1/send.jsonl --csv results/r1/smtp.csv`).
- `dns.json`: what public DNS served for every record right before the run.
- `headers.md`: seed header excerpts for s02 and s11 at Libero, Virgilio, Proton and Yandex.

- `glockapps.csv`: per case and provider group, the seeds, where the message landed (inbox, other
  tab, spam, not delivered) and the SPF, DKIM and DMARC results GlockApps read from the seeds'
  headers. Its DMARC column is empty for Microsoft and Yahoo even when they passed: GlockApps
  doesn't parse their header format. Its SPF column isn't always the receiver's verdict either.
  Libero and Virgilio write only `Received-SPF`, Proton puts SPF and DMARC in separate
  Authentication-Results headers, and T-Online, vodafone and freenet record no SPF result at all;
  for them GlockApps shows a value of its own, which passes s02 (11 lookups) and gave s11 (two
  records) `pass` in this run and `permerror` in r2. The receivers' own results are in the text below.

## What the receivers did at SMTP

About 58 seeds in every case refused the IP itself (Spamhaus PBL and the receivers' own lists, as in
p1): Microsoft, Yahoo/AOL/att, Apple, GMX/web.de/mail.com, freenet, T-Online, vodafone, Zoho, Amazon
WorkMail. They never evaluate SPF and are left out below.

GlockApps' "Spam Filter Check" seeds sit behind filters: Barracuda, SpamAssassin, Google's filter,
Microsoft EOP and Proofpoint. In this copy their domains, like those of GlockApps' own Google
Workspace, Microsoft 365 and WorkMail seeds, are replaced with `*.seed.example` labels.

All the others accepted both controls (s00, s01) and the cases that match before reaching the problem
(s03, s05, s07). For the rest, ✓ accepted, ✗ refused, ⏸ kept deferring:

| Receiver | s02 lookups | s04 voids | s06 include, no record | s08 `ip4=` | s09 `ipv4:` | s10 ptr | s11 two records | s12 none |
|---|---|---|---|---|---|---|---|---|
| Gmail, Google Workspace | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| Mail.ru, Laposte, naver, mailo | ✗ | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| Yandex | ✗ | ✓ | ✗ | ✗ | ✗ | ✓ | ✓ | ✗ |
| Onet | ✗ | ✗ | ✗ | ✗ at RCPT | ✗ | ✓ | ✗ | ✗ |
| Interia | ✗ at RCPT | ✓ | ✗ at RCPT | ✗ at RCPT | ⏸ | ✓ | ✗ / ⏸ | ⏸ |
| Barracuda filter (barracuda-filter.seed.example seed) | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| ukr.net | ✓ | ✓ | ⏸ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Seznam, Libero, Virgilio, Proton | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

Refusals after DATA are DMARC (`p=reject`) rejections, or quote the SPF result. Interia refuses at
RCPT with `Rejected due to SPF with invalid content` and defers s09 and s12 "due to policy";
ukr.net defers s06 with `451 4.1.0 Temporary error during SPF verification`, treating a missing
include target as a temporary error rather than the permerror RFC 7208 5.2 calls for.

What it says so far:

- **The 10-lookup limit (s02)** is enforced by Mail.ru, Yandex, Laposte, Onet, Interia, naver and
  mailo, and not by Gmail or Google Workspace: the same split as in p1.
- **The void-lookup limit (s04)** is enforced by Onet and by the Barracuda filter seed only.
- **An include without a record (s06)** is refused by everyone who refuses anything, Gmail included.
- **Two records (s11)**: Yandex accepts; the others refuse.
- **ptr (s10)** passes everywhere; our PTR is forward-confirmed.
- **Seznam, Libero, Virgilio, Proton and ukr.net accept even s08 and s12**, whose SPF can't pass:
  they don't act on `p=reject` at SMTP, so their verdicts must come from the seeds' own headers and
  DMARC reports.

## Where the accepted messages went (GlockApps)

The folder follows reputation, not SPF, at the large receivers: Gmail and Google Workspace put
every passing case in spam, controls included (a new IP and new domains), and Yandex did the same.
Seznam put everything in spam except the DKIM-signed control.

The receivers that accept everything at SMTP deal with a failing record in three ways:

- **Seznam drops it silently.** s06, s08, s09, s11 and s12 were accepted at SMTP and never reached
  a seed; Seznam's DMARC reports give their disposition as `reject`.
- **Italiaonline (Libero, Virgilio) and Proton put it in spam.** Both also put s02 in spam, and
  their own headers say why: Libero and Virgilio `Received-SPF: permerror`, Proton `spf=fail` and
  `dmarc=fail`. They enforce the lookup limit; the `pass` in GlockApps' SPF column is GlockApps'
  own value (checked against the raw headers on 2026-10-25).
- **ukr.net puts it in spam with an accurate SPF result.** It reports `permerror` for s04 (three
  void lookups) and `fail` for s10 (ptr): the only receiver here that applies the void limit
  without refusing, and the only one where ptr fails.

For s11 (two records) Yandex delivered with `spf=pass`, in both runs. Italiaonline and Proton failed
it in both runs (Libero and Virgilio `Received-SPF: permerror`, Proton `spf=fail`) and put it in
spam; GlockApps' SPF column, which says `pass` here and `permerror` in r2, is its own value.

## DMARC aggregate reports

`dmarc.csv`, re-read from DMARKOFF on 2026-10-25: Google, Seznam, Mail.ru, Interia and Outlook.com
reported; Zoho's report for one s02 message (`permerror`, `reject`) arrived on 2026-10-25, 57 hours
after its 07:00–07:00 UTC window, and was added on 2026-10-26. `report_date` is the date DMARKOFF gives the report: the UTC date its window starts. Seznam's
window runs 22:00–22:00 UTC, so its report for a day's mail is dated the day before. Google's
report says 00:00–23:59 UTC but follows Pacific time: mail sent before 07:00 UTC lands in the
previous day's report. Messages refused at RCPT or never accepted (Interia's
s02, s06, s08, s09, s12) never reach DMARC evaluation and are absent from reports; only the SMTP log
has them. r2's reports give the same verdict for every receiver and case.

- **The lookup limit (s02):** Google and Seznam `pass`, Mail.ru `permerror` and `reject`.
- **Errors are labelled differently.** For the include without a record (s06) everyone says
  `permerror`. For `ipv4:` (s09) Google says `fail`, Mail.ru `none` (as if there were no record)
  and Seznam `permerror`. For two records (s11) Google, Interia and Outlook.com say `fail`, Mail.ru
  and Seznam `permerror`. `ip4=` (s08) is `fail` and no record (s12) `none` everywhere, as the RFC
  expects.
- **Seznam gives `reject` as the disposition for every failing case,** although it accepted all of
  them at SMTP: the report is the only place its silent drop shows.
- **Outlook.com** reported the one message each of s01, s03 and s07 it accepted from our IP as
  passing, and none of them reached a seed: Microsoft drops what it lets through from this IP.
