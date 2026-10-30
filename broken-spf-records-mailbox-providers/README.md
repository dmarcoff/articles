# Broken SPF records vs mailbox providers: data

Data behind the DMARKOFF blog article [What Mailbox Providers Really Do With Broken SPF Records: We Tested 21 of Them](https://dmarkoff.com/blog/broken-spf-records-mailbox-providers).

A follow-up article on the receivers' bounce codes, not published yet, reads the receivers' replies from the same `smtp.csv` and `events.csv`.

Between 21 and 23 October 2026 we sent about 3,800 test messages from 26 subdomains of `mailpath.io`, 13 SPF configurations on each of two sending paths, to GlockApps seed mailboxes at 21 mailbox providers and five spam filters. Every subdomain had `p=reject` and, except for one control per path, no aligned DKIM signature, so DMARC depended on SPF alone. This folder holds what we recorded: every SMTP reply, where each message landed, the authentication results in the seeds' headers, and the receivers' own DMARC aggregate reports.

## Quick start

You need Python 3.11 or later; there are no dependencies.

```bash
cd broken-spf-records-mailbox-providers
python3 summary.py
```

It prints, run by run, what each receiver did at SMTP with each case: `A` accepted (delivered, for the Mailgun run), `R` refused, `D` still deferred, with counts where recipients of the same receiver differed. The output is in [results/summary.txt](results/summary.txt).

```bash
python3 bounces.py
```

It prints the counts behind the follow-up article: direct-path messages by how they ended, with the SMTP step of every refusal, and Mailgun's failure reasons, late bounces and retries for the Mailgun run. The output is in [results/bounces.txt](results/bounces.txt).

## The cases

The records are defined in [cases/spf.yaml](cases/spf.yaml) (direct path, subdomains `s00` to `s12`) and [cases/spf-mailgun.yaml](cases/spf-mailgun.yaml) (Mailgun path, `m00` to `m12`). Case `mNN` mirrors `sNN`, with Mailgun's include, `include=`/`includes:` typos and `ptr:mailgun.net` in place of our address.

| Case | Record (direct path; our IP is 184.195.33.8) |
|---|---|
| s00 | `v=spf1 ip4:<IP> -all`, DKIM signed (control) |
| s01 | `v=spf1 ip4:<IP> -all` (control) |
| s02 | 11 includes, then `ip4:<IP>` |
| s03 | `ip4:<IP>`, then 11 includes |
| s04 | 3 void lookups (`a:` for missing hosts), then `ip4:<IP>` |
| s05 | 2 void lookups, then `ip4:<IP>` |
| s06 | include of a name without an SPF record, then `ip4:<IP>` |
| s07 | `ip4:<IP>`, then the include without a record |
| s08 | `ip4=<IP>` (unknown modifier) |
| s09 | `ipv4:<IP>` (unknown mechanism) |
| s10 | `ptr:mailpath.io` |
| s11 | two records: `v=spf1 ip4:<IP> -all` and `v=spf1 -all` |
| s12 | no record |

## The runs

| Run | Path | Date (UTC) | Cases | Seeds per case |
|---|---|---|---|---|
| [p1](results/p1/) | direct, from our AWS address (PTR `mta.mailpath.io`) | 2026-10-21 19:29–19:51 | s00–s02 | 111 |
| [r1](results/r1/) | direct | 2026-10-22 06:57–09:09 | s00–s12 | 110–111 |
| [r2](results/r2/) | direct | 2026-10-23 08:02–10:16 | s00–s12 | 110–112 |
| [g1](results/g1/) | Mailgun's US shared IPs | 2026-10-23 06:22–07:30 | m00–m12 | 44 |

Our AWS address was in Spamhaus PBL, so on the direct path about half the seeds refused it before evaluating SPF. The Mailgun run covers those receivers. Each run's `README.md` holds the notes we wrote during the experiment, with the GlockApps test ID of every case. Paths in them such as `runs/` or commands like `mailexp` refer to our private working repository, where the raw logs with seed addresses stay.

## Files per run

**`smtp.csv`** (direct runs): one row per delivery attempt.

| Column | Meaning |
|---|---|
| `time` | when the attempt ended, UTC |
| `case` | test case |
| `n` | recipient number within the case |
| `attempt` | 1 for the first try, higher for retries of temporary refusals |
| `rcpt_domain` | the recipient's domain (addresses are not published) |
| `dkim` | 1 if the message was DKIM signed |
| `mx`, `tls` | the server we delivered to and the TLS version |
| `stage` | `accepted`, or the SMTP stage that failed: `connect`, `ehlo`, `starttls`, `mail`, `rcpt`, `data` |
| `code`, `reply` | the receiver's SMTP reply |
| `duration_ms` | how long the attempt took |

**`events.csv`** (Mailgun run): Mailgun's delivery events, matched to cases by Message-ID. `event` is `accepted` (by Mailgun), `delivered` or `failed`; `severity` tells permanent from temporary failures; `reply` is the receiver's answer; `reason` is Mailgun's own classification (`espblock`, `generic`, or `old` when it gave up), `enhanced_code` the receiver's enhanced status code and `provider` Mailgun's name for the recipient's provider. Mailgun retried temporary failures for 8 hours, then gave up with `602 Too old`.

**`glockapps.csv`**: one row per case and GlockApps provider group: the number of seeds, how many landed in the inbox, another tab or spam, how many never arrived, and the SPF, DKIM and DMARC results GlockApps read from the delivered seeds' headers (`-` where the header had none; GlockApps doesn't parse Microsoft's and Yahoo's DMARC result, so those cells are empty even when DMARC passed). The SPF column is not the receiver's own verdict for Libero, Virgilio, Proton, T-Online, Vodafone and freenet: their headers have no `spf=` clause GlockApps reads (Libero and Virgilio write only `Received-SPF`, Proton uses separate Authentication-Results headers, the three German providers record no SPF result), and GlockApps shows a value of its own, which passes the 11-lookup record. The receivers' own results are in the run READMEs and the article. Five spam-filter seeds are counted by GlockApps' totals but not listed per group.

**`dmarc.csv`**: the receivers' aggregate reports for the run's mail, one row per reporter and distinct result: messages, disposition, DMARC result, SPF result and domain, DKIM results with `domain/selector`. `report_date` is the UTC date the report's window starts. Two reporters need care when you match reports to a run:

- Seznam's day runs 22:00 to 22:00 UTC, so its report for a day's mail is dated the day before.
- Google's reports state 00:00 to 23:59 UTC, but its day follows Pacific time: mail sent before 07:00 UTC is in the previous day's report. For g1 that's the cases sent before 07:00; their Google rows are dated 2026-10-22 and were told apart from the previous day's warm-up by the missing DKIM signature of the case domain. m00, signed like the warm-up, has no Google rows here.

Message counts in the reports are not message counts we sent: Google counts deferred attempts too, and Seznam's counts for passing mail are double what we sent. Quote the verdicts, not the counts.

**`dns.json`**: every record of the experiment as public DNS (1.1.1.1) served it right before the run.

**`headers.md`** (every run): excerpts of seed headers, with addresses reduced to their domain: Gmail's `spf=pass` for the 11-lookup record, Mailgun's own `d=mailgun.org` DKIM signature, and the SPF verdicts Libero, Virgilio, Proton, ukr.net, Amazon WorkMail, Yandex and Microsoft wrote themselves, including where GlockApps' summary shows a different value.

**`bounce-server.md`** (in `results/`): what our bounce server received during the direct runs: no DSN from any receiver.

**Mailgun extras** (g1): `bounce-classification.json` (Mailgun's bounce classification report for the 13 domains), `suppressions.csv` (the suppression lists, empty after the run) and `warmup-suppression.csv` (the one address that was suppressed, during the warm-up).

## Seed domains

Consumer mailbox domains (`gmail.com`, `outlook.com`, `yahoo.com` and so on) are published as they are. GlockApps' own seed domains are replaced with labels, in every file:

| Label | Seed type |
|---|---|
| `workspace-4y-a.seed.example`, `workspace-4y-b.seed.example` | Google Workspace (4 years+) |
| `workspace-new-a.seed.example`, `workspace-new-b.seed.example` | Google Workspace (up to 6 months) |
| `microsoft365-a.seed.example`, `microsoft365-b.seed.example` | Microsoft 365 (Exchange Online) |
| `workmail-a.seed.example`, `workmail-b.seed.example` | Amazon WorkMail |
| `barracuda-filter.seed.example` | Barracuda filter |
| `spamassassin-filter.seed.example` | SpamAssassin filter |
| `microsoft-eop-filter.seed.example` | Microsoft EOP filter |
| `proofpoint-filter.seed.example` | Proofpoint filter (delivers into Microsoft 365) |

`currently.com` is an AT&T consumer domain.

## Screenshots

[screenshots/](screenshots/) has the images used in both articles, with seed addresses hidden; its README says how each one was made.

## Caveats

- One or two seeds per mailbox type per case and run; every case ran three times, twice directly and once through Mailgun.
- Seed mailboxes are test accounts with their own history, so folders depend on reputation as much as on our records.
- 12 of the 21 providers sent no aggregate reports during the test.
- Receivers change their filtering without notice. This describes 21 to 23 October 2026.

## How to cite

The article:

> DMARKOFF. (2026, October 28). *What Mailbox Providers Really Do With Broken SPF Records: We Tested 21 of Them*. DMARKOFF blog. https://dmarkoff.com/blog/broken-spf-records-mailbox-providers

This folder:

> Markau, A., & DMARKOFF. (2026). *Broken SPF records vs mailbox providers: data* [Data set]. GitHub. https://github.com/dmarcoff/articles/tree/main/broken-spf-records-mailbox-providers

For licensing, see [License](../README.md#license) in the repository README.
