# Mailgun run g7 (2026-11-06)

Two SPF records that both list a real sender, in both orders. g1's two-record case (m11) paired our
sender's record with `v=spf1 -all`, which DNS returned first, so a `fail` from Google or Interia could
mean either that they read only the first record or that `fail` is how they label any domain with two
records. Here both records end in `~all`, so every label says which record was read: `pass` is the
record listing Mailgun, `softfail` the record listing Google, `permerror` neither (RFC 7208 §4.5), and
`fail` comes from neither record, so it can only be a label for the two-record state.

The cases are in `cases/spf-two-records.yaml`. They were sent once each through Mailgun's
shared IPs, with DKIM off for our domains, to the 45 GlockApps addresses of g5: 42 mailboxes at 20
providers, the Barracuda and SpamAssassin filter seeds, and GlockApps' monitor, which accepts every
message. Each subdomain is the From and the MAIL FROM domain and publishes `p=reject`. These names live
in cx.mailpath.io, where our own authoritative server (authdns) answers in the order of the zone file
and logs every query; Route 53 doesn't keep the order of a change batch. The records went live at
07:27:39 UTC and every domain stayed active in Mailgun throughout. c01, c03 and c04 are g4's domains
reused; g4's mail is from 2026-10-31, so the reports don't overlap.

| Case | Records | Sent (UTC) | GlockApps test |
|---|---|---|---|
| c04 | `v=spf1 include:_spf.google.com ~all`, then `v=spf1 include:_spf.mailgun.org ~all` | 07:33 | 2026-11-06-07:26:42:306t |
| c01 | `v=spf1 include:_spf.mailgun.org include:_spf.google.com ~all` (control) | 07:34 | 2026-11-06-07:26:40:810t |
| c03 | `v=spf1 include:_spf.mailgun.org ~all`, then `v=spf1 include:_spf.google.com ~all` | 07:35 | 2026-11-06-07:26:41:614t |

## Record order

authdns answered every TXT query for c03 and c04 from the switch to 07:37:33 UTC, when the log was
copied, in zone order: 93 queries for c03 and 94 for c04, Google's, Microsoft's and Yahoo's resolvers
among them. Public resolvers don't keep it. Ten queries each on 2026-11-06 (M = the Mailgun record first,
G = the Google record first):

| Resolver | c03 | c04 |
|---|---|---|
| 1.1.1.1 | MMMMMMMMMM | GGGGGGGGGG |
| 8.8.8.8 | MMGGGMGGGG | GMMMGGGMGG |
| 9.9.9.9 | MGMMMGGMMM | MGMMGMMMMG |
| 208.67.222.222 | GGGGGGGGGG | GGGGGGGGGG |
| 77.88.8.8 | GGMMGMMGGG | GMGMMGMMGG |

So the order a receiver's SPF code saw is known only up to its resolver: what our server sent it.

## Results

| Receiver (addresses) | c01 merged | c03 ours first | c04 ours second |
|---|---|---|---|
| Gmail, Google Workspace (6) | 250, inbox | 250, inbox | 550 5.7.26 |
| Outlook.com, Hotmail (6) | 250, spam | 250, spam | Hotmail 2 and Outlook.com 1: 250, spam; Outlook.com 1, .de, .fr: 550 5.7.509 |
| Microsoft 365 (4, 2 of them behind filter seeds) | 250 | 250, then 1 bounced 5.7.509 | 250, then 2 bounced 5.7.509 |
| Yahoo, AOL, AT&T (5) | 250, spam | 554 5.7.9 | 554 5.7.9 |
| Apple (1) | 250, spam | 554 5.7.1 | 554 5.7.1 |
| GMX, WEB.DE, mail.com (4) | 250, inbox | 554 | 554 |
| La Poste, Mail.ru, Zoho (1 each) | 250, inbox | 550 5.7.1 | 550 5.7.1 |
| Onet (1) | 250, inbox | 554 5.7.1 | 554 5.7.1 |
| mailo (1) | 250, inbox | 550 | 550 |
| Barracuda (filter) | 250 | 550 | 250 |
| Interia (1) | 250, Offers tab | 451 4.5.1 and 451 4.4.0, 7 attempts, then 602 Too old | same |
| Seznam, Naver (1 each) | 250, inbox | 250, not in the seed | 250, not in the seed |
| Yandex (1) | 250, spam | 250, spam, `spf=softfail` | 250, spam, `spf=pass` |
| ukr.net, Libero, Virgilio (1 each) | 250, inbox | 250, spam | 250, spam |
| freenet (1) | 250, inbox | 457 greylisted, then 250, spam | same |
| Amazon WorkMail (1) | 250, inbox | 250, inbox, `spf=permerror`, `dmarc=temperror` | same |
| T-Online, Vodafone (1 each) | 250, inbox | 250, inbox | 250, inbox |

- **Gmail and Google Workspace followed the order,** 6 of 6 each way: c03 delivered to the inbox with
  `spf=pass` and `dmarc=pass` (headers), c04 refused with `5.7.26`. Google's resolvers asked for the TXT
  record once per message.
- **Microsoft's answer changed from message to message:** 9 of 10 delivered with our record first and
  5 of 10 with it second, every refusal and bounce `5.7.509`. In c04, one Outlook.com seed took the
  message and the other refused it; both Hotmail seeds took it.
- **Most receivers refused both orders:** the Yahoo family, Apple, GMX, WEB.DE, mail.com, La Poste,
  Mail.ru, Zoho, Onet and mailo, 15 seeds that all took the control. No order dependence there.
- **Interia never accepted either order.** Seven attempts each, `451 4.5.1 Message deferred due to
  policy reasons` and `451 4.4.0 Deferred due to SPF unsafe` in no fixed order (c03: 4.5.1, 4.4.0,
  4.5.1, 4.5.1, 4.4.0, 4.4.0, 4.4.0; c04: 4.4.0, 4.5.1, 4.4.0, 4.4.0, 4.5.1, 4.5.1, 4.4.0), until
  Mailgun gave up at 15:38 (c04) and 15:40 (c03).
- **Seznam and Naver answered `250` and dropped both:** nothing in the seeds by 2026-11-08, no bounce.
- **Yandex and Barracuda each split the pair the other way from Google,** on one message per case.
  Yandex's `softfail` for c03 and `pass` for c04 are the results of the second record in our server's
  order. Barracuda refused c03 and delivered c04.
- **ukr.net was the one receiver that named the cause** (`multiple SPF records provided by …`, headers).
  Amazon WorkMail delivered both to the inbox with `spf=permerror` and `dmarc=temperror`.
- **The control reached all 44 tracked seeds:** 30 inbox, 1 tab and 13 spam, as in g5.

## Files

- `events.csv`: every Mailgun event for these messages (export of 2026-11-07 12:08 UTC, 289 events), as
  in `results/g1`, recipients reduced to their domain.
- `dns.json`: the case records as resolved before sending.
- `headers.md`: excerpts of the delivered copies' headers, read in GlockApps' Header view on 2026-11-06.
- `glockapps.csv` and `dmarc.csv`: GlockApps' results, read on 2026-11-08, and the receivers' aggregate
  reports in DMARKOFF (below), written to CSV by a script in our private repository.

`glockapps.csv` holds GlockApps' per-group rows, which cover 39 of its 44 tracked seeds, as in g5: the
other five are one Google Workspace seed and the Microsoft EOP, Proofpoint, Barracuda and SpamAssassin
filter seeds. Their SMTP answers are in `events.csv`. GlockApps still lists c03 and c04 as unfinished,
because some seeds never got the message.

## DMARC aggregate reports

Read in DMARKOFF on 2026-11-07, 2026-11-08 and 2026-11-09 (Microsoft's arrived 2026-11-08, 27 to 36
hours after their window closed).

| Reporter (messages per case) | c01 | c03 ours first | c04 ours second |
|---|---|---|---|
| Google (6) | pass, none | pass, none | softfail, reject |
| Outlook.com (6) | pass, none | pass, none | 3 pass, none; 3 softfail, reject |
| Microsoft 365 (4) | pass, none | 3 pass, none; 1 softfail, reject | 2 pass, none; 2 softfail, reject |
| Interia (1, then 3 per two-record case) | pass, none | fail, reject | fail, reject |
| Yahoo Mail (5) | pass, none | permerror, reject | permerror, reject |
| GMX Mail (2) | pass, none | permerror, reject | permerror, reject |
| WEB.DE Mail, mail.com, Seznam.cz, Zoho (1 each) | pass, none | permerror, reject | permerror, reject |

- **Google evaluated only the first record our server returned.** c04's `softfail` is the `~all` of
  `v=spf1 include:_spf.google.com ~all`, first in c04; c03's `pass` is our record, first in c03. A label
  for two records would have been the same in both. That fits m11 in g1 too, where Google's `fail` is
  the result of `v=spf1 -all`, which came first. Google's two rows per case differ only in whether
  Mailgun's unaligned `d=mailgun.org` signature was added.
- **Microsoft evaluated one of the two records for each message, and never returned `permerror`.**
  Its counts match the SMTP side one to one: every delivered message is a `pass`, every refused or
  bounced one a `softfail`, the result of the Google record. The reports don't tie rows to messages, so
  this is a count match. Since our server sent every resolver the records in zone order, whatever made
  Microsoft use the second record happened on its side. If it picked a record at random for each
  message, 9 or more passes out of 10 in c03 would happen about once in a hundred tries, so the order
  probably weighs in without deciding; ten messages per order can't settle it.
- **Interia wrote `fail` for both orders,** although neither record can fail our sender: both end in
  `~all`. So `fail` is Interia's label for a domain with two records, as in g1. Its 3 messages per case
  match the three `451 4.5.1` deferrals among the seven attempts (c03 attempts 1, 3, 4; c04 attempts 2,
  5, 6); the `451 4.4.0` ones aren't counted. A count match as well.
- **Yahoo, GMX, WEB.DE, mail.com, Seznam and Zoho wrote `permerror` for both orders,** as RFC 7208
  §4.5 says. Seznam's rows confirm the silent drop: `250` at SMTP, nothing in the seed, `reject` in the
  report.
- **No row carries a policy override or a comment.** Microsoft's reports have no DKIM entry for these
  domains. All of Yahoo's rows and half of Google's carry Mailgun's own `d=mailgun.org` signature with a
  `pass`, which doesn't align.
- **Dates.** Google's window is its Pacific day and is filed under 2026-11-05, as is Seznam's, which
  starts at midnight Prague time, 23:00 UTC on 2026-11-05. Zoho's is filed under 2026-11-04: its
  window ends at 08:00 UTC on 2026-11-05, before this mail was sent, as in g1, g4 and g5, and it arrived
  2026-11-06 22:53 UTC. The others are dated 2026-11-06.
- **Not received by 2026-11-09.** Mail.ru sent no report for any of the three domains, the control
  included, so it isn't about two records; it reported g4 on these domains (window ending 2026-11-01).
  La Poste's reports usually come about six days after the mail, here about 2026-11-12. We stopped
  waiting on 2026-11-10: it sent none for g4 or g5, and the newest window it reported for any of our
  domains ends on 2026-10-23 (g1). Naver, Apple, Yandex, Onet, mailo, ukr.net, Libero, Virgilio, freenet,
  T-Online, Vodafone and WorkMail sent none in g1 or g5 either.
