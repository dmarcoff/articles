# Mailgun run g5 (2026-11-02)

Does the `all` qualifier matter under `p=reject`? Microsoft's SPF setup guide says that DMARC counts
`-all` and `~all` as SPF failures, but "the DMARC policy is effectively ignored for SPF `~all`
failures" when the message has no DKIM signature. RFC 9989 counts SPF toward DMARC only when the
result is a `pass` on an aligned domain, so `fail`, `softfail` and `neutral` should all miss in the
same way.

The cases of `cases/spf-all-qualifier.yaml` differ only in the `all` qualifier, with `ip4:192.0.2.1`
in front of it, an address reserved for documentation that matches no sender. They were sent once
each through Mailgun's shared IPs, with DKIM off for our domains, to 45 GlockApps addresses: 42
mailboxes at 20 providers, the Barracuda and SpamAssassin filter seeds, and GlockApps' monitor, which
accepts every message. That is g1's list without its Proton seed, which GlockApps has removed, plus
one more Microsoft 365 mailbox. Each subdomain is the From and the MAIL FROM domain and publishes
`p=reject`. The records went live at 11:49:12 UTC and every domain stayed active in Mailgun throughout.

| Case | Record | Result for our sender | Sent (UTC) | GlockApps test |
|---|---|---|---|---|
| m22 | `v=spf1 ip4:192.0.2.1 ~all` | softfail | 11:54 | 2026-11-02-11:46:37:143t |
| m01 | `v=spf1 include:_spf.mailgun.org -all` | pass (control) | 11:57 | 2026-11-02-11:46:35:450t |
| m21 | `v=spf1 ip4:192.0.2.1 -all` | fail | 11:59 | 2026-11-02-11:46:36:348t |
| m23 | `v=spf1 ip4:192.0.2.1 ?all` | neutral | 12:02 | 2026-11-02-11:46:37:897t |

## Results

| Receiver (addresses) | m21 `-all` | m22 `~all` | m23 `?all` |
|---|---|---|---|
| Outlook.com, Hotmail (6) | 550 5.7.509 | 550 5.7.509 | 550 5.7.509 |
| Microsoft 365 (4, 2 of them behind filter seeds) | 250, then bounced 5.7.509 | same | same |
| Gmail, Google Workspace (6) | 550 5.7.26 | 550 5.7.26 | 550 5.7.26 |
| Yahoo, AOL, AT&T (5) | 554 5.7.9 | 554 5.7.9 | 554 5.7.9 |
| Apple (1) | 5.7.1 | 5.7.1 | 5.7.1 |
| GMX, WEB.DE, mail.com (4) | 554 | 554 | 554 |
| La Poste, Mail.ru, Zoho (1 each) | 5.7.1 | 5.7.1 | 5.7.1 |
| mailo (1) | 550 | 550 | 550 |
| Barracuda (filter) | 550 | 550 | 550 |
| Onet (1) | 550 5.7.23 at RCPT | 554 5.7.1 after DATA | 554 5.7.1 after DATA |
| Interia (1) | 550 5.7.1 at RCPT | 451 4.4.0 at RCPT, 7 times, then 602 Too old | same |
| Naver (1) | 550 5.7.1 | 250, not in the seed | 250, not in the seed |
| Yandex (1) | 250, spam | 550 5.7.1 | 550 5.7.1 |
| Seznam, Amazon WorkMail (1 each) | 250, not in the seed | same | same |
| Libero, Virgilio, ukr.net (1 each) | 250, spam | same | same |
| freenet (1) | 457 greylisted, then 250, spam | same | same |
| T-Online, Vodafone (1 each) | 250, inbox | 250, inbox | 250, inbox |

- **Microsoft refused `~all` as it refused `-all`.** Outlook.com and Hotmail answered with `550 5.7.509
  … does not pass DMARC verification and has a DMARC policy of reject` during the SMTP session for all
  three records. Microsoft 365 answered `250` and then returned each message with the same code.
- **No receiver refused `-all` and put `~all` or `?all` in a mailbox.** Without an aligned signature,
  16 of the 20 providers treated all three records the same. The other four are Onet, Interia, Naver
  and Yandex.
- **Three receivers cited SPF for `-all` and did something else with the other two:** Interia
  (`Rejected due to SPF`, then `Deferred due to SPF unsafe`), Onet (`SPF fail`, then a plain
  `Rejected`) and Naver (`Sender rejected because SPF check failed`, then `250` with nothing in the
  seed). Run g6 sent the same records signed to tell whether those refusals come before DKIM can count.
- **Yandex went the other way,** on one message per case: `-all` to spam, `~all` and `?all` refused
  with `Email rejected per DMARC policy`. In g1 it refused a `-all` failure (m08) with that code.
- **T-Online and Vodafone delivered all three to the inbox.** The mail came through Mailgun on verified
  domains. Both refused our own AWS address in r1 and r2. The headers of m21 at T-Online and m22 at
  Vodafone carry `dkim=none` and no SPF or DMARC result (GlockApps' Header view, 2026-11-04).
- **The control reached all 44 tracked seeds:** 30 inbox, 1 tab and 13 spam. Outlook.com, Hotmail, the
  Yahoo family, Apple and Yandex put even the control in spam, so a spam folder there says little about
  SPF.

## Files

- `events.csv`: every Mailgun event for these messages, as in `results/g1`, recipients reduced to
  their domain.
- `dns.json`: the case records as resolved before sending.
- `glockapps.csv` and `dmarc.csv`: GlockApps' results and the receivers' aggregate reports in
  DMARKOFF, both read on 2026-11-05 and written to CSV by a script in our private repository.

`glockapps.csv` holds GlockApps' per-group rows, which cover 39 of its 44 tracked seeds. The other five
are one Google Workspace seed and the Microsoft EOP, Proofpoint, Barracuda and SpamAssassin filter seeds.
Their SMTP answers are in `events.csv`. GlockApps' own totals for m21 to m23 count a third inbox, which
is the SpamAssassin filter seed: it accepts every message.

## DMARC aggregate reports

Read in DMARKOFF on 2026-11-05. La Poste sent no report for this run. Its reports usually come about
six days after the mail (here by about 11:30 UTC on 2026-11-09), and none had arrived by 14:05 UTC on
2026-11-10, nor for g4 or g7. The newest window it reported for any of our domains ends on 2026-10-23
(g1), and DMARKOFF dropped none of its reports on arrival.

| Reporter (messages per case) | m01 | m21 `-all` | m22 `~all` | m23 `?all` |
|---|---|---|---|---|
| Google (6) | pass, none | fail, reject | softfail, reject | neutral, reject |
| Yahoo Mail (5) | pass, none | fail, reject | softfail, reject | neutral, reject |
| Outlook.com (6) | pass, none | fail, reject | softfail, reject | neutral, reject (5 of 6) |
| Microsoft 365 (4) | pass, none | fail, reject | softfail, reject | neutral, reject |
| GMX Mail (2) | pass, none | fail, reject (1 of 2) | softfail, reject | neutral, reject |
| WEB.DE Mail, mail.com, Mail.ru, Seznam.cz, Zoho (1 each) | pass, none | fail, reject | softfail, reject | neutral, reject |
| Interia (1) | pass, none | no row | no row | no row |
| La Poste (1) | no report | no report | no report | no report |

- **DMARC failed on every failing record, and no row carries a policy override or a comment.**
- **Microsoft's reports have no DKIM entry for these domains,** so its mailboxes saw what its note
  describes: an SPF softfail with no DKIM signature. Zoho's have none either. All of Yahoo's rows and
  half of Google's carry Mailgun's own `d=mailgun.org` signature with a `pass`, which doesn't align.
- **Interia reported only the control,** having answered the other three at RCPT.
- **Seznam answered `250` to all three and reported them as `reject`.** They didn't reach the seed.
- **Dates.** Every report is dated 2026-11-02 except two. Seznam's window starts at midnight Prague
  time, 23:00 UTC on 2026-11-01. Zoho's window ends at 08:00 UTC on 2026-11-02, before this mail was
  sent, as in g1 and g4.
